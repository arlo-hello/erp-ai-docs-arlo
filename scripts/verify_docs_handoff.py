#!/usr/bin/env python3
"""Verify that a Multica implementation issue has a merged docs handoff."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


REQUIRED = ("docs_repo", "docs_branch", "docs_commit", "docs_paths")


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, text=True, capture_output=True, check=check)


def metadata(issue: str) -> dict[str, object]:
    result = run(
        ["multica", "issue", "metadata", "list", issue, "--output", "json"],
        check=False,
    )
    if result.returncode:
        raise SystemExit(result.stderr.strip())
    data = json.loads(result.stdout or "{}")
    if isinstance(data, list):
        return {str(item.get("key")): item.get("value") for item in data}
    return data


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", required=True)
    parser.add_argument("--version-branch")
    args = parser.parse_args()

    values = metadata(args.issue)
    missing = [key for key in REQUIRED if not values.get(key)]
    if missing:
        raise SystemExit("Missing docs metadata: " + ", ".join(missing))
    if values.get("docs_state") != "merged_for_development":
        raise SystemExit(
            f"docs_state={values.get('docs_state')!r}; expected merged_for_development"
        )

    docs_branch = str(values["docs_branch"])
    match = re.fullmatch(
        r"docs/(v\d+\.\d+\.\d+|hotfix-\d{8}-p\d+)_\d{4,}",
        docs_branch,
    )
    if not match:
        raise SystemExit(f"Invalid docs task branch metadata: {docs_branch}")
    base = args.version_branch or f"docs/{match.group(1)}"
    commit = str(values["docs_commit"])
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise SystemExit(f"Invalid docs_commit: {commit}")

    run(["git", "fetch", "origin", base])
    ancestor = run(
        ["git", "merge-base", "--is-ancestor", commit, f"origin/{base}"],
        check=False,
    )
    if ancestor.returncode:
        raise SystemExit(f"docs_commit {commit} is not merged into origin/{base}")

    paths_value = values["docs_paths"]
    try:
        paths = json.loads(paths_value) if isinstance(paths_value, str) else paths_value
    except json.JSONDecodeError as error:
        raise SystemExit(f"docs_paths is not valid JSON: {paths_value}") from error
    if not isinstance(paths, list) or not paths:
        raise SystemExit("docs_paths must be a non-empty JSON array")

    for path in paths:
        exists = run(["git", "cat-file", "-e", f"{commit}:{path}"], check=False)
        if exists.returncode:
            raise SystemExit(f"Path missing in docs commit: {path}")

    print("docs handoff valid")
    print(f"docs_commit={commit}")
    print(f"version_branch={base}")
    print("paths:")
    for path in paths:
        print(f"  - {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
