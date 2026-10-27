---
name: solution-consistency-checker
role: architect
description: >
  产品方案与真实代码的一致性/漂移校对器:拿一份已有的产品方案/PRD/产品文档,回头和代码对照,
  查它有没有真被实现、有没有漂移、还准不准——一端是文档、另一端是代码本身,以代码为事实源,
  逐项核对方案里的功能点、领域事件、字段、业务链路、影响范围在代码里存不存在、对不对得上,
  只报差异、不评设计。触发场景:用户手上已有某模块的方案/PRD(常在 docs/product/{模块}/),
  想确认代码有没有按它落地。典型说法:"核对方案和代码"、"方案跟代码对得上吗"、
  "产品文档/方案跟代码有没有漂移"、"PRD 还准不准/落地了吗"、"代码有没有按方案实现"、
  "方案写的字段/领域事件/调用链代码里实现了没"、"trace 一下看是不是按方案走的"、
  "看看退货方案跟代码差多少"。凡是"已有文档 ↔ 已写代码"之间的一致性核对都走本 skill。
  区别开:erp-product-doc-generator 是生成/梳理方案;erp-frontend-backend-crosscheck 是
  前端方案文档 ↔ 后端方案文档(两端都是文档);erp-api-integration 是代码 ↔ api-design.md。
  本 skill 独占"产品方案 ↔ 落地代码"的核对,依赖 codebase-memory-mcp 取代码事实。
version: "0.3"
updated: 2026-07-09
changelog:
  - "0.3: 优化 description 触发描述(采纳 run_loop 生成器的高质量改写)。注:run_loop 报 recall≡0 是其检测的命名冲突 bug——已安装的真身 skill 被正常触发,但 run_eval 只匹配自建的临时 command 名(带 hash 后缀),故永远不计。经手动 Codex -p 诊断确认触发正常"
  - "0.2: 字段增「类型/长度」+「孤儿列/API断链」两项必做子检查;报告增 P0/P1/P2 修复优先级 + 调用工具清单;基于 iteration-1 评测反馈"
  - "0.1: 初版——修正草稿 6 个虚构工具→真实 14 工具,兼容新旧命名,五维对比"
---

# 产品方案与代码一致性校对器

> **一句话**:`erp-product-doc-generator` 把需求/代码正向变成产品方案;本 skill 反向——拿产品方案回头**核对真实代码**,输出一份"方案说的 vs 代码有的"差异报告。座右铭:**只报告差异,不评价设计。**

---

## 定位:与现有 skills 的边界(先读这一节)

多个 skill 名字里都有"核对/一致性",极易踩重。四者做的是**不同层的对比**,别混:

| Skill | 对比的两端 | 时机 | 事实源 |
|:---|:---|:---|:---|
| `erp-product-doc-generator` | 需求/代码 → **生成** 产品方案 | 方案阶段 | (正向,非对比) |
| **`solution-consistency-checker`(本)** | **产品方案 ↔ 真实代码** | 方案已存在、代码已(部分)实现后 | **代码(图谱)** |
| `erp-frontend-backend-crosscheck` | 前端方案文档 ↔ 后端方案文档 | 编码前 | 产品方案字段表 |
| `erp-api-integration` | 已写代码 ↔ api-design.md | 编码后 | api-design.md |
| `erp-scout-protocol` | (通用侦察,Glob/Grep 定位) | 任务第零步 | 代码文件 |

**本 skill 独占的格子**:产品方案(PRD)与**已落地代码**之间的一致性/漂移。典型用途:
1. 用了"代码驱动模式"逆向生成的 PRD,想反向验证它是否忠实于代码;
2. 一份老 PRD,想确认它对当前代码还准不准(**漂移检测**);
3. 需求变更实现后,核对代码是否覆盖了方案里的每个功能点/事件/字段。

> 与 `erp-scout-protocol` 的关系:侦察协议用 Glob/Grep 手工定位,本 skill 是**图谱驱动版**——用 codebase-memory-mcp 一次拿到调用链、依赖、字段,快且全。可把本 skill 视为"带图谱的、面向 PRD 的深度侦察对照"。

---

## 核心原则

1. **代码是事实源**:代码里有什么就记录什么。方案有、代码无 → 标 `❌ 待确认`;代码有、方案无 → 标 `⚠️ 方案遗漏`。绝不为了让方案"看起来对"而编造代码里没有的东西。
2. **只输出差异**:一致项不占篇幅(仅在总结里计数)。人工只审不一致项——这是本报告存在的意义。
3. **每个差异可追溯**:差异必须带来源——代码侧 `文件:行号` 或符号限定名,方案侧 `文件 + 章节/表格`。无法定位来源的"差异"不可信,不要写。

---

## 依赖能力:codebase-memory-mcp 的真实工具

> ⚠️ **只用下面这些真实工具**。历史草稿里的 `get_symbol_details` / `get_call_map` / `get_outgoing_calls` / `get_incoming_calls` / `get_dependents` / `get_blast_radius` **都不存在**,已按下表映射到真实工具。

### 调用方式(两种等价)
- **MCP 模式**(Codex 已加载 `.mcp.json` 时):直接调用工具,如 `search_graph({...})`。
- **CLI 兜底**(MCP 未加载 / 子代理环境):`codebase-memory-mcp cli <工具名> '{...json参数...}'`,同引擎同输出。
- **每次开工先跑 `list_projects`** 拿准确项目名(本项目为 `Users-apple-ERPAI-erp-service-php`、`Users-apple-ERPAI-dtcplus-web-ts`),后续所有查询都带 `"project": "<名>"` 以免跨库串味。

### 工具映射表(草稿假名 → 真实工具)

| 需求 | 真实工具 | 关键参数 | 说明 |
|:---|:---|:---|:---|
| 摸清图谱结构 | `get_graph_schema` | `project` | 开场先跑,知道有哪些标签/边 |
| 找符号(类/方法/组件) | `search_graph` | `name_pattern`(正则)、`label`、`file_pattern`、`project`、`limit` | 定位入口,拿 `qualified_name` |
| 读某符号源码 | `get_code_snippet` | `qualified_name` | 先 `search_graph` 拿限定名再读 |
| 文本/模式搜索 | `search_code` | `pattern`、`project` | grep 式,搜事件发布/onClick 等 |
| 它调用了谁 | `trace_path` | `function_name` 或 `qualified_name`、`direction:"outbound"` | 追 Controller→Service→Repo |
| 谁调用了它 / 依赖方 | `trace_path` | `direction:"inbound"` | 找调用者、订阅者、依赖方 |
| 双向调用链 | `trace_path` | `direction:"both"`、`depth:1-5` | 完整上下游 |
| 自定义图查询 | `query_graph` | `query`(只读 openCypher 子集)、`project` | 查 IMPORTS/USES_TYPE 边、死代码 |
| 架构/路由/热点总览 | `get_architecture` | `aspects:[...]`、`project` | 拿路由清单、高扇入枢纽 |
| **本次改动**的影响面 | `detect_changes` | `project` | ⚠️ 只映射**未提交 git diff**,不是"任意实体的影响" |

> **实体级"影响范围"怎么算**(方案 §影响范围常写"改 ReturnOrder 会波及…"):`detect_changes` 只看 git diff,**不能**传一个实体名。正确姿势:`search_graph` 找到该 Model/实体 → `trace_path(direction:"inbound")` 拿依赖方 + `query_graph` 查 `IMPORTS`/`USES_TYPE`/`CALLS` 入边。只有当"本次需求已产生未提交改动"时,才用 `detect_changes` 拿真实 blast radius。

---

## 输入

| 输入 | 来源 | 提供什么 |
|:---|:---|:---|
| 产品方案(必需) | `docs/product/{module}/` | 功能点、线框/按钮、字段表、事件、链路、影响范围 |
| 目标模块名 | 从路径或用户话里取 | 定位方案目录 + 图谱查询范围 |
| 代码图谱(必需) | codebase-memory-mcp 已索引的项目 | 代码事实源 |

### 方案文件结构(两种命名都要认)

| 概念 | 新格式(现行) | 旧格式(已废弃但仍有存量) |
|:---|:---|:---|
| 领域事件 | `00-events.md` | 散见于 `05-feature-points.md` / `08-flow-linkage.md` |
| 影响/影响范围 | `01-impact.md` | `02-change-analysis.md` / `04-data-change-analysis.md` |
| 业务链路/泳道 | `02-chains.md` | `08-flow-linkage.md` / `09-state-linkage-matrix.md` |
| 模块/功能树 | `03-modules.md` | `05-feature-points.md` |
| 功能点/线框/字段/物理模型 | `04-features.md` | `01-product-design.md` / `03-data-relationships.md` |
| 整合 PRD | `05-design.md` | (旧格式无独立整合) |
| 交付项 WBS | `06-deliverables.md` | — |

> Step 0 先 `ls docs/product/{module}/` 判定命名格式,再决定读哪些文件。文件缺失 → 该维度标"方案未提供,跳过"。

---

## 执行流程(按顺序)

### Step 0：前置检查
- `list_projects` 确认目标仓库已索引;未索引 → 🛑 提示先 `index_repository`,不要在空图谱上瞎跑。
- `ls docs/product/{module}/` 判定新/旧命名;方案目录不存在 → 🛑 提示先用 `erp-product-doc-generator` 生成。
- `get_graph_schema` + `get_architecture(aspects:["languages","routes"])` 建立代码全局认知。

### Step 1：从方案提取"方案基线"
按上表读对应文件,逐类提取(**逐行,禁止摘要压缩**):
1. **功能点清单**:功能名 + 所在页面 + 触发按钮(来源 `04-features.md` 功能点表/按钮表/线框图)。
2. **业务链路**:核心流程的有序步骤(来源 `02-chains.md` 泳道图/单据三元组)。
3. **领域事件**:事件名 + 发布时机 + 订阅方(来源 `00-events.md`)。
4. **字段基线**:实体 → 字段名/类型/必填(来源 `04-features.md` 字段表 + 物理数据模型)。
5. **影响范围**:方案声明会受影响的模块/实体/文件(来源 `01-impact.md`)。

### Step 2：从代码生成"事实基线"
对 Step 1 每一类,用真实工具取代码事实:

- **2.1 功能点 → 代码**:后端按钮/操作 → `get_architecture(aspects:["routes"])` 拿路由清单 + `search_graph(label:"Route"/"Method")` 定位 Controller 方法;前端交互 → `search_code(pattern:"onClick|@click|useMutation|form\\.")` + `search_graph(label:"Function", name_pattern:"页面名")`。产出《代码功能点清单》(功能 → 符号限定名 → 文件:行号)。
- **2.2 业务链路 → 代码**:找入口 Controller 方法(`search_graph`)→ `trace_path(direction:"outbound", depth:5)` 追到叶子(DB 写入/事件发布/外部调用)。产出《代码链路图》(完整路径 + 每节点签名与位置)。
- **2.3 领域事件 → 代码**:`search_code(pattern:"event\\(new|dispatch\\(|::dispatch")` 找所有发布点;每个事件 `trace_path(inbound)` 找发布者、搜 Listener/Handler 找订阅者。产出《代码事件清单》(事件 → 发布位置 → 订阅者)。
- **2.4 字段 → 代码**:`search_graph(label:"Class", name_pattern:"实体名")` → `get_code_snippet(qualified_name)` 读 Model 字段/`$fillable`/常量;必要时查 migration。前端 `search_code(pattern:"columns|accessorKey|z\\.")` 拿列/校验。产出《代码字段基线》。
  - **字段类型/长度子检查(必做)**:每个字段取 Request 校验(`max:N`/`required`/`nullable`)与 DB 列定义(`varchar(N)`/`not null`)对比——Request 上限 > DB 列长 → 标 `🔶 超长入库风险(可能 500)`;必填性不一致 → 标 `🔶`。此项 grep/read 也能做,但必须做,别漏。
  - **API 打通三层核对(必做)**:一个字段"落地" = DB 列存在 **且** Request 可写 **且** Resource 可读。仅 DB 有列但 Request/Service/Resource 未经手 → 标 `🕳️ 孤儿列/API断链`(功能实为未落地),**不可当作"一致"**。这是本类代码库最常见的伪一致陷阱。
- **2.5 影响范围 → 代码**:核心实体 `search_graph` 定位 → `trace_path(inbound)` + `query_graph`(查 `IMPORTS`/`USES_TYPE` 入边)得依赖方全集;若本次需求已有未提交改动,叠加 `detect_changes` 的 blast radius。产出《代码影响范围》(受影响文件,按类型分组)。

> 任一工具调用失败/返回空:在报告对应项标 **`⛔ 无法验证`** 并附原因,**不要跳过、不要猜**。

### Step 3：交叉对比(五维)
逐项比对"方案基线"与"事实基线",每维产出差异表。状态图标统一:
`✅ 一致` · `❌ 方案有代码无(待确认/未实现)` · `⚠️ 代码有方案无(方案遗漏)` · `🔶 类型/长度不一致` · `🕳️ 孤儿列/API断链(DB 有列但 Request/Service/Resource 未打通)` · `⛔ 无法验证`

对比五维:① 功能点 ② 业务链路(方案步骤 vs 代码调用链,标出方案缺的代码步骤 & 代码有方案没写的分支)③ 领域事件(发布点是否存在、订阅者是否完整)④ 字段(遗漏/疑似新增/类型或长度不一致 + **孤儿列断链**——见 2.4 两项必做子检查)⑤ 影响范围(方案列的 vs 图谱算的,标方案漏掉的文件)。

### Step 4：输出报告
按下方固定模板,分级 + 可操作。

### Step 5：自检
跑"自检清单",输出"自检报告"。

---

## 报告模板(固定结构)

```markdown
# 产品方案一致性报告 · {模块名}

## 基本信息
- 审核模块 / 方案目录 / 命名格式(新|旧)
- 代码项目(图谱项目名 + 分支 + HEAD)
- 审核时间 / 审核人:solution-consistency-checker(AI)

## 差异总览
| 维度 | 一致 | 差异 | 无法验证 |
|:--|:--|:--|:--|
| 功能点 / 业务链路 / 领域事件 / 字段 / 影响范围 | ... | ... | ... |

## 一、功能点差异
| 方案功能点 | 代码实际(符号 / 文件:行号) | 状态 | 说明与修复方向 |

## 二、业务链路差异
### 方案链路   ### 代码链路   ### 差异点(❌ 缺失步骤 / ⚠️ 未描述分支)

## 三、领域事件差异
| 事件名 | 方案有? | 代码发布位置 | 订阅者 | 状态 |

## 四、字段差异
| 字段 | 实体 | 差异类型(遗漏/疑似新增/类型长度/🕳️孤儿列断链) | 方案 | 代码(DB列·Request·Resource 三层状态) | 来源 |

## 五、影响范围差异
| 方案列出 | 图谱分析 | 状态 |

## 总结
- 一致 X · 差异 Y · 待确认 Z · 无法验证 W
- 🔴 阻断项(如有)优先处理:...

## 修复优先级(可操作)
| 优先级 | 差异项 | 修复方向 | 修复端 |
|:--|:--|:--|:--|
| P0 | 阻断/静默丢数据(断链恒空字段、超长入库、核心功能缺失) | ... | 代码/方案 |
| P1 | 功能异常但不崩(字段错层、旧流未关闭) | ... | |
| P2 | 文档过时/命名/清理孤儿列 | ... | |

## 本次调用工具清单(可审计)
`list_projects` ×n · `search_graph` ×n · `get_code_snippet` ×n · `trace_path` ×n · `search_code` ×n …(逐一列出,便于人工复核结论来源)
```

**分级(借鉴 crosscheck)**:🔴 阻断(方案核心功能/事件代码完全缺失)· 🟠 严重(字段/链路关键节点不符,会导致功能异常)· 🟡 警告(命名/次要分支不一致)· 🟢 建议(代码有增强、方案可补记)。

---

## 边界情况

| 情况 | 策略 |
|:---|:---|
| 方案目录不存在 | 🛑 提示先 `erp-product-doc-generator` |
| 代码未索引 | 🛑 提示先 `index_repository` |
| 某方案文件缺失 | 该维度标"方案未提供,跳过",不推断 |
| 图谱查不到符号 | 先放宽 `name_pattern` 重试;仍无 → 标 `⛔ 无法验证`,不猜 |
| 方案是旧格式命名 | 按输入表映射旧文件,报告注明"旧格式" |
| 实体是 DB 表而非代码符号 | 图谱索引的是代码符号;转为找引用该表的 Model/Repository 符号 |

---

## 约束

- **只读**:绝不修改任何代码或方案文档;只产出报告。
- **不评设计**:只报"一致/不一致",不判断方案好坏、不建议重设计。
- **可追溯**:每个差异必须有代码 `文件:行号`/限定名 + 方案 `文件:章节`。
- **失败显式**:工具调用失败标 `⛔ 无法验证` + 原因,禁止静默跳过或编造。
- **禁止一句话声明**:不得用"已全部核对,无差异"代替逐项对照表(与 crosscheck 同规矩)。

---

## 自检清单(输出前逐条)
- [ ] Step 0 前置检查通过(项目已索引 + 方案目录存在 + 命名格式已判定)
- [ ] Step 1 五类方案基线均已逐行提取(非摘要)
- [ ] Step 2 五类事实基线均由**真实工具**取得,失败项已标 `⛔`
- [ ] Step 3 五维对比全部完成
- [ ] 每个差异项都带双侧来源(代码 + 方案)
- [ ] 一致项已省略,仅在总览计数
- [ ] 分级正确(🔴🟠🟡🟢),并给出 P0/P1/P2 修复优先级
- [ ] 字段维度已做「类型/长度」+「孤儿列/API断链」两项子检查
- [ ] 报告正文回显了本次调用的工具清单(可审计)

## 自检报告格式
```
## 自检报告
- [x] 前置检查:项目 {名} 已索引;方案 {module} 命名格式 {新|旧}
- [x] 方案基线:功能点 X · 事件 Y · 字段 Z · 链路 A 条 · 影响项 B
- [x] 代码事实:调用工具 N 次(search_graph/trace_path/...),无法验证 M 项
- [x] 交叉对比:差异 P(🔴a 🟠b 🟡c 🟢d),待确认 Q
- [x] 所有差异均带双侧来源
```

---

## 关联技能
- `erp-product-doc-generator` — 正向生成产品方案(本 skill 的逆向对象/前置)
- `erp-scout-protocol` — 通用侦察(本 skill 是其图谱驱动 + 面向 PRD 的深化)
- `erp-frontend-backend-crosscheck` — 文档↔文档核对(编码前,不同层)
- `erp-api-integration` — 代码↔api-design.md 核对(编码后,不同层)
- codebase-memory-mcp — 代码事实源(14 工具,详见 `.mcp.json` 与项目 README)
