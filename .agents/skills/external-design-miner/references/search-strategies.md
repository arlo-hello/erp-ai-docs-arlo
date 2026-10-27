# 搜索策略速查

> 本文档为 external-design-miner 的搜索策略参考。按业务领域预置搜索模板，减少每次生成关键词的消耗。

---

## 1. ERP 采购域搜索模板

### 1.1 付款与结算

| 场景 | 联网搜索词 | GitHub 搜索词 |
|------|-----------|--------------|
| 账期管理 | `account period payment ERP design pattern` | `payment term schedule due date` |
| CN/贷项通知单 | `credit note deduction ERP best practice` | `credit note debit note payment system` |
| 多类型付款 | `multi payment type COD prepaid ERP design` | `payment method factory pattern` |
| 分批付款 | `installment payment partial ERP workflow` | `partial payment installment billing` |

### 1.2 退货与逆向流程

| 场景 | 联网搜索词 | GitHub 搜索词 |
|------|-----------|--------------|
| 退货仓库选择 | `return order warehouse selection design` | `return warehouse allocation` |
| 退货金额冲抵 | `return refund offset pending payment design` | `return refund accounting` |
| 退货超额 CN | `excess return credit note auto generate ERP` | `credit note auto generation` |

### 1.3 审批与状态机

| 场景 | 联网搜索词 | GitHub 搜索词 |
|------|-----------|--------------|
| 付款审批流 | `payment approval workflow design enterprise` | `payment approval state machine` |
| 跨实体状态联动 | `cross entity state synchronization design` | `state synchronization saga pattern` |

---

## 2. 通用搜索策略

### 2.1 关键词优先级

```
1. 精确英文技术词 > 模糊中文业务词
2. 具体功能名 > 宽泛领域名
3. 含 "design pattern" / "best practice" / "architecture" > 纯搜索
```

### 2.2 筛选标准

| 来源类型 | 最低标准 | 优先标准 |
|---------|---------|---------|
| 技术博客 | 有代码示例或架构图 | 有系统设计对比 |
| 开源仓库 | Star ≥ 50 | Star ≥ 500 + 活跃维护 |
| GitHub Issue | 有实质性讨论 | 含最终决策理由 |
| 产品文档 | 官方或知名产品 | 含交互流程图 |

### 2.3 去重规则

- 同一域名下的结果最多保留 2 条
- 同一作者/仓库的内容最多保留 1 条
- 内容高度相似（摘要相似度 > 80%）保留质量更高的

---

## 3. 不可搜索的主题

以下主题**禁止**联网搜索（属于内部机密）：
- 公司内部系统架构
- 具体的客户数据或供应商信息
- 内部定价策略
- 未公开的业务流程

搜索时只使用通用功能描述词，不包含公司名称、项目名称、内部术语。
