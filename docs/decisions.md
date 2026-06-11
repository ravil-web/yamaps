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
