from __future__ import annotations

import importlib
import os
import sys
import types
from pathlib import Path
from typing import Any

from .models import ParserParams

LEGACY_ROOT = Path(__file__).resolve().parents[1] / "legacy"


class LegacyAdapter:
    """Thin adapter over the immutable selected legacy parser implementation."""

    def __init__(self, params: ParserParams, session_name: str) -> None:
        _ensure_utf8_console()
        legacy_path = str(LEGACY_ROOT)
        if legacy_path not in sys.path:
            sys.path.insert(0, legacy_path)
        self.config = importlib.import_module("src.config")
        self.yandex_module = importlib.import_module("src.parsers.yandex_parser")
        self.single_module = importlib.import_module("src.parsers.single_parser")
        self.params = params
        self._apply_params(params)
        if os.getenv("PARSER_HEADLESS", "1") != "0":
            self._enable_headless_browser()
        self.parser = self.yandex_module.MainParser(session_name=session_name)

    def collect_urls(self, search_url: str) -> list[str]:
        self.config.SEARCH_URL = search_url
        self.yandex_module.SEARCH_URL = search_url
        return self.parser.extract_business_urls()

    def parse_business(self, url: str) -> dict[str, Any] | None:
        single = self.single_module.SingleBusinessParser(
            session_folder=f"{self.parser.session_folder}/businesses"
        )
        single.max_products = int(self.params.get("target_products_count", self.config.TARGET_PRODUCTS_COUNT))
        original_timed_find = single.find_element_by_selectors_with_timeout
        address_timeout = int(self.params.get("single.address_timeout", 5))
        selector_timeout = int(self.params.get("single.find_element_by_selectors_with_timeout.timeout", 10))

        def configured_timed_find(instance: Any, selectors: list[str], timeout: int = 10) -> Any:
            configured_timeout = address_timeout if timeout == 5 else selector_timeout if timeout == 10 else timeout
            return original_timed_find(selectors, timeout=configured_timeout)

        single.find_element_by_selectors_with_timeout = types.MethodType(configured_timed_find, single)
        try:
            return single.parse_single_business(url)
        finally:
            single.close()

    def close(self) -> None:
        self.parser.close()

    def _apply_params(self, params: ParserParams) -> None:
        target = int(params.get("target_businesses_count", self.config.TARGET_BUSINESSES_COUNT))
        products = int(params.get("target_products_count", self.config.TARGET_PRODUCTS_COUNT))
        delays = dict(self.config.DELAYS)
        for name in delays:
            delays[name] = params.get(f"delays.{name}", delays[name])
        self.config.TARGET_BUSINESSES_COUNT = target
        self.config.TARGET_PRODUCTS_COUNT = products
        self.config.DELAYS = delays
        browser_options = dict(self.config.BROWSER_OPTIONS)
        for name in browser_options:
            browser_options[name] = params.get(f"browser.{name}", browser_options[name])
        error_handling = dict(self.config.ERROR_HANDLING)
        for name in error_handling:
            error_handling[name] = params.get(f"error.{name}", error_handling[name])
        self.config.BROWSER_OPTIONS = browser_options
        self.config.ERROR_HANDLING = error_handling
        for config_name, prefix in (
            ("FOLDER_STRUCTURE", "folder"),
            ("LOGGING", "logging"),
            ("SAVE_OPTIONS", "save"),
        ):
            configured = dict(getattr(self.config, config_name))
            for name in configured:
                configured[name] = params.get(f"{prefix}.{name}", configured[name])
            setattr(self.config, config_name, configured)
            setattr(self.yandex_module, config_name, configured)
        self.yandex_module.TARGET_BUSINESSES_COUNT = target
        self.yandex_module.TARGET_PRODUCTS_COUNT = products
        self.yandex_module.DELAYS = delays
        self.yandex_module.BROWSER_OPTIONS = browser_options
        self.yandex_module.ERROR_HANDLING = error_handling

    def _enable_headless_browser(self) -> None:
        for module in (self.yandex_module, self.single_module):
            if getattr(module.Options, "_web_headless_factory", False):
                continue
            base_options = module.Options

            def headless_options(base: Any = base_options) -> Any:
                options = base()
                options.add_argument("--headless=new")
                options.add_argument("--disable-gpu")
                return options

            headless_options._web_headless_factory = True
            module.Options = headless_options


def _ensure_utf8_console() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (AttributeError, OSError):
                pass
