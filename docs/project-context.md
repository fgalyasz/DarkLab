# DarkLab project context

DarkLab is a local-first desktop photo application. The product promise is Lightroom Classic workflow parity: the same photographer jobs, in the same seven modules, without a subscription.

## Language

- Chat with Ferenc: Hungarian.
- Code, PRDs, architecture, GitHub issues, and commits: English.

## Product decisions already made

- Workflow parity with Lightroom Classic. Not Adobe catalog compatibility, and not pixel-identical Adobe rendering.
- Desktop only. macOS, Windows, and Linux from one codebase.
- No account and no network requirement for import, library, develop, or export.
- The seven modules are Library, Develop, Map, Book, Slideshow, Print, and Web. Import is a dialog.
- MVP is one shoot: import, cull, basic develop, export, with originals left unchanged.
- Stack stays Python and PyQt6. Domain logic does not live in widgets.
- Catalog is one SQLite file. Develop settings round-trip through XMP sidecars.
- Basic parity does not include tethered capture, an Adobe plugin ABI, Lightroom cloud sync, or Blurb ordering.

## Engineering constraints

- PEP 8, type hints, no docstrings, no long comments.
- Functions stay at or under ten lines. One task per function.
- No nested classes, nested functions, or nested try/except.
- New domain modules target at least 95% line coverage, with positive and negative tests.
- Do not rewrite working UI code only to satisfy style. Apply the constraints to code you touch and to all new domain code.

## Where the plan lives

- Process: `docs/pdlc.md`
- Brief: `_bmad-output/planning-artifacts/briefs/brief-DarkLab-2026-10-10/brief.md`
- PRD: `_bmad-output/planning-artifacts/prds/prd-DarkLab-2026-10-10/prd.md`
- Architecture: `_bmad-output/planning-artifacts/architecture.md`
- Epics: `_bmad-output/planning-artifacts/epics.md`
- Board: https://github.com/users/fgalyasz/projects/11 (`docs/pdlc/project.json`)

## Current code on main

Committed code has an import dialog (destination, rename, IPTC presets), a library grid, RAW and EXIF reads, and placeholder panels for Develop, Print, Slideshow, and Web. Map, Book, and the module bar exist in the local working tree and are not the baseline on `main`.
