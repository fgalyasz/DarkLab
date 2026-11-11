---
title: DarkLab GitHub release assets for Linux and Windows
status: final
created: 2026-11-11
parent_issue: 71
story_issue: 101
---

# PRD: Three-platform GitHub release assets

## Purpose

Milestone 1 promises the same behaviour on Windows, macOS, and Linux. CI already builds Linux and Windows bundles. This slice publishes them on the same GitHub Release as the macOS DMG and lists all three on the product gateway page.

## FR-79: GitHub Release lists three installers

**Consequences (testable):**

- `src/release/downloads.py` names `DarkLab.dmg`, `DarkLab-linux-x86_64.tar.gz`, and `DarkLab-windows-x64.zip`.
- Release upload includes every bundle present under `dist/` when `deploy_site.sh` runs.
- Gateway HTML links to each uploaded asset.

## Non-Goals

- Code signing on Windows or Linux.
- Replacing tenprintsoftware.com catalogue copy in this slice.
