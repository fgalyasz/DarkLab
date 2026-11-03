---
title: DarkLab Catalog crash safety and schema migrations
status: final
created: 2026-11-03
updated: 2026-11-03
extends: prd-DarkLab-2026-10-10
parent_issue: 90
story_issue: 92
---

# PRD: Catalog crash safety and schema migrations

## 0. Document Purpose

This PRD records the implementation of baseline FR-R2 and FR-R5 for story 22.2. It adds no new FR id.

## 1. Vision

An app crash, a power cut, or an app update never leaves the Photographer with an unreadable archive index.

## 2. Features

#### FR-R2, as implemented here

Catalog writes commit atomically.

**Consequences (testable):**
- A write killed before its commit leaves the previous commit on the next open; the integrity check rolls the interrupted write back instead of calling the Catalog damaged.
- Catalog settings and index images are replaced as a whole file (write to a sibling file, flush, rename). A failed replace keeps the previous file and leaves no partial file.

#### FR-R5, as implemented here

Catalog `schema` is versioned and upgraded on open.

**Consequences (testable):**
- A Catalog with a lower schema is backed up first (backup folder beside the Catalog), then upgraded in one transaction, and its schema matches the app afterwards.
- If the backup fails, the Catalog is not upgraded. If a step fails, every change of the upgrade is rolled back and the old schema stays.
- A Catalog with a higher schema than the app is refused with a message to update DarkLab, and is not changed.
- Schema 1 to 2 adds the Develop Settings, mark, hash, and Folder storage that older Catalogs lack.

## 3. Non-Goals

- Write-ahead logging or multi-process writers.
- Atomic export presets and sidecars.

## 4. Open Questions

None.
