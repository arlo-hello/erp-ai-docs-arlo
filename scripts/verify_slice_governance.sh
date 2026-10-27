#!/usr/bin/env bash
# 一键运行全部切片治理校验。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

echo "== 1/8 slice_validate（Schema）"
python3 scripts/slice_validate.py specs/slices

echo "== 2/8 gate_check（Gate 证据/转换/契约 digest）"
python3 scripts/gate_check.py specs/slices

echo "== 3/8 registry_check（注册表计数）"
python3 scripts/registry_check.py

echo "== 4/8 contract_check（切片准入）"
python3 scripts/contract_check.py specs/slices

echo "== 5/8 单测"
python3 -m unittest discover -s scripts/tests -p "test_*.py" -v

echo "== 6/8 YAML 解析"
python3 - <<'PY'
import yaml
from pathlib import Path
files = [
    "specs/slice-registry.yaml",
    "specs/slices/SL-ORD-001/slice.yaml",
    "specs/slices/SL-ORD-001/runs/SL-ORD-001-MIG-001/run.yaml",
    "specs/slices/SL-ORD-001/runs/SL-ORD-001-MIG-001/definitions/0001/business-rules.yaml",
    "specs/slices/SL-ORD-001/runs/SL-ORD-001-MIG-001/definitions/0001/acceptance-examples.yaml",
    "specs/slices/SL-ORD-001/runs/SL-ORD-001-MIG-001/definitions/0001/contract-refs.yaml",
    "specs/slices/SL-ORD-001/runs/SL-ORD-001-MIG-001/collaboration/tasks/ARCH-01/task.yaml",
    "specs/slices/SL-ORD-001/runs/SL-ORD-001-MIG-001/collaboration/events/slice/0001-scope-approved.yaml",
    "specs/slices/SL-MPL-QUERY/runs/SL-MPL-QUERY-MIG-001/definitions/0001/contract-refs.yaml",
    "contracts/SL-ORD-001/1.0/manifest.yaml",
    "contracts/SL-ORD-001/1.0/api.openapi.yaml",
    "contracts/SL-ORD-001/1.0/events.yaml",
    "contracts/SL-ORD-001/1.0/data-ownership.yaml",
    "contracts/SL-MPL-QUERY/1.0/manifest.yaml",
    "contracts/SL-MPL-QUERY/1.0/api.openapi.yaml",
]
for f in files:
    yaml.safe_load(Path(f).read_text(encoding="utf-8"))
print(f"YAML OK: {len(files)} files")
PY

echo "== 7/8 Python 语法"
python3 -m compileall -q scripts/slice_validate.py scripts/slice_init.py scripts/gate_check.py scripts/registry_check.py scripts/contract_check.py scripts/multica_title_check.py

echo "== 8/8 Multica 标题样例"
python3 scripts/multica_title_check.py \
  --title "[v0.28.4][REQ][ORD] 拦截缺门牌号订单流入 WMS" \
  --title "[v0.28.4][DEV][ERP-SLICE-ORD-021] 拦截缺门牌号订单流入 WMS"

echo "ALL GOVERNANCE CHECKS PASSED"
