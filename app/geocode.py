from __future__ import annotations

from typing import Any

import httpx


def suggest_addresses(address: str, limit: int = 5) -> list[dict[str, Any]]:
    response = httpx.get(
        "https://nominatim.openstreetmap.org/search",
        params={"format": "jsonv2", "limit": limit, "q": address, "accept-language": "ru"},
        headers={"User-Agent": "YandexMapsParserLocal/1.0"},
        timeout=15,
    )
    response.raise_for_status()
    return [
        {
            "latitude": float(item["lat"]),
            "longitude": float(item["lon"]),
            "address": item.get("display_name", address),
        }
        for item in response.json()
    ]


def geocode_address(address: str) -> dict[str, Any] | None:
    items = suggest_addresses(address, limit=1)
    return items[0] if items else None
