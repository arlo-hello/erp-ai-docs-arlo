#!/usr/bin/env python3
"""Commit PM document changes and record a stable handoff in Multica."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


TASK_BRANCH = re.compile(
    r"^docs/(v\d+\.\d+\.\d+|hotfix-\d{8}-p\d+)_\d{4,}$"
)
REMOTE_PATTERN = re.compile(
    r"github(?:\.com)[:/]([^/]+)/([^/]+?)(?:\.git)?$"
)


def run(
    command: list[str],
    *,
    input_text: str | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["GH_PROMPT_DISABLED"] = "1"
    return subprocess.run(
        command,
        input=input_text,
        text=True,
        capture_output=True,
        check=check,
        env=env,
    )


def git(*args: str) -> str:
    return run(["git", *args]).stdout.strip()


def staged_changes_exist() -> bool:
    return run(["git", "diff", "--cached", "--quiet"], check=False).returncode != 0


def repository() -> str:
    remote = git("remote", "get-url", "origin")
    match = REMOTE_PATTERN.search(remote)
    if not match:
        raise SystemExit(f"Cannot parse GitHub remote: {remote}")
    return f"{match.group(1)}/{match.group(2)}"


def changed_paths() -> set[str]:
    paths: set[str] = set()
    for line in git("status", "--porcelain=v1").splitlines():
        if not line:
            continue
        value = line[3:]
        if " -> " in value:
            value = value.split(" -> ", 1)[1]
        paths.add(value.strip('"'))
    return paths


def normalize_paths(values: list[str], root: Path) -> list[str]:
    normalized: list[str] = []
    for value in values:
        path = Path(value)
        if path.is_absolute():
            path = path.relative_to(root)
        clean = path.as_posix()
        if clean.startswith("../") or clean in {"..", "."}:
            raise SystemExit(f"Path escapes docs repository: {value}")
        normalized.append(clean)
    return normalized


def normalize_issue(value: str) -> str:
    if re.fullmatch(r"\d+", value):
        return f"ERP-{value}"
    return value


def issue_task_number(issue: str) -> str | None:
    match = re.fullmatch(r"ERP-(\d+)", issue)
    return f"{int(match.group(1)):04d}" if match else None


def validate(args: argparse.Namespace, draft: bool) -> list[str]:
    commands = [["python3", "scripts/check_governance.py"]]
    if not draft:
        if not args.title:
            raise SystemExit("--title is required when saving a non-draft update")
        root = Path(__file__).resolve().parents[1]
        branch = git("branch", "--show-current")
        version = branch.split("_", 1)[0].removeprefix("docs/")
        registry = Path("specs") / version / "slice-registry.yaml"
        registry_path = str(registry) if registry.is_file() else "specs/slice-registry.yaml"
        contract_root = Path("specs") / version / "slices"
        contract_path = str(contract_root) if contract_root.is_dir() else "specs/slices"
        commands.extend(
            [
                [
                    "python3",
                    "scripts/multica_title_check.py",
                    "--title",
                    args.title,
                ],
                ["python3", "scripts/registry_check.py", registry_path],
                ["python3", "scripts/contract_check.py", contract_path],
            ]
        )

    evidence: list[str] = []
    for command in commands:
        result = run(command, check=False)
        output = (result.stdout + result.stderr).strip()
        evidence.append("$ " + " ".join(command) + "\n" + output)
        if result.returncode:
            print("\n\n".join(evidence), file=sys.stderr)
            raise SystemExit(result.returncode)
    return evidence


def github_pr(
    repo: str,
    branch: str,
    base: str,
    title: str,
    body: str,
    draft: bool,
) -> tuple[str, bool]:
    view = run(
        [
            "gh",
            "pr",
            "view",
            "-R",
            repo,
            branch,
            "--json",
            "number,url,isDraft",
        ],
        check=False,
    )
    if view.returncode == 0:
        data = json.loads(view.stdout)
        if not draft and data.get("isDraft"):
            ready = run(
                ["gh", "pr", "ready", "-R", repo, str(data["number"])],
                check=False,
            )
            if ready.returncode:
                print(ready.stderr.strip(), file=sys.stderr)
        return str(data["url"]), False

    root = Path(__file__).resolve().parents[1]
    temp = tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        delete=False,
        dir=root,
        prefix=".pm-autosave-pr-",
        suffix=".md",
    )
    try:
        temp.write(body)
        temp.close()
        command = [
            "gh",
            "pr",
            "create",
            "-R",
            repo,
            "--base",
            base,
            "--head",
            branch,
            "--title",
            title,
            "--body-file",
            temp.name,
        ]
        if draft:
            command.append("--draft")
        created = run(command, check=False)
        if created.returncode == 0:
            return created.stdout.strip().splitlines()[-1], True
        print(created.stderr.strip(), file=sys.stderr)
    finally:
        Path(temp.name).unlink(missing_ok=True)

    return (
        f"https://github.com/{repo}/compare/{base}...{branch}?expand=1",
        False,
    )


def multica_record(
    issue: str,
    refs: dict[str, object],
    comment: str,
    skip_multica: bool,
) -> None:
    if skip_multica:
        return
    result = run(
        ["multica", "issue", "comment", "add", issue, "--content-stdin"],
        input_text=comment,
        check=False,
    )
    if result.returncode:
        print(result.stderr.strip(), file=sys.stderr)
        raise SystemExit(result.returncode)

    for key, value in refs.items():
        encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        result = run(
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
            ],
            check=False,
        )
        if result.returncode:
            print(result.stderr.strip(), file=sys.stderr)
            raise SystemExit(result.returncode)


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)

    parser = argparse.ArgumentParser()
    parser.add_argument("--issue", required=True)
    parser.add_argument("--title")
    parser.add_argument("--slice-id")
    parser.add_argument("--path", action="append", required=True)
    parser.add_argument("--message")
    parser.add_argument("--draft", action="store_true")
    parser.add_argument("--skip-multica", action="store_true")
    args = parser.parse_args()

    branch = git("branch", "--show-current")
    match = TASK_BRANCH.fullmatch(branch)
    if not match:
        raise SystemExit(f"PM autosave must run on a docs task branch, current={branch}")
    version = match.group(1)
    base = f"docs/{version}"
    task_number = branch.rsplit("_", 1)[1]
    issue = normalize_issue(args.issue)
    expected_number = issue_task_number(issue)
    if expected_number and task_number != expected_number:
        raise SystemExit(
            f"Issue {issue} does not match task branch {branch}; expected suffix {expected_number}"
        )

    paths = normalize_paths(args.path, root)
    changes = changed_paths()
    unknown = changes - set(paths)
    if unknown:
        raise SystemExit(
            "Refusing to commit unrelated changes:\n" + "\n".join(sorted(unknown))
        )
    missing = set(paths) - changes
    if missing:
        raise SystemExit("No change detected for:\n" + "\n".join(sorted(missing)))

    evidence = validate(args, args.draft)
    run(["git", "add", "--", *paths])
    if not staged_changes_exist():
        raise SystemExit("No staged changes after filtering")

    message = args.message or f"docs: {issue} update slice plan"
    git("commit", "-m", message)
    run(["git", "push", "-u", "origin", branch])
    commit = git("rev-parse", "HEAD")
    repo = repository()
    state = "draft" if args.draft else "ready_for_review"

    yaml_paths = "\n".join(f"  - {path}" for path in paths)
    body = f"""## Docs autosave

```yaml
multica_issue: {issue}
slice_id: {args.slice_id or ""}
docs_repo: {repo}
docs_branch: {branch}
docs_head_commit: {commit}
docs_paths:
{yaml_paths}
```

State: `{state}`

## Validation

```text
{chr(10).join(evidence)}
```

## Human gate

- [ ] Review and merge this PR into `{base}`.
- [ ] After merge, run `scripts/sync_merged_docs.py` to replace the task head commit with the merge commit.
- [ ] Only a human may move the implementation issue from backlog to todo.
"""
    title = args.title or f"[docs][{issue}] slice plan update"
    pr, created = github_pr(repo, branch, base, title, body, args.draft)

    refs = {
        "docs_repo": repo,
        "docs_branch": branch,
        "docs_head_commit": commit,
        "docs_paths": paths,
        "docs_pr": pr,
        "docs_state": state,
    }
    if args.slice_id:
        refs["slice_id"] = args.slice_id

    comment = body
    if not created and pr.startswith("https://github.com/"):
        comment += f"\nPR: {pr}\n"
    multica_record(issue, refs, comment, args.skip_multica)

    print(f"committed: {commit}")
    print(f"branch: {branch}")
    print(f"pr: {pr}")
    print(f"state: {state}")
    if not created and not pr.startswith("https://github.com/"):
        print("warning: GitHub PR creation unavailable; open the compare URL manually")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
