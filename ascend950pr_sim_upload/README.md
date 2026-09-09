# 950PR 双卡仿真材料

- [Perfetto 原生流水](perfetto_megamoe/README.md)：刚重新导出的 MegaMoE 两卡全部实际核，JSON 未修改。
- [开发者讨论入口](developer_discussion/README.md)：[helper 两个问题的可读版说明](developer_discussion/docs/HELPER_TWO_ISSUES.md)，有具体例子和需要确认的问题。
- [可复用技能](ascend950pr-multichip-sim/SKILL.md)：默认原生 npusim/Perfetto，可选 Insight。可下载 [skill ZIP](ascend950pr-multichip-sim.zip) 解压到 ~/.codex/skills。
- [完整归档分片](archive_parts/README.md)：非平凡用例、原始采集、Perfetto/Insight 报告和 skill 均保留。12 个分片已经上传，下载整个 archive_parts 目录后执行 assemble.py 校验并还原完整 tar.gz。

默认先用 Perfetto，helper 相关问题先交开发者确认；Insight 路线保留。SHA256SUMS 校验本目录实际上传的文件；还原后的完整归档校验值见 archive_parts/manifest.json。
