# DarkLab product PDLC

Every new product feature and every user-visible bugfix follows this path. The agent does not wait to be asked for a PRD, an epic, or a project item. Chat stays Hungarian. Artifacts, code, GitHub, and commit messages stay English.

This repo uses the BMad method as the AI-PDLC. Skills run locally in Cursor. Their outputs are committed here so a reader can follow the product without the skill pack.

## Track

| Track | When | Skip |
| ----- | ---- | ---- |
| Feature | New capability or user-visible change | Nothing below |
| Fix | Bug with a product consequence | Coaching-path PRD. Still write a thin PRD or an investigation plus functional requirements |
| Chore | Typo, refactor with no behavior change, process-only | PRD, GitHub epic, project items |

## Pipeline

1. **Classify.** Feature, fix, or chore. A chore stops after the change.
2. **Plan on the fast path** unless Ferenc asks for the coaching path. Record decisions in the run folder's `.decision-log.md`.
3. **PRD.** `_bmad-output/planning-artifacts/prds/prd-DarkLab-<slug>/` with `prd.md`, `.decision-log.md`, and `addendum.md` when technical detail does not belong in the PRD. Stable `FR-` ids. The baseline PRD is `prd-DarkLab-2026-10-10`.
4. **Architecture when the change needs a new boundary.** Update `_bmad-output/planning-artifacts/architecture.md` instead of inventing a second stack in a story.
5. **Epic, stories, and the GitHub project.** `gh issue create` an `[EPIC]`, then `[STORY]` sub-issues with `--parent`. Link the PRD from the epic. Add every epic and story to the DarkLab project and set Status to `Todo`. Start of implementation sets `In Progress`. Close sets `Done`. Helper: `./scripts/pdlc-project-item.sh <issue> "Todo"`.
6. **Build.** English names. New domain logic goes in `src/catalog`, `src/importing`, `src/develop`, `src/exporting`, or `src/imaging`. Widgets call services. Services do not import Qt.
7. **Unit tests.** New domain logic at or above 95% line coverage. Positive and negative cases. No timing-sensitive asserts. `python -m unittest discover -s tests` must pass.
8. **Review.** Diff against the story's acceptance criteria and the functional requirements it cites. Fix blockers before commit.
9. **Changelog.** User-visible changes get an entry in `CHANGELOG.md`.
10. **Commit and push.** One commit for the change after tests pass. Push `origin HEAD`. Close the stories and the epic when the epic's stories are done. Set those project items to `Done`.

## Do not

- Skip the PRD because the change looks obvious.
- Claim Adobe catalog compatibility or pixel-identical Lightroom rendering.
- Commit secrets, catalogs, or photo libraries.
- Force-push `main`.
- Put domain rules in a widget because the screen is the only caller.
- Rewrite unrelated UI to satisfy style rules.

## References

- Project context: `docs/project-context.md`
- Issue templates: `.github/ISSUE_TEMPLATE/`
- Baseline PRD, architecture, and epics: `_bmad-output/planning-artifacts/`
- Board map, written by the seed script: `docs/pdlc/project.json`

If `gh project` returns Forbidden, refresh token scopes: `gh auth refresh -s project`.
