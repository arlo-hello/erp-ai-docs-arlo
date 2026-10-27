#!/usr/bin/env python3
"""Validate ERP Multica issue titles."""

from __future__ import annotations

import argparse
import re
import sys


DOMAIN_CODES = {
    "PRODUCT",
    "ORD",
    "B2C",
    "IMS",
    "ASS",
    "FIN",
    "PUR",
    "PLAT",
}
STAGES = {"REQ", "PM", "DEV", "REV", "FIX", "QA", "BUG"}
IMPLEMENTATION_STAGES = {"DEV", "REV", "FIX", "QA"}
VERSION_PATTERN = re.compile(
    r"^(?:v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)|hotfix-[0-9]{8})$"
)
CANONICAL_SLICE_PATTERN = re.compile(
    r"^ERP-SLICE-(PRODUCT|ORD|B2C|IMS|ASS|FIN|PUR|PLAT)-[0-9]{3,4}$"
)
LEGACY_SLICE_PATTERN = re.compile(r"^SL-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
BRACKET_TITLE_PATTERN = re.compile(r"^\[([^\]]+)\]\[([^\]]+)\](?:\[([^\]]+)\])?\s+(.+)$")
PATH_LIKE_PATTERN = re.compile(
    r"(?:^|\s)(?:feat|hotfix|major)/|[A-Za-z0-9_.-]+\.(?:php|ts|tsx|js|jsx|yaml|yml|md)\b|erp-service-php/|dtcplus-web-ts/"
)


def validate_title(title: str) -> list[str]:
    issues: list[str] = []
    match = BRACKET_TITLE_PATTERN.match(title.strip())
    if not match:
        return [
            "标题必须为 [v{version}][{stage}][{Slice ID 或 domain}] {业务结果}；无切片 Bug 为 [v{version}][BUG] {业务结果}，紧急修复也可使用 [hotfix-YYYYMMDD]"
        ]

    version, stage, slice_token, outcome = match.groups()
    if not VERSION_PATTERN.match(version):
        issues.append(f"版本 {version!r} 必须是 vMAJOR.MINOR.PATCH 或 hotfix-YYYYMMDD")
    if stage not in STAGES:
        issues.append(f"阶段 {stage!r} 只允许 {'/'.join(sorted(STAGES))}")
    if not outcome.strip():
        issues.append("业务结果不能为空")
    if PATH_LIKE_PATTERN.search(outcome):
        issues.append("业务结果不能包含文件路径、仓库名或分支名")

    if stage == "BUG":
        if slice_token is not None:
            issues.append("无切片 Bug 不使用第三个中括号；若已登记切片，stage 应改为 DEV/FIX/QA")
        return issues

    if slice_token is None:
        issues.append("非 BUG 任务必须携带第三个中括号（Slice ID 或 domain）")
        return issues

    if stage in {"REQ", "PM"}:
        if slice_token not in DOMAIN_CODES and not is_slice_id(slice_token):
            issues.append("REQ/PM 任务第三个中括号必须是域代码或 Slice ID")
    else:
        if not is_slice_id(slice_token):
            issues.append(f"{stage} 任务必须使用完整 Slice ID，而不是域代码")

    if slice_token in DOMAIN_CODES and stage in IMPLEMENTATION_STAGES:
        issues.append("DEV/REV/FIX/QA 不允许只写域代码")
    return issues


def is_slice_id(value: str) -> bool:
    return bool(CANONICAL_SLICE_PATTERN.match(value) or LEGACY_SLICE_PATTERN.match(value))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate ERP Multica issue title format")
    parser.add_argument("--title", action="append", default=[], help="title to validate; repeatable")
    parser.add_argument("--stdin", action="store_true", help="read one title per line from stdin")
    args = parser.parse_args(argv)

    titles = list(args.title)
    if args.stdin:
        titles.extend(line.rstrip("\n") for line in sys.stdin if line.strip())
    if not titles:
        parser.error("provide --title at least once, or use --stdin")

    failures = 0
    for title in titles:
        issues = validate_title(title)
        if issues:
            failures += 1
            print(f"FAIL {title}")
            for issue in issues:
                print(f"  - {issue}")
        else:
            print(f"PASS {title}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
