#!/usr/bin/env python3
"""Scaffold a new ERP business slice directory.

Usage:
    python3 scripts/slice_init.py ERP-SLICE-ORD-001 --kind WRITE --entry NEW_CAPABILITY
    python3 scripts/slice_init.py SL-PUR-001 --kind WRITE --entry LEGACY_MIGRATION --minimal

Options:
    --root PATH   slice root, default specs/slices
    --minimal     only create slice.yaml and slice-state.json (CANDIDATE registry entry)
    --force       overwrite existing files
"""

import argparse
import json
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import re


CN_TZ = timezone(timedelta(hours=8))
CANONICAL_SLICE_ID_PATTERN = re.compile(
    r"^ERP-SLICE-(PRODUCT|ORD|B2C|IMS|ASS|FIN|PUR|PLAT)-[0-9]{3,4}$"
)
LEGACY_SLICE_ID_PATTERN = re.compile(r"^SL-[A-Z0-9]+(?:-[A-Z0-9]+)*$")


def now_iso():
    return datetime.now(CN_TZ).isoformat()


def run_suffix(entry_mode):
    return {
        "LEGACY_MIGRATION": "MIG",
        "NEW_CAPABILITY": "NEW",
        "EXISTING_SLICE_CHANGE": "CHG",
    }[entry_mode]


def validate_slice_id(slice_id, entry_mode):
    if CANONICAL_SLICE_ID_PATTERN.match(slice_id):
        return
    if LEGACY_SLICE_ID_PATTERN.match(slice_id) and entry_mode != "NEW_CAPABILITY":
        return
    raise ValueError(
        "新增能力必须使用 ERP-SLICE-{DOMAIN}-{NNN}；SL-* 仅可在 legacy 迁移/存量变更中引用"
    )


def slice_yaml(slice_id, kind):
    return f"""slice_id: {slice_id}
name: {slice_id}
slice_kind: {kind}
value_stream: TBD
capability: TBD
primary_actor: TBD
business_owner: TBD
domain_owner: TBD
created_at: {now_iso()}
"""


def slice_state(slice_id, run_id, kind):
    read_target = "LEGACY_QUERY"
    return {
        "slice_id": slice_id,
        "deployed": {
            "run_id": run_id.replace("-001", "-000", 1) if run_id.endswith("-001") else run_id,
            "lifecycle_state": "PRIMARY",
            "spec_version": "1.0",
            "contract_version": "0.0",
            "write_authority": {"mode": "SINGLE", "default_owner": "LEGACY" if kind == "WRITE" else "NONE"},
            "read_route": {"mode": "SINGLE", "default_target": read_target},
            "write_revision": 0,
            "read_revision": 0,
        },
        "active_runs": [{"run_id": run_id, "state_ref": f"runs/{run_id}/run-state.json"}],
        "state_revision": 1,
        "updated_at": now_iso(),
    }


def run_yaml(slice_id, run_id, entry_mode, kind):
    return f"""run_id: {run_id}
slice_id: {slice_id}
entry_mode: {entry_mode}
slice_kind: {kind}
created_at: {now_iso()}
definition_policy: APPEND_ONLY
initial_definition_revision: 1
initial_definition_ref: specs/slices/{slice_id}/runs/{run_id}/definitions/0001/run-definition.yaml
"""


def run_state(slice_id, run_id, entry_mode, kind):
    write_authority = None
    read_route = None
    if kind == "WRITE":
        write_authority = {
            "mode": "SINGLE",
            "owner_bindings": {"SOURCE": "LEGACY", "TARGET": f"RUN:{run_id}"},
            "default_owner": "SOURCE",
            "partition_key": None,
            "overrides": [],
        }
    else:
        read_route = {
            "mode": "PARTITIONED",
            "route_bindings": {"SOURCE": "LEGACY_QUERY", "TARGET": f"RUN:{run_id}"},
            "partition_key": "tenant_id",
            "default_route": "SOURCE",
            "overrides": [],
        }
    return {
        "slice_id": slice_id,
        "run_id": run_id,
        "entry_mode": entry_mode,
        "slice_kind": kind,
        "data_delivery_mode": "DIRECT_QUERY" if kind == "READ_ONLY" else "SNAPSHOT_CDC",
        "active_definition_revision": 1,
        "active_definition_ref": f"specs/slices/{slice_id}/runs/{run_id}/definitions/0001/run-definition.yaml",
        "lifecycle_state": "DISCOVERED",
        "current_stage": "discovery",
        "gates": {"G-SCOPE": "PENDING"},
        "optional_state_decisions": {"ASSISTED": {"decision": "PENDING", "approvers": [], "reason": None, "alternative_evidence_refs": []}},
        "candidate_write_authority": write_authority,
        "candidate_read_route": read_route,
        "state_event_refs": [],
        "last_transition": {
            "from": "NOT_EXISTS",
            "to": "DISCOVERED",
            "gate": "START",
            "actor": "slice-owner",
            "reason": "初始化",
            "evidence_refs": [],
            "at": now_iso(),
        },
        "updated_at": now_iso(),
    }


def run_definition(slice_id, run_id):
    return f"""run_id: {run_id}
slice_id: {slice_id}
definition_revision: 1
spec_version: "1.0"
contract_version: "0.0"
data_delivery_mode: TBD

trigger:
  event: TBD

outcome:
  result: TBD

state_change:
  aggregate: TBD
  from: NOT_EXISTS
  to: []

primary_write_domain: TBD

out_of_scope: []
risk:
  level: L0
  irreversible: false

release:
  feature_flag: null
  rollback: disable_feature_flag
"""


COLLAB_README = """# 切片协作目录

- `task-board.yaml` 只由主控对话修改；
- 状态变化通过追加事件文件报告，不覆盖旧事件；
- Result Packet 格式遵循正式方案 §14。
"""


def init_slice(slice_id, kind, entry_mode, root, force=False, minimal=False):
    base = Path(root) / slice_id
    run_id = f"{slice_id}-{run_suffix(entry_mode)}-001"
    run_dir = base / "runs" / run_id
    definition_dir = run_dir / "definitions" / "0001"

    if minimal:
        files = {
            base / "slice.yaml": slice_yaml(slice_id, kind),
            base / "slice-state.json": json.dumps(
                {**slice_state(slice_id, run_id, kind), "active_runs": []},
                ensure_ascii=False,
                indent=2,
            )
            + "\n",
        }
    else:
        files = {
            base / "slice.yaml": slice_yaml(slice_id, kind),
            base / "slice-state.json": json.dumps(slice_state(slice_id, run_id, kind), ensure_ascii=False, indent=2) + "\n",
            run_dir / "run.yaml": run_yaml(slice_id, run_id, entry_mode, kind),
            run_dir / "run-state.json": json.dumps(run_state(slice_id, run_id, entry_mode, kind), ensure_ascii=False, indent=2) + "\n",
            definition_dir / "run-definition.yaml": run_definition(slice_id, run_id),
            run_dir / "collaboration" / "README.md": COLLAB_README,
        }

    created = []
    for path, content in files.items():
        if path.exists() and not force:
            print(f"SKIP {path} (已存在，使用 --force 覆盖)")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        created.append(str(path))
    return run_id, created


def main(argv):
    parser = argparse.ArgumentParser(description="Scaffold ERP slice")
    parser.add_argument("slice_id")
    parser.add_argument("--kind", choices=["WRITE", "READ_ONLY"], required=True)
    parser.add_argument("--entry", choices=["LEGACY_MIGRATION", "NEW_CAPABILITY", "EXISTING_SLICE_CHANGE"], required=True)
    parser.add_argument("--root", default="specs/slices")
    parser.add_argument("--minimal", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args(argv)
    try:
        validate_slice_id(args.slice_id, args.entry)
    except ValueError as exc:
        parser.error(str(exc))

    run_id, created = init_slice(
        args.slice_id, args.kind, args.entry, args.root, force=args.force, minimal=args.minimal
    )
    print(f"run_id: {run_id}")
    for path in created:
        print(f"created: {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
