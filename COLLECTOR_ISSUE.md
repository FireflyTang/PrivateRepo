# npusim 双卡采集：重复 ID 与未配对事件复现

环境：950PR / dav_3510，CANN 9.2.0-weekly.20260902.01，2 chip 离线
`npusim record -c CASE -o NEW_OUTPUT`。Dispatch 原例和 MegaMoE 均完成两个 TASK_DONE、退出 0。
每次运行使用全新的模型目录和输出目录；原始 chip0.db / chip1.db 的 quick_check 均为 ok。

## 问题一：同一指令先记录零时长，再插入完整时长时主键冲突

MegaMoE 归档：`artifacts/run_CPjCN7/output/npusim_20260908052238_case`。
共 866 条 UNIQUE constraint failed，两卡各 433 个被拒绝 ID：
每卡 401 个在原始 instr.bin 中只有一对完整起止，32 个存在跨流水线多事件。
Dispatch 原例归档 `artifacts/run_yLMwFj/output/npusim_20260908045805_case`，
共 2312 条，每卡 1156 个，均属于一对完整起止与已有提前零时长记录冲突。

MegaMoE chip0 最小例：

```
ExecInstrId = 57999238378526
instr_id = 13342, core = 0, sub_core = 2, name = RV_SMOV
DB:  PC=0x10b008, start=14968, end=14968
raw: PC=0x4010b008, RVECSU start=14971, end=14972
```

两种 PC 表达包含装载基址差异，不是两条不同源码指令。
“某个提前事件被当作完整指令先插入，随后真实执行事件再次 INSERT”是与证据一致的推断；
因 helper 未提供可见实现源码，尚未确认具体 C++ 分支。
不能用清库、关闭 UNIQUE、INSERT OR IGNORE 或修改 SQLite URI 默认值修复其时长语义。

已提供 `audit_duplicate_ids.py`，对 helper 错误 ID、DB 行、原始事件逐条只读核对。
结果见 `artifacts/mega_duplicate_audit.json`、`artifacts/dispatch_duplicate_audit.json`。
`repair_report_copy.py` 只对“恰好一 start、一 end、PC 相同、已有提前零时长”记录修正
**新副本**，逐行保留前后值，拒绝覆盖已有目录。它不是上游采集器修复。
零权重 Mega 副本每卡修正 401 条，报告已重新生成；多流水线记录保持原样。

## 问题二：原始事件本身存在不对称阶段，不能凭空补时长

Mega helper 两次 flush 均报告 pending_start=156 / pending_end=142。
按 chip0 原始 `(core, sub_core, instr_id)` 聚合，有以下不平衡模式：

| 指令 | 数量 | 原始 start / end 数 |
| --- | --- | --- |
| BAR | 40 | 0 / 1 |
| RV_SEND | 102 | 5 / 3（跨 RVECSU、RVECLD、RVECST） |
| RV_SMEM_BAR | 4 | 1 / 0 |
| RV_SMEM_BAR | 34 | 2 / 1 |
| RV_SMEM_BAR | 16 | 3 / 2 |

例：core0/sub1/id2257，PC=0x401003e4，仅 ALL 管线 end=5891，没有 start，DB 也没有该 ID。
例：core0/sub2/id13610 的 RV_SEND，RVECSU 15012→15013；RVECLD 只有 start=15013；
RVECST start=15027,15028,15028，end=15037,15037。DB 同 ID 低32位对应多个管线记录。
详细原始事件见 `artifacts/mega_raw_unbalanced.json`。

这说明 dropped 不能直接解释成同等数量的完整 kernel 指令丢失：
其中一些是同一指令的多阶段事件，但 BAR 的完整区间确实无法从该原始流恢复。
未伪造缺失起止；报告可用于观察通路，但不能声明完整无损或用于严格周期验收。

## 请开发者确认

### 新一轮双卡非零用例的完整数量核对

MegaMoE 非零归档 `run_mtGw3w` 复现相同 866 条主键冲突和每卡 156 / 142 pending。
Dispatch 不重复 ID 归档 `run_Dv9QaQ` 数值全部正确，仍复现相同 2312 条冲突，
每卡 pending_start=791 / pending_end=2513。因此采集问题独立于 Dispatch 原例的精度问题。

`audit_raw_pairing.py` 扫描两卡全部原始事件，结果：

| Dispatch 每卡类别 | 原始不平衡逻辑 ID 数 |
| --- | --- |
| BAR 仅 end | 512 |
| GET_BUF 仅 end | 672 |
| RLS_BUF 仅 end | 672 |
| RV_SEND 5 start / 3 end | 657 |
| RV_SMEM_BAR 2 start / 1 end | 134 |

数量与 helper 日志精确对应：`791 = 657 + 134`，
`2513 = 512 + 672 + 672 + 657`。
MegaMoE 同样对应：`156 = 102 + 4 + 34 + 16`，`142 = 40 + 102`。
这把所有 pending 数量定位到具体指令类别；具体内部配对分支仍需 helper 源码确认。
不能据此编造仅 end 事件的 start，也不能声称原始区间可完整恢复。

审计结果：`artifacts/dispatch_unique_raw_pairing.json`、`artifacts/mega_nontrivial_raw_pairing.json`。
Dispatch 报告副本的每卡 1156 条确定区间均已修正，全部保留修改清单。

### 待确认问题

1. 当前 helper 是否把 VF 标量提前阶段与实际执行阶段合并成相同 ExecInstrId？应如何更新已有行？
2. BAR 只有 end、RV_SEND / RV_SMEM_BAR 多流水线不等量事件，属于模型事件协议还是已知缺陷？
3. 是否有匹配该 weekly 的 helper/model 修正版或官方配对规则？

上述为本地已整理的排查材料，未代用户发送。原始归档均保留，可按 ID 继续定位。
