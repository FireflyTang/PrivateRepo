# 原生报告与参数调查

结论：应优先使用原生 msprof。此前主要沿着 npusim 的报告 JSON 做兼容修复，过早承担了展示层逻辑。现在已实际跑通“原始 instr.bin → 模型文本记录 → msprof 原生报告”，不再由自写脚本指定 JSON 名称、颜色、时长或连线。

## 已核实的参数

`msprof op simulator --export DIR --soc-version=Ascend950PR_9589 --aic-metrics=PipeUtilization,ResourceConflictRatio`

官方文档明确：`ResourceConflictRatio` 控制同步事件细节；单独指定 `PipeUtilization` 会关闭它。离线 `--export` 可以解析已有 dump。见 [msopprof 官方说明](https://github.com/Ascend/msopprof/blob/master/docs/en/user_guide/msopprof_simulator_user_guide.md)。

本机版本是 `msopprof 26.2.0.dev202609020100`，CANN weekly 20260902。安装版本与参考的开源源码提交不同，完整记录见 `../PROVENANCE.json`。

实测把 instr.bin 直接放进 `--export` 目录无效：日志报 `Failed to get any available dump file to parse`，虽然进程返回 0。原生扫描器要找 `core*.{cubecore0,veccore0,veccore1}.{instr,instr_popped}_log.dump`。脚本同时检查日志与实际 trace 内容，避免把退出 0 当成成功。

本机 npusim report 的公开参数中未找到 Insight 专用导出开关；`--smart-pipes`、底层 `--no-ticks-to-ns` 也不是这个功能。已检查范围内未找到不代表所有内部版本都没有。

重新检索本地 npu-simulator 的 README 与全部 docs Markdown，未找到 msprof/Insight 对接、instr_decoder、CORE_SIM_CFG 或文本日志导出步骤。`docs/zh/user_guide/01_user_guide.md` 第 123、134 行明确推荐 Chrome/Perfetto 查看 trace_core*.json。网上检索也未补到该对接用法；尝试核对 GitCode 最新 HEAD 时远端要求认证，未能确认远端最新文档与本地提交完全一致。不能据此断言内部文档不存在。

## 文本恢复为何仍需要小脚本

开源 npu-simulator 自带 `cannsim/core/public/instr_decoder.py`；本机安装包里没有这个模块。其 `LogEntry.__str__` 在 decode 与 execution 参数之间只放一个空格。实际运行它再交给本机 msprof，会生成报告，但 Flag 的 `args.detail` 为空，因此配对不能信任。

msopprof 的正则要求这里是两个空格或括号。模型库内原生格式字符串也是 `[{:08d}] {:s}  {:s}`。当前 `export_msprof.py` 使用两个空格，保留原 tick、PC、名称、参数和起止类别。二进制结构为 `<QIIQB200s200s7x`，kind=1 对应 popped/start，kind=0 对应 completion；按 chip 分开、core ID 模 32 还原局部编号。

此脚本不配对普通指令、不修正数据库、不生成 JSON。所有流水布局、命名、颜色、同步处理均交给安装的 msprof。源数据没有 I-cache/MTE 等独立日志和完整源码映射信息，因此这不是一次完整 msprof 在线采集的所有功能。导出日志中的缺少 pc_start_addr、debug_line 和源码映射提示已经保留。

## 是否能让模型直接输出文本

模型确实有文本日志实现，静态检查也找到了 `CORE_SIM_CFG`、`LOG.file_print_level`、`LOG.enable_list`。但不能把“存在字符串”当作“当前公开发行版可配置”。

隔离探针设置 CORE_SIM_CFG 指向只含 LOG 段的 TOML 后，模型立即报告：

```
Config file is not in hard_code_toml_cfg_map. filename=.../core_config.toml
Assertion failed: core_wrapper.cpp:267 init_new_core_cfg
```

随后出现缺少架构配置键的错误，因此主动终止，未用于数值或性能验收。证据在 `../evidence/native_export/native_logging`。没有修改安装文件。这说明该入口在当前加密模型中受内置配置表约束；尚未找到受支持的用户覆盖方式。

给开发人员的具体问题：**950PR weekly 20260902 的 npusim record -c 双卡模式，是否支持在保留内置硬件配置的前提下，通过配置/参数输出原生 instr_log 和 instr_popped_log 文本？应使用哪个入口？CORE_SIM_CFG 自定义路径被 hard_code_toml_cfg_map 拒绝，是否另有 override 或配套模型版本？**

## 与之前适配器的差别

| 项目 | 旧适配路线 | 当前原生 msprof |
| --- | --- | --- |
| 配色 | 最初人为按指令名着色，后改参考管线色表 | 工具原生 cname，不再自行分配 |
| 管线和排序 | 继承 npusim 的 FC、SCALAR_LDST、PUSHQ 等映射及排序 | msprof 自己解析和命名，含 FLOWCTRL、SCALARLDST、VECTOR 等 |
| WAIT 开始时间 | 使用完整原始 popped 时间 | 按 msprof 规则可裁到前一条同管线非同步指令结束时刻 |
| SET | 模拟最后一个 tick | 原生最后一个 tick；换算并四舍五入后仍可能显示 0 ns |
| 参数 | 混合 npusim 字段与手补字段 | 原生 pc_addr/code/detail；源码缺失时 code 为空 |
| 事件数 | 受 helper DB 和定向修复影响 | 直接解析原始阶段日志，使用自身多阶段配对/裁剪规则 |
| 统计波形 | 有 npusim unit_utilization 等 counter | 本次仅提供指令文本，不带原先 npusim counter |
| 输出 | 自写 Chrome Trace JSON | 原生汇总 trace.json、visualize_data.bin、CSV、单核报告 |

MegaMoE 两卡分别有 100 / 98 条 WAIT 被原生 exporter 裁剪；这是真实差异，不是染色造成的。每卡全部 752 条 SET/WAIT 均与原始记录核对，376 对参数一致。Dispatch 的 core0 每卡 240 条、120 对，分别 2 条 WAIT 被裁剪。

官方 Insight Flag 处理函数和 SQL 检查分别解析出 376、376、120、120 对可关联关系，结果在 `../evidence/insight/native_validation.json`。未在完整最新版 GUI 中再次验收，不应宣称所有交互已验证。

原生报告也不能补出原始流缺少的阶段。BAR、RV_SEND 等协议问题与 helper 重复 ID 仍需区分，详见 ISSUES.md。没有把 native export 的成功等同于全流水周期准确。

## 开发人员补充：helper 的零时长处理

用户向开发人员确认 helper 有零时长指令处理逻辑后，进一步检查了本机 libcannsim_helper.so、原始 DB 和 finalize 日志。确实找到以下 SQL 逻辑：对于起止相等的 SET_FLAG、WAIT_FLAG、SET/WAIT_INTRA_BLOCK、GET/RLS_BUF、SET_CROSS_CORE，将 ExecInstrTickStart 减 1。

本机日志为 `normalized zero-duration sync instructions: 792`（MegaMoE 每卡）。数据库内每卡 376 条 SET_FLAG 和 376 条 WAIT_FLAG 全部为 1 tick，而原始二进制的 WAIT 存在较长完整区间。数据库仍有其他零时长普通指令，所以不能称为“所有零时长指令都被删除”。该步骤在日志上发生于 pending flush 之后、finalize 之前；此前已发生的 UNIQUE 插入冲突不能靠这条 UPDATE 撤销。

因此起点压缩不只涉及 Python report 的 FixStartTimeAnalyzer：helper 数据库也已采用一 tick 的同步展示区间。前期解释对 helper 层说明不足。当前直接读原始二进制再交给 msprof 的路线不经过这个数据库归一化步骤。SQL 字符串、库 SHA256、两卡 DB/raw 对比统计见 `../evidence/helper_zero_duration`。这不能排除开发人员所指的另一版本还有其他清理逻辑，需要按库版本核对。
