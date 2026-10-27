#!/usr/bin/env python3
"""Record the human-merged docs commit as the development handoff."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
from pathlib import Path


def run(command: list[str], *, input_text: str | None = None) -> str:
    env = os.environ.copy()
    env["GH_PROMPT_DISABLED"] = "1"
    result = subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )
    return result.stdout.strip()


def repository() -> str:
    remote = run(["git", "remote", "get-url", "origin"])
    match = re.search(r"github(?:\.com)[:/]([^/]+)/([^/]+?)(?:\.git)?$", remote)
    if not match:
        raise SystemExit(f"Cannot parse GitHub remote: {remote}")
    return f"{match.group(1)}/{match.group(2)}"


def pr_merge_commit(repo: str, pr: str) -> tuple[str, str, str]:
    number = re.sub(r".*/pull/", "", pr.rstrip("/"))
    data = json.loads(
        run(
            [
                "gh",
                "pr",
                "view",
                "-R",
                repo,
                number,
                "--json",
                "state,mergeCommit,url,baseRefName",
            ]
        )
    )
    if data.get("state") != "MERGED":
        raise SystemExit(f"Docs PR is not merged: {data.get('url')}")
    merge_commit = data["mergeCommit"]["oid"]
    return merge_commit, data["url"], data["baseRefName"]


def metadata(issue: str, key: str, value: object) -> None:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    run(
        [
            "multica",
            "issue",
            "metadata",
            "set",
            issue,
            "--key",
            key,
            "--value",
            encoded,
            "--type",
            "string",
        ]
    )


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", required=True)
    parser.add_argument("--pr")
    parser.add_argument("--merge-commit")
    parser.add_argument("--version-branch")
    args = parser.parse_args()

    if not args.pr and not args.merge_commit:
        raise SystemExit("One of --pr or --merge-commit is required")

    repo = repository()
    pr = args.pr or ""
    if args.merge_commit:
        merge_commit = args.merge_commit
        base = args.version_branch
        if not base:
            raise SystemExit("--version-branch is required with --merge-commit")
    else:
        merge_commit, pr, base = pr_merge_commit(repo, pr)

    run(["git", "fetch", "origin", base])
    check = subprocess.run(
        [
            "git",
            "merge-base",
            "--is-ancestor",
            merge_commit,
            f"origin/{base}",
        ],
        check=False,
    )
    if check.returncode:
        raise SystemExit(f"{merge_commit} is not present in origin/{base}")

    issue = args.issue
    values = {
        "docs_commit": merge_commit,
        "docs_merged_commit": merge_commit,
        "docs_state": "merged_for_development",
    }
    if pr:
        values["docs_pr"] = pr
    for key, value in values.items():
        metadata(issue, key, value)

    comment = f"""## Docs handoff merged

```yaml
docs_repo: {repo}
docs_commit: {merge_commit}
docs_version_branch: {base}
docs_pr: {pr or 'not provided'}
docs_state: merged_for_development
```

This commit is now the only valid development input. A human still decides whether the implementation issue moves from backlog to todo.
"""
    run(
        ["multica", "issue", "comment", "add", issue, "--content-stdin"],
        input_text=comment,
    )
    print(f"docs_commit={merge_commit}")
    print(f"docs_state=merged_for_development")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
