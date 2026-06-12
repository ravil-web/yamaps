# Definition of Done Audit

Date: 2026-06-12

| Requirement | Evidence | Status |
|---|---|---|
| One-command startup | `python run.py` health/root smoke; `run.py`; Docker Compose config | PASS |
| Embedded Yandex map | `app/static/app.js` loads Yandex Maps JS API 2.1; browser smoke verifies missing-key placeholder | PASS |
| Search query input | SPA `#query`; job create API | PASS |
| Rectangle and polygon area | SPA rectangle drag and polygon click/double-click; area validation/unit tests | PASS |
| Original parser parameters in UI | `params_schema.json` has 30 selected-baseline parameters; generated form; adapter wiring test | PASS |
| Real-time progress | item/progress callbacks, SQLite updates, one-second SPA polling; API tests | PASS |
| Result markers and clustering | Yandex Placemark + Clusterer integration; normalized coordinates; E2E coordinate checks | PASS |
| CSV/XLSX/JSON export | export endpoints and E2E content checks for all three formats | PASS |
| Reuse original parser logic | `LegacyAdapter` invokes immutable `legacy/src/parsers/yandex_parser.py` and `single_parser.py`; no legacy changes | PASS |
| Remove excess runtime functionality | New runtime excludes terminal menu, Ozon, old dashboards, kids-English, debug/duplicate parsers | PASS |
| README and env example | `README.md`, `.env.example` | PASS |
| Tests and three E2E scenarios | `python -m pytest -q`: 13 passed; `tests/test_e2e_scenarios.py` | PASS |

## Additional Validation

- `python -m compileall -q app parser_core run.py`: pass
- `node --check app/static/app.js`: pass
- `docker compose config`: pass
- Browser smoke without API key: pass
- `legacy/` working-tree changes: none

## External Runtime Note

A bounded live Selenium smoke initialized ChromeDriver and reached Yandex Maps,
then the external Chrome session terminated during the immutable legacy scroll
routine and produced no results. The application handled this without a crash.
Live Yandex DOM, captcha, browser-driver stability, and map rendering with a
user API key remain external-environment limitations. Reproducible E2E evidence
uses the deterministic demo core while exercising the complete API, SQLite,
stop, result, and export path.
