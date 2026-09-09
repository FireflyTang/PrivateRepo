# 可选的原生 msprof / Insight 路线

保留已有结果，用户没有要求时不要用它替换默认 Perfetto 路线。

本机 msprof op simulator --export 只识别文本 dump，不能直接吃 instr.bin。脚本 export_msprof.py 原样还原模型文本，随后调用安装的 msprof；不生成/修饰 trace JSON：

```bash
python3 SKILL_DIR/scripts/export_msprof.py ARCHIVE/record/chip0_instr.bin --core-id 0,1 --output NEW_REPORT
```

脚本参数用逗号列出核，内部会转换成 msprof 需要的 `--core-id=0|1`。默认soc为Ascend950PR_9589，与本例1650MHz换算匹配。两卡分开处理，保持原生core0.cubecore0等名称，不自行加chip前缀。导入输出的汇总simulator/trace.json或visualize_data.bin；本版单核子目录trace不含相同的SET/WAIT关系。

原生参数 `--aic-metrics=PipeUtilization,ResourceConflictRatio` 启用管线与同步详情，单独PipeUtilization会关闭同步详情。注意返回0不一定成功，要检查实际trace与导出日志。

二进制结构<QIIQB200s200s7x，kind=1对应popped/start，kind=0对应完成。原生模型文本中decode与参数之间是两个空格；参考仓的Python decoder使用一空格，本机msprof会静默丢detail。用脚本后应确认Flag的detail非空，并可用validate_msprof_raw_flags.py核对原始起止和关系。

没有重新实现配色或等待时长。msprof会按自身规则裁剪WAIT，与原始popped区间不一定完全相同。本路线不补齐原始流缺少的多阶段事件，也不提供没有采集的I-cache/MTE数据或缺失的源码映射。

CORE_SIM_CFG自定义TOML在本加密模型被hard_code_toml_cfg_map拒绝，勿重复盲试或更改模型架构配置。询问开发者是否有受支持的文本日志开关或匹配版本即可。
