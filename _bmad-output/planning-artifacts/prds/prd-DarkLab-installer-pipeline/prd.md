---
title: DarkLab installer pipeline (Linux and Windows)
status: final
created: 2026-11-09
updated: 2026-11-09
extends: prd-DarkLab-2026-10-10
parent_issue: 71
story_issue: 72
---

# PRD: Installer pipeline for three OSes

## 0. Document Purpose

This PRD extends Epic 18 story 18.1. The macOS DMG pipeline already ships on `main`. This slice adds Linux and Windows PyInstaller bundles in CI and makes log paths work on every desktop OS.

## 1. Vision

A Photographer on Linux or Windows can download a frozen DarkLab build from the same release workflow that already produces `DarkLab.dmg`, launch it, and reach Select Catalog without write failures or missing native libraries for `pyexiv2`.

## 2. Features

### 2.1 Cross-platform log directory

#### FR-77: Frozen builds write logs to a user-writable folder

**Consequences (testable):**
- `src/startup.log_directory()` uses `~/Library/Logs/DarkLab` on macOS, `%LOCALAPPDATA%/DarkLab/logs` on Windows, and `$XDG_STATE_HOME/DarkLab/logs` (default `~/.local/state/DarkLab/logs`) on Linux.
- `log_file()` still appends file names under that folder.

### 2.2 Linux and Windows CI artifacts

#### FR-78: Release workflow builds three platforms

**Consequences (testable):**
- `scripts/build_linux.sh` runs PyInstaller with `--collect-binaries pyexiv2` and packs `dist/DarkLab` into `dist/DarkLab-linux-x86_64.tar.gz` without bumping `docs/version.txt`.
- `scripts/build_windows.ps1` produces `dist/DarkLab-windows-x64.zip` with the same PyInstaller flags.
- `.github/workflows/installer.yml` runs Linux and Windows jobs on `main` and uploads those archives as workflow artifacts (macOS keeps signing, release upload, and deploy on the existing job).
- Build scripts stay free of secrets.

## 3. Non-Goals

- Replacing the macOS-only `deploy_site.sh` download page in this slice.
- Apple notarization or Windows code signing.

## 4. Open Questions

None.
