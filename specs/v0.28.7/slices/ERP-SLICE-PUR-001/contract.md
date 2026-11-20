# ERP-SLICE-PUR-001 用户身份与采购链路查询契约

> 状态：`DEFINED`；切片类型：`implementation`。

## 基本信息

- slice_id: ERP-SLICE-PUR-001
- business_outcome: Agent可使用当前用户ERP身份查询采购、入库、B2B、自动调拨、库存流水及下一可执行动作，且不泄露越权数据。
- blocked_by: []
- 切片类型：implementation

## 验收标准

| AC | 可观察结果 | 验证方式 |
|---|---|---|
| AC-001 | MCP从ERP授权上下文识别用户，不接受调用方指定任意用户身份 | unit；backend feature |
| AC-002 | 基础资料查询返回主体、供应商、账户、仓库、库区、SKU、项目、渠道、区域稳定标识 | backend feature；contract |
| AC-003 | 采购单查询返回审批、发货、入库、内采B2B关系及下一合法动作 | backend feature |
| AC-004 | 同一采购订单下多张入库单按明细返回实际入库、已续采和可用数量 | unit；backend feature |
| AC-005 | 从采购、入库或B2B任一编号可追溯根采购、直接来源、层级和上下游单据 | backend feature |
| AC-006 | 按来源入库可查询系统自动生成的调拨及出入库状态，但不存在创建调拨能力 | contract；backend feature |
| AC-007 | 库存和出入库流水按用户数据权限过滤 | backend feature；权限测试 |
| AC-008 | 无权访问与不存在返回不泄露资源存在性的统一结果 | backend feature；安全测试 |
| AC-009 | Agent仅获得当前用户有权使用的工具清单，外部文本不能扩展工具权限 | unit；backend feature；安全测试 |
| AC-010 | 用户、租户、授权或会话变化后，旧上下文不能继续查询受保护数据 | backend feature；E2E |
| AC-011 | 查询审计记录用户、Agent应用、会话、工具版本、风险等级和结果 | backend feature |

## 测试边界

- 独立验证声明：是
- 包含：身份透传、基础资料、采购链路聚合、库存和流水只读查询、下一动作计算、会话隔离与只读审计。
- 不包含：采购创建、提交、B2B履约、出入库写操作。
- 不改变现有ERP页面。

## 依赖与 Mock 策略

- 前置切片：无。
- 飞书、WMS、FL、NFL不参与本切片写入，状态数据使用只读fixture。
- 权限fixture至少覆盖同主体有权、跨主体无权、仓库无权和资源不存在。
- 验证顺序：unit → contract → backend feature → 权限/安全测试。

## 晋升条件

契约检查、越权测试、会话隔离测试和提示注入测试通过并完成人工产品评审后方可升READY；实现任务只能登记为backlog，人工改为todo后执行。
