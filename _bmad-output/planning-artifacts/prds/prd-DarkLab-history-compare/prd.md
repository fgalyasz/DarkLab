---
title: DarkLab History Steps and before/after
status: final
created: 2026-10-30
updated: 2026-10-30
extends: prd-DarkLab-2026-10-10
parent_issue: 12
story_issue: 15
---

# PRD: History Steps and before/after

## 0. Document Purpose

This PRD adds FR-70 and FR-71. It realizes the first-milestone part of FR-32: walk History Steps and compare before and after. Snapshots and copy/paste stay in Epic 6.

## 1. Vision

A bad correction is one click from undone, and the Photographer can see what the edit did without touching it.

## 2. Features

#### FR-70: History Steps

The Develop panel lists History Steps for the shown Photo. The first Step is Import. Each settled change to a tone slider or a crop control adds a Step named for what changed.

**Consequences (testable):**
- Selecting an older Step sets the tone and crop controls to that Step's Develop Settings and stores them in the Catalog.
- Selecting a Step does not add a Step.
- A change made after selecting an older Step replaces the later Steps.
- A drag that settles as one change is one Step.
- A change that is still pending when a Step is selected is recorded first.
- A Photo that already has stored settings when it is first shown starts with Import and a "Saved settings" Step.
- The Original and its content hash are unchanged.

#### FR-71: Before/after

A Before/After toggle shows the Preview with the Import settings, then the current settings again.

**Consequences (testable):**
- Toggling writes no History Step and no Develop Settings, and moves no control.
- Changing a control while the toggle is on turns it off and shows the current settings.
- Import settings are the defaults: zero tone and an empty crop.

## 3. Non-Goals

- History that survives quitting DarkLab. Steps live for the session. The stored settings do survive (FR-60, FR-64), and the next session starts a new History from them.
- Snapshots, copy/paste, and named Steps (Epic 6).
- Side-by-side or split compare.

## 4. Open Questions

Whether History should be stored in the Catalog (a table keyed by Photo) for a later story.
