# 技能7：切片发现与契约产出

> 从产品方案中识别最小端到端业务结果，产出切片契约。

**角色**：产品经理 + 架构师视角

**输入**：技能6输出的PRD（含功能点、数据模型、接口定义）

**任务**：从产品方案中识别最小端到端业务结果（切片），为每个切片产出统一格式的契约文件，登记到切片注册表。

---

## 切片定义

一个切片 = 一个最小可独立交付的端到端业务结果。不是按页面拆、不是按 CRUD 拆，而是按"做完这整块，业务能跑通一个完整结果"拆。

**判断标准**：这个拆分单元如果单独上线，业务是否能获得一个完整的端到端价值？能 → 是切片；不能（只是某个页面、某个接口）→ 太细，需要合并。

---

## 切片发现七步法

### 步骤1：从功能点提取业务结果

读技能5的功能点列表（`功能设计说明.md`），按"端到端业务结果"聚合：

| 功能点 | 归属业务结果（业务结果名） | 理由 |
|:---|:---|:---|
| F-01 ~ F-05 | 创建异常监控页面 | 这5个功能点组合后业务获得"查看异常"这个完整结果 |
| F-06 ~ F-08 | 分类规则配置 | 组合后业务获得"自配置分类"这个完整结果 |

> 聚合原则：一个业务结果包含的功能点，去掉任何一个都会导致结果不完整。

### 步骤2：依赖排序

按数据流和业务时序排序：

| 切片 | 依赖 | 依赖原因 |
|:---|:---|:---|
| SL-XX-001 事件表 | 无 | 基础数据层 |
| SL-XX-002 规则表 | 无 | 基础配置层 |
| SL-XX-003 写入引擎 | 001 + 002 | 读写依赖前两层 |

### 步骤3：分配 Slice ID

命名规则：`SL-{DOMAIN}-{序号}`

- DOMAIN 从技能4模块划分的领域缩写取（ORDER/IMS/PUR/PRODUCT/PLAT/LOGIS/ASS/PAY/FIN/COMM）
- 序号三位数字，同域内递增
- 查 `specs/slice-registry.yaml` 确认序号不冲突

🔴 **切片名规则**：`slice_id` 是工程稳定 ID；`name` 必须是业务结果名，格式为“动作/结果 + 业务对象 + 可感知业务结果”，不得只写技术实现、类名或双写机制。示例：`识别异常订单并分派处理`。端侧页面名仍使用技能1的端侧展示名，不用切片名替代。

### 步骤4：产出 slice.yaml（每个切片一份）

统一路径：`specs/slices/{slice-id}/slice.yaml`

```yaml
slice_id: SL-ORD-007
name: 识别异常订单并分派处理
slice_kind: WRITE          # WRITE / READ_ONLY
entry_mode: NEW_CAPABILITY # NEW_CAPABILITY / LEGACY_MIGRATION / EXISTING_SLICE_CHANGE
value_stream: order-to-fulfillment
capability: exception-monitor
primary_actor: operations
domain_owner: ORDER
depends_on:                # 依赖的其他 slice-id
  - SL-ORD-005
  - SL-ORD-006
prd_ref: docs/product/exception-monitor/ERP-52-异常订单实时监控-prd.md#§7.2
code_targets:
  backend:
    path: erp-service-php/app/Domains/B2cOrders/Services/OrderExceptionService.php
    layers: [Services]
  frontend:
    path: ""
    layers: []
```

### 步骤5：产出 contract.md（每个切片一份）

统一路径：`specs/slices/{slice-id}/contract.md`

**契约模板**：

```markdown
# {slice-id} {业务结果名} 契约（前后端共用唯一契约）

> 契约冻结后，前后端编码以本文件为唯一输入。变更须创建新 Definition revision。

- slice_id: {slice-id} | status: DEFINED
- 后端：{code_path} | 前端：{code_path}

## 1. 改造范围 / 新建范围

| 方法/页面 | 现状 | 改造内容 |
|:---|:---|:---|
| ... | ... | ... |

## 2. 数据模型变更（如有）

| 表 | 变更类型 | 字段 | 说明 |
|:---|:---|:---|:---|
| 新增表/加字段/改字段 | ... | ... | ... |

## 3. API 端点（如有）

| 方法 | 路径 | 请求 | 响应 | 说明 |
|:---|:---|:---|:---|:---|
| GET | /api/... | ... | ... | ... |

## 4. 业务规则

（从 PRD 提取与本切片直接相关的规则，逐条列出）

## 5. 验收标准

| # | 验收项 | 通过条件 |
|:---|:---|:---|
| 1 | ... | ... |

## 6. 依赖说明

| 依赖切片 | 依赖内容 | 影响（如依赖未就绪） | 降级方案 |
|:---|:---|:---|:---|
| ... | ... | ... | 填可执行的替代路径；确无降级时写“不上线”并说明原因 |
```

### 步骤6：更新 slice-registry.yaml

在 `specs/slice-registry.yaml` 的 `slices:` 列表末尾追加新切片条目：

```yaml
  - slice_id: SL-ORD-007
    name: 识别异常订单并分派处理
    slice_kind: WRITE
    status: DEFINED          # DEFINED=契约已产出 / READY=人工确认后 / VERIFIED=编码测试通过
    value_stream: order-to-fulfillment
    capability: exception-monitor
    domain_owner: ORDER
    business_owner: operations
    depends_on: [SL-ORD-005, SL-ORD-006]
    source_ref: docs/product/{module}/ERP-XX-prd.md
    notes: 一句话说明
```

同时更新 `summary:` 部分（total/write/read_only/defined/candidate 计数），逐行数表确认。

### 步骤7：自检

| # | 检查项 | 通过条件 |
|:---|:---|:---|
| 1 | 所有功能点被覆盖 | 功能点列表中每个 F-XX 都归属于某个切片 |
| 2 | Slice ID 无冲突 | 查 registry 确认无重复 |
| 3 | 依赖无环 | 依赖关系是 DAG（有向无环图）|
| 4 | contract.md 统一格式 | 每个切片都有 slice.yaml + contract.md |
| 5 | registry summary 计数正确 | 逐行数表，不声明总数 |
| 6 | 切片粒度合理 | 每个切片是端到端业务结果，不是单个页面或接口 |
| 7 | 切片命名合规 | `slice_id` 保持稳定；`name` 是业务结果名，不写纯技术实现 |
| 8 | 依赖可降级 | 每个依赖写影响和降级方案；确无降级时明确不上线 |

---

## 产出文件

| 文件 | 路径 | 说明 |
|:---|:---|:---|
| slice.yaml | `specs/slices/{slice-id}/slice.yaml` | 切片元数据 |
| contract.md | `specs/slices/{slice-id}/contract.md` | 前后端共用契约 |
| registry 更新 | `specs/slice-registry.yaml` | 追加新切片条目 |

> 注意：不再产出 `06-deliverables.md`（WBS 交付项清单）。交付拆分由切片体系承接。

---

## 与下游的衔接

| 下游 | 读什么 | 何时 |
|:---|:---|:---|
| 人工审核 | contract.md + PRD | 产品方案审核 Gate |
| erp-slice-orchestrator | slice.yaml + slice-state.json | 编码阶段 Gate 推进 |
| backend-doc-generator | contract.md + PRD 对应章节 | 后端技术方案 |
| frontend-doc-generator | contract.md + PRD 对应章节 | 前端技术方案 |
| backend-code-generator | contract.md + 技术方案 | 后端编码 |
| frontend-code-generator | contract.md + 技术方案 | 前端编码 |
