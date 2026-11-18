# ERP-SLICE-PUR-003 多动作端到端接续契约

> 状态：`CANDIDATE`；切片类型：`final`。依赖合并前不得晋升实现。

## 基本信息

- slice_id: ERP-SLICE-PUR-003
- business_outcome: 采购、入库与调拨来源可按冻结流程完成条件判断和多动作有序接续，异常恢复后不重复已成功节点。
- blocked_by: [ERP-SLICE-PUR-001, ERP-SLICE-PUR-002]
- 切片类型：final

## 验收标准

| AC | 可观察结果 | 验证方式 |
|---|---|---|
| AC-001 | 普通采购 FL/NFL、同/不同主体、中转/不中转按九类完结口径触发 | backend feature 参数化；E2E |
| AC-002 | 条件组按冻结来源事实求值，同一输入重复求值得到同一分支 | unit；backend feature |
| AC-003 | 内采、发货和三类调拨可按显式顺序组合，前一步未成功不得执行下一步 | backend integration；E2E |
| AC-004 | 每一步以上一步完成后的主体、项目、渠道、区域、仓库与可承接数量作为输入 | backend feature integration；不变量断言 |
| AC-005 | 任一步失败后恢复不重复已成功单据，最终实例只关联一套目标链 | backend feature integration 故障注入 |
| AC-006 | 编辑、禁用、删除流程不改变运行中实例的节点、字段和顺序 | backend integration；E2E |
| AC-007 | 旧采购自动链保持原回归结果，选择新流程的来源不会重复进入旧链 | backend feature legacy regression；integration |
| AC-008 | 全链路商品数量不超出来源可处理数量，完成或取消后占用变化可追溯 | unit 守恒；backend integration |

## 测试边界

- 切片类型：final
- 这是 final 集成切片，只在前置切片合并后验证真实链路。
- 包含：完整条件分支、多动作顺序、九类完结口径、版本隔离、旧链兼容、数量守恒。
- 不包含：未确认的自动匹配、分批推进、自动越权审批、跨主体虚拟调拨。

## 依赖与 Mock 策略

- 前置切片：ERP-SLICE-PUR-001、ERP-SLICE-PUR-002，必须先合并到版本集成分支。
- 外部系统：合并前可用 contract stub 预演，但不据此晋升实现；真实联调覆盖成功、拒绝、超时、回查已存在。
- 验证顺序：registry/contract → 前置回归 → backend integration → frontend E2E → 旧链回归 → 故障注入。

## 晋升条件

前置切片合并、D01至D04关闭、跨系统测试环境可用后，才可由人工将本切片从候选状态推进。
