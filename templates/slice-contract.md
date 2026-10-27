# {SLICE_ID} 切片契约

- slice_id: {SLICE_ID}
- version: v{VERSION}
- multica_issue: {ISSUE_ID}

## 业务结果

一句话描述该切片交付后的可验证业务结果。

## 范围

- 本切片负责：
- 依赖但不负责：
- 明确不做：

## 验收标准

| AC | 场景 | 预期 | 验证方式 |
| --- | --- | --- | --- |
| AC-001 |  |  | unit / feature / E2E / mock |

## 测试边界

每个 AC 必须能通过 unit / feature / E2E / mock 中至少一种方式独立验证。

- 独立验证声明：是
- 本切片可在自己的任务分支上验证全部 AC。
- 外部系统只通过契约明确允许的 mock 边界替换。

## 依赖与 Mock 策略

- 前置依赖：
- 外部系统：
- Mock 边界：
- 未合入依赖处理：

## 开发交接

```yaml
version: v0.28.4
multica_issue: ERP-
slice_id: ERP-SLICE-
docs_repo: arlo-hello/erp-ai-docs
docs_branch: docs/v0.28.4_{四位任务号}
docs_head_commit: <任务分支 head commit；草稿或待审>
docs_commit: <人工合并进版本分支后的 commit；开发输入>
docs_paths:
  -
```
