# 950PR 离线 task 字段核对

核对版本：CANN 9.2.0-weekly.20260902.01，2026-09-08。
用户最后确认补充 `latency:1`；本轮非零 MegaMoE 用例已包含。

| 字段 | 非零小用例值 | 核对结论 |
| --- | --- | --- |
| sqe_type / mix / ratio | AIC / 1 / 2 | MIX 的 Cube 主入口和两个 Vector 子核配置；已有完整执行证据 |
| block_dim / group_dim | 2 / 1 | 本用例使用 2 Cube + 4 Vector；用户原例为 block_dim=32，不能只改此字段而不改 tiling |
| hbm_para_addr / sub_hbm_para_addr | chip0 均 0x8100000000 | 主、副入口共用参数表；chip1 加 0x10000000000 |
| group_slice | 32 | 本轮按用户给值；先前零权重成功例为 16 |
| schem | 1 | 本地模型确实读取此拼写；不是 scheme。缺省读取路径为 0 |
| aic_icache_prefetch_cnt | 0 | 本地模型读取；缺省 0 |
| aiv_icache_prefetch_cnt | 0 | 本地模型读取；缺省 0。用户最初的 aiv_icache_prefetch 缺少 _cnt |
| aic_dcache_prefetch_cnt / aiv_dcache_prefetch_cnt | 64 / 64 | 保留用户给值；本地 libstars_wrapper.so 未找到相应键或读取路径，不能声称生效 |
| task_type | 6 | 同上，未确认当前版本读取此键 |
| latency | 1 | construct_aic_sqe 确实读取并存入任务相关 map；缺省 0，单位及调度语义仍需开发者确认 |
| BIN | name / addr / sub_name / sub_addr | 对应 AIC / AIV 二进制文件与装载地址，四字段足够表达该 MIX 镜像 |

静态证据来自安装目录 `x86_64-linux/simulator/dav_3510/camodel/libstars_wrapper.so`，
完整反汇编保存在 `../evidence/task_fields/stars_full_disasm.txt`。字符串构造及调用引用对应：

| 键 | 字符串只读地址 | 全局字符串对象 | 读取调用位置（举例） |
| --- | --- | --- | --- |
| aic_icache_prefetch_cnt | 0xb68e6 | 0xe0128 | 0x59ab9 |
| aiv_icache_prefetch_cnt | 0xb68fe | 0xe0120 | 0x59af1 |
| schem | 0xb6916 | 0xe0118 | 0x59b29 |
| latency | 0xb6972 | 0xe00a0 | 0x5d422 |

以上是此二进制版本的证据，不能外推所有 CANN 版本。JSON 能正常解析不等于每个键都被读取。
无需为了这些字段改 SQLite、报告工具源码或 CANN 安装文件。

曾尝试用 `LD_PRELOAD` 拦截 ConfigTable getter 做诊断，但拦截函数 ABI 不匹配，
造成独立运行 `run_mOWo7j` 初始化期 SIGSEGV，未进入 kernel。
已撤出后续运行；该失败不能用于判断算子正确性。反汇编显示 getter 有隐藏返回对象参数，
不能把 `optional<unsigned>` 简化成 uint64 返回值。
