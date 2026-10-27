#!/usr/bin/env python3
"""Validate the selected PM skill baseline and its local dependencies."""

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
SKILLS = {
    "erp-product-doc-generator",
    "erp-requirement-analyzer",
    "erp-slice-orchestrator",
    "external-design-miner",
    "solution-consistency-checker",
    "systematic-debugging",
    "verification-before-completion",
    "erp-scout-protocol",
}
REQUIRED_FILES = {
    "scripts/slice_init.py",
    "scripts/slice_validate.py",
    "scripts/gate_check.py",
    "config/mcp.example.json",
    "agents/ERP-PM.md",
    ".agents/SKILL_REGISTRY.md",
}
CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")


def main() -> int:
    issues: list[str] = []
    for skill in sorted(SKILLS):
        path = ROOT / ".agents" / "skills" / skill / "SKILL.md"
        if not path.is_file():
            issues.append(f"missing skill entry: {path.relative_to(ROOT)}")

    for relative in sorted(REQUIRED_FILES):
        if not (ROOT / relative).is_file():
            issues.append(f"missing dependency: {relative}")

    for path in (ROOT / ".agents" / "skills").rglob("*"):
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for marker in CONFLICT_MARKERS:
            if any(line.startswith(marker) for line in text.splitlines()):
                issues.append(
                    f"unresolved conflict marker {marker!r}: {path.relative_to(ROOT)}"
                )
                break

    if issues:
        print("Skill baseline check failed:")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(f"Skill baseline check passed: {len(SKILLS)} skills.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

