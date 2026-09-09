# MegaMoE 双卡原生 npusim 流水（Perfetto）

先下载 [chip0/trace_core0.json](chip0/trace_core0.json)，在 https://ui.perfetto.dev 用 Open trace file 打开。其他芯片/核文件也可单独查看。

这些 JSON 来自 npusim report -e ARCHIVE -n all，原生 gzip 输出只做无损解压；没有修改事件名称、颜色、时间、同步关系或 helper 数据库。

本机为该报告进程使用系统 SQLite 解决 Conda URI 挂库兼容问题。完整命令及环境覆盖见 command.json，日志见 export.log。HTML 索引警告已保留，不影响这四份 JSON 的生成和解析。

| 文件 | 事件数 | MMAD |
| --- | ---: | ---: |
| chip0/trace_core0.json | 39330 | 20 |
| chip0/trace_core1.json | 34836 | 4 |
| chip1/trace_core0.json | 39138 | 20 |
| chip1/trace_core1.json | 35443 | 4 |

数值验证使用的是已成功的非平凡输入，此次没有重跑 kernel。helper 的 WAIT 展示和重复 ID 问题先交开发者确认；打开成功不等于对等待区间语义的验收。Insight 原生 msprof 报告仍保存在本地完整归档。
