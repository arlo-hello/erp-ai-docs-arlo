#!/usr/bin/env python3
"""Validate ERP AI Docs branch, file, and slice governance rules."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

import yaml


VERSION_BRANCH = re.compile(
    r"^docs/(v\d+\.\d+\.\d+|hotfix-\d{8}-p\d+)$"
)
TASK_BRANCH = re.compile(
    r"^docs/(v\d+\.\d+\.\d+|hotfix-\d{8}-p\d+)_\d{4,}$"
)
SLICE_ID = re.compile(
    r"^ERP-SLICE-(PRODUCT|ORD|B2C|IMS|ASS|FIN|PUR|PLAT)-\d{3,4}$"
)
FORBIDDEN_PATHS = (
    ".DS_Store",
    "__pycache__",
    ".pyc",
    ".diff",
    ".patch",
    ".log",
    ".zip",
)
VERSION_PATH = re.compile(
    r"^(?:docs|specs)/(?:v\d+\.\d+\.\d+|hotfix-\d{8}-p\d+)(?:/|$)"
)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], text=True).strip()


def changed_files() -> list[str]:
    tracked = git("ls-files").splitlines()
    has_head = subprocess.run(
        ["git", "rev-parse", "--verify", "HEAD"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    ).returncode == 0
    modified = (
        git("diff", "--name-only", "HEAD").splitlines()
        if has_head
        else git("status", "--porcelain").splitlines()
    )
    names = []
    for name in tracked + modified:
        name = name[3:] if name.startswith(("?? ", "M  ", "A  ")) else name
        if name:
            names.append(name)
    return sorted(set(names))


def check_files(files: list[str]) -> list[str]:
    return [
        f"Forbidden file in docs repository: {name}"
        for name in files
        if any(part in name for part in FORBIDDEN_PATHS)
    ]


def check_registry(path: Path) -> list[str]:
    if not path.is_file():
        return [f"Missing {path.as_posix()}"]

    issues: list[str] = []
    registry = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    domains = set(registry.get("domains", []))
    expected_pattern = (
        "^ERP-SLICE-(%s)-[0-9]{3,4}$" % "|".join(sorted(domains, reverse=True))
        if domains
        else "^ERP-SLICE-[A-Z0-9]+-[0-9]{3,4}$"
    )
    seen: set[str] = set()
    counts = {"WRITE": 0, "READ_ONLY": 0, "DEFINED": 0, "CANDIDATE": 0}

    for entry in registry.get("slices", []):
        slice_id = entry.get("slice_id", "")
        if not slice_id:
            issues.append("Registry entry missing slice_id")
            continue
        if slice_id in seen:
            issues.append(f"Duplicate slice_id: {slice_id}")
        seen.add(slice_id)
        if not SLICE_ID.match(slice_id):
            issues.append(f"Invalid canonical slice_id: {slice_id}")

        kind = entry.get("slice_kind")
        status = entry.get("status")
        if kind not in counts:
            issues.append(f"{slice_id}: invalid slice_kind {kind}")
        else:
            counts[kind] += 1
        if status not in {"DEFINED", "CANDIDATE"}:
            issues.append(f"{slice_id}: invalid status {status}")
        else:
            counts[status] += 1

        if SLICE_ID.fullmatch(slice_id):
            slice_root = path.parent / "slices" / slice_id
            for required in ("slice.yaml", "contract.md"):
                if not (slice_root / required).is_file():
                    issues.append(f"{slice_id}: missing {required}")

    if not registry.get("id_pattern"):
        issues.append("id_pattern is required")
    return issues


def check_contracts(spec_root: Path) -> list[str]:
    issues: list[str] = []
    for contract in spec_root.glob("ERP-SLICE-*/contract.md"):
        text = contract.read_text(encoding="utf-8")
        for section in ("验收标准", "测试边界", "依赖与 Mock 策略"):
            if section not in text:
                issues.append(f"{contract}: missing section {section}")
        if not re.search(r"AC-\d{3}", text):
            issues.append(f"{contract}: missing AC-NNN acceptance criteria")
    return issues


def registry_paths(root: Path, branch: str) -> tuple[list[Path], list[str]]:
    if branch == "template":
        return [], []

    version_match = VERSION_BRANCH.match(branch) or TASK_BRANCH.match(branch)
    if version_match:
        current = root / "docs" / "versions" / "current.txt"
        if not current.is_file():
            return [], ["Missing docs/versions/current.txt"]
        version = current.read_text(encoding="utf-8").strip()
        if version != version_match.group(1):
            return [], [
                f"Branch {branch} does not match docs/versions/current.txt={version}"
            ]
        return [root / "specs" / version / "slice-registry.yaml"], []

    paths = sorted(
        [
            path
            for path in (root / "specs").glob("*/slice-registry.yaml")
            if VERSION_BRANCH.fullmatch(f"docs/{path.parent.name}")
        ]
    )
    legacy = root / "specs" / "slice-registry.yaml"
    if branch == "main" and not paths and legacy.is_file():
        return [legacy], []
    if branch in {"main", "template", "HEAD"} and not paths:
        return [], []
    if not paths:
        return [], ["No version slice registry found under specs/{version}/"]
    return paths, []


def main() -> int:
    root = Path.cwd()
    branch = git("branch", "--show-current") or os.environ.get("GITHUB_HEAD_REF", "")
    files = changed_files()
    issues = check_files(files)

    if (
        branch not in {"main", "template", "HEAD"}
        and not VERSION_BRANCH.match(branch)
        and not TASK_BRANCH.match(branch)
    ):
        issues.append(f"Invalid branch name: {branch}")
    if branch == "template":
        forbidden = any(
            VERSION_PATH.match(name)
            or name.startswith(
                (
                    "docs/hotfix-",
                    "docs/product/",
                    "docs/requirements/",
                    "docs/tech/",
                    "docs/changelogs/",
                    "docs/hotfix/",
                    "specs/hotfix-",
                    "specs/slices/",
                )
            )
            and name
            not in {
                "docs/product/README.md",
                "docs/requirements/README.md",
                "docs/tech/README.md",
                "docs/changelogs/.gitkeep",
                "docs/hotfix/README.md",
            }
            or name == "docs/versions/current.txt"
            for name in files
        )
        if forbidden:
            issues.append("Template branch must not contain version or task documents")

    registries, registry_issues = registry_paths(root, branch)
    issues.extend(registry_issues)
    for registry in registries:
        issues.extend(check_registry(registry))
        issues.extend(check_contracts(registry.parent / "slices"))

    if issues:
        print("Docs governance check failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print("Docs governance check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
