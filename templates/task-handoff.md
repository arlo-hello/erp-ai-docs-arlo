# {ISSUE_ID} 文档交接

## 任务信息

- Multica Issue：
- 版本：
- 切片 ID：
- 文档任务分支：`docs/v0.28.4_{四位任务号}`
- 建议执行人：
- 并行策略：

## 稳定引用

```yaml
docs_repo: arlo-hello/erp-ai-docs
docs_branch: docs/v0.28.4_{四位任务号}
docs_head_commit: <任务分支 head commit；草稿或待审>
docs_commit: <人工合并进版本分支后的 commit；开发输入>
docs_paths:
  - docs/v0.28.4/
  - specs/v0.28.4/
```

## 校验结果

- 标题规范：
- 切片 ID：
- 契约完整性：
- 独立可测试：
- 依赖与 Mock：

## 人工放行

- [ ] 产品文档 PR 已审核并合入版本分支。
- [ ] Multica 实现任务已记录 `docs_commit`。
- [ ] 人工将实现任务从 `backlog` 改为 `todo`。

> Agent 禁止代替人工执行 `backlog -> todo`。
