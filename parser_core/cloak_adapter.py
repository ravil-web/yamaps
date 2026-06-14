from __future__ import annotations

import asyncio
import logging
import os
import re
import threading
import time
from datetime import datetime
from typing import Any

from .models import ParserParams

logger = logging.getLogger(__name__)

_browser_path: str | None = None
_pw = None
_browser = None
_loop: asyncio.AbstractEventLoop | None = None
_loop_thread: threading.Thread | None = None
_init_lock = threading.Lock()


def _start_loop():
    global _loop, _loop_thread
    _loop = asyncio.new_event_loop()
    asyncio.set_event_loop(_loop)
    _loop_thread = threading.Thread(target=_loop.run_forever, daemon=True, name="playwright-loop")
    _loop_thread.start()


def _ensure_browser():
    global _pw, _browser, _browser_path
    with _init_lock:
        if _browser is not None:
            return
        from cloakbrowser import binary_info

        info = binary_info()
        _browser_path = info.get("path") or os.path.expanduser(
            "~/.cloakbrowser/chromium-146.0.7680.177.5/chrome.exe"
        )
        if not os.path.exists(_browser_path):
            raise FileNotFoundError(f"CloakBrowser binary not found at {_browser_path}")

        if _loop is None:
            _start_loop()

        async def _init():
            global _pw, _browser
            from playwright.async_api import async_playwright
            headless = os.getenv("PARSER_HEADLESS", "1") != "0"
            _pw = await async_playwright().start()
            _browser = await _pw.chromium.launch(
                executable_path=_browser_path,
                headless=headless,
                args=["--no-sandbox", "--disable-dev-shm-usage"],
            )
            logger.info("CloakBrowser initialized (headless=%s, path=%s)", headless, _browser_path)

        future = asyncio.run_coroutine_threadsafe(_init(), _loop)
        future.result(timeout=30)


def _run_async(coro):
    if _loop is None:
        raise RuntimeError("Playwright loop not initialized")
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    return future.result(timeout=120)


class CloakAdapter:
    """Adapter using CloakBrowser (Playwright-based stealth Chromium)."""

    def __init__(self, params: ParserParams, session_name: str) -> None:
        self.params = params
        self.session_name = session_name
        self.session_folder = f"parsing_results/{session_name}"
        os.makedirs(f"{self.session_folder}/businesses", exist_ok=True)
        self._page = None
        self._setup()

    def _setup(self) -> None:
        _ensure_browser()
        width, height = 1920, 1080
        ws = self.params.get("browser.window_size", "1920,1080")
        if "," in ws:
            try:
                width, height = (int(x.strip()) for x in ws.split(",", 1))
            except ValueError:
                pass

        async def _new_page():
            page = await _browser.new_page(viewport={"width": width, "height": height})
            timeout_s = int(self.params.get("delays.page_load", 5))
            page.set_default_timeout(max(timeout_s, 15) * 1000)
            page.set_default_navigation_timeout(max(timeout_s, 15) * 1000)
            return page

        self._page = _run_async(_new_page())

    def collect_urls(self, search_url: str, stop_flag: threading.Event | None = None) -> list[str]:
        stop_flag = stop_flag or threading.Event()
        delays_scroll = int(self.params.get("delays.scroll", 1))
        nav_timeout = 30000

        async def _collect():
            page = self._page
            logger.info("Navigating to: %s", search_url[:120])
            try:
                await page.goto(search_url, wait_until="domcontentloaded", timeout=nav_timeout)
            except Exception as exc:
                logger.error("Navigation failed: %s", exc)
                return []

            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                logger.warning("networkidle timeout, continuing")

            for wait_sel in [
                "div.search-list-view__list",
                "div.search-snippet-view",
                "div.scroll__container",
                "div.search-tab-business",
                "a[href*='/maps/org/']",
                "a[href*='/org/']",
            ]:
                try:
                    await page.wait_for_selector(wait_sel, state="attached", timeout=8000)
                    logger.info("Found element: %s", wait_sel)
                    break
                except Exception:
                    continue

            if stop_flag.is_set():
                return []

            scroll_container = await self._find_scroll_container(page)
            if scroll_container:
                await self._scroll_container(page, scroll_container, stop_flag)

            if stop_flag.is_set():
                return []

            await self._scroll_window(page, delays_scroll, stop_flag)

            if stop_flag.is_set():
                return []

            return await self._collect_links(page, stop_flag)

        result = _run_async(_collect())
        logger.info("Found %d business URLs", len(result))
        return result

    async def _find_scroll_container(self, page) -> str | None:
        selectors = [
            "div.search-list-view__list",
            "div.search-snippet-view",
            "div.scroll__container",
            "div.search-tab-business",
        ]
        for attempt in range(3):
            for sel in selectors:
                try:
                    count = await page.locator(sel).count()
                    if count > 0:
                        logger.info("Found scroll container: %s (%d)", sel, count)
                        return sel
                except Exception:
                    continue
            if attempt < 2:
                await asyncio.sleep(3)

        try:
            title = await page.title()
            url = page.url
            body_len = await page.evaluate("document.body.innerHTML.length")
            logger.warning("No scroll container. title=%s url=%s body=%d", title, url[:100], body_len)
        except Exception:
            pass
        return None

    async def _scroll_container(self, page, container_sel: str, stop_flag: threading.Event) -> None:
        for i in range(30):
            if stop_flag.is_set():
                return
            try:
                await page.evaluate(f'document.querySelector("{container_sel}").scrollTop += 1000')
                await asyncio.sleep(0.3)
                info = await page.evaluate(
                    f'(() => {{ const c = document.querySelector("{container_sel}"); '
                    f'return {{top: c.scrollTop, h: c.scrollHeight, ch: c.clientHeight}}; }})()'
                )
                if info["top"] + info["ch"] >= info["h"] - 100:
                    break
                if i % 5 == 0:
                    logger.info("Container scroll: %d/30", i + 1)
            except Exception:
                break

    async def _scroll_window(self, page, delays_scroll: int, stop_flag: threading.Event) -> None:
        last_height = 0
        try:
            last_height = await page.evaluate("document.body.scrollHeight")
        except Exception:
            pass

        for i in range(15):
            if stop_flag.is_set():
                return
            try:
                await page.evaluate("window.scrollBy(0, 800)")
            except Exception:
                break
            await asyncio.sleep(delays_scroll * 0.5)
            try:
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height > last_height:
                    last_height = new_height
            except Exception:
                pass

            try:
                show_more = page.locator(
                    "xpath=//button[contains(text(), 'Показать ещё') or contains(text(), 'Показать еще') or contains(@class, 'show-more')]"
                )
                if await show_more.count() > 0 and await show_more.first.is_visible():
                    await show_more.first.click()
                    await asyncio.sleep(1)
            except Exception:
                pass

            if i % 5 == 0:
                logger.info("Window scroll: %d/15", i + 1)

    async def _collect_links(self, page, stop_flag: threading.Event) -> list[str]:
        business_urls: list[str] = []
        seen: set[str] = set()
        target = int(self.params.get("target_businesses_count", 0))

        all_links = []
        try:
            all_links = await page.query_selector_all("a[href*='/org/']")
            logger.info("query_selector_all found %d links", len(all_links))
        except Exception as exc:
            logger.warning("query_selector_all failed: %s", exc)

        for link in all_links:
            if stop_flag.is_set():
                break
            try:
                href = await link.get_attribute("href")
                if not href or "/org/" not in href:
                    continue
                if any(x in href for x in ["/reviews/", "/gallery/", "/photos/", "/menu/"]):
                    continue
                clean = href.split("?")[0].split("#")[0]
                if not clean.endswith("/"):
                    clean += "/"
                if clean.startswith("/maps/org/"):
                    clean = f"https://yandex.ru{clean}"
                if clean in seen:
                    continue
                seen.add(clean)
                business_urls.append(clean)
                if target > 0 and len(business_urls) >= target:
                    break
            except Exception:
                continue

        if len(business_urls) < target and len(business_urls) < 15:
            logger.info("Few links, trying placemarks...")
            try:
                placemarks = await page.locator(
                    "xpath=//*[contains(@data-id, '') or contains(@class, 'placemark') or contains(@class, 'marker')]"
                ).all()
                for elem in placemarks[:15]:
                    if stop_flag.is_set():
                        break
                    try:
                        original_url = page.url
                        await elem.click()
                        await asyncio.sleep(1.5)
                        current = page.url
                        if "/org/" in current and current != original_url:
                            clean = current.split("?")[0].split("#")[0]
                            if not clean.endswith("/"):
                                clean += "/"
                            if clean not in seen:
                                seen.add(clean)
                                business_urls.append(clean)
                        await page.go_back()
                        await asyncio.sleep(1)
                    except Exception:
                        continue
            except Exception:
                pass

        return business_urls

    def parse_business(self, url: str) -> dict[str, Any] | None:
        clean_url = url.split("/gallery/")[0].split("/reviews/")[0].split("/photos/")[0].split("/menu/")[0]
        if not clean_url.endswith("/"):
            clean_url += "/"

        async def _parse():
            page = self._page
            try:
                await page.goto(clean_url, wait_until="networkidle", timeout=20000)
            except Exception:
                try:
                    await page.goto(clean_url, wait_until="domcontentloaded", timeout=15000)
                except Exception:
                    return None

            try:
                await page.wait_for_selector("xpath=//h1", timeout=10000)
            except Exception:
                pass

            data: dict[str, Any] = {
                "url": clean_url,
                "extraction_date": datetime.now().isoformat(),
                "yandex_id": self._extract_yandex_id(clean_url),
            }

            data.update(await self._extract_basic_info(page))
            data.update(await self._extract_contact_info(page))
            data["products_and_services"] = await self._extract_products(page)

            if not data.get("name"):
                return None
            return data

        return _run_async(_parse())

    def close(self) -> None:
        if self._page:
            async def _close():
                try:
                    await self._page.close()
                except Exception:
                    pass
            try:
                _run_async(_close())
            except Exception:
                pass

    def _extract_yandex_id(self, url: str) -> str:
        match = re.search(r"/org/.+?/(\d+)/", url)
        return match.group(1) if match else ""

    async def _find_text_by_selectors(self, page, selectors: list[str]) -> str:
        for sel in selectors:
            try:
                if "/@" in sel:
                    xpath = sel.split("/@")[0]
                    attr = sel.split("/@")[1]
                    loc = page.locator(f"xpath={xpath}").first
                    if await loc.count() > 0:
                        val = await loc.get_attribute(attr)
                        if val:
                            return val.strip()
                else:
                    loc = page.locator(f"xpath={sel}").first
                    if await loc.count() > 0:
                        text = await loc.text_content()
                        if text and text.strip():
                            return text.strip()
            except Exception:
                continue
        return ""

    async def _find_element_by_selectors(self, page, selectors: list[str]):
        for sel in selectors:
            try:
                loc = page.locator(f"xpath={sel}").first
                if await loc.count() > 0:
                    return loc
            except Exception:
                continue
        return None

    async def _extract_basic_info(self, page) -> dict[str, Any]:
        data: dict[str, Any] = {}
        data["name"] = await self._find_text_by_selectors(page, [
            "//h1[@itemprop='name']",
            "//h1[contains(@class, 'orgpage-header-view__header')]",
            "//h1[contains(@class, 'card-title-view__title')]",
            "//h1",
        ])

        rating_loc = await self._find_element_by_selectors(page, [
            "//span[contains(@class, 'business-rating-badge-view__rating-text')]",
        ])
        data["rating"] = (await rating_loc.text_content()).strip() if rating_loc else ""

        data["address"] = await self._find_text_by_selectors(page, [
            "//div[contains(@class, 'orgpage-header-view__address')]",
            "//div[contains(@class, 'business-contacts-view__address')]",
            "//div[contains(@class, 'address')]",
            "//span[contains(@class, 'address')]",
            "//meta[@itemprop='address']/@content",
        ])
        if data["address"]:
            lines = data["address"].split("\n")
            clean = [
                l.strip()
                for l in lines
                if l.strip()
                and "Показать входы" not in l
                and "Маршрут" not in l
                and len(l.strip()) > 5
            ]
            data["address"] = " ".join(clean)

        categories: list[str] = []
        for sel in [
            "//a[contains(@class, 'business-categories-view__category')]",
            "//div[contains(@class, 'business-card-title-view__categories')]//a",
            "//div[contains(@class, 'categories')]//a",
        ]:
            try:
                elems = await page.locator(f"xpath={sel}").all()
                for elem in elems:
                    text = (await elem.text_content()).strip()
                    if text and text not in categories:
                        categories.append(text)
            except Exception:
                continue
        data["categories"] = categories
        return data

    async def _extract_contact_info(self, page) -> dict[str, Any]:
        phones: list[str] = []
        for sel in [
            "//span[@itemprop='telephone']",
            "//div[contains(@class, 'card-phones-view__number')]//span",
        ]:
            try:
                elems = await page.locator(f"xpath={sel}").all()
                for elem in elems:
                    phone = (await elem.text_content()).strip()
                    if phone and phone not in phones:
                        phones.append(phone)
            except Exception:
                continue

        website_loc = await self._find_element_by_selectors(page, [
            "//a[contains(@class, 'business-urls-view__link')][@itemprop='url']",
        ])
        website = (await website_loc.get_attribute("href")) if website_loc else ""

        return {"phones": phones, "website": website or ""}

    async def _extract_products(self, page) -> list[dict[str, str]]:
        products: list[dict[str, str]] = []
        max_products = int(self.params.get("target_products_count", 10))

        for sel in [
            "//div[@class='tabs-select-view__title _name_prices']",
            "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Цены')]",
            "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Товары')]",
            "//div[contains(@class, 'tabs-select-view__title') and contains(text(), 'Услуги')]",
            "//a[contains(@href, 'prices')]",
        ]:
            try:
                loc = page.locator(f"xpath={sel}").first
                if await loc.count() > 0:
                    await loc.click()
                    await asyncio.sleep(1)
                    break
            except Exception:
                continue

        last_height = 0
        try:
            last_height = await page.evaluate("document.body.scrollHeight")
        except Exception:
            pass
        for _ in range(5):
            try:
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            except Exception:
                break
            await asyncio.sleep(0.5)
            try:
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height <= last_height:
                    break
                last_height = new_height
            except Exception:
                break

        product_elems = []
        primary = [
            "//div[contains(@class, 'business-full-items-grouped-view__item')]",
            "//div[contains(@class, 'related-item-photo-view')]",
            "//div[contains(@class, 'related-item-list-view__item')]",
            "//div[contains(@class, 'related-product-view')]",
        ]
        for sel in primary:
            try:
                elems = await page.locator(f"xpath={sel}").all()
                if elems:
                    product_elems = elems
                    break
            except Exception:
                continue

        if not product_elems:
            additional = [
                "//div[contains(@class, 'product-item')]",
                "//div[contains(@class, 'service-item')]",
                "//div[contains(@class, 'price-item')]",
                "//li[contains(@class, 'item')]",
            ]
            for sel in additional:
                try:
                    elems = await page.locator(f"xpath={sel}").all()
                    if elems:
                        product_elems = elems
                        break
                except Exception:
                    continue

        if not product_elems:
            return products

        if max_products > 0:
            product_elems = product_elems[:max_products]

        for elem in product_elems:
            try:
                title = ""
                for t_sel in [
                    ".//div[contains(@class, 'related-item-list-view__title')]",
                    ".//div[contains(@class, 'related-item-photo-view__title')]",
                    ".//div[contains(@class, 'title')]",
                    ".//span[contains(@class, 'title')]",
                    ".//h3", ".//h4",
                ]:
                    try:
                        t_loc = elem.locator(f"xpath={t_sel}").first
                        if await t_loc.count() > 0:
                            title = (await t_loc.text_content()).strip()
                            if title:
                                break
                    except Exception:
                        continue

                price = ""
                for p_sel in [
                    ".//div[contains(@class, 'related-item-list-view__price')]",
                    ".//div[contains(@class, 'price')]",
                    ".//span[contains(@class, 'price')]",
                    ".//div[contains(text(), '₽')]",
                ]:
                    try:
                        p_loc = elem.locator(f"xpath={p_sel}").first
                        if await p_loc.count() > 0:
                            price = (await p_loc.text_content()).strip()
                            if price:
                                break
                    except Exception:
                        continue

                if title or price:
                    products.append({"title": title, "price": price, "description": ""})
            except Exception:
                continue

        return products
