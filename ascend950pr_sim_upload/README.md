# 950PR 双卡仿真归档与开发者讨论材料

- **长期归档**：[ascend950pr_sim_bundle.tar.gz](ascend950pr_sim_bundle.tar.gz)。包含最终非平凡 Dispatch/MegaMoE 用例、实际输出和 golden、原始采集、原生 msprof 报告、脚本、历史问题及校验文件。解压后从 README.md 开始。
- **开发者讨论**：[developer_discussion/README.md](developer_discussion/README.md)。可以先发这个入口，按问题定位日志和统计，不必先下载整个归档。

当前结论是执行与数值验证已通过，报告改用原生 msprof；二进制转文本仍需小脚本。希望开发者确认官方原生导出入口及 helper 同步事件语义，没有把整条运行逻辑判为错误。

SHA256SUMS 可校验本目录全部文件。完整归档内部还有独立 SHA256SUMS 与 verify_bundle.py。
