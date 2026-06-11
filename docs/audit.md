# Legacy Audit

## Scope

The immutable reference is `legacy/`. The selected behavioral baseline is the
entry point `legacy/main.py`, which composes:

- `legacy/src/config.py` (Yandex section)
- `legacy/src/parsers/yandex_parser.py` (`MainParser`)
- `legacy/src/parsers/single_parser.py` (`SingleBusinessParser`)

Static reports are candidates rather than proof. Dynamic entry points and
Selenium selectors were reviewed before assigning categories.

## CORE

Preserve and refactor without changing selectors, waits, delays, retry/error
behavior, scrolling, or anti-detection behavior:

- `legacy/src/parsers/yandex_parser.py`
  - Selenium driver setup and `navigator.webdriver` masking
  - search result loading, scrolling, URL collection and deduplication
  - target-count limiting and per-business orchestration
- `legacy/src/parsers/single_parser.py`
  - business-card navigation and extraction
  - selector fallback chains and explicit waits
  - products/services extraction
  - Yandex ID extraction and interrupt-safe behavior
- Yandex configuration in `legacy/src/config.py`
  - limits, delays, browser options, logging, saving, and error behavior

The new area search must generate Yandex search URLs using selected bbox/tile
center and span values, then invoke the preserved URL-collection logic per
tile. Polygon results are filtered by coordinates after extraction and
deduplicated by Yandex ID, then coordinates.

## KEEP

Preserve behavior and reuse where practical:

- JSON and CSV serialization from
  `legacy/src/parsers/single_parser.py`
- summary/result persistence patterns from
  `legacy/src/parsers/yandex_parser.py`
- XLSX output behavior demonstrated by `legacy/targeted_parser.py` and existing
  output artifacts; implement as a focused export adapter because the active
  baseline does not expose XLSX
- existing result field contract and saved output fixtures for tests

## DROP

Do not carry into the new runtime:

- terminal input, banners, menus, interactive captcha prompts, and debug prints
- Ozon parser/config/dashboard functionality
- `legacy/kids-english-app/`
- static/client/modern dashboard generators; the new SPA replaces them
- `_trash/`, archived zip files, generated dashboards, historical output, and
  parsing result artifacts
- duplicate standalone parser experiments such as `universal_parser.py`,
  `targeted_parser.py`, `scrolling_parser.py`, `ultimate_parser.py`, and
  `working_parser.py`
- debug, quick-test, and legacy integration scripts that do not test the
  selected active stack
- unused imports and statically unreachable helpers listed in
  `docs/dead_code.txt` and `docs/unused.txt`, after confirming they are outside
  the selected baseline

## Extracted Company Contract

The active parser extracts identity/basic information, address, rating,
reviews, categories, contact details, opening hours, website/social links,
products/services, source URL, and Yandex ID. Coordinates are required by the
web application and are available from Yandex URLs/cards; the adapter will
normalize them into `latitude` and `longitude` while retaining original fields.

## External Dependencies

- Selenium: browser automation and extraction
- pandas/openpyxl: XLSX export adapter
- standard-library JSON/CSV/logging/signal modules: persistence and runtime
  behavior
- webdriver-manager appears in an alternative parser, but the selected active
  baseline uses the installed Chrome driver directly

## Risks

- Yandex DOM selectors and anti-automation behavior are externally unstable.
- The selected baseline has no native polygon traversal; tiling and
  post-extraction polygon filtering are new orchestration around frozen CORE.
- Existing coordinates are inconsistent across parser variants, so coordinate
  normalization needs fixture and end-to-end coverage.
- Static dead-code reports may include dynamically reached entry points; no
  deletion is performed inside immutable `legacy/`.

