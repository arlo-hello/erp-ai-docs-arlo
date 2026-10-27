# PM Skill 注册表

本文件记录当前仓库维护的产品经理 Skills。Skill 是否在 Multica 中启用，必须由人工选择；仓库中的存在不表示自动启用。

| Skill | 类型 | 主要用途 | 直接依赖 |
| --- | --- | --- | --- |
| `erp-requirement-analyzer` | 核心 | 需求分析与结构化 | 内部 references |
| `external-design-miner` | 核心 | 外部方案与行业参考 | 网络检索能力 |
| `erp-product-doc-generator` | 核心 | 产品方案与切片发现 | `erp-scout-protocol`、内部 references |
| `erp-slice-orchestrator` | 核心 | 切片初始化、Gate 与状态维护 | `scripts/slice_init.py`、`slice_validate.py`、`gate_check.py` |
| `solution-consistency-checker` | 核心 | 产品方案与代码一致性检查 | `erp-scout-protocol`、codebase-memory MCP |
| `systematic-debugging` | 通用 | 根因调查与调试 | 同目录参考资料 |
| `verification-before-completion` | 通用 | 完成前证据校验 | 无仓库内直接依赖 |
| `erp-scout-protocol` | 依赖 | 现状侦察与证据收集 | 代码读取/搜索能力 |

## 维护规则

1. 修改 Skill 前先记录来源版本与修改原因。
2. `SKILL.md` 不得含未解决的 Git 冲突标记。
3. Skill 引用的仓库内文件必须存在；外部工具依赖必须在说明中显式列出。
4. `.mcp.json` 属于本机配置，不提交；仅维护 `config/mcp.example.json`。
5. 未经人工确认，不在 Multica 中自动增加或启用 Skill。

