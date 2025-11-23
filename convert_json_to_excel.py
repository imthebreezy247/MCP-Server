#!/usr/bin/env python3
"""
Utility script to convert JSON exports in the repo root into Excel files.
Each JSON file (except credentials/tokens) gets a matching .xlsx file.
Dict-based JSONs become multi-sheet workbooks; list-based JSONs become single sheets.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List

import pandas as pd

# Root directory (this script lives in repo root)
ROOT_DIR = Path(__file__).parent

# Skip sensitive/auxiliary JSON exports
SKIP_PREFIXES = ("token", "credentials", ".claude")
SKIP_EXACT = {
    "claude_desktop_config.json",
}


def should_skip(path: Path) -> bool:
    """Return True when the JSON file should not be converted."""
    name = path.name
    if name in SKIP_EXACT:
        return True
    return name.startswith(SKIP_PREFIXES)


def sanitize_sheet_name(name: str, existing: Iterable[str]) -> str:
    """Make a sheet name Excel-friendly and unique."""
    cleaned = re.sub(r"[\[\]*?:/\\]", " ", name).strip() or "Sheet"
    cleaned = cleaned[:31]
    if cleaned not in existing:
        return cleaned

    # Append numeric suffix until unique (respect 31-char limit)
    counter = 1
    base = cleaned.rstrip()
    while True:
        suffix = f"_{counter}"
        trimmed_base = base[: 31 - len(suffix)] or base
        candidate = f"{trimmed_base}{suffix}"
        if candidate not in existing:
            return candidate
        counter += 1


def records_to_dataframe(records: List[Any]) -> pd.DataFrame:
    """Convert a list into a DataFrame, flattening dict records when possible."""
    if not records:
        return pd.DataFrame()

    first = records[0]
    if isinstance(first, dict):
        return pd.json_normalize(records)

    # Heterogeneous or scalar list -> single column
    return pd.DataFrame({"value": records})


def anydict_to_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """Convert a dict into a single-row DataFrame, flattening nested keys."""
    return pd.json_normalize([data])


def write_value_to_excel(writer: pd.ExcelWriter, sheet_name: str, value: Any, existing: set[str]) -> None:
    """Write any JSON value to a sheet within the Excel writer."""
    safe_name = sanitize_sheet_name(sheet_name, existing)
    existing.add(safe_name)

    if isinstance(value, list):
        df = records_to_dataframe(value)
    elif isinstance(value, dict):
        df = anydict_to_dataframe(value)
    else:
        df = pd.DataFrame({"value": [value]})

    df.to_excel(writer, sheet_name=safe_name, index=False)


def convert_json_file(path: Path) -> Path:
    """Convert a JSON file to Excel and return the output path."""
    excel_path = path.with_suffix(".xlsx")
    data = json.loads(path.read_text(encoding="utf-8"))

    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        used_sheets: set[str] = set()
        if isinstance(data, dict):
            for key, value in data.items():
                write_value_to_excel(writer, key, value, used_sheets)
        else:
            write_value_to_excel(writer, path.stem, data, used_sheets)

    return excel_path


def main() -> None:
    json_files = sorted(ROOT_DIR.glob("*.json"))
    if not json_files:
        print("No JSON files found in repo root.")
        return

    converted = []
    skipped = []

    for json_path in json_files:
        if should_skip(json_path):
            skipped.append(json_path.name)
            continue

        try:
            excel_path = convert_json_file(json_path)
            converted.append((json_path.name, excel_path.name))
            print(f"[OK] {json_path.name} -> {excel_path.name}")
        except Exception as exc:
            print(f"[ERROR] Failed to convert {json_path.name}: {exc}")

    if converted:
        print("\nConverted files:")
        for src, dst in converted:
            print(f"  - {src} -> {dst}")

    if skipped:
        print("\nSkipped files:")
        for name in skipped:
            print(f"  - {name} (marked as sensitive/auxiliary)")


if __name__ == "__main__":
    main()
