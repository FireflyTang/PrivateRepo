---
name: ascend950pr-multichip-sim
description: 在 Ascend 950PR 上准备、执行和验证 npusim record -c 多卡离线仿真，默认还原原始指令文本并用原生 msprof 导出 Insight 流水，保留 npusim report/Perfetto 作为备用。适用于 Dispatch、MegaMoE 等完整 task case 的复现或开发；本流程实测双卡，不等同于普通单卡 host app 仿真或真机 profiling。
---

# 950PR 多卡离线仿真

默认采集入口是 `npusim record -c CASE`；默认报告路径为原始 `chipN_instr.bin` → 模型文本 `.dump` → 原生 `msprof op simulator --export` → MindStudio Insight。使用随技能提供的 `export_msprof.py` 还原文本并调用 msprof，不自行生成或修改流水 JSON。该路径不使用 helper 数据库，不需要为它加载 SQLite 兼容库。已有成功采集时直接导出，不重跑 kernel；已有符合需求的 Insight 报告可直接交付。用户明确选择 Perfetto 时再使用备用路径。

## 选择起点

- **已有采集，只要流水**：读 [默认 Insight 导出](references/insight.md)，用 `scripts/export_msprof.py` 调用安装的 msprof；检查实际汇总 JSON 文件，原样交付。不要自行改颜色、管线名称、同步时长或连线。
- **已有完整 case，需要运行或复现**：读 [执行与数值验证](references/run-and-validate.md)。先复制到新工作目录并重定位 top.json，防止误读上次输出或覆盖证据。
- **只有 kernel，需要准备多卡 case**：读 [case 构造](references/case-construction.md)。kernel 镜像必须配合参数、tiling、通信 context、拓扑和任务队列；top.json 本身不是调用壳。
- **用户选择 Perfetto 或需要对照 npusim 原生报告**：读 [备用 Perfetto 路径](references/native-report.md)，使用原生 `npusim report`；保留已有 Insight 结果。

## 已验证的范围

CANN 9.2.0-weekly.20260902.01 / 950PR，双卡离线 Dispatch 与 MegaMoE 非平凡用例。核数、编译产物、参数布局和环境兼容处理都是该版本实例，不外推为其他型号或版本的固定要求。四卡/八卡只有拓扑入口线索，不宣称已经验证执行。

本技能的脚本不包含 CANN 或完整数据集。复现实例需要配套 `ascend950pr_sim_bundle`；用 `--bundle` 显式传入位置，不依赖原机器用户名。当前工作区可寻找 `examples/ascend950pr_sim_bundle`，找不到时说明缺少哪项输入，不伪造用例。

## 完成标准与问题处理

执行成功、数值正确、报告成功是三项独立判断：检查任务完成和每卡记录，再核对输出，再打开/解析实际 trace。只看 CLI 返回 0、DB quick_check 或某个 die finished 都不够。

遇到环境问题，先核对精确错误和匹配的工具版本，可进行局部、可逆的环境处理；不要修改安装文件或原始采集去凑结果。当前报告成功不需要解决所有历史 collector 问题。用户要求先搁置时，保留日志、继续能完成的原生流程。

helper 的 WAIT 展示语义和重复 INSERT 尚待开发人员确认。需要讨论时读 [已知现象](references/known-observations.md)，把现象、推断、影响分开。记录命令、版本、具体 ID 和前后时间交给用户，不擅自联系开发者或发布材料。
