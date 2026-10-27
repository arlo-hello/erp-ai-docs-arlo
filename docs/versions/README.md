# 版本管理

## 版本规则

- 计划版本：`v{MAJOR}.{MINOR}.{PATCH}`，例如 `v0.28.4`。
- 版本迭代：进入当前 semver 版本。
- Bug 修复：非紧急 Bug 进入当前 semver 版本。
- 大版本重构：MAJOR 递增，并使用 `major/v{版本}` 代码集成分支。
- 紧急修复：`hotfix-{YYYYMMDD}-p{N}`，不占用 semver 序号。

## 文档分支

```text
docs/v0.28.4
docs/v0.28.4_0111
```

版本分支从 `template` 创建，并在首次提交中创建 `docs/{version}/`、`specs/{version}/` 和 `docs/versions/current.txt`。任务分支从版本分支创建并 PR 回版本分支。任务号来自 Multica `ERP-{number}`，不足四位左侧补零，例如 `ERP-111` 对应 `0111`。版本交付完成后，`docs/v0.28.4` 再人工合回 `main` 形成长期档案。

## 代码分支对应

| 文档分支 | 代码集成分支 |
| --- | --- |
| `docs/v0.28.4` | `feat/v0.28.4` |
| `docs/v1.0.0` | `major/v1.0.0` |
| `docs/hotfix-20260908-p1` | `hotfix/v20260908-p1` |

开发任务只基于代码集成分支创建子分支，不直接基于文档分支创建代码分支。
