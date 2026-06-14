from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SCHEMA_PATH = Path(__file__).resolve().parents[1] / "params_schema.json"


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def defaults() -> dict[str, Any]:
    return {item["name"]: item["default"] for item in load_schema()["parameters"]}


def validate_params(values: dict[str, Any]) -> dict[str, Any]:
    schema = load_schema()
    definitions = {item["name"]: item for item in schema["parameters"]}
    unknown = sorted(set(values) - set(definitions) - {"area.tile_rows", "area.tile_columns"})
    if unknown:
        raise ValueError(f"unknown parser parameters: {', '.join(unknown)}")
    result = defaults()
    result.update(values)
    for name in ("area.tile_rows", "area.tile_columns"):
        raw = values.get(name, 1)
        try:
            result[name] = int(raw)
        except (TypeError, ValueError):
            raise ValueError(f"{name} must be an integer, got {type(raw).__name__}: {raw!r}") from None
        if not 1 <= result[name] <= 20:
            raise ValueError(f"{name} must be between 1 and 20")
    return result

