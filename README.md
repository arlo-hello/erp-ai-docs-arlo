# ERP AI Docs & PM Agent Workspace

ERP 产品方案、需求、切片契约、版本档案与产品经理 Agent Skills 的统一维护仓库。本仓库不承载前后端业务代码，也不包含原项目的真实生产文档。

## 职责边界

| 位置 | 职责 |
| --- | --- |
| `docs/`、`specs/` | 产品方案、需求、切片契约、版本档案和任务交接引用 |
| `agents/` | Multica Agent 提示词基线 |
| `.agents/skills/` | 经选择的 Skills 及其内部参考资料 |
| `scripts/` | 文档治理、切片校验和交接脚本 |
| `config/` | 不含密钥和本机绝对路径的配置示例 |
| 后端 / 前端代码仓库 | 业务代码实现、代码 PR 和发版 tag |

产品 Agent 新产出的方案、切片、契约和版本记录必须提交到本仓库。前后端代码仓库仅作为只读侦察或开发目标，不作为产品文档事实源。

## 当前范围

- 已保留文档治理基线、模板和必要脚本。
- 已收录用户指定的七个 Skill，并补充直接依赖 `erp-scout-protocol`。
- 未收录任何真实任务、真实切片、知识库、前后端源码、凭证或本机 MCP 配置。
- Skill 的启用与组合仍在 Multica 中人工选择；本仓库负责版本化维护。
- 当前内容是迁移基线，后续再根据个人工作方式调整 Agent 和 Skill。

## 分支模型

```text
main                      # 已完结版本档案和治理结果
template                  # 模板、脚本和治理规则基线，不放业务文档
docs/v0.28.4              # 当前版本文档集成分支
docs/v0.28.4_0111         # 当前切片任务文档分支
```

版本分支从 `template` 创建，并在版本分支首次提交中创建 `docs/{version}/` 与 `specs/{version}/`。任务分支从对应版本分支创建。任务文档 PR 只合并回对应版本分支，版本完结后再由 `docs/v0.28.4` 人工审核合回 `main`。

## 任务分支命名

```text
docs/{version}_{issue-id}
```

示例：

```text
docs/v0.28.4_0111
```

任务号是 Multica `ERP-{number}` 的四位零填充形式；超过四位时保留完整位数。任务分支、Multica Issue 和切片 ID 的映射必须写在任务交接中。不要使用 `codex/`、`tmp/`、`update/` 这类无法追溯任务的分支名。

## 跨 Agent 交接

产品 agent 完成方案后，必须提供稳定引用：

```yaml
docs_repo: arlo-hello/erp-ai-docs
docs_branch: docs/v0.28.4_0111
docs_commit: <40-bit commit SHA>
docs_paths:
  - docs/product/v28.4/...
  - specs/slices/ERP-SLICE-ORD-021/contract.md
```

禁止使用“当前工作区”“最新文件”“刚才生成的文件”作为交接引用。没有 commit SHA 的文档视为草稿，不允许放行开发。

## 人工放行闸门

1. 产品 agent 在任务分支产出文档。
2. 每次修改后运行 PM autosave：自动校验、显式路径提交、push 任务分支、创建或更新 PR，并写回 Multica metadata / comment。
3. Orchestrator 校验标题、切片 ID、契约和准入门槛。
4. 人工审核并合并产品文档 PR。
5. 合并后运行 merged docs sync，把 `docs_commit` 更新为版本分支上的 merge commit。
6. Orchestrator 运行 handoff verify；全部通过后仅登记 backlog 实现任务。
7. 人工把实现任务从 `backlog` 改为 `todo`。
8. 开发 agent 才能按 `docs_commit` 创建代码任务分支并执行。

## PM 自动沉淀

草稿更新：

```bash
python3 scripts/pm_autosave.py \
  --issue ERP-111 \
  --path docs/v0.28.4/tasks/0111/product-plan.md \
  --draft
```

完成更新：

```bash
python3 scripts/pm_autosave.py \
  --issue ERP-111 \
  --title "[v0.28.4][PM][ORD] 业务结果" \
  --slice-id ERP-SLICE-ORD-021 \
  --path docs/v0.28.4/tasks/0111/product-plan.md \
  --path specs/v0.28.4/ERP-SLICE-ORD-021/contract.md
```

人工合并 PR 后：

```bash
python3 scripts/sync_merged_docs.py \
  --issue ERP-111 \
  --pr https://github.com/arlo-hello/erp-ai-docs/pull/1
```

开发放行前：

```bash
python3 scripts/verify_docs_handoff.py --issue ERP-111
```

PM autosave 永远不会合并 PR，也不会修改实现 Issue 状态。任务分支上的 head commit 只表示草稿或待审版本；开发只能使用已写入 Multica metadata 的 `docs_commit`。

## 目录结构

```text
docs/
  README.md
  versions/             # 版本索引和 current.txt
  v0.28.4/              # 当前版本的任务、需求和方案档案
specs/
  README.md
  v0.28.4/
    slice-registry.yaml # 当前版本切片索引
    slices/             # 当前版本每个切片的契约和状态
templates/
  product-plan.md
  slice-contract.md
  task-handoff.md
scripts/
  create_version_branch.sh
  create_task_branch.sh
  check_governance.py
  pm_autosave.py
  sync_merged_docs.py
  verify_docs_handoff.py
  multica_title_check.py
  registry_check.py
  contract_check.py
```
