---
title: DarkLab Catalog Folders
status: final
created: 2026-10-31
updated: 2026-10-31
extends: prd-DarkLab-2026-10-10
parent_issue: 7
story_issue: 9
---

# PRD: Catalog Folders

## 0. Document Purpose

This PRD adds FR-73 and FR-74. It realizes FR-11 for the first milestone: Library lists the directories of the Originals in the Catalog and shows one Folder's Photos.

## 1. Vision

The card the Photographer imported is a set she can open and cull, and a directory that moved outside DarkLab is flagged until she points DarkLab at it again.

## 2. Features

#### FR-73: Folders list and selection

The Folders section of Library lists each directory that holds the Original of at least one Photo in the Catalog, with its Photo count. Selecting a Folder shows only its Photos in the grid. Choosing All Photographs shows every Photo again.

**Consequences (testable):**
- A Folder is derived from the stored Original paths and is not a copy of the files. Selecting it copies, moves, or writes no file.
- The grid count equals the Photo count shown for the Folder.
- The Folders list refreshes whenever Library reloads, so a new Import adds its Folder.
- A selected Folder that no longer has Photos is dropped and Library shows all Photos.
- Filters and sorting apply inside the selected Folder.

#### FR-74: Missing Folder and relink

A Folder whose directory no longer exists is marked MISSING. Relink Folder points it at a replacement directory.

**Consequences (testable):**
- A directory renamed or removed outside DarkLab shows its Folder as MISSING the next time Library refreshes.
- The Photos of a missing Folder stay in the grid with their own MISSING badge and Develop Settings.
- Relink Folder is available only for a missing Folder.
- Relink needs every Photo's file name to exist in the replacement directory and checks its content hash against the stored one. Nothing is written when any file is absent or differs.
- A successful relink stores the new paths in one transaction, clears the MISSING mark, and keeps Develop Settings, marks, and Preview images.
- The Original files and their content hashes are unchanged.

## 3. Non-Goals

- A directory tree with sub-Folders and parent counts.
- Adding or removing a Folder on its own, and moving files between Folders.
- Confirming a relink to different content in the UI. The domain call supports it and the dialog does not offer it yet.
- Watching directories for live changes. Refresh happens when Library reloads.

## 4. Open Questions

None.
