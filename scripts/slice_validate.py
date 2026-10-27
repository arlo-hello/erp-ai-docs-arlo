#!/usr/bin/env python3
"""Validate ERP slice governance files against JSON Schemas.

Usage:
    python3 scripts/slice_validate.py [path ...]

Default path is specs/slices. Exits non-zero when any file fails.
"""

import json
import sys
from datetime import date, datetime
from pathlib import Path

import jsonschema
import yaml


SCHEMA_DIR = Path(__file__).resolve().parent / "slice_schemas"


def _load_schema(name):
    with (SCHEMA_DIR / name).open(encoding="utf-8") as fh:
        return json.load(fh)


SCHEMAS = {
    "slice.yaml": _load_schema("slice.yaml.schema.json"),
    "run.yaml": _load_schema("run.yaml.schema.json"),
    "slice-state.json": _load_schema("slice-state.json.schema.json"),
    "run-state.json": _load_schema("run-state.json.schema.json"),
    "task.yaml": _load_schema("task.yaml.schema.json"),
    "event.yaml": _load_schema("event.yaml.schema.json"),
}


def load_document(path):
    text = Path(path).read_text(encoding="utf-8")
    if str(path).endswith(".json"):
        return json.loads(text)
    return _stringify_datetimes(yaml.safe_load(text))


def _stringify_datetimes(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, list):
        return [_stringify_datetimes(item) for item in value]
    if isinstance(value, dict):
        return {key: _stringify_datetimes(item) for key, item in value.items()}
    return value


def schema_for(path):
    name = Path(path).name
    if name in SCHEMAS:
        return name, SCHEMAS[name]
    parts = Path(path).parts
    if "events" in parts and name.endswith((".yaml", ".yml", ".json")):
        return "event.yaml", SCHEMAS["event.yaml"]
    return None, None


def validate_file(path, verbose=False):
    kind, schema = schema_for(path)
    if schema is None:
        return 0, None
    try:
        doc = load_document(path)
    except Exception as exc:
        return 1, f"{path}: 无法解析文件: {exc}"
    try:
        jsonschema.validate(instance=doc, schema=schema)
        if verbose:
            print(f"PASS {kind}: {path}")
        return 0, None
    except jsonschema.ValidationError as exc:
        return 1, f"{path}: {exc.message} (at {'/'.join(map(str, exc.absolute_path)) or '$'})"


def validate_tree(root):
    errors = []
    checked = 0
    for path in sorted(Path(root).rglob("*")):
        if not path.is_file() or path.name.startswith("."):
            continue
        code, message = validate_file(path, verbose=False)
        if message:
            errors.append(message)
        if code == 0 and schema_for(path)[0] is not None:
            checked += 1
    return checked, errors


def main(argv):
    targets = argv or ["specs/slices"]
    checked_total = 0
    errors = []
    for target in targets:
        path = Path(target)
        if path.is_dir():
            checked, errs = validate_tree(path)
            checked_total += checked
            errors.extend(errs)
        else:
            code, message = validate_file(path, verbose=True)
            checked_total += 1 if code == 0 else 0
            if message:
                errors.append(message)
    if errors:
        print("切片治理校验失败：")
        for err in errors:
            print(f"  - {err}")
        print(f"检查 {checked_total} 个文件，{len(errors)} 个错误")
        return 1
    print(f"切片治理校验通过：{checked_total} 个文件")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
