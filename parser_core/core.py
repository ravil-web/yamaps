from __future__ import annotations

import threading
import uuid
from collections.abc import Callable
from typing import Any

from .geometry import build_search_url, make_tiles
from .legacy_adapter import LegacyAdapter
from .models import Area, Company, ParserParams, Progress
from .normalize import company_key, normalize_company


class ParserCore:
    def __init__(self, adapter_factory: Callable[[ParserParams, str], Any] = LegacyAdapter) -> None:
        self.adapter_factory = adapter_factory

    def run(
        self,
        query: str,
        area: Area,
        params: ParserParams,
        on_progress: Callable[[Progress], None] | None = None,
        on_item: Callable[[Company], None] | None = None,
        stop_flag: threading.Event | None = None,
    ) -> list[Company]:
        if not query.strip():
            raise ValueError("query must not be empty")
        on_progress = on_progress or (lambda progress: None)
        on_item = on_item or (lambda company: None)
        stop_flag = stop_flag or threading.Event()
        rows = int(params.get("area.tile_rows", 1))
        columns = int(params.get("area.tile_columns", 1))
        tiles = make_tiles(area, rows, columns)
        adapter = self.adapter_factory(params, f"web_{uuid.uuid4().hex[:12]}")
        urls: dict[str, None] = {}
        companies: dict[str, Company] = {}
        processed = 0
        try:
            for index, tile in enumerate(tiles, 1):
                if stop_flag.is_set():
                    break
                on_progress(
                    Progress(
                        progress=int((index - 1) / max(len(tiles), 1) * 30),
                        processed=processed,
                        found=len(companies),
                        message=f"Поиск в области {index}/{len(tiles)}",
                    )
                )
                for url in adapter.collect_urls(build_search_url(query, tile)):
                    urls.setdefault(url, None)

            total = len(urls)
            for index, url in enumerate(urls, 1):
                if stop_flag.is_set():
                    break
                raw = adapter.parse_business(url)
                processed += 1
                if raw:
                    company = normalize_company(raw)
                    if (
                        area.type != "polygon"
                        or company.longitude is None
                        or company.latitude is None
                        or area.contains(company.longitude, company.latitude)
                    ):
                        key = company_key(company)
                        if key not in companies:
                            companies[key] = company
                            on_item(company)
                on_progress(
                    Progress(
                        progress=30 + int(index / max(total, 1) * 70),
                        processed=processed,
                        found=len(companies),
                        message=f"Обработка предприятия {index}/{total}",
                    )
                )
            return list(companies.values())
        finally:
            adapter.close()

