from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .models import Area, Company

COORDINATE_RE = re.compile(r"(?P<lon>-?\d{1,3}\.\d+)[,%2C]+(?P<lat>-?\d{1,2}\.\d+)", re.I)
ID_RE = re.compile(r"/(\d{5,})/?(?:[?#]|$)")


def normalize_company(raw: dict[str, Any]) -> Company:
    data = dict(raw)
    longitude, latitude = _coordinates(data)
    data["longitude"] = longitude
    data["latitude"] = latitude
    if not data.get("yandex_id"):
        match = ID_RE.search(str(data.get("url", "")))
        if match:
            data["yandex_id"] = match.group(1)
    return Company(data)


def company_key(company: Company) -> str:
    data = company.data
    if data.get("yandex_id"):
        return f"id:{data['yandex_id']}"
    if data.get("url"):
        return f"url:{str(data['url']).split('?')[0].rstrip('/')}"
    if company.longitude is not None and company.latitude is not None:
        return f"coord:{company.longitude:.6f},{company.latitude:.6f}"
    return f"name:{data.get('name', '')}|address:{data.get('address', '')}"


def filter_and_deduplicate(companies: list[Company], area: Area) -> list[Company]:
    result: dict[str, Company] = {}
    for company in companies:
        if (
            area.type == "polygon"
            and company.longitude is not None
            and company.latitude is not None
            and not area.contains(company.longitude, company.latitude)
        ):
            continue
        result.setdefault(company_key(company), company)
    return list(result.values())


def _coordinates(data: dict[str, Any]) -> tuple[float | None, float | None]:
    longitude = _float(data.get("longitude") or data.get("lon"))
    latitude = _float(data.get("latitude") or data.get("lat"))
    coordinates = data.get("coordinates")
    if isinstance(coordinates, dict):
        latitude = latitude or _float(coordinates.get("lat") or coordinates.get("latitude"))
        longitude = longitude or _float(coordinates.get("lon") or coordinates.get("longitude"))
    if longitude is not None and latitude is not None:
        return longitude, latitude
    url = unquote(str(data.get("url", "")))
    query = parse_qs(urlparse(url).query)
    for key in ("ll", "sll"):
        if key in query:
            match = COORDINATE_RE.search(query[key][0])
            if match:
                return float(match.group("lon")), float(match.group("lat"))
    match = COORDINATE_RE.search(url)
    if match:
        return float(match.group("lon")), float(match.group("lat"))
    return None, None


def _float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None

