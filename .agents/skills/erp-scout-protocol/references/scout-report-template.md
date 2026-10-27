# 侦察报告模板

> 由 `erp-scout-protocol` 生成。根据任务类型选择对应模板。

---

## 模板 A：新建功能

```
🗺️ 侦察报告 — 新建功能
━━━━━━━━━━━━━━━━━━━━━━━━━━
任务: {描述}
侦察深度: 标准 / 深度
━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 代码地图（已验证存在）

  前端:
    pages/{module}/
    ├── list.tsx          ← 页面入口
    ├── columns.tsx       ← 表格列定义
    └── schema.ts         ← 表单 Schema

  后端:
    Api/Controllers/{Module}/{Module}Controller.php
    Domains/{Module}/Services/{Module}Service.php
    Domains/{Module}/Models/{Model}.php

📐 可用模式（可参考的类似实现）

  | 模块 | 文件 | 可复用模式 |
  |------|------|-----------|
  | {similar_module} | {file}:{line} | {pattern description} |

🏙️ 双城边界建议

  新城（新建）:
    - {new_file_path}  ← 新建
    - {new_service}     ← 新建

  旧城（只读/谨慎修改）:
    - {existing} → 仅添加调用点

🗄️ DB 迁移需求

  | 表 | 操作 | 关键字段 |
  |----|------|---------|
  | {table} | CREATE/ALTER | {fields} |

⚠️ 风险点

  1. {risk} — {location} — {mitigation}
  2. {risk} — {location} — {mitigation}

📋 下一步
  → erp-product-doc-generator（产品方案）
  → backend-code-generator（后端实现）
  → frontend-code-generator（前端实现）
```

---

## 模板 B：修改功能

```
🗺️ 侦察报告 — 修改功能
━━━━━━━━━━━━━━━━━━━━━━━━━━
任务: {描述}
侦察深度: 快速 / 标准
━━━━━━━━━━━━━━━━━━━━━━━━━━

📍 修改目标

  | 文件 | 位置 | 修改内容 |
  |------|------|---------|
  | {file} | :{line} | {change} |

🔗 调用方清单（影响面）

  | 调用方 | 文件:行号 | 影响 |
  |--------|----------|------|
  | {caller} | {file}:{line} | {impact} |

🕐 Git 最近修改（避免覆盖）

  | 提交 | 日期 | 说明 |
  |------|------|------|
  | {hash} | {date} | {msg} — ⚠️ 注意保留此逻辑 |

⚠️ 风险点

  1. {risk} — {affected_callers} 个调用方受影响
  2. {risk} — 上次修复 {hash} 可能被覆盖

📋 下一步
  → 确认修改范围无误
  → backend-doc-generator（场景 B：变更影响面分析）
```

---

## 模板 C：调查问题

```
🗺️ 侦察报告 — 调查问题
━━━━━━━━━━━━━━━━━━━━━━━━━━
问题: {描述}
侦察深度: 标准 / 深度
━━━━━━━━━━━━━━━━━━━━━━━━━━

🔍 数据流追踪

  {entry_point}:{line}
    → {middle_layer}:{line}
      → {data_source}:{line}

❓ 可疑点

  | # | 位置 | 可疑原因 |
  |---|------|---------|
  | 1 | {file}:{line} | {reason} |
  | 2 | {file}:{line} | {reason} |

💡 根因假设

  最可能: {hypothesis} — 置信度 {high/medium/low}
  次可能: {alternative}

⚠️ 风险点

  1. {risk}
  2. {risk}

📋 下一步
  → 验证根因假设
  → 确认修复方案后再编码
```
