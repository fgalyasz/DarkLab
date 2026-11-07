---
title: DarkLab Preview cache policy
status: final
created: 2026-11-07
updated: 2026-11-07
extends: prd-DarkLab-2026-10-10
parent_issue: 90
story_issue: 97
---

# PRD: Preview cache policy

## 0. Document Purpose

This PRD records FR-P3 as implemented for story 22.7.

## 1. Vision

A long-lived Catalog must not let disposable preview files grow without bound.

## 2. Features

#### FR-P3, as implemented here

Per-Catalog settings in `settings.json` cap grid index previews and optional 1:1 Develop cache files. File → Preview Cache Settings edits them on the open Catalog.

**Consequences (testable):**
- `preview.standard_long_edge` and `preview.standard_quality` default to 360 and 80. Import and Rebuild Previews build grid index JPEGs within those caps.
- `preview.full_long_edge` and `preview.full_quality` default to 2048 and 85. A new 1:1 cache file under `previews/full/` is built within those caps when written.
- `preview.discard_full_enabled` defaults to off. When on, `preview.discard_full_days` (default 7) removes `previews/full/*.jpg` older than that many days on catalog open. Grid files `previews/{id}.jpg` are never removed.
- Unknown settings keys round-trip. Launch policy stays in application config (FR-54).

## 3. Non-Goals

- Idle or on-quit Optimize (story 22.8).
- On-disk 1:1 cache while Develop still renders only in memory (writers exist for the next Develop cache story).

## 4. Open Questions

None.
