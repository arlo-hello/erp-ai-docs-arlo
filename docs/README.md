# 文档目录

本目录是产品、需求、技术方案和版本档案的工作区。新增文档必须先判断归属版本，再从对应 `docs/v{version}` 分支创建任务分支。

## 写入规则

- 当前版本读取 `docs/versions/current.txt`。
- 一个任务只提交该任务相关的文档。
- 方案、切片契约、验收标准必须在合入前自包含。
- 跨 agent 交接只认 commit SHA，不认本地未提交文件。
- 历史文档迁移必须单独提交，并说明来源仓库和来源 commit。

## 推荐目录

```text
docs/product/{version-slug}/
docs/requirements/{topic}/
docs/tech/{topic}/
docs/versions/
docs/changelogs/
docs/hotfix/
```

