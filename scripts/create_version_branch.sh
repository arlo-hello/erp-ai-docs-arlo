#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: ./scripts/create_version_branch.sh v0.29.0" >&2
  exit 2
fi

version="$1"
if [[ ! "$version" =~ ^(v[0-9]+\.[0-9]+\.[0-9]+|hotfix-[0-9]{8}-p[0-9]+)$ ]]; then
  echo "Invalid version: $version" >&2
  exit 1
fi

branch="docs/${version}"
git fetch origin template
if git show-ref --verify --quiet "refs/heads/${branch}"; then
  echo "Branch already exists: ${branch}" >&2
  exit 1
fi

git checkout -b "$branch" origin/template
mkdir -p "docs/${version}/requirements" "docs/${version}/tasks" "specs/${version}/slices"
printf '%s\n' "$version" > docs/versions/current.txt

cat > "specs/${version}/slice-registry.yaml" <<EOF
schema: 1
current_version: ${version}
domains:
  - PRODUCT
  - ORD
  - B2C
  - IMS
  - ASS
  - FIN
  - PUR
  - PLAT
id_pattern: '^ERP-SLICE-(PRODUCT|ORD|B2C|IMS|ASS|FIN|PUR|PLAT)-[0-9]{3,4}$'
slices: []
summary:
  total_slices: 0
  write: 0
  read_only: 0
  defined: 0
  candidate: 0
EOF

git add "docs/${version}" "specs/${version}" docs/versions/current.txt
git commit -m "docs: initialize ${version} version branch"
git push -u origin "$branch"
echo "Created version branch: ${branch}"
