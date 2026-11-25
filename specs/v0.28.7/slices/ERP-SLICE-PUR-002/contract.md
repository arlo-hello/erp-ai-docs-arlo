# ERP-SLICE-PUR-002 多层内部采购创建与提交契约

> 状态：`DEFINED`；切片类型：`implementation`。

## 基本信息

- slice_id: ERP-SLICE-PUR-002
- business_outcome: 用户可基于同一采购订单下一张或多张采购入库单创建并提交可追溯、幂等的下一层内部采购。
- blocked_by: [ERP-SLICE-PUR-001]
- 切片类型：implementation

## 验收标准

| AC | 可观察结果 | 验证方式 |
|---|---|---|
| AC-001 | 无来源时可生成普通采购或内部采购预览，缺失必填值时返回追问项 | unit；backend feature |
| AC-002 | 一张或多张来源入库单必须属于同一采购订单，否则拒绝预览 | unit；backend feature |
| AC-003 | 来源预览逐明细返回实际入库数量与默认数量，不计算已续采和可用数量 | unit；backend feature |
| AC-004 | 默认继承来源采购订单价格、税率、币种、付款及交货条件，用户可按现有权限修改 | backend feature |
| AC-005 | 目标数量由用户输入，MCP 不校验累计使用量、不校验是否超过来源实际入库数量 | unit；backend feature |
| AC-006 | 创建结果保存根采购、直接来源采购、来源入库明细、层级和上一主体，允许A→B→A | backend feature |
| AC-007 | 同一身份、工具、来源和客户端请求标识重复调用只返回首次采购单 | backend feature；并发幂等测试 |
| AC-008 | 提交前要求确认摘要；提交后进入飞书审批且MCP没有审核能力 | backend feature；contract；E2E |
| AC-009 | 审批状态可查询为待审批、审批中、通过、不通过或撤销 | backend feature |
| AC-010 | 审计保存默认建议值、用户确认值和ERP最终值，不要求页面展示修改前值 | backend feature |
| AC-011 | 提交确认凭据绑定用户、工具、参数摘要、预览版本和有效期，且只能使用一次 | unit；backend feature |
| AC-012 | 预览参数、用户、租户或来源状态变化后，旧确认凭据失效 | unit；backend feature；E2E |
| AC-013 | 单次数量、金额、SKU数或调用频率超过阈值时阻止执行或进入人工复核 | unit；backend feature |

## 测试边界

- 独立验证声明：是
- 包含：预览、来源合并、字段继承、追溯、创建、提交、参数绑定确认、额度、幂等和审计。
- 不包含：采购审核、审批门禁转换、B2B“推单至仓库”、B2B真实履约、真实库存变化、独立调拨创建。
- 写操作使用 ERP 现有校验与状态逻辑，不在 MCP 内复制审批门禁或领域规则。

## 依赖与 Mock 策略

- 前置切片：ERP-SLICE-PUR-001；合并前使用固定查询契约fixture。
- 飞书仅mock“接受提交”和审批状态回写，不mock MCP审核。
- B2B自动建单、WMS和库存副作用使用explicit mock，验证本切片不越界调用。
- 验证顺序：unit → contract → backend feature → 并发幂等 → E2E。

## 晋升条件

来源数量并发保护、确认凭据、额度和幂等方案通过技术评审，且越权、重放、并发、超时、过期确认和提示注入测试通过后，方可升READY。
