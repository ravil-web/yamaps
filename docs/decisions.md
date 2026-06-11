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
