# Agent instructions

Follow [docs/pdlc.md](docs/pdlc.md) for every new product feature and user-visible bugfix. That includes a PRD when the change has product consequences, GitHub issues, and the DarkLab project board.

Speak Hungarian in chat. Use English in code, PRDs, GitHub issues, and commits.

The product baseline is `_bmad-output/planning-artifacts/prds/prd-DarkLab-2026-10-10/prd.md`. Do not widen it into Adobe catalog compatibility or pixel-identical Lightroom rendering.

Load the local BMad skills when the PDLC calls for them (`bmad-prd`, `bmad-create-architecture`, `bmad-create-epics-and-stories`). Their outputs are committed under `_bmad-output/`. The skill files themselves stay out of the public repo.

## Model & Execution Optimization Policy

- **PRDs, Architecture, and Documentation:** Always create PRDs, architecture documents, epics/stories, and technical documentation with the best available planning model that plans most thoroughly and comprehensively.
- **Development Optimized for Cost-Effective Models:** Optimize implementation and unit testing for cost-effective models (such as `Composer 2.5 Fast`). Every PRD and Story must specify exact target files (`src/catalog`, `src/importing`, `src/develop`, `src/exporting`, `src/imaging`, `src/ui`), function/class contracts (respecting the ≤10-line function limit and no-Qt domain boundary), settings/SQLite keys, and deterministic unit test targets (`tests/test_*.py` at ≥95% line coverage) so cost-effective models can implement each story in one pass.
