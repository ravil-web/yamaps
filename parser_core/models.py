from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Coordinate = tuple[float, float]


@dataclass(frozen=True)
class Area:
    type: Literal["bbox", "polygon"]
    coordinates: tuple[float, float, float, float] | tuple[Coordinate, ...]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Area":
        area_type = value.get("type")
        coordinates = value.get("coordinates")
        if area_type == "bbox":
            if not isinstance(coordinates, list) or len(coordinates) != 4:
                raise ValueError("bbox coordinates must contain [west, south, east, north]")
            west, south, east, north = (float(item) for item in coordinates)
            if west >= east or south >= north:
                raise ValueError("bbox west/south must be below east/north")
            _validate_lon_lat(west, south)
            _validate_lon_lat(east, north)
            return cls("bbox", (west, south, east, north))
        if area_type == "polygon":
            if not isinstance(coordinates, list) or len(coordinates) < 4:
                raise ValueError("polygon must contain at least four points")
            points = tuple((float(point[0]), float(point[1])) for point in coordinates)
            for point in points:
                _validate_lon_lat(*point)
            if points[0] != points[-1]:
                raise ValueError("polygon ring must be closed")
            return cls("polygon", points)
        raise ValueError("area type must be bbox or polygon")

    @property
    def bbox(self) -> tuple[float, float, float, float]:
        if self.type == "bbox":
            return self.coordinates  # type: ignore[return-value]
        points = self.coordinates  # type: ignore[assignment]
        longitudes = [point[0] for point in points]
        latitudes = [point[1] for point in points]
        return min(longitudes), min(latitudes), max(longitudes), max(latitudes)

    def contains(self, longitude: float, latitude: float) -> bool:
        west, south, east, north = self.bbox
        if not (west <= longitude <= east and south <= latitude <= north):
            return False
        if self.type == "bbox":
            return True
        inside = False
        points = self.coordinates  # type: ignore[assignment]
        j = len(points) - 1
        for i, (xi, yi) in enumerate(points):
            xj, yj = points[j]
            crosses = (yi > latitude) != (yj > latitude)
            if crosses and longitude < (xj - xi) * (latitude - yi) / (yj - yi) + xi:
                inside = not inside
            j = i
        return inside


@dataclass
class ParserParams:
    values: dict[str, Any] = field(default_factory=dict)

    def get(self, name: str, default: Any = None) -> Any:
        return self.values.get(name, default)


@dataclass
class Company:
    data: dict[str, Any]

    @property
    def longitude(self) -> float | None:
        return _optional_float(self.data.get("longitude"))

    @property
    def latitude(self) -> float | None:
        return _optional_float(self.data.get("latitude"))


@dataclass(frozen=True)
class Progress:
    progress: int
    processed: int
    found: int
    message: str


def _validate_lon_lat(longitude: float, latitude: float) -> None:
    if not -180 <= longitude <= 180 or not -90 <= latitude <= 90:
        raise ValueError("coordinates are outside valid longitude/latitude range")


def _optional_float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "") else None
    except (TypeError, ValueError):
        return None

