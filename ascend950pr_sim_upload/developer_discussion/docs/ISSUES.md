# 已解决问题与遗留问题

关于 WAIT 只有 1 tick 和重复 ID 插入，请先读 [helper 两个现象的完整说明](HELPER_TWO_ISSUES.md)：包含数据来源、具体记录、影响及需要确认的设计语义。

## 数值结果

最终验证文件位于 `../results/{megamoe,dispatch}/validation.json`，输入、输出、golden 均在相应 case 中。

Dispatch 原参考例的首 token 存在重复 expert ID，导致路由槽覆盖及空输出行。保留原例失败输入/输出于 `../evidence/dispatch_duplicate_experts/case`。最终 case 修正 token 内 expert ID 唯一性，并用非零 FP16 输入核对量化结果、scale、路由、专家分组及计数，已通过。这不是改 kernel 掩盖错误。

MegaMoE 最初零权重例只能证明通路，最终保留的是非零输入、非零稀疏 FP8 权重和跨卡路由例。两卡全部 BF16 输出逐位正确。core0 的 20 个 MMAD_MX 与 core1 的 4 个来自当前 GMM1/GMM2 的任务分配，不是缺采 16 个 MMAD：GMM1 的 16 个在 core0，GMM2 两核各 4 个。

## 已处理的环境/流程问题

- Conda 的 SQLite 连接没有启用 URI，而 npusim 报告代码使用 file URI 只读挂库。`report_with_sqlite_uri.py` 在报告进程中启用 uri=True，保持只读，不改 SQLite 或 CANN 安装文件。现在推荐的原生 msprof 路线不使用 helper DB，不需要此包装。
- 输出必须通过 task 根层 ast_output_array 配置，并预先创建目标文件。MegaMoE y 为 BF16，不能按 FP16 解码。
- MIX 要有 AIC/AIV 两个入口、正确共享参数地址、与 tiling 匹配的 block 数；仅有 top.json 拓扑不能运行 kernel。
- 不同版本 context 结构不同，Dispatch 的 576 字节 context 不能直接用于 MegaMoE 的 16400 字节 Mc2MoeContext；权重采用 TensorList 描述符，不能直接填裸数组地址。
- kernel tiling key 是模板枚举编码，本分支为 0，不是直接拼接属性所得的 52。
- ACLNN 507035 的独立问题是 aclCreateTensor 收到 `&devX` 而非设备指针 `devX`；详情及成功日志在 `../references/aclnn_507035`。它与多卡仿真采集问题无关。

## 采集器问题仍未修复

每次都使用全新数据库，quick_check 为 ok，但仍有 UNIQUE constraint failed。因此不是历史脏数据，也不应靠清库、关闭唯一约束或忽略 INSERT 消除。

| 最终用例 | 两卡重复插入错误总数 | 每卡可用唯一 raw 起止修正的记录 | 每卡仍有歧义的重复记录 |
| --- | --- | --- | --- |
| MegaMoE | 866 | 401 | 32 |
| Dispatch | 2312 | 1156 | 0 |

旧 npusim helper 路线只在新副本修正确定区间，逐条清单在 timing_repair_manifest.json；原始 DB 和二进制未改。原生 msprof 报告绕开该数据库，但并不修复 helper 本身。

另已确认 helper 在 finalize 时把零时长同步指令的 start 减 1 tick。MegaMoE 每卡日志记录归一化 792 条，DB 中全部 SET/WAIT 都成为 1 tick。这不是恢复原始 WAIT 区间，也不是删除所有零时长指令。证据见 `../evidence/helper_zero_duration`，与重复主键及未配对阶段分开记录。

原始阶段也不完全对称：MegaMoE 每卡 pending_start/end 为 156/142；Dispatch 为 791/2513。raw_pairing.json 将它们全部分解到 BAR、GET_BUF、RLS_BUF、RV_SEND、RV_SMEM_BAR。部分只有结束事件，部分是一条指令的多流水线阶段；不能简单称为同等数量的完整指令丢失，也不能凭空补开始时间。

需开发人员确认：helper 是否将提前阶段和完成阶段映射到同一主键；多阶段数量不等属于模型协议还是缺陷；是否有匹配此 weekly 的修正版或官方配对规则。证据是 results 中的原始 helper 日志、duplicate_audit.json、raw_pairing.json。

## 字段与展示

用户给出的 latency=1 已纳入最终 MegaMoE case。schem、latency、icache prefetch 键的读取已静态核实；dcache prefetch 和 task_type 在此版本未确认读取。见 TASK_FIELDS.md。

原生报告参数、两空格分隔问题、未开放的 CORE_SIM_CFG 配置入口以及与旧适配器的差异见 NATIVE_REPORT.md。推荐文件通过同步原始数据/Insight SQL 核对；普通指令的全部多阶段时间、完整 GUI 交互、真实硬件性能和所有 tiling 分支不属于本次已完成验收。
