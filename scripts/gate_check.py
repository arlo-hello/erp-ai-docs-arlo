#!/usr/bin/env python3
"""Check slice run-state gate evidence, transitions and contract freeze integrity.

Usage:
    python3 scripts/gate_check.py specs/slices/SL-ORD-001
    python3 scripts/gate_check.py specs/slices
"""

import json
import sys
from pathlib import Path

import yaml


VALID_TRANSITIONS = {
    ("NOT_EXISTS", "DISCOVERED"): {"START"},
    ("DISCOVERED", "DEFINED"): {"G-SCOPE"},
    ("DEFINED", "READY"): {"G-PRODUCT", "G-CONTRACT"},
    ("READY", "BUILDING"): {"START_CHECK"},
    ("BUILDING", "VERIFIED"): {"G-BUILD", "G-VERIFY"},
    ("VERIFIED", "SHADOW"): {"G-DATA-READY", "G-DEPLOY"},
    ("SHADOW", "ASSISTED"): {"G-SHADOW"},
    ("SHADOW", "PRIMARY"): {"G-SHADOW", "G-PRIMARY"},
    ("ASSISTED", "PRIMARY"): {"G-PRIMARY"},
    ("PRIMARY", "LEGACY_RETIRED"): {"G-RETIRE"},
    ("BUILDING", "READY"): {"R-CONTRACT"},
    ("SHADOW", "VERIFIED"): {"R-SHADOW"},
    ("ASSISTED", "SHADOW"): {"R-ASSISTED"},
    ("PRIMARY", "ASSISTED"): {"R-PRIMARY"},
}


def load_yaml_or_json(path):
    text = Path(path).read_text(encoding="utf-8")
    if str(path).endswith(".json"):
        return json.loads(text)
    return yaml.safe_load(text)


def evidence_dir_for(run_dir, gate):
    return run_dir / "evidence" / gate


def check_run_state(run_state_path):
    run_state_path = Path(run_state_path)
    issues = []
    state = load_yaml_or_json(run_state_path)
    run_dir = run_state_path.parent

    transition = state.get("last_transition", {})
    from_state = transition.get("from")
    to_state = transition.get("to")
    gate = transition.get("gate")
    if (from_state, to_state) not in VALID_TRANSITIONS:
        issues.append(f"{run_state_path}: 非法状态转换 {from_state} -> {to_state}")
    else:
        required_gates = VALID_TRANSITIONS[(from_state, to_state)]
        gate_set = set(gate.split("+")) if gate else set()
        if gate not in required_gates and not required_gates.issubset(gate_set):
            issues.append(f"{run_state_path}: 转换 {from_state}->{to_state} 需要 Gate {sorted(required_gates)}，实际 {gate}")
    if to_state != state.get("lifecycle_state"):
        issues.append(f"{run_state_path}: last_transition.to={to_state} 与 lifecycle_state={state.get('lifecycle_state')} 不一致")

    for gate_name, result in state.get("gates", {}).items():
        if result == "PASSED":
            evidence_dir = evidence_dir_for(run_dir, gate_name)
            files = list(evidence_dir.glob("*")) if evidence_dir.exists() else []
            if not files:
                issues.append(f"{run_state_path}: Gate {gate_name} 标记 PASSED 但 evidence/{gate_name}/ 无证据文件")
        if result == "RUNNING":
            evidence_dir = evidence_dir_for(run_dir, gate_name)
            files = list(evidence_dir.glob("*")) if evidence_dir.exists() else []
            if not files:
                issues.append(f"{run_state_path}: Gate {gate_name} 标记 RUNNING 但 evidence/{gate_name}/ 无草稿证据")

    revision = state.get("active_definition_revision")
    contract_refs_path = run_dir / "definitions" / str(revision).zfill(4) / "contract-refs.yaml"
    if state.get("gates", {}).get("G-CONTRACT") == "PASSED":
        issues.extend(check_contract_integrity(run_dir, state, require_freeze=True))
    elif contract_refs_path.exists():
        issues.extend(check_contract_integrity(run_dir, state, require_freeze=False))

    if state.get("slice_kind") == "READ_ONLY" and state.get("candidate_write_authority") is not None:
        issues.append(f"{run_state_path}: READ_ONLY 切片 candidate_write_authority 必须为 null")
    if state.get("slice_kind") == "WRITE" and state.get("candidate_write_authority") is None:
        issues.append(f"{run_state_path}: WRITE 切片必须声明 candidate_write_authority")

    return issues


def check_contract_integrity(run_dir, state, require_freeze):
    issues = []
    revision = state.get("active_definition_revision")
    definition_dir = run_dir / "definitions" / str(revision).zfill(4)
    contract_refs_path = definition_dir / "contract-refs.yaml"
    if not contract_refs_path.exists():
        return [f"{run_dir}: 缺少 definitions/{revision}/contract-refs.yaml"]

    refs = load_yaml_or_json(contract_refs_path)
    bundle = refs.get("contract_bundle", {})
    if require_freeze and bundle.get("git_commit") in (None, "PENDING"):
        issues.append(f"{contract_refs_path}: G-CONTRACT 冻结需要 git_commit，当前 PENDING")

    manifest_ref = bundle.get("manifest_ref")
    if not manifest_ref:
        issues.append(f"{contract_refs_path}: 缺少 manifest_ref")
        return issues
    manifest_path = Path(manifest_ref)
    if not manifest_path.exists():
        issues.append(f"{contract_refs_path}: manifest 不存在 {manifest_ref}")
        return issues

    manifest = load_yaml_or_json(manifest_path)
    manifest_bundle = manifest.get("contract_bundle", {})
    files = manifest_bundle.get("files", [])
    for entry in files:
        rel = entry["relative_path"]
        digest = entry["file_sha256"]
        actual = _sha256(manifest_path.parent / rel)
        if actual != digest:
            issues.append(f"{manifest_ref}: {rel} SHA-256 不匹配，manifest={digest} 实际={actual}")
    recomputed = _bundle_digest(files)
    if manifest_bundle.get("bundle_digest") != recomputed:
        issues.append(f"{manifest_ref}: bundle_digest 不匹配，manifest={manifest_bundle.get('bundle_digest')} 重算={recomputed}")
    if bundle.get("bundle_digest") not in (None, manifest_bundle.get("bundle_digest")):
        issues.append(f"{contract_refs_path}: contract-refs bundle_digest 与 manifest 不一致")
    return issues


def _sha256(path):
    import hashlib

    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _bundle_digest(files):
    import hashlib

    records = sorted(f"{entry['relative_path']}:{entry['file_sha256']}" for entry in files)
    raw = "\n".join(records) + "\n"
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def main(argv):
    targets = argv or ["specs/slices"]
    issues = []
    checked = 0
    for target in targets:
        path = Path(target)
        if path.is_dir() and path.name != "slices":
            for run_state in path.rglob("run-state.json"):
                checked += 1
                issues.extend(check_run_state(run_state))
        elif path.is_dir():
            for run_state in path.rglob("run-state.json"):
                checked += 1
                issues.extend(check_run_state(run_state))
        elif path.name == "run-state.json":
            checked += 1
            issues.extend(check_run_state(path))
    if issues:
        print("Gate 校验失败：")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(f"Gate 校验通过：{checked} 个 run-state")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
