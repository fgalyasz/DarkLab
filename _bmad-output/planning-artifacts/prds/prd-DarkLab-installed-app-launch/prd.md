---
title: DarkLab installed macOS app launch
status: final
created: 2026-11-08
updated: 2026-11-08
extends: prd-DarkLab-2026-10-10
parent_issue: 71
story_issue: 100
---

# PRD: Installed macOS app launches cleanly

## 0. Document Purpose

This PRD adds FR-76 to fix the macOS packaged `.app` launch failure under Epic 18 (story 18.4).

## 1. Vision

A Photographer who installs `DarkLab.dmg` into `/Applications` and opens `DarkLab.app` from Finder reaches Select Catalog or the workspace without native-library or read-only filesystem crashes.

## 2. Features

### 2.1 Self-contained macOS bundle and user-writable logs

#### FR-76: Installed `.app` launches from Finder

**Consequences (testable):**
- `scripts/build_dmg.sh` collects `pyexiv2` native binaries (`libexiv2.dylib` and its dependent dynamic libraries) into `DarkLab.app` so `import pyexiv2` succeeds inside the frozen bundle.
- Startup and panel file loggers write to a user-writable log directory (`~/Library/Logs/DarkLab/`) instead of the process working directory (`/`) or inside the signed `.app` bundle.
- Launching `DarkLab.app` when the working directory is read-only (`/`) does not fail with `Read-only file system` or `PyInstallerImportError`.

## 3. Non-Goals

- Windows and Linux installer pipelines (remained in story 18.1).
- Apple Developer ID notarization.

## 4. Open Questions

None.
