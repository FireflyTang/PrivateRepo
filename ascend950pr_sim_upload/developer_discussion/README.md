# 950PR 双卡仿真：请开发者确认官方报告路径

一句话问题：**950PR 双卡用 `npusim record -c` 跑完后，官方推荐怎样直接导出带 SET/WAIT 连线的 MindStudio Insight 流水，需要启用什么参数或配套版本？**

**关于“WAIT 只有 1 tick”和“重复 ID”两个问题，请先看 [可读版说明](docs/HELPER_TWO_ISSUES.md)**。文中有完整例子和开发者需要确认的问题，不用先读全部审计 JSON。

我们优先希望使用原生工具；下面是已验证事实与尚待确认问题，并不预设仿真运行方式或 helper 必然有 bug。

## 当前处理决定

先按开发者建议使用原生 `npusim report -e ARCHIVE -n all`，用 Perfetto 查看。已导出 MegaMoE 两卡各 core0/core1，默认流程不修复 DB、不改流水展示。helper 的两个问题先交开发者确认，Insight 路线保留。导出结果见云盘同级 ../perfetto_megamoe/，可读版问题说明见下方链接。

## 当前流程和验证边界

- CANN 9.2.0-weekly.20260902.01，msopprof 26.2.0.dev202609020100；完整版本见 PROVENANCE.json。
- Dispatch、MegaMoE 都通过双卡离线 case 执行；非平凡输出通过独立 golden 核对。原始输入、kernel、DB、instr.bin、报告与完整复现说明已通过 [完整归档分片](../archive_parts/README.md) 上传；下载后执行 assemble.py 还原。
- 保留的可选 Insight 展示链路：instr.bin → 还原模型文本 → 原生 `msprof op simulator --export`。脚本不生成或修改 JSON 的名称、颜色、时长和连线。
- 原生报告同步记录已与 raw 对照，并用 Insight 的 Flag 处理函数/SQL 核验关联。尚未再次完整验收最新版 GUI；普通多阶段指令也不能声称全量无损。

## 请优先回答

1. 上述双卡离线 case 模式是否为该版本支持的采集入口？如不推荐，请给一个可以直接执行的双卡最小命令或样例。
2. 是否已有 npusim/helper 的 Insight 原生导出选项，或可直接输出 msprof 所需文本的配置？我们的自定义 CORE_SIM_CFG 被 hard_code_toml_cfg_map 拒绝，因此没有继续用这份配置跑 kernel。
3. helper 的同步事件一 tick 展示是否是预期设计？如需要等待区间，官方应使用哪条数据/报告路径？

## 关键证据

| 观察 | 证据 | 希望确认 |
| --- | --- | --- |
| helper finalize 对零时长同步记录执行 start -= 1；MegaMoE 每卡日志 normalized=792 | evidence/helper_zero_duration/ | 这是展示归一化，还是另有完整 WAIT 数据应读取？ |
| MegaMoE 每卡 376 条 WAIT 在 DB 中全部 1 tick；raw 中 319 条大于 0，chip0 最长 14409 tick | evidence/helper_zero_duration/audit.json | 不把 raw popped 区间直接解释成纯同步停顿；请确认官方语义 |
| 新数据库仍有重复 INSERT：MegaMoE 每卡 433，Dispatch 每卡 1156 | results/*/duplicate_audit.json 和 cannsim_helper.log | 提前阶段/多阶段事件如何更新及配对？ |
| pending 的全部数量可分解到 BAR、RV_SEND 等阶段不对称 | results/*/raw_pairing.json | 协议定义还是缺陷，有无配套修订？ |
| msprof --export 直接接 instr.bin 报无 dump，但返回 0 | evidence/native_export/native_export_probe/ | 是否有直接读 bin 的入口？ |
| 开源 instr_decoder 输出一空格，msprof 丢失 detail；两个空格可正常读取 | scripts/export_msprof.py、docs/NATIVE_REPORT.md | 是否已有匹配版本/官方转换命令？ |

完整过程见 [NATIVE_REPORT.md](docs/NATIVE_REPORT.md)，其他运行问题见 [ISSUES.md](docs/ISSUES.md)。这些文件保留历史路径以定位证据；复现请用完整归档中的 scripts/prepare_case.py 建立新 case，不覆盖保存结果。

无需一开始下载整包：先看可读版说明中的两个具体例子和版本信息；需要原始数据重现时，下载同级 archive_parts 目录并执行 assemble.py。
