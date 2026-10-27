#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: ./scripts/create_task_branch.sh <ERP-111|0111> [docs/v0.28.4]" >&2
  exit 2
fi

task="$1"
branch="$(git branch --show-current)"
base="${2:-}"
version_pattern='^(v[0-9]+\.[0-9]+\.[0-9]+|hotfix-[0-9]{8}-p[0-9]+)$'

if [[ "$branch" =~ ^docs/(v[0-9]+\.[0-9]+\.[0-9]+|hotfix-[0-9]{8}-p[0-9]+)$ ]]; then
  if [[ -n "$base" && "$base" != "$branch" ]]; then
    echo "Current branch $branch does not match requested base $base" >&2
    exit 1
  fi
  base="$branch"
elif [[ -n "$base" ]]; then
  if [[ "$base" != docs/* ]]; then
    echo "Version base must look like docs/v0.28.4: $base" >&2
    exit 1
  fi
  if ! [[ "${base#docs/}" =~ $version_pattern ]]; then
    echo "Invalid version branch: $base" >&2
    exit 1
  fi
else
  echo "Run from docs/{version}, or pass an explicit docs/{version} base" >&2
  exit 1
fi

git fetch origin "$base"
if ! git show-ref --verify --quiet "refs/remotes/origin/${base}"; then
  echo "Remote version branch does not exist: origin/${base}" >&2
  exit 1
fi
version="${base#docs/}"

if [[ "$task" =~ ^([eE][rR][pP]-)?([0-9]+)$ ]]; then
  task_number="${BASH_REMATCH[2]}"
  slug="$(printf '%04d' "$task_number")"
else
  slug=""
fi

if [[ -z "$slug" ]]; then
  echo "Invalid task id: $task" >&2
  exit 1
fi

target="docs/${version}_${slug}"
if git show-ref --verify --quiet "refs/heads/${target}" || git show-ref --verify --quiet "refs/remotes/origin/${target}"; then
  echo "Branch already exists: ${target}" >&2
  exit 1
fi

if [[ "$branch" == "$base" ]]; then
  git pull --ff-only origin "$base"
  git checkout -b "$target"
else
  git checkout -b "$target" "origin/${base}"
fi

echo "Created task branch: ${target}"
