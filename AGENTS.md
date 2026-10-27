# ERP AI Docs Agent Rules

## 身份与目标

本仓库是 ERP 文档事实源。所有 agent 在本仓库内只处理产品方案、需求、切片契约、版本记录和任务交接，不修改业务代码。

## 硬规则

1. 新增产品文档必须写入本仓库，不再写入 `erp-ai-coding/docs`。
2. 每个任务必须从对应版本分支创建任务分支，格式为 `docs/v{版本}_{四位任务号}`。
3. 任务号来自 `ERP-{number}`，例如 `ERP-111` 对应 `docs/v0.28.4_0111`。
4. 提交前必须明确本任务相关文件，禁止 `git add .`。
5. 跨 agent 交接必须提供仓库、分支、commit SHA 和文件路径。
6. 未提交、未推送或未合并的文档只是草稿，不能作为开发输入。
7. `backlog -> todo` 只能人工操作，agent 不得代替人工放行。
8. 实现切片必须独立可测试，并在契约中写明验收标准、测试边界、依赖与 Mock 策略。
9. 新增切片 ID 使用 `ERP-SLICE-{DOMAIN}-{NNN}`；`SL-*` 仅作为 legacy 兼容。
10. 版本号使用 `v{MAJOR}.{MINOR}.{PATCH}`；紧急修复使用 `hotfix-{YYYYMMDD}-p{N}`。
11. 大文件、临时 diff、日志、生成缓存不入库。
12. PM 修改文档后必须运行 `scripts/pm_autosave.py`，禁止手工 `git add / commit / push` 绕过自动沉淀。
13. 任务分支 head commit 不是开发输入；开发输入必须是人工合并后同步到 Multica metadata 的 `docs_commit`。

## 建议工作流

```bash
git checkout docs/v0.28.4
git pull origin docs/v0.28.4
./scripts/create_task_branch.sh ERP-111
```

完成文档后：

```bash
python3 scripts/pm_autosave.py \
  --issue ERP-111 \
  --title "[v0.28.4][PM][ORD] 业务结果" \
  --slice-id ERP-SLICE-ORD-021 \
  --path docs/v0.28.4/tasks/0111/product-plan.md \
  --path specs/v0.28.4/ERP-SLICE-ORD-021/contract.md
```

脚本会执行治理校验、只提交显式路径、push 任务分支、创建或更新 PR，并写入 Multica metadata / comment。草稿阶段加 `--draft`。

人工合并 PR 后，由人工或 Orchestrator 执行：

```bash
python3 scripts/sync_merged_docs.py --issue ERP-111 --pr <docs-pr-url>
python3 scripts/verify_docs_handoff.py --issue ERP-111
```

Orchestrator 只有在 verify 通过后才能创建 backlog 实现任务；`backlog -> todo` 仍必须由人工完成。
