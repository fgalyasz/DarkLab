---
title: DarkLab catalog package
status: final
created: 2026-10-10
updated: 2026-10-10
extends: prd-DarkLab-2026-10-10
parent_issue: 50
---

# PRD: Catalog package

## 0. Document Purpose

This PRD extends the baseline DarkLab PRD. It specifies what one Catalog folder holds. FR-51 through FR-54 continue the baseline ids. Glossary terms from the baseline apply. The new term is defined here.

## 1. Vision

A Photographer should be able to copy one Catalog and take the shoot's DarkLab state with it: which folders were imported, the index images, and the settings that belong to that Catalog. Originals stay where they are. Choosing which Catalog opens at launch stays outside the folder, because that choice is needed before any Catalog is open.

## 2. Target User

### 2.1 Jobs To Be Done

- Copy one Catalog folder to another disk and keep its folders, index images, and settings.
- See the imported photo folders recorded in that Catalog, the way Classic records them.
- Rebuild index images later without losing the Catalog.

### 2.2 Key User Journeys

- **UJ-9. Anna copies the wedding Catalog.**
  - **Persona + context:** Anna finished culling on one disk and wants the same Catalog on another.
  - **Entry state:** The wedding Catalog is a folder she created in DarkLab.
  - **Path:** She copies that folder. She does not copy the camera card again.
  - **Climax:** The copy lists the same imported folders and the same Catalog settings. Index images are either in the copy or can be rebuilt.
  - **Resolution:** The Originals are still the files on disk, not a second set inside the Catalog.
  - **Edge case:** Deleting the index images leaves the Catalog, its folders, and its settings usable.

## 3. Glossary

- **Catalog package** — The folder the Photographer copies. It contains the Catalog database, the preview cache, and that Catalog's settings.

## 4. Features

### 4.1 Catalog package

**Description:** Creating a Catalog creates one folder. That folder is the home for imported folder records, index images, Catalog settings, and later Catalog rows. Realizes UJ-9.

**Functional Requirements:**

#### FR-51: One folder

The Photographer gets one Catalog folder. Copying that folder copies the database, the preview cache, and that Catalog's settings.

**Consequences (testable):**
- Creating a Catalog produces a folder whose name ends in `.darklab`.
- The folder contains the SQLite database, a preview directory, and a settings file.
- Creating the same Catalog again does not remove Photos, folders, index images, or settings.
- A Catalog saved earlier as a single database file still opens.
- Later Catalog data (Develop Settings, Collections, Keywords, History Steps) is stored in that same database. This change does not implement those rows.

#### FR-52: Imported folders

The Catalog records each imported photo folder by its path. Recording a folder does not copy or modify the files in it.

**Consequences (testable):**
- Recording a folder path lists that path on the Catalog.
- Recording the same path again does not add a second row.
- An empty path is refused.
- Two Catalogs do not share folder rows.

#### FR-53: Index images

Index images are files in the Catalog's preview cache. The cache can be deleted and rebuilt.

**Consequences (testable):**
- Storing bytes for a Photo writes a file under the preview directory and reads those bytes back.
- A Photo with no index image reads as missing.
- A non-positive Photo id is refused.
- Removing the preview directory leaves the database, the folder list, and the settings usable.

#### FR-54: Catalog settings

Settings that belong to one Catalog are stored in that Catalog folder. Launch policy is not one of those settings.

**Consequences (testable):**
- A saved key is read back from that Catalog only.
- An unknown key reads as missing.
- An empty key is refused.
- Settings that are not valid JSON are refused.
- Startup Mode, the most recent Catalog, and the pinned Catalog stay in the application config, outside the Catalog folder.

## 5. Non-Goals

- Copying Originals into the Catalog folder.
- Reading or writing a Lightroom catalog.
- Generating index images from pixels in this change. The cache has a place to store them.
- Moving Startup Mode into the Catalog.

## 6. MVP Scope

FR-51, FR-52, FR-53, and FR-54 are in scope for this change.

## 7. Success Metrics

- **SM-5:** A new Catalog folder round-trips one imported folder, one index image, and one setting, and a second Catalog does not see them. Validates FR-51, FR-52, FR-53, FR-54.

**Counter-metrics**

- **SM-C4:** Do not copy Originals into the Catalog folder. Validates the FR-52 boundary.

## 8. Open Questions

None for this change.

## 9. Assumptions Index

- Imported folders are path records, as in Classic, not copies of the files. [ASSUMPTION: "contains the imported folders" means the Catalog remembers those folders.]
- Launch policy stays outside the Catalog. [ASSUMPTION: a setting that chooses the Catalog cannot live only inside a Catalog that is not open yet.]
- A Catalog created as a single database file before this change still opens. [ASSUMPTION: do not strand a Catalog made while trying the previous build.]
