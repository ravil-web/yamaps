---
stage: 5
done: [0, 1, 2, 3, 4]
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

## Validation

- `legacy/` has no working-tree changes.
- Audit JSON files parse successfully.
- UI schema: 30 parameters, 10 selector metadata records, 7 field metadata
  records; no Ozon/dashboard DROP parameters.
- Parser core unit tests pass without network or Selenium.
- Parser core and backend API suite: 8 tests pass.
