from __future__ import annotations

import threading
import time
from collections.abc import Callable

from parser_core import Area, Company, ParserParams, Progress


class DemoParserCore:
    """Deterministic offline core for smoke tests and UI demonstrations."""

    def __init__(self, item_delay: float = 0.03) -> None:
        self.item_delay = item_delay

    def run(
        self,
        query: str,
        area: Area,
        params: ParserParams,
        on_progress: Callable[[Progress], None],
        on_item: Callable[[Company], None],
        stop_flag: threading.Event,
    ) -> list[Company]:
        west, south, east, north = area.bbox
        target = int(params.get("target_businesses_count", 12)) or 12
        target = min(target, 40)
        results: list[Company] = []
        index = 0
        attempts = 0
        while len(results) < target and attempts < target * 5:
            attempts += 1
            column = attempts % 7 + 1
            row = attempts // 7 + 1
            longitude = west + (east - west) * column / 9
            latitude = south + (north - south) * row / 9
            if not area.contains(longitude, latitude):
                continue
            if stop_flag.wait(self.item_delay):
                break
            company = Company(
                {
                    "name": f"{query.title()} #{index + 1}",
                    "address": f"Тестовый адрес, {index + 1}",
                    "phones": [f"+7 900 000-{index:02d}-{index:02d}"],
                    "rating": round(4.0 + (index % 10) / 10, 1),
                    "url": f"https://yandex.ru/maps/org/demo/{100000 + index}/",
                    "yandex_id": str(100000 + index),
                    "longitude": longitude,
                    "latitude": latitude,
                    "categories": [query],
                }
            )
            results.append(company)
            on_item(company)
            index += 1
            on_progress(
                Progress(
                    progress=int(len(results) / target * 100),
                    processed=len(results),
                    found=len(results),
                    message=f"Демо: обработано {len(results)}/{target}",
                )
            )
        return results
