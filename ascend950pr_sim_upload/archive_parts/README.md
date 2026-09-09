# 完整归档分片

整包上传遇到 GitHub 规则校验超时，因此这里按 8 MiB 分片；内容没有删减。完整包包含非平凡 Dispatch/MegaMoE 输入输出、原始采集、原生 Perfetto 与可选 Insight 报告、复现脚本、skill 和问题说明。

下载本目录全部文件，在本机执行：

```bash
python3 assemble.py
tar -xzf ascend950pr_sim_bundle.tar.gz
```

assemble.py 先核对各分片，再核对还原后的完整 SHA256；不会覆盖已有输出。还原后从 ascend950pr_sim_bundle/README.md 开始。只想看流水或讨论问题，无需下载本目录，使用上一级对应入口即可。

归档内部是分片上传之前制作的已校验快照；部分历史说明中的“整包尚未上传”描述当时单文件上传失败的状态。本目录的分片已解决传输问题，实际数据完整性以 manifest.json 校验为准。
