---
title: DarkLab DMG Applications drop window
status: final
created: 2026-11-21
updated: 2026-11-21
extends: prd-DarkLab-2026-10-10
parent_issue: https://github.com/fgalyasz/DarkLab/issues/157
---

# PRD: DMG Applications drop window

## 0. Document Purpose

Studio macOS installers must match: open the DMG, drag the app onto Applications. DarkLab's DMG only contained `DarkLab.app`, so photographers had no Applications drop target.

## 1. Vision

A Photographer who opens `DarkLab.dmg` sees a TenPrint-branded drop window: `DarkLab.app`, an Applications shortcut, and a dark maze background with a drag arrow — the same installer pattern as the other studio macOS apps.

## 2. Features

### 2.1 Branded drag-to-Applications DMG layout

#### FR-77: DMG includes Applications drop target and TenPrint background

**Consequences (testable):**
- `scripts/build_dmg.sh` stages `DarkLab.app` beside a symlink to `/Applications` before creating the image.
- The read-write DMG layout positions `DarkLab.app` and `Applications` in icon view (app left, Applications right) via Finder AppleScript before converting to UDZO.
- `dmg_background.png` (740×440, TenPrint dark maze + product accent) is copied into `.background/background.png` and set as the Finder window background.
- Unit tests assert the script contains the Applications symlink, Applications icon position, and `dmg_background.png` reference.

## 3. Non-Goals

- Custom volume icon / `.VolumeIcon.icns`.
- Changing auto-update install destination (`/Applications/DarkLab.app`).
- Apple Developer ID notarization.

## 4. Open Questions

None.
