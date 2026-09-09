# 执行与数值验证

对于配套归档的两个已验证 case，调用技能脚本：

```bash
python3 SKILL_DIR/scripts/prepare_case.py megamoe --bundle SIM_BUNDLE --output NEW_CASE
bash SKILL_DIR/scripts/run_case.sh NEW_CASE
python3 SKILL_DIR/scripts/validate_outputs.py mega NEW_CASE --output NEW_CHECK.json
```

Dispatch 对应 prepare_case 的 `dispatch` 和 validate_outputs 的 `dispatch`。prepare_case 复制完整 case、重定位 top.json 的绝对 case_path 并补尾部 `/`，实际输出预填 0xA5。它只支持配套这两例的布局，不用于任意第三方 case。

run_case.sh 依赖已经加载的 ASCEND_HOME_PATH 和 npusim，在新目录复制模型文件后执行 `npusim record -c`，默认上限 600 秒，之前两例各约五分钟。可用 SIM_RUN_ROOT 指定新运行目录，串行运行以免共享模型路径冲突。不要把同一个 CANN 安装的 camodel 工作目录直接当多任务共享目录。

检查两卡 TASK_DONE、正常退出、两卡非空 DB/二进制，再独立核对实际输出。输出文件是否被替换、dtype、routing、counts 都需要检查；预置 golden 或旧 actual 不能证明这次执行成功。

已知实例：MegaMoE BS16/H1024/hidden512/topK1，每卡一个专家，非零 BF16 输入和非零稀疏 FP8 E5M2 权重，跨卡路由及不同路由权重；每卡 16384 BF16 输出逐位正确。Dispatch BS8/H7168/topK8，总8专家，每卡64个量化输出行，INT8值、FP32 scales、路由、分组及计数通过。

数值结果通过后，默认把新 capture/record/chipN_instr.bin 传给 scripts/export_msprof.py，由原生 msprof 生成 Insight 报告，具体见 insight.md。用户选择 Perfetto 时才把 capture 目录传给 npusim report，见 native-report.md。不因打包或重新看流水重复运行五分钟仿真。
