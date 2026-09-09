# 从 kernel 到完整双卡 case

先查已验证的配套归档和当前仓库真实样例；适配已有完整样例通常比从文档猜字段可靠。当前 MegaMoE 来自 ops-transformer，具体提交在归档 PROVENANCE.json。不要用普通单卡 runtime app 的设备选择方式代替 offline 多卡 case。

完整链条是 top.json → 每卡 sq_top.json → SQ 描述 → task.json → BIN、输入输出参数和内存镜像。top 中 case_path 需要绝对路径并以 / 结尾，sq_file 必须存在。

本次 MegaMoE 使用 AIC MIX：sqe_type=AIC、mix=1、ratio=2、block_dim=2、group_dim=1、group_slice=32。用户参考例 block_dim=32；改核数必须同步改 tiling 的 aicNum/blockAivNum/blockNumPerEP 等，不能只改 task。

BIN 四键 name/addr/sub_name/sub_addr 分别描述 AIC/AIV。Cube/Vector 共享参数表：chip0 的 hbm_para_addr 与 sub_hbm_para_addr 均为0x8100000000。chip1 地址按本例加0x10000000000。必须根据模型地址布局核对，不把它推广成任意型号常量。

MegaMoE 的关键构造：

- 使用该源码版本16400字节的 Mc2MoeContext；Dispatch参考例576字节不能直接复用。每卡窗口从0x8000000000开始，kernel内部加60KiB。
- 23个参数槽：context=0、x=1、ids=2、topkWeights=3、weights/scales=4..7、y=19、counts=20、workspace=21、tiling=22；当前分支未用的可选参数留空。
- weights需要TensorList描述符，不是裸数组；本例首uint64为指针表偏移8，下一uint64为数据地址。
- ELF的AIC/AIV入口不同，含.data全局窗口指针。生成器保留相对布局，不能只截一段.text就假定可执行。
- 当前编译分支tiling key为模板枚举0，不是直接拼接属性所得的52。
- task根层ast_output_array配置输出，并先创建文件；本版write_bin依赖realpath，文件不存在会跳过。y按BF16解码。
- schem确有此拼写；aiv_icache_prefetch_cnt需_cnt后缀；latency=1在最终case中。dcache prefetch/task_type是否被该weekly读取未确认，JSON能解析不能证明生效。

生成脚本已随技能提供：build_tiling_fixture.py + tiling_fixture_main.inc 需要匹配的host源码构建树；generate_mega_case.py需要ELF和tiling；prepare_nontrivial_mega.py通过--source读取前者输出后生成非零输入。先读各脚本--help，使用新目录。ELF/tiling现成实例在配套归档references/rebuild中。本流程未验证在任意全新机器上一键编译，不应承诺完全自包含。

Dispatch参考输入曾含token内重复expert ID，造成空输出行；最终非平凡例使用每token内唯一expert ID。该输入问题与数据库执行记录重复ID无关。
