#!/usr/bin/env python3
"""Check testability admission gates for canonical ERP slices."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


CANONICAL_SLICE_PATTERN = re.compile(
    r"^ERP-SLICE-(PRODUCT|ORD|B2C|IMS|ASS|FIN|PUR|PLAT)-[0-9]{3,4}$"
)
TEST_METHOD_PATTERN = re.compile(
    r"(?:\bunit\b|\bfeature\b|\be2e\b|\bmock\b|单元测试|功能测试|端到端测试|契约测试)",
    re.IGNORECASE,
)
REQUIRED_SECTIONS = ("验收标准", "测试边界", "依赖与 Mock 策略")


def normalize_heading(value: str) -> str:
    return re.sub(r"^\d+(?:[.、])?\s*", "", value.strip())


def section_text(text: str, heading: str) -> str:
    lines = text.splitlines()
    collecting = False
    collected: list[str] = []
    for line in lines:
        match = re.match(r"^#{2,6}\s+(.+?)\s*$", line)
        if match:
            if collecting:
                break
            collecting = normalize_heading(match.group(1)) == heading
            continue
        if collecting:
            collected.append(line)
    return "\n".join(collected).strip()


def parse_table(section: str) -> tuple[list[str], list[list[str]]]:
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    if not lines:
        return [], []
    header = split_table_row(lines[0])
    data: list[list[str]] = []
    for line in lines[1:]:
        cells = split_table_row(line)
        if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells):
            continue
        data.append(cells)
    return header, data


def split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip("|").split("|")]


def check_slice(slice_dir: Path) -> list[str]:
    slice_id = slice_dir.name
    issues: list[str] = []
    contract_path = slice_dir / "contract.md"
    slice_yaml_path = slice_dir / "slice.yaml"
    if not contract_path.is_file():
        return [f"{contract_path}: canonical 切片缺少 contract.md"]
    if not slice_yaml_path.is_file():
        issues.append(f"{slice_yaml_path}: canonical 切片缺少 slice.yaml")
    else:
        slice_yaml = slice_yaml_path.read_text(encoding="utf-8")
        if not re.search(rf"(?m)^\s*slice_id:\s*{re.escape(slice_id)}\s*$", slice_yaml):
            issues.append(f"{slice_yaml_path}: slice_id 必须等于目录名 {slice_id}")

    text = contract_path.read_text(encoding="utf-8")
    if not re.search(rf"(?m)^\s*[-*]\s*(?:\*\*)?slice_id(?:\*\*)?\s*:\s*{re.escape(slice_id)}\s*(?:\|.*)?$", text):
        issues.append(f"{contract_path}: 契约元数据缺少 slice_id: {slice_id}")

    for heading in REQUIRED_SECTIONS:
        if not section_text(text, heading):
            issues.append(f"{contract_path}: 缺少 {heading!r} 章节")
    if any("缺少" in issue and "章节" in issue for issue in issues):
        return issues

    acceptance = section_text(text, "验收标准")
    header, rows = parse_table(acceptance)
    if not header or not rows:
        issues.append(f"{contract_path}: 验收标准必须包含至少一条表格式 AC")
    else:
        try:
            method_index = header.index("验证方式")
        except ValueError:
            issues.append(f"{contract_path}: 验收标准表必须包含 '验证方式' 列")
            method_index = None
        if method_index is not None:
            for number, row in enumerate(rows, start=1):
                if len(row) <= method_index:
                    issues.append(f"{contract_path}: 第 {number} 条 AC 列数不完整")
                    continue
                method = row[method_index]
                if not method:
                    issues.append(f"{contract_path}: 第 {number} 条 AC 缺少验证方式")
                elif not TEST_METHOD_PATTERN.search(method):
                    issues.append(f"{contract_path}: 第 {number} 条 AC 验证方式必须是 unit/feature/E2E/mock")

    boundary = section_text(text, "测试边界")
    independent = re.search(r"(?m)^\s*[-*]\s*(?:\*\*)?独立验证声明(?:\*\*)?\s*[：:]\s*是\s*$", boundary)
    integration_type = re.search(
        r"(?m)^\s*[-*]\s*(?:\*\*)?切片类型(?:\*\*)?\s*[：:]\s*(?:integration|final)\s*$",
        boundary,
        re.IGNORECASE,
    )
    if not independent and not integration_type:
        issues.append(
            f"{contract_path}: 测试边界必须声明 '独立验证声明：是'，或标记 '切片类型：integration/final'"
        )

    dependencies = section_text(text, "依赖与 Mock 策略")
    if dependencies:
        content_lines = [line for line in dependencies.splitlines() if line.strip()]
        if not content_lines:
            issues.append(f"{contract_path}: 依赖与 Mock 策略不能为空")
    return issues


def targets(paths: list[str]) -> list[Path]:
    result: list[Path] = []
    for value in paths:
        path = Path(value)
        if not path.exists():
            continue
        if path.is_dir():
            if CANONICAL_SLICE_PATTERN.match(path.name):
                result.append(path)
            else:
                result.extend(
                    child
                    for child in sorted(path.iterdir())
                    if child.is_dir() and CANONICAL_SLICE_PATTERN.match(child.name)
                )
        elif path.is_file() and path.name == "contract.md":
            result.append(path.parent)
        else:
            result.append(path)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate canonical ERP slice testability admission")
    parser.add_argument("paths", nargs="*", default=["specs/slices"])
    args = parser.parse_args(argv)

    slice_dirs = targets(args.paths)
    issues: list[str] = []
    for slice_dir in slice_dirs:
        if not CANONICAL_SLICE_PATTERN.match(slice_dir.name):
            issues.append(f"{slice_dir}: 只支持 ERP-SLICE-{{DOMAIN}}-{{NNN}} 新规范切片")
            continue
        issues.extend(check_slice(slice_dir))

    if issues:
        print("切片准入校验失败：")
        for issue in issues:
            print(f"  - {issue}")
        return 1
    print(f"切片准入校验通过：{len(slice_dirs)} 个 canonical 切片")
    return 0


if __name__ == "__main__":
    sys.exit(main())
