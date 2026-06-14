from __future__ import annotations

import os
import threading
import time
from typing import Any

import httpx

_MIN_INTERVAL = 1.0
_last_request_time = 0.0
_rate_lock = threading.Lock()

_MAX_RETRIES = 2
_RETRY_BACKOFF = [0.5, 1.5]


def _rate_wait() -> None:
    global _last_request_time
    with _rate_lock:
        now = time.monotonic()
        wait = _MIN_INTERVAL - (now - _last_request_time)
        if wait > 0:
            time.sleep(wait)
        _last_request_time = time.monotonic()


def _yandex_suggest(address: str, limit: int = 5) -> list[dict[str, Any]]:
    api_key = os.getenv("YANDEX_MAPS_API_KEY", "")
    if not api_key:
        return []
    try:
        response = httpx.get(
            "https://geocode-maps.yandex.ru/1.x/",
            params={
                "apikey": api_key,
                "geocode": address,
                "format": "json",
                "results": limit,
                "lang": "ru_RU",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        members = (
            data.get("response", {})
            .get("GeoObjectCollection", {})
            .get("featureMember", [])
        )
        results = []
        for item in members:
            geo = item.get("GeoObject", {})
            pos = geo.get("Point", {}).get("pos", "")
            coords = pos.split() if pos else []
            lon = float(coords[0]) if len(coords) >= 2 else 0
            lat = float(coords[1]) if len(coords) >= 2 else 0
            name = geo.get("name", "")
            description = geo.get("description", "")
            full_name = f"{name}, {description}" if description else name
            results.append({
                "latitude": lat,
                "longitude": lon,
                "address": full_name,
                "name": name,
                "description": description,
            })
        return results
    except Exception:
        return []


def _nominatim_suggest(address: str, limit: int = 5) -> list[dict[str, Any]]:
    last_exc: Exception | None = None
    for attempt in range(_MAX_RETRIES + 1):
        _rate_wait()
        try:
            response = httpx.get(
                "https://nominatim.openstreetmap.org/search",
                params={
                    "format": "jsonv2",
                    "limit": limit,
                    "q": address,
                    "accept-language": "ru",
                    "addressdetails": 1,
                },
                headers={"User-Agent": "YandexMapsParserLocal/1.0"},
                timeout=15,
            )
            if response.status_code == 429:
                retry_after = float(response.headers.get("Retry-After", _RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)]))
                if attempt < _MAX_RETRIES:
                    time.sleep(retry_after)
                    continue
                response.raise_for_status()
            response.raise_for_status()
            results = []
            for item in response.json():
                addr = item.get("address", {})
                parts = []
                for key in ["house_number", "road", "suburb", "city_district", "city", "state", "country"]:
                    if addr.get(key):
                        parts.append(addr[key])
                short = ", ".join(parts) if parts else item.get("display_name", address)
                results.append({
                    "latitude": float(item["lat"]),
                    "longitude": float(item["lon"]),
                    "address": item.get("display_name", address),
                    "name": short,
                    "description": item.get("type", ""),
                })
            return results
        except (httpx.TimeoutException, httpx.ConnectError) as exc:
            last_exc = exc
            if attempt < _MAX_RETRIES:
                time.sleep(_RETRY_BACKOFF[min(attempt, len(_RETRY_BACKOFF) - 1)])
                continue
            raise
    raise last_exc  # type: ignore[misc]


def suggest_addresses(address: str, limit: int = 5) -> list[dict[str, Any]]:
    results = _yandex_suggest(address, limit)
    if results:
        return results
    return _nominatim_suggest(address, limit)


def geocode_address(address: str) -> dict[str, Any] | None:
    items = suggest_addresses(address, limit=1)
    return items[0] if items else None
