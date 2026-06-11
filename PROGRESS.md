---
stage: 2
done: [0, 1]
core_frozen: false
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

## Validation

- `legacy/` has no working-tree changes.
- Audit JSON files parse successfully.
- UI schema: 30 parameters, 10 selector metadata records, 7 field metadata
  records; no Ozon/dashboard DROP parameters.
