---
stage: complete
done: [0, 1, 2, 3, 4, 5, 6, 7]
core_frozen: true
legacy_immutable: true
params_file: docs/parser_params.md
api_contract: docs/api.md
open_bugs: []
---

# Progress

## Stage 0 - Preparation

- Git repository initialized and original state committed.
- Working branch: `rework`.
- Original parser and related artifacts moved into `legacy/`.
- `legacy/` is the immutable reference for all later stages.

## Stage 1 - Audit

- S1 code map covers all legacy Python modules and dependency entry points.
- S2 extracted an exhaustive draft and a frontend-consumable Yandex parameter
  schema with original defaults.
- S3 identified dead-code and unused-import candidates without modifying
  `legacy/`.
- Behavioral baseline and CORE / KEEP / DROP classification documented.

## Stage 2 - Architecture

- Selected FastAPI + managed background threads + SQLite + dependency-free SPA.
- Defined parser boundary, job lifecycle, persistence, failures, and test
  strategy.
- Defined API contract and bbox/polygon-to-Yandex-tile translation.

## Stage 3 - Parser Core

- Added `parser_core/` boundary with area models, tiling, URL generation,
  normalization, polygon filtering, deduplication, callbacks, and cooperative
  stopping.
- The adapter imports and invokes the immutable selected classes directly from
  `legacy/`; selectors, waits, scrolling, extraction, and anti-detection logic
  are not copied or rewritten.
- Added deterministic unit tests with a fake adapter.

## Stage 4 - Backend

- Added FastAPI endpoints for jobs, status, results, stop, parameter schema,
  export, public map configuration, and health.
- Added managed background job lifecycle with immediate result persistence and
  cooperative stopping.
- Added SQLite storage with per-operation connections, WAL, job state, and
  deduplicated results.
- Added CSV/XLSX/JSON exports, including partial results.
- Added deterministic API integration tests and fixed a stop-status race found
  by those tests.

## Stage 5 - Frontend And Map

- Added a responsive single-screen SPA served by FastAPI.
- Parameter controls are generated from `/api/params/schema`.
- Added Yandex Maps API 2.1 loading, missing-key setup placeholder, rectangle
  drag, polygon clicks/double-click completion, clear-area control, result
  markers and clustering.
- Connected job start/stop, polling progress/results, result table, map
  markers, and CSV/XLSX/JSON exports.
- Browser-verified desktop layout, generated parameter controls, missing-key
  guidance, and area-required validation.

## Stage 6 - End-To-End Debugging

- Added deterministic demo core for reproducible offline E2E runs.
- Passed three required scenarios: small bbox/narrow query, medium
  bbox/popular category with repeat run, and complex polygon with mid-run stop
  plus partial export.
- Verified result deduplication, marker coordinates, CSV/XLSX/JSON exports,
  empty results, and graceful parser/blocking failure.
- Fixed cross-tile global target limit and the earlier stop-status race.

## Stage 7 - Finalization

- Added one-command local startup, `.env.example`, runtime requirements,
  Dockerfile, Docker Compose, `.dockerignore`, pytest configuration, and
  Russian README.
- Completed parameter wiring for the selected Yandex baseline, including
  browser, delay, save, logging, error, limit, and selector timeout controls.
- Final validation covers product tests, JavaScript syntax, Python compilation,
  Docker Compose configuration, local `python run.py` startup, missing map key
  behavior, and browser UI smoke.

## Artifacts

- `legacy/`
- `docs/decisions.md`
- `docs/code_map.txt`
- `docs/parser_params.draft.json`
- `docs/parser_params.md`
- `params_schema.json`
- `docs/dead_code.txt`
- `docs/unused.txt`
- `docs/audit.md`
- `docs/architecture.md`
- `docs/api.md`
- `parser_core/`
- `tests/test_parser_core.py`
- `app/`
- `tests/test_api.py`
- `app/static/`
- `app/demo.py`
- `tests/test_e2e_scenarios.py`
- `README.md`
- `.env.example`
- `requirements.txt`
- `run.py`
- `Dockerfile`
- `docker-compose.yml`
- `pytest.ini`

## Validation

- `legacy/` has no working-tree changes.
- Audit JSON files parse successfully.
- UI schema: 30 parameters, 10 selector metadata records, 7 field metadata
  records; no Ozon/dashboard DROP parameters.
- Parser core unit tests pass without network or Selenium.
- Parser core, backend API, and E2E suite pass.
- Local browser smoke test passes without a Yandex Maps API key.
- `python run.py` health/root smoke test passes in demo mode.
- `docker compose config` passes.
- A bounded live Selenium smoke initialized WebDriver and reached Yandex Maps;
  the external Chrome session terminated during legacy scrolling and returned
  no results. Reproducible product/E2E validation therefore remains offline
  demo-based; live availability is a known external limitation.

## Final Summary

### Preserved

- Immutable selected legacy Selenium URL collection and business-card
  extraction behavior, including selectors, scrolling, waits, and
  anti-detection setup.
- Original Yandex parser defaults exposed through the UI schema.
- JSON/CSV persistence behavior, with XLSX export added from existing legacy
  patterns.

### Removed From New Runtime

- Terminal menus/input, Ozon, historical dashboard generators, kids-English
  application, debug variants, generated output, archives, and duplicate
  experimental parsers. These remain only in immutable `legacy/`.

### Known Limitations

- Live Yandex DOM/captcha behavior and live Yandex map rendering require
  external availability, Chrome/Chromium, and a user-supplied API key.
- Stop is cooperative and may wait for an active Selenium wait to finish.
- Background threads and SQLite target a local single-user deployment.
