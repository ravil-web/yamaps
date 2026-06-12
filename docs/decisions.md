# Decisions

## 2026-06-12

- `INSTRUCTIONS.MD` is treated as the primary project specification because
  `agent_instruction.md` is absent and `INSTRUCTIONS.MD` contains the complete
  Definition of Done and stages 0-7.
- The repository had no Git metadata and no `legacy/` directory. The complete
  original working tree was committed first, then parser-related files and
  artifacts were moved into `legacy/` on branch `rework`.
- `INSTRUCTIONS.MD`, `SKILLS.MD`, and the root `.gitignore` remain outside
  `legacy/` because they govern the rework rather than form runtime parser
  behavior.
- Repository-local Git identity is `Codex <codex@local>` because no user Git
  identity was configured.
- `legacy/main.py` and its `src.config` / `MainParser` /
  `SingleBusinessParser` dependency chain define the behavioral baseline.
  Numerous standalone parser variants are experiments or duplicates and are
  classified as DROP rather than merged into a new parser implementation.
- The selected area will wrap frozen CORE through Yandex search URL tiles.
  Polygon membership is enforced after extraction, with deduplication by
  Yandex ID and then coordinates.
- Ozon and dashboard-generation parameters remain documented in the exhaustive
  audit draft but are excluded from the new UI because their subsystems are
  classified as DROP.
- FastAPI managed background threads are used instead of Celery. They are
  sufficient for a local single-user Selenium application, support cooperative
  stopping, and avoid an external broker.
- SQLite uses one short-lived connection per operation. Results are persisted
  on every item callback so progress markers and partial exports survive a
  stopped or failed task.
- The frontend is dependency-free HTML/CSS/JavaScript and uses Yandex Maps API
  2.1 because its drawing controls and clustering API directly satisfy the
  rectangle, polygon, and marker requirements without a frontend build step.
- Product `pytest` discovery is intentionally limited to `tests/`. Historical
  tests inside immutable `legacy/` target removed experiments, contain broken
  imports/encodings, and are classified as DROP rather than product gates.
## 2026-06-12: Selenium runs headless by default

The web application keeps the immutable legacy Selenium parser as its parsing engine, but wraps both legacy Chrome option factories with `--headless=new`. This prevents separate browser windows from opening while parsing is controlled and observed through the application UI. Set `PARSER_HEADLESS=0` only for local parser debugging.
