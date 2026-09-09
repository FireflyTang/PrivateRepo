# 950PR 双卡仿真材料

- [Perfetto 原生流水](perfetto_megamoe/README.md)：刚重新导出的 MegaMoE 两卡全部实际核，JSON 未修改。
- [开发者讨论入口](developer_discussion/README.md)：[helper 两个问题的可读版说明](developer_discussion/docs/HELPER_TWO_ISSUES.md)，有具体例子和需要确认的问题。
- [可复用技能](ascend950pr-multichip-sim/SKILL.md)：默认原生 npusim/Perfetto，可选 Insight。可下载 [skill ZIP](ascend950pr-multichip-sim.zip) 解压到 ~/.codex/skills。
- 完整非平凡用例、原始采集及历史结果已在本地 ascend950pr_sim_bundle 归档。整包此前上传遇到 GitHub 规则校验超时，云盘暂未提供，不要把入口文件已上传误认为整包已上传。

默认先用 Perfetto，helper 相关问题先交开发者确认；Insight 路线保留。SHA256SUMS 同时包含本地完整归档及本次上传材料的校验值，完整归档缺失属于已知上传限制。
