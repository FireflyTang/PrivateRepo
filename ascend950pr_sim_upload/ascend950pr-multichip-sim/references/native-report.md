# 备用：原生 npusim 报告与 Perfetto

仅在用户选择 Perfetto 或需要原生 npusim 报告作对照时使用；默认 Insight 路线见 insight.md。

加载对应 CANN set_env.sh，查看本机 `npusim report --help`。基本命令：

```bash
npusim report -e /path/to/npusim_xxx_case -n all -o /path/to/NEW_REPORT
```

末尾不要附加孤立的 `-`。`-o` 用来避免覆盖原来的报告；不是格式转换选项。当前版本也有原生 `-m` 合并选项，仅在需要合并时使用，不自行拼 JSON。

双卡目录包含 record/chip0_instr.bin、chip1_instr.bin 和 helper 的 chip0.db、chip1.db。本次默认 report 会使用 helper DB。结果可能位于：

```
NEW_REPORT/chip0_result/results/0000_kernel_reports/core_0/trace_core0.json.gz
NEW_REPORT/chip0_result/results/0000_kernel_reports/core_1/trace_core1.json.gz
NEW_REPORT/chip1_result/results/0000_kernel_reports/core_0/trace_core0.json.gz
NEW_REPORT/chip1_result/results/0000_kernel_reports/core_1/trace_core1.json.gz
```

目录和压缩与否随版本变化，实际搜索 `trace_core*.json*`，包括被 gitignore 排除的文件。可用 Python pathlib.rglob；仅凭默认 rg --files 没输出不能判定不存在。

将 gzip 原样解压为 .json 即可导入 Perfetto；可以复制为易找的交付路径，但不改内部事件。校验 JSON 可解析、事件非空、报告核覆盖预期。MegaMoE 已知实例每卡 core0/core1 分别有 20/4 个 MMAD_MX，不能作为任意新用例的固定验收值。

## 本机曾遇到的 SQLite 环境兼容

Conda SQLite 没有默认启用 URI，而报告通过 file URI 只读挂库。外层可能只报 BiProfRunner 失败并建议安装依赖，不能因此盲目安装全部依赖。可在空内存连接中只读 ATTACH 实际 DB，验证 URI 是否可用。

本次成功使用系统自带、编译时启用了 USE_URI 的 SQLite 3.45.1，仅为报告进程指定库：

```bash
LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libsqlite3.so.0 \
  npusim report -e ARCHIVE -n all -o NEW_REPORT
```

这是当前 x86_64 Linux 环境的实例，不是通用必选参数。先检查库存在、ABI/版本适配、原生 Python sqlite3 可正常导入并完成只读 ATTACH；不要在其他平台照抄路径，不覆盖用户已有 LD_PRELOAD。优先用已兼容的运行环境。不能确认时给出准确报错让开发者处理，不改报告数据。

本次没有使用自写 report 包装脚本、没有修复 helper DB、没有重命名事件。工具提示 aggregated index.html 警告但实际每卡 trace 已生成；保留警告，无需为了查看 Perfetto 去修 HTML。

Perfetto 是查看器。它不会恢复数据库已省略的时间，也不证明等待时间语义正确。用户暂时搁置这些问题时原样交付，不启动额外修复工程。
