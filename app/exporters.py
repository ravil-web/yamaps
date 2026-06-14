from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Mapping
from typing import Any


def _json_default(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:  # pragma: no cover - defensive
            pass
    return str(value)


def _stringify_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return json.dumps(value, ensure_ascii=False, default=_json_default)


def _flatten_value(value: Any, prefix: str = "", seen: set[int] | None = None) -> dict[str, Any]:
    if seen is None:
        seen = set()

    if isinstance(value, Mapping):
        value_id = id(value)
        if value_id in seen:
            return {prefix.rstrip("_") or "value": "<cycle>"}
        seen.add(value_id)
        flat: dict[str, Any] = {}
        for key, item in value.items():
            child_prefix = f"{prefix}{key}_"
            flat.update(_flatten_value(item, child_prefix, seen))
        seen.remove(value_id)
        return flat

    if isinstance(value, (list, tuple, set, frozenset)):
        value_id = id(value)
        if value_id in seen:
            return {prefix.rstrip("_") or "value": "<cycle>"}
        seen.add(value_id)
        items = list(value)
        if all(not isinstance(item, (Mapping, list, tuple, set, frozenset)) for item in items):
            seen.remove(value_id)
            return {prefix.rstrip("_") or "value": ", ".join(str(_stringify_scalar(item)) for item in items)}

        flat: dict[str, Any] = {}
        for index, item in enumerate(items):
            child_prefix = f"{prefix}{index}_"
            flat.update(_flatten_value(item, child_prefix, seen))
        seen.remove(value_id)
        return flat

    key = prefix.rstrip("_") or "value"
    return {key: _stringify_scalar(value)}


def _flatten_row(row: Mapping[str, Any]) -> dict[str, Any]:
    flat: dict[str, Any] = {}
    for key, value in row.items():
        flat.update(_flatten_value(value, f"{key}_"))
    return flat


def _flatten_results(results: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    return [_flatten_row(result) for result in results]


def export_json(results: Iterable[Mapping[str, Any]]) -> bytes:
    payload = list(results)
    return json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default).encode("utf-8")


def export_csv(results: Iterable[Mapping[str, Any]]) -> bytes:
    rows = _flatten_results(results)
    buffer = io.StringIO()
    if not rows:
        buffer.write("result\n")
        return b"\xef\xbb\xbf" + buffer.getvalue().encode("utf-8")

    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)

    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return b"\xef\xbb\xbf" + buffer.getvalue().encode("utf-8")


def export_xlsx(results: Iterable[Mapping[str, Any]]) -> bytes:
    from openpyxl import Workbook

    rows = _flatten_results(results)
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Results"

    if rows:
        fieldnames: list[str] = []
        for row in rows:
            for key in row:
                if key not in fieldnames:
                    fieldnames.append(key)

        sheet.append(fieldnames)
        for row in rows:
            sheet.append([row.get(column) for column in fieldnames])

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()
