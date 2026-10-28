#!/usr/bin/env python3
"""Validate specs/slice-registry.yaml: unique IDs, patterns and summary counts."""

import re
import sys
from pathlib import Path

import yaml


CANONICAL_SLICE_ID_PATTERN = re.compile(
    r"^ERP-SLICE-(PRODUCT|ORD|B2C|IMS|ASS|FIN|PUR|PLAT)-[0-9]{3,4}$"
)
LEGACY_SLICE_ID_PATTERN = re.compile(r"^SL-[A-Z0-9]+(-[A-Z0-9]+)*$")


def check_registry(path):
    issues = []
    registry = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    slices = registry.get("slices", [])

    seen = {}
    counts = {"total": 0, "write": 0, "read_only": 0, "defined": 0, "candidate": 0}
    for entry in slices:
        slice_id = entry.get("slice_id")
        if not slice_id:
            issues.append(f"{path}: 存在无 slice_id 的行")
            continue
        if CANONICAL_SLICE_ID_PATTERN.match(slice_id):
            slice_root = path.parent / "slices" / slice_id
            if not (slice_root / "slice.yaml").is_file():
                issues.append(f"{path}: canonical slice_id {slice_id} 缺少 {slice_root}/slice.yaml")
            if not (slice_root / "contract.md").is_file():
                issues.append(f"{path}: canonical slice_id {slice_id} 缺少 {slice_root}/contract.md")
        elif LEGACY_SLICE_ID_PATTERN.match(slice_id):
            pass
        else:
            issues.append(
                f"{path}: slice_id {slice_id} 必须是 ERP-SLICE-{{DOMAIN}}-{{NNN}}；SL-* 仅 legacy 兼容"
            )
        if slice_id in seen:
            issues.append(f"{path}: slice_id {slice_id} 重复（第 {seen[slice_id]} 行）")
        seen[slice_id] = slices.index(entry) + 1

        kind = entry.get("slice_kind")
        status = entry.get("status")
        counts["total"] += 1
        if kind == "WRITE":
            counts["write"] += 1
        elif kind == "READ_ONLY":
            counts["read_only"] += 1
        else:
            issues.append(f"{path}: {slice_id} slice_kind={kind} 非法")
        if status == "DEFINED":
            counts["defined"] += 1
        elif status == "CANDIDATE":
            counts["candidate"] += 1
        else:
            issues.append(f"{path}: {slice_id} status={status} 非法")

    summary = registry.get("summary", {})
    for key in ("total_slices", "write", "read_only", "defined", "candidate"):
        expected = counts[key] if key != "total_slices" else counts["total"]
        if summary.get(key) != expected:
            issues.append(f"{path}: summary.{key}={summary.get(key)} 与逐行计数 {expected} 不一致")
    return issues, counts


def main(argv):
    path = Path(argv[0] if argv else "specs/slice-registry.yaml")
    issues, counts = check_registry(path)
    if issues:
        print("注册表校验失败：")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(f"注册表校验通过：{counts['total']} 个切片（WRITE {counts['write']} / READ_ONLY {counts['read_only']}）")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
