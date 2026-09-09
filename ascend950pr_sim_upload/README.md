# MegaMoE 双卡 Insight 流水

在 MindStudio Insight 中打开 [megamoe_insight.json](megamoe_insight.json)，只需这一个文件（约 27.7 MB）。

950PR，双卡；从两卡原始 instr.bin 还原模型文本，由一次原生 msprof 导出。未修改 JSON 的配色、名称、时长或连线，也未移动两卡时间轴。

| 卡 | 文件中的原生核号 | MMAD 数量 |
| --- | --- | --- |
| chip0 | core0 / core1 | 20 / 4 |
| chip1 | core32 / core33 | 20 / 4 |

每个核包含 cubecore0、veccore0、veccore1。共 48 条 MMAD、1504 条 SET/WAIT、752 对同步关系。指令及同步切片与此前逐卡原生结果一致；同步参数和结束时间与原始记录一致，官方 Insight 处理函数及 SQL 关联检查通过。这不等同于再次完整 GUI 验收或全量指令无损保证。

非平凡用例：BS=16、H=1024、hidden=512、topK=1，每卡一个专家；非零 BF16 输入、稀疏 FP8 权重、跨卡路由和不同路由权重。每卡 16384 个 BF16 输出与 CPU golden 逐位相等，最大绝对误差 0，接收计数 16 正确。

[开发者待确认问题](HELPER_TWO_ISSUES.md) 保留 WAIT 时间语义和重复 INSERT 两个具体例子。这份 Insight 流水直接使用原始指令记录，不经过 helper 数据库。

原始 instr.bin、数据库、case、执行日志、验证脚本和完整证据只保留在本地 examples/ascend950pr_sim_bundle。云盘不含 Dispatch、压缩包、skill 或早期排查材料；仅在用户明确要求传输时更新。
