---
title: DarkLab auto-update channel
status: final
created: 2026-11-21
extends: prd-DarkLab-2026-10-10
parent_issue: 71
story_issue: 74
---

# PRD: Auto-update channel

## 0. Document Purpose

Photographers on a shipped installer must learn about newer GitHub Releases and install them without hunting the gateway. Story 18.3 requires an update offer that works offline for catalog work and keeps Community separate from any future Pro channel.

## 1. Vision

DarkLab checks the public Community release feed, offers a newer build, downloads the matching installer asset, and hands off install for that OS. Import, Library, Develop, and Export keep working when the network is down.

## 2. Features

### FR-U1 Read the running Community version

**Consequences (testable):**
- `src/release/versioning.py` reads `docs/version.txt` from the project root in development and from the frozen bundle resource when packaged.
- Invalid or missing text raises `ValueError` with a clear message; the UI treats that as “cannot check”.

### FR-U2 Detect a newer Community release

**Consequences (testable):**
- `src/release/update_check.py` fetches `https://api.github.com/repos/fgalyasz/DarkLab/releases/latest` with a DarkLab User-Agent.
- Semver compare (`is_newer`) treats `1.0.11` newer than `1.0.10`; equal and older return false.
- A skipped version in config (`updates.skipped_version`) suppresses the offer for that version only.
- Network failure raises `UpdateCheckError`; quiet startup checks log and stay silent; Help → Check for Updates shows the error.

### FR-U3 Offer install or dismiss

**Consequences (testable):**
- Startup check runs once after the main window is ready on packaged builds when `updates.check_on_startup` is true (default true). Source runs skip the quiet startup check.
- Help menu includes Check for Updates… and About DarkLab (shows the running version).
- Dialog actions: Update, Later, Skip this version. Skip writes `updates.skipped_version`.

### FR-U4 Download and hand off the platform asset

**Consequences (testable):**
- Asset names match `src/release/downloads.py` (`DarkLab.dmg`, `DarkLab-linux-x86_64.tar.gz`, `DarkLab-windows-x64.zip`).
- Download writes under a temp directory with progress; cancel stops the transfer.
- macOS mounts the DMG after quit, copies `DarkLab.app` into `/Applications/DarkLab.app` with `ditto`, unmounts, and opens the new app. Windows and Linux extract beside the frozen install root and schedule a replace script that restarts DarkLab after this process exits.
- Non-frozen (dev) Update opens the asset URL in the system browser instead of replacing files.

### FR-U5 Community channel only

**Consequences (testable):**
- Update metadata comes only from the public GitHub Releases latest tag for this repo (Community).
- No Pro feed, license gate, or entitlement cross-check in this slice.

## 3. Non-Goals

- Sparkle / WinSparkle frameworks (equal: first-party GitHub Releases updater).
- Pro-branded builds or Epic 16 entitlement wiring.
- Silent background install without a user click on Update.
- Notarization or Windows/Linux code signing.

## 4. Open Questions

None. Story 18.3 acceptance criteria and Epic 18 outcome bind this slice.
