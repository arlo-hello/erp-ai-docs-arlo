# ERP-SLICE-PUR-001 自动化流程配置与发布契约

> 状态：`CANDIDATE`。D01至D04与发货动作字段关闭后复核准入。

## 基本信息

- slice_id: ERP-SLICE-PUR-001
- business_outcome: 负责人可创建、校验、发布、停用和删除自动化流程，运行实例始终读取不可变版本。
- blocked_by: []
- 切片类型：implementation

## 验收标准

| AC | 可观察结果 | 验证方式 |
|---|---|---|
| AC-001 | 列表支持查询、新建、详情、编辑、启停、删除，除新建外操作位于操作列菜单 | frontend component；E2E |
| AC-002 | 仅负责人可编辑、发布、启停和删除，越权请求不改变数据 | backend feature；E2E |
| AC-003 | 条件支持组间与组内且/或及八类字段，保存后读取语义不漂移 | unit；backend feature；frontend component |
| AC-004 | 五类动作配置按字段规则校验；发货动作在字段关闭前以 explicit mock 禁止发布 | backend feature；explicit mock |
| AC-005 | 流程存在唯一开始节点、无循环、所有路径可达末端；非法图不得发布 | unit；backend feature |
| AC-006 | 发布生成不可变版本；编辑生成新草稿，旧版本内容不变 | backend feature |
| AC-007 | 禁用或删除后不再进入新业务候选集，历史版本仍可查看 | backend feature；E2E |
| AC-008 | 两人并发编辑时后提交者收到版本冲突，先提交结果不被覆盖 | backend feature 并发测试 |

## 测试边界

- 独立验证声明：是
- 包含：流程 CRUD、负责人权限、图校验、字段校验、版本、启停、删除保护。
- 不包含：来源单据选择、完结事件消费、真实建单和跨系统联调。
- 未决业务项通过发布门禁显式 mock 为“禁止发布”，不伪造默认答案。

## 依赖与 Mock 策略

- 前置切片：无。
- 外部系统：无。
- 主数据下拉以只读适配器 mock 验证主体、供应商、仓库、库区、项目、渠道、区域、SKU。
- 验证顺序：unit → backend feature → frontend component → E2E。

## 晋升条件

D01至D04关闭，发货动作字段确定，随后运行 registry/contract 检查；人工评审前不得升 `READY`。
