from __future__ import annotations

from dataclasses import dataclass
from math import log, tan, pi
from urllib.parse import quote

from .models import Area


@dataclass(frozen=True)
class Tile:
    west: float
    south: float
    east: float
    north: float

    @property
    def center(self) -> tuple[float, float]:
        return (self.west + self.east) / 2, (self.south + self.north) / 2

    @property
    def span(self) -> tuple[float, float]:
        return self.east - self.west, self.north - self.south


def make_tiles(area: Area, rows: int = 1, columns: int = 1) -> list[Tile]:
    if rows < 1 or columns < 1 or rows > 20 or columns > 20:
        raise ValueError("tile rows and columns must be between 1 and 20")
    west, south, east, north = area.bbox
    width = (east - west) / columns
    height = (north - south) / rows
    return [
        Tile(
            west + column * width,
            south + row * height,
            west + (column + 1) * width,
            south + (row + 1) * height,
        )
        for row in range(rows)
        for column in range(columns)
    ]


def build_search_url(query: str, tile: Tile) -> str:
    longitude, latitude = tile.center
    longitude_span, latitude_span = tile.span
    zoom = _zoom_for_span(max(longitude_span, latitude_span), latitude)
    encoded_query = quote(query.strip(), safe="")
    return (
        f"https://yandex.ru/maps/?ll={longitude:.6f}%2C{latitude:.6f}"
        f"&mode=search&text={encoded_query}"
        f"&sll={longitude:.6f}%2C{latitude:.6f}"
        f"&sspn={longitude_span:.6f}%2C{latitude_span:.6f}&z={zoom:.2f}"
    )


def _zoom_for_span(span: float, latitude: float) -> float:
    if span <= 0:
        return 16.0
    latitude_factor = max(0.2, abs(tan((45 + latitude / 2) * pi / 180)))
    return max(3.0, min(19.0, 8.0 - log(span * latitude_factor, 2)))

