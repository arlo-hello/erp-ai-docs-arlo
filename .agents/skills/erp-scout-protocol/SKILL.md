---
name: erp-scout-protocol

> ⚠️ **输出铁律**：所有文件路径必须经 Glob/Grep 验证存在——禁止写"可能在"/"大概在"/"类似于"。字段名/类名/方法名必须 Read 确认后引用，标注行号。不做零侦察。
role: architect
description: |
  ERP 侦察协议 — 任何代码任务的强制性第零步。必须始终先侦察再行动。
  自动触发：任何涉及ERP代码的请求、用户说"侦察"/"看一下"/"代码在哪"。
  核心铁律：只读探索，严禁猜测路径，严禁在侦察阶段修改任何代码。
  即使用户说"不用侦察"，仍需执行快速扫描，不能零侦察。
version: "1.1"
updated: 2026-06-29
---

# ERP 侦察协议（Scout Protocol）

> **侦察兵只看地图，不动枪。** 本阶段严禁修改任何代码。

---

## 边界情况

| 情况 | 策略 |
|------|------|
| 模块不存在 | 搜索近似名称，无结果则告知用户"模块未找到" |
| git 不可用 | 跳过 Step 4（Git 历史），标注"Git 不可用" |
| 文件量巨大（>200 匹配） | 缩小范围，只取核心文件（Controller/Model/Service/路由） |

## 三步核心流程

```
❶ 判定侦察深度 → ❷ 执行侦察 → ❸ 输出报告 → ❸.5 自检
```

---

## ❶ 侦察深度判定

根据任务类型自动选择深度（节省 token，精准打击）：

| 深度 | 适用场景 | 步骤 |
|------|---------|------|
| **快速** (1-2 min) | 修 Bug、改文案、小调整、回答"这段代码做什么" | Step 1 文件定位 + Step 2 关键引用 |
| **标准** (3-5 min) | 新页面/新功能、中等需求、跨 2-3 文件修改 | 全部 5 步（Step 3 执行 3.1-3.3） |
| **深度** (5-8 min) | 新模块、跨域变更、DB Schema 变更、架构调整 | 全部 5 步（Step 3 完整深度分析）+ 跨域依赖 + Git 历史 |

**判定规则**：
- 用户说"修复"、"Bug"、"报错" → 快速
- 用户说"新增"、"添加页面"、"实现" → 标准
- 用户说"新模块"、"数据库变更"、"跨模块" → 深度
- 不确定时默认 **标准**

---

## ❷ 侦察步骤

> **工具优先**: 优先使用 Glob / Grep / Read 等 Codex 内置工具（高效、不产生 shell 噪音）。Bash 仅用于工具覆盖不了的复杂查询（如 git log 统计、DB schema 查询）。

### Step 1 — 文件定位（严禁猜测）

找到所有相关文件，验证真实存在。

```
前端定位:
  Glob: dtcplus-web-ts/apps/nexus-erp/src/pages/{module}/**/*.tsx
  Glob: dtcplus-web-ts/apps/nexus-erp/src/api/{module}/**/*.ts
  Glob: dtcplus-web-ts/apps/nexus-erp/src/components/{module}/**/*.tsx

后端定位:
  Glob: erp-service-php/app/Domains/{Domain}/**/*.php
  Glob: erp-service-php/app/Api/Controllers/{Module}/**/*.php
  Grep: 搜索类名/关键词 → erp-service-php/app --include="*.php"

路由定位:
  Grep: 搜索路由路径 → erp-service-php/routes --include="*.php"
```

### Step 2 — 依赖分析（谁在用？谁被用？）

```bash
# 查找所有调用方（影响面）
grep -rn "{ClassName}" erp-service-php/app --include="*.php" | head -30

# 前端 API 调用方
grep -rn "{apiFunction}" dtcplus-web-ts/apps/nexus-erp/src --include="*.ts" --include="*.tsx"
```

### Step 3 — 数据层探查（深度侦察时执行，标准侦察至少执行 3.1-3.3）

#### 3.1 Model 深度分析（必须）

对每个相关 Model 执行**完整读取**（不再只看前 80 行），输出结构化清单：

```
Read: erp-service-php/app/Models/{Domain}/{Model}.php (完整文件)

输出: 已有能力清单
  ├── 完整字段清单（字段名 + 类型 + 注释，逐字段列出）
  ├── 所有常量（含值 + 注释含义）
  ├── 所有关联方法签名（hasMany/belongsTo/morphMany + 外键名）
  ├── 所有自定义方法签名（静态查询 + 实例方法 + 参数 + 返回值）
  └── 所有 accessor/mutator 列表（getXxxAttribute / setXxxAttribute）
```

#### 3.2 Migration 历史（必须）

```
Bash: ls -lt erp-service-php/database/migrations/ | grep "{table}" | head -10
```

输出该表所有历史 Migration，标注最新 Schema 状态。

#### 3.3 已有能力 vs 新需求对比

基于 3.1 的"已有能力清单"，与新需求对比：

| 维度 | 已有 | 新增需求 | 差异 |
|------|------|---------|------|
| 字段 | {已有字段列表} | {新需求字段} | {缺失字段} |
| 关联 | {已有关联列表} | {新需求关联} | {缺失关联} |
| 方法 | {已有方法列表} | {新需求方法} | {缺失方法} |

> 此对比直接决定：复用还是新建。重叠度 > 50% → 默认复用。

### Step 4 — Git 历史（深度侦察时执行，快速/标准可跳过）

```bash
# 最近修改和 Bug 修复
git log -n 5 --pretty=format:"%h %s %ad" --date=short -- erp-service-php/app/Domains/{Domain}/
git log --grep="fix:" -n 3 --pretty=format:"%h %s" -- erp-service-php/app/Domains/{Domain}/
```

### Step 5 — 测试盘点（标准+深度侦察时执行）

```
Glob: erp-service-php/tests/**/*{Module}*.php
Glob: dtcplus-web-ts/apps/nexus-erp/src/pages/{module}/**/__tests__/**/*.test.*
```

---

## ❸ 侦察报告

根据任务类型选择模板（详见 `references/scout-report-template.md`）：

| 任务类型 | 必须包含的章节 |
|---------|--------------|
| **新建功能** | 代码地图 + 可用模式（类似实现作为参考）+ 双城建议 + DB 迁移需求 |
| **修改功能** | 代码地图 + 调用方清单（影响面）+ 风险点 + Git 最近修复（避免覆盖） |
| **调查问题** | 代码地图 + 数据流追踪 + 可疑点 + 根因假设 |

### 报告核心要求

1. **所有文件路径必须已验证存在**（Glob/Read 确认过）
2. **关键代码引用必须含行号**（`file.tsx:42`）
3. **风险点至少 2 条**
4. **必须给出可执行的下一步建议**

### 报告前自检

> 输出侦察报告前，逐项确认：

- [ ] 所有列出的文件路径已经 Glob/Read 验证存在（非猜测）
- [ ] 关键引用含精确行号
- [ ] 风险点 ≥ 2 条，每条有位置 + 缓解建议
- [ ] 双城边界已判断（新城新建 / 旧城只读修改）
- [ ] 下一步建议明确（指向具体 Skill 名称）

---

## 禁止行为

- ❌ 跳过侦察直接写代码（用户说"不用侦察"也必须执行快速扫描）
- ❌ 猜测文件路径（必须用 Glob/Grep 验证）
- ❌ 假设类名/方法名（必须确认存在）
- ❌ 在侦察阶段修改任何文件
- ✅ 输出中所有路径必须可点击跳转

---

## 侦察后交接

| 任务类型 | 下一步 Skill |
|---------|------------|
| 新功能/页面 | → `erp-product-doc-generator`（产品方案）或 `backend-doc-generator`（后端方案） |
| 功能变更 | → `backend-doc-generator` 或 `frontend-doc-generator`（场景 B：影响面分析） |
| Bug 修复 | → 直接修复（快速侦察即可） |
| 调查问题 | → 根据根因假设选择对应 Skill |

## 验收标准

| # | 验收项 | 通过标准 |
|---|--------|---------|
| 1 | 文件定位 | 所有相关文件已 Glob 定位且验证存在 |
| 2 | 深度匹配 | 侦察深度（快速/标准/深度）与任务类型匹配 |
| 3 | 风险识别 | 至少 2 条风险点，含位置和缓解建议 |
| 4 | 自检通过 | 报告前 5 项自检全部 ✅ |
| 5 | 可执行 | 下一步建议指向具体 Skill 名称 |

PLACEHOLDER
- `erp-product-doc-generator` — 侦察→产品方案
- `backend-doc-generator` — 侦察→后端方案
- `frontend-doc-generator` — 侦察→前端方案
- `backend-doc-generator` — 侦察→后端方案（含变更影响面分析）
- `frontend-doc-generator` — 侦察→前端方案（含变更影响面分析）

## 关联规范

- `.context/backend/backend-scout-rules.md` — 后端侦察深度规范（Model 深度分析标准、复用判定规则、常见失误防范）
- `.context/constitution/GLOSSARY.md` — ERP 术语表（侦察输出中实体/状态/域缩写必须使用术语表标准名称）
