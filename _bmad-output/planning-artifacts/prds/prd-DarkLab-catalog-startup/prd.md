---
title: DarkLab catalog startup
status: final
created: 2026-10-10
updated: 2026-10-10
extends: prd-DarkLab-2026-10-10
parent_issue: 45
---

# PRD: Catalog startup

## 0. Document Purpose

This PRD extends the baseline DarkLab PRD. It specifies how a launch chooses a Catalog. FR-48 and FR-49 continue the baseline ids. Glossary terms from the baseline apply. The new term is defined here.

## 1. Vision

A Photographer who keeps more than one Catalog should decide what the next launch does. Some want the Open Catalog window every time. Some want yesterday's Catalog. Some want one Catalog pinned, even after they open another during the day.

## 2. Target User

### 2.1 Jobs To Be Done

- Start on a chosen Catalog without hunting for the file.
- Keep a pinned Catalog stable while still opening a different Catalog for one session.
- Change that choice later.

### 2.2 Key User Journeys

- **UJ-7. Anna pins the wedding Catalog.**
  - **Persona + context:** Anna keeps a wedding Catalog and a separate personal Catalog.
  - **Entry state:** The wedding Catalog is open.
  - **Path:** She opens Catalog Settings, chooses "Always open this catalog," and selects the wedding file. Later she opens the personal Catalog to grab one Photo, then quits.
  - **Climax:** The next launch opens the wedding Catalog, not the personal one.
  - **Resolution:** The personal Catalog is still the most recent Catalog, so switching the setting to "most recent" would open that one instead.
  - **Edge case:** If the pinned file has been moved, launch shows the Open Catalog window instead of an empty library with no explanation.

- **UJ-8. Anna wants to be asked.**
  - Anna sets startup to always ask. The next launch shows the Open Catalog window before a Catalog is current. Cancel leaves the window open with no Catalog.

## 3. Glossary

- **Startup Mode** — How launch chooses a Catalog. One of ask, recent, or fixed. Ask shows the Open Catalog window. Recent opens the last Catalog the Photographer opened. Fixed opens the pinned Catalog file.

## 4. Features

### 4.1 Startup Mode

**Description:** Catalog Settings stores one Startup Mode. Launch follows it. Opening a Catalog during a session updates the most recent Catalog and does not change a pin. Realizes UJ-7 and UJ-8.

**Functional Requirements:**

#### FR-48: Choose a Startup Mode

The Photographer can set Startup Mode to ask, recent, or fixed. The choice is still there after a restart.

**Consequences (testable):**
- The default Startup Mode, when none is stored, is recent.
- An unknown stored value is treated as recent.
- Ask shows the Open Catalog window even when a recent Catalog file exists.
- Canceling that window leaves no Catalog current.
- Recent opens the last opened Catalog when that file exists.
- Recent does not show the Open Catalog window when no last Catalog is stored or the file is missing.

#### FR-49: Pin a Catalog

In fixed Startup Mode the Photographer chooses one Catalog file. Launch opens that file until the setting is changed.

**Consequences (testable):**
- Saving fixed without an existing file is refused, and the previous setting stays.
- Opening a different Catalog does not change the pinned file.
- Launch opens the pinned file when it exists.
- Launch shows the Open Catalog window when the pinned file is missing.
- Switching Startup Mode away from fixed keeps the pinned path stored, so returning to fixed uses the same file.

## 5. Non-Goals

- A list of many recent Catalogs.
- Opening more than one Catalog at the same time.
- Changing Startup Mode from the command line.

## 6. MVP Scope

FR-48 and FR-49 are in scope for this change. They do not wait for the rest of the baseline milestone.

## 7. Success Metrics

- **SM-4:** A restart after each Startup Mode follows the consequences in FR-48 and FR-49 on a fixture with two Catalog files. Validates FR-48, FR-49.

**Counter-metrics**

- **SM-C3:** Do not open a file dialog on launch for recent mode when the Photographer has not asked to be prompted. Counterbalances the temptation to make ask the default.

## 8. Open Questions

None for this change.

## 9. Assumptions Index

- Default Startup Mode is recent. [ASSUMPTION: existing installs keep opening the last Catalog.]
- The pinned value is one file path. [ASSUMPTION: "fix the setting" means pin that Catalog, and the Photographer can still change the setting later.]
