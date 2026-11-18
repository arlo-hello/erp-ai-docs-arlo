# ERP-SLICE-PUR-002 单动作运行与幂等恢复契约

> 状态：`CANDIDATE`。依赖未合并时使用固定版本 fixture 独立验证。

## 基本信息

- slice_id: ERP-SLICE-PUR-002
- business_outcome: 业务选择流程后，来源单据完成可触发一个动作，重复事件不重复建单，失败可从原节点恢复。
- blocked_by: [ERP-SLICE-PUR-001]
- 切片类型：implementation

## 验收标准

| AC | 可观察结果 | 验证方式 |
|---|---|---|
| AC-001 | 合法来源单据可选择已启用流程并冻结版本、来源明细与数量 | backend feature；E2E；依赖未合并用 fixture |
| AC-002 | 同一来源明细的已占用数量不可被旧自动链或另一实例重复占用 | unit；backend feature 并发测试 |
| AC-003 | 各入口仅在约定完结节点触发；未完成和重复完成事件不重复执行 | unit 参数化；backend feature |
| AC-004 | 单个内采、发货、直接、预报、虚拟调拨动作可由适配器生成目标单据关联 | adapter contract；各类型 explicit mock |
| AC-005 | 同一实例节点重复执行只返回原目标单据，不创建第二张单据 | backend feature 幂等测试 |
| AC-006 | 跨系统超时进入结果未知，恢复时先查询目标单据再决定重试 | unit；explicit mock |
| AC-007 | 动作失败停止后续，异常负责人可见失败原因、输入摘要和已成功结果 | backend feature；E2E |
| AC-008 | 成功、失败、重复和恢复均记录审计日志且可从来源追溯目标单据 | backend feature |

## 测试边界

- 独立验证声明：是
- 配置依赖以冻结版本 fixture 替代。
- 包含：选择、快照、完结判定、单动作、幂等、数量占用、异常恢复、审计。
- 不包含：多动作真实串联、跨系统生产联调、分批推进与自动审批。

## 依赖与 Mock 策略

- 前置切片：ERP-SLICE-PUR-001；依赖内容为发布版本契约。
- 合并前 mock：只读固定流程版本 fixture，不依赖配置页面或配置表真实存在。
- 外部系统：WMS/FL/NFL 单据适配器使用 explicit mock 覆盖成功、业务失败、超时、查询已存在。
- 验证顺序：unit → adapter contract → backend feature → frontend E2E → 依赖合并后的契约回归。

## 晋升条件

D01至D04关闭、五类动作适配器责任边界确认、旧自动链互斥方案通过技术评审后，才可改为 `DEFINED`。
