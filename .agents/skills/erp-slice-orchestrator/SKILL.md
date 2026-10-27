---
name: erp-slice-orchestrator
role: architect
description: >
  切片编排器。负责创建 Slice ID、初始化切片目录、路由入口模式、调用现有方案/编码/测试/审查 Skills、
  维护 slice-state.json、执行 Gate、保存证据、控制返工和状态回退。
  生命周期到 VERIFIED 终止（DEC-20260806-001）；SHADOW/PRIMARY/RETIRE 由 erp-slice-rollout 承载。
  现有 erp-pipeline-orchestrator 是其方案设计子流程。
version: "0.2"
updated: 2026-08-24
---

# ERP Slice Orchestrator — 切片执行编排器

> 本 Skill 在编码阶段启动。切片的创建和契约产出由 erp-product-doc-generator 技能7完成。

## 职责

1. 读取已有的 `specs/slices/{slice-id}/slice.yaml` + `contract.md`（product-doc-generator 产出）；
2. 按切片的 `entry_mode` 路由编码入口；
3. 调用编码/测试/审查 Skills：`backend-doc-generator`、`frontend-doc-generator`、`backend-code-generator`、`frontend-code-generator`、`erp-frontend-backend-crosscheck`、`backend-code-review`、`frontend-code-review`、`backend-api-test`；
4. 维护 `slice-state.json` 与 `run-state.json`；
5. 执行 Gate（G-CONTRACT → G-BUILD → G-VERIFY）；
6. 保存证据到 `specs/slices/{slice-id}/runs/{run-id}/evidence/{GATE}/`；
7. 控制返工与状态回退。

## 不做的事（已转移）

| 职责 | 承载者 |
|:---|:---|
| 从产品方案识别切片 | erp-product-doc-generator 技能7 |
| 产出 slice.yaml | erp-product-doc-generator 技能7 |
| 产出 contract.md | erp-product-doc-generator 技能7 |
| 更新 slice-registry.yaml | erp-product-doc-generator 技能7 |

## Gate 流程（编码阶段）

```
读 slice.yaml + contract.md（已由 product-doc-generator 产出）
→ G-CONTRACT: 前后端方案生成 + crosscheck → 冻结契约 → status: READY
→ G-BUILD: 编码到 erp-service-php / dtcplus-web-ts → 自动测试通过
→ G-VERIFY: 代码审查 + E2E 测试 → 无阻断问题 → status: VERIFIED
→ 每 Gate 收集 evidence，更新 slice-state.json
```

> G-SCOPE 和 G-PRODUCT 在产品方案阶段由 PM + 人工审核完成，不在本 Skill 范围。

## 不可违反

- 不直接修改业务代码（编码由 backend/frontend-code-generator 执行）；
- 不自行批准自己的 Gate；
- 不自动 Commit/Push/Merge；
- 状态变化必须记录时间、执行者、原因、证据；
- 仅凭完成声明不得通过 Gate；
- 切片代码写入现有项目（erp-service-php / dtcplus-web-ts），不新建 erp-next（DEC-20260806-001）；
- 技术方案按 slice-id 组织（docs/tech/{slice-id}/），不按模块名（DEC-20260806-001）。

## 文件结构（统一格式）

每个切片目录：
```
specs/slices/{slice-id}/
├── slice.yaml              # 元数据（product-doc-generator 产出）
├── contract.md             # 前后端共用契约（product-doc-generator 产出）
├── slice-state.json        # 生命周期状态（本 Skill 维护）
└── runs/{run-id}/
    ├── definitions/{ver}/  # Definition revision
    └── evidence/{GATE}/    # Gate 通过证据
```

## 验证

- 每个 Gate 使用 `scripts/slice_validate.py` 校验状态文件；
- 更新注册表并跑 `count-from-table` 检查。

## 关联技能

| Skill | 关系 | 何时协作 |
|:---|:---|:---|
| erp-product-doc-generator | 上游（技能7产出切片契约） | 产品方案阶段 |
| backend-doc-generator | 下游（读 contract.md 出后端方案） | G-CONTRACT |
| frontend-doc-generator | 下游（读 contract.md 出前端方案） | G-CONTRACT |
| backend-code-generator | 下游（读 contract.md + 方案编码） | G-BUILD |
| frontend-code-generator | 下游（读 contract.md + 方案编码） | G-BUILD |
| erp-frontend-backend-crosscheck | 下游（前后端方案核对） | G-CONTRACT |
| backend-code-review | 下游（后端代码审查） | G-VERIFY |
| frontend-code-review | 下游（前端代码审查） | G-VERIFY |
