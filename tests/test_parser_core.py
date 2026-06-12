from __future__ import annotations

import threading

import pytest

from parser_core.core import ParserCore
from parser_core.geometry import Tile, build_search_url, make_tiles
from parser_core.models import Area, Company, ParserParams, Progress
from parser_core.normalize import (
    company_key,
    filter_and_deduplicate,
    normalize_company,
)


def test_area_validation_contains_and_bbox() -> None:
    bbox = Area.from_dict({"type": "bbox", "coordinates": [39.65, 47.2, 39.75, 47.3]})
    assert bbox.bbox == (39.65, 47.2, 39.75, 47.3)
    assert bbox.contains(39.7, 47.25)
    assert bbox.contains(39.65, 47.2)
    assert not bbox.contains(39.8, 47.25)

    polygon = Area.from_dict(
        {
            "type": "polygon",
            "coordinates": [
                [39.65, 47.2],
                [39.75, 47.2],
                [39.75, 47.3],
                [39.65, 47.3],
                [39.65, 47.2],
            ],
        }
    )
    assert polygon.bbox == (39.65, 47.2, 39.75, 47.3)
    assert polygon.contains(39.7, 47.25)
    assert not polygon.contains(39.8, 47.25)

    with pytest.raises(ValueError, match="bbox west/south must be below east/north"):
        Area.from_dict({"type": "bbox", "coordinates": [39.75, 47.3, 39.65, 47.2]})

    with pytest.raises(ValueError, match="polygon ring must be closed"):
        Area.from_dict(
            {
                "type": "polygon",
                "coordinates": [
                    [39.65, 47.2],
                    [39.75, 47.2],
                    [39.75, 47.3],
                    [39.65, 47.3],
                ],
            }
        )

    with pytest.raises(ValueError, match="coordinates are outside valid longitude/latitude range"):
        Area.from_dict({"type": "bbox", "coordinates": [181, 0, 182, 1]})


def test_make_tiles_and_build_search_url() -> None:
    area = Area.from_dict({"type": "bbox", "coordinates": [0, 0, 4, 2]})
    tiles = make_tiles(area, rows=2, columns=2)
    assert tiles == [
        Tile(0.0, 0.0, 2.0, 1.0),
        Tile(2.0, 0.0, 4.0, 1.0),
        Tile(0.0, 1.0, 2.0, 2.0),
        Tile(2.0, 1.0, 4.0, 2.0),
    ]

    url = build_search_url("coffee shop", tiles[0])
    assert (
        url
        == "https://yandex.ru/maps/?ll=1.000000%2C0.500000&mode=search&text=coffee%20shop"
        "&sll=1.000000%2C0.500000&sspn=2.000000%2C1.000000&z=6.99"
    )


def test_normalize_company_and_deduplicate_by_id_url_and_coordinates() -> None:
    inside_area = Area.from_dict({"type": "bbox", "coordinates": [39.6, 47.2, 39.8, 47.3]})

    id_first = normalize_company(
        {
            "name": "Id first",
            "url": "https://yandex.ru/maps/org/example/12345/?ll=39.700000%2C47.250000",
        }
    )
    id_second = normalize_company(
        {
            "name": "Id second",
            "url": "https://yandex.ru/maps/org/other/12345/?ll=39.710000%2C47.260000",
        }
    )
    assert id_first.longitude == pytest.approx(39.7)
    assert id_first.latitude == pytest.approx(47.25)
    assert id_first.data["yandex_id"] == "12345"

    url_first = normalize_company(
        {
            "name": "Url first",
            "url": "https://example.com/company/?x=1",
        }
    )
    url_second = normalize_company(
        {
            "name": "Url second",
            "url": "https://example.com/company/?x=2",
        }
    )

    coord_first = normalize_company(
        {
            "name": "Coord first",
            "longitude": 39.700001,
            "latitude": 47.250001,
        }
    )
    coord_second = normalize_company(
        {
            "name": "Coord second",
            "longitude": 39.700001,
            "latitude": 47.250001,
        }
    )

    assert company_key(id_first) == "id:12345"
    assert company_key(url_first) == "url:https://example.com/company"
    assert company_key(coord_first) == "coord:39.700001,47.250001"

    deduplicated = filter_and_deduplicate(
        [id_first, id_second, url_first, url_second, coord_first, coord_second],
        inside_area,
    )
    assert [company.data["name"] for company in deduplicated] == [
        "Id first",
        "Url first",
        "Coord first",
    ]


class FakeAdapter:
    def __init__(self, params: ParserParams, session_name: str, collect_batches: list[list[str]], parsed: dict[str, dict[str, object] | None]) -> None:
        self.params = params
        self.session_name = session_name
        self.collect_batches = collect_batches
        self.parsed = parsed
        self.collect_calls: list[str] = []
        self.parse_calls: list[str] = []
        self.closed = False

    def collect_urls(self, search_url: str) -> list[str]:
        self.collect_calls.append(search_url)
        return list(self.collect_batches[len(self.collect_calls) - 1])

    def parse_business(self, url: str) -> dict[str, object] | None:
        self.parse_calls.append(url)
        return self.parsed.get(url)

    def close(self) -> None:
        self.closed = True


def test_parser_core_calls_callbacks_dedups_and_filters_polygon_results() -> None:
    area = Area.from_dict(
        {
            "type": "polygon",
            "coordinates": [
                [39.6, 47.2],
                [39.8, 47.2],
                [39.8, 47.3],
                [39.6, 47.3],
                [39.6, 47.2],
            ],
        }
    )
    params = ParserParams({"area.tile_rows": 1, "area.tile_columns": 1})

    inside_url = "https://yandex.ru/maps/org/alpha/123/?ll=39.700000%2C47.250000"
    outside_url = "https://yandex.ru/maps/org/outside/999/?ll=40.000000%2C47.250000"
    parsed = {
        inside_url: {
            "name": "Inside A",
            "url": inside_url,
        },
        outside_url: {
            "name": "Outside",
            "url": outside_url,
        },
    }
    adapter = FakeAdapter(params, "web_test", [[inside_url, inside_url, outside_url]], parsed)

    progress_updates: list[Progress] = []
    items: list[Company] = []

    core = ParserCore(adapter_factory=lambda p, s: adapter)
    result = core.run(
        "coffee",
        area,
        params,
        on_progress=progress_updates.append,
        on_item=items.append,
        stop_flag=threading.Event(),
    )

    assert adapter.collect_calls == [
        "https://yandex.ru/maps/?ll=39.700000%2C47.250000&mode=search&text=coffee"
        "&sll=39.700000%2C47.250000&sspn=0.200000%2C0.100000&z=8.97"
    ]
    assert adapter.parse_calls == [inside_url, outside_url]
    assert adapter.closed is True
    assert len(items) == 1
    assert items[0].data["name"] == "Inside A"
    assert items[0].longitude == pytest.approx(39.7)
    assert items[0].latitude == pytest.approx(47.25)
    assert [company.data["name"] for company in result] == ["Inside A"]
    assert [update.processed for update in progress_updates] == [0, 1, 2]
    assert [update.found for update in progress_updates] == [0, 1, 1]
    assert progress_updates[-1].progress == 100


def test_parser_core_stops_between_urls_and_tiles() -> None:
    area = Area.from_dict({"type": "bbox", "coordinates": [0, 0, 4, 2]})
    params = ParserParams({"area.tile_rows": 1, "area.tile_columns": 2})

    first_tile_first = "https://yandex.ru/maps/org/alpha/123/?ll=1.000000%2C0.500000"
    first_tile_second = "https://yandex.ru/maps/org/beta/124/?ll=1.500000%2C0.500000"
    second_tile_url = "https://yandex.ru/maps/org/gamma/125/?ll=3.000000%2C0.500000"
    parsed = {
        first_tile_first: {
            "name": "First",
            "url": first_tile_first,
        },
        first_tile_second: {
            "name": "Second",
            "url": first_tile_second,
        },
        second_tile_url: {
            "name": "Third",
            "url": second_tile_url,
        },
    }
    adapter = FakeAdapter(
        params,
        "web_stop",
        [[first_tile_first, first_tile_second], [second_tile_url]],
        parsed,
    )

    progress_updates: list[Progress] = []
    stop_flag = threading.Event()
    item_calls: list[str] = []

    def on_item(company: Company) -> None:
        item_calls.append(company.data["name"])

    def on_progress(progress: Progress) -> None:
        progress_updates.append(progress)
        stop_flag.set()

    core = ParserCore(adapter_factory=lambda p, s: adapter)
    result = core.run(
        "coffee",
        area,
        params,
        on_progress=on_progress,
        on_item=on_item,
        stop_flag=stop_flag,
    )

    assert adapter.collect_calls == [
        "https://yandex.ru/maps/?ll=1.000000%2C1.000000&mode=search&text=coffee"
        "&sll=1.000000%2C1.000000&sspn=2.000000%2C2.000000&z=6.97"
    ]
    assert adapter.parse_calls == []
    assert adapter.closed is True
    assert item_calls == []
    assert result == []
    assert [update.processed for update in progress_updates] == [0]
    assert [update.found for update in progress_updates] == [0]
