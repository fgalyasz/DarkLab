---
stepsCompleted:
  - step-01-validate-prerequisites
  - step-02-design-epics
  - step-03-create-stories
  - step-04-final-validation
inputDocuments:
  - _bmad-output/planning-artifacts/prds/prd-DarkLab-2026-10-10/prd.md
  - _bmad-output/planning-artifacts/prds/prd-DarkLab-2026-10-10/addendum.md
  - _bmad-output/planning-artifacts/architecture.md
status: final
---

# DarkLab - Epic Breakdown

## Overview

Epic and story breakdown for DarkLab. Requirements come from the baseline PRD and the architecture document. There is no separate UX specification. The Module bar in PRD section 11 is the information architecture.

Fast path, 2026-10-10. Epic order follows the thesis: finish one shoot, then organize, then complete Develop, then the output Modules.

## Requirements Inventory

### Functional Requirements

- FR-1 Catalog lifecycle
- FR-2 Original references and relink
- FR-3 Catalog backup and restore
- FR-4 Sidecar round-trip
- FR-5 Import Add, Copy, and Move
- FR-6 Import destination, rename, Metadata, and Keywords
- FR-7 Import pre-commit summary
- FR-8 Duplicate detection
- FR-9 Grid and loupe
- FR-10 Compare and survey
- FR-11 Folders
- FR-12 Collections
- FR-13 Smart Collections
- FR-14 Rating, Flag, and Color Label
- FR-15 Filter
- FR-16 Keywords
- FR-17 Metadata
- FR-18 Stacks
- FR-19 Virtual Copies
- FR-20 Quick Develop
- FR-21 Non-destructive Develop Settings
- FR-22 Crop and straighten
- FR-23 Basic tone and white balance
- FR-24 Tone curve
- FR-25 HSL
- FR-26 Color grading
- FR-27 Detail
- FR-28 Lens corrections and transform
- FR-29 Effects and calibration
- FR-30 Masks
- FR-31 Healing
- FR-32 History, Snapshots, before/after, copy/paste
- FR-33 Develop Presets
- FR-34 Histogram
- FR-35 Export JPEG and TIFF
- FR-36 Export Presets
- FR-37 Export leaves Originals and the Catalog unchanged
- FR-38 Map pins
- FR-39 Assign location and tracklog
- FR-40 Book layout
- FR-41 Book PDF
- FR-42 Slideshow playback
- FR-43 Slideshow video
- FR-44 Print layouts
- FR-45 Print to printer and JPEG
- FR-46 Static web gallery
- FR-47 Face confirmation
- FR-48 Choose a Startup Mode
- FR-49 Pin a Catalog
- FR-50 A Catalog is required
- FR-51 One Catalog folder
- FR-52 Imported folder paths
- FR-53 Index images
- FR-54 Catalog settings
- FR-55 A new Catalog shows no Photos
- FR-56 The Library grid lists Catalog index images
- FR-57 Import writes index images
- FR-80 Configurable Auto-Cull criteria, weights, thresholds, and profiles
- FR-81 Per-Photo quality metric extraction (sharpness, eyes open, smile, exposure, framing, pHash) and SQLite cache
- FR-82 Burst and near-duplicate grouping with best-shot selection
- FR-83 Automatic Flag, Rating, and Color Label assignment rules
- FR-84 Import Assisted Culling workflow
- FR-85 Library Auto-Cull batch action and explainable score breakdown
- FR-86 Full Basic panel, B&W Treatment, and live preview binding
- FR-87 Parametric and Point Tone Curve (RGB, R, G, B)
- FR-88 8-Band Color Mixer (HSL) and 4-Way Color Grading Wheels
- FR-89 Detail (Sharpening & Noise Reduction) with 1:1 preview and unique keys
- FR-90 Lens Corrections and Perspective Transform with Constrain Crop
- FR-91 Post-Crop Vignetting, Film Grain, and Camera Calibration
- FR-92 Interactive Crop Overlay, Spot Heal/Clone, Red Eye, and Local Masks
- FR-93 Develop Presets with Amount slider, Snapshots, Copy/Paste, Soft Proofing, and Persistent History
- FR-94 Scene-analyzed Auto Tone (Exposure, Contrast, Highlights, Shadows, Whites, Blacks)
- FR-95 Auto White Balance (Temp and Tint)
- FR-96 Auto Presence (Vibrance, Clarity, Dehaze)
- FR-97 Auto Lens Profile & Chromatic Aberration Correction
- FR-98 Integrated Auto Upright & Horizon Leveling (Auto, Level, Vertical, Full)
- FR-99 AI Scene-Aware Auto-Develop and Subject Relight
- FR-100 AI Semantic Masking (Subject, Sky, Background, and People-Parts)
- FR-101 AI Portrait Retouch (Skin Smoothing, Eye Enhancer, Teeth Whitening)
- FR-102 AI Denoise and AI Sharpen / Motion Deblur Assist
- FR-103 AI Sensor Dust and Blemish Auto-Heal
- FR-104 AI Adaptive Presets with Amount Scaling
- FR-105 Auto-Crop configuration model and presets
- FR-106 Subject, Face, Eye-Line, and Saliency Anchor Detection
- FR-107 Composition-Rule and Aspect-Ratio Crop Solver
- FR-108 Straighten-Constrained Inscribed Bounding Box
- FR-109 Develop and Library Auto-Crop UI and History Integration
- FR-110 Multi-Photo Selection in Develop Filmstrip and Library Grid
- FR-111 Selective Sync Dialog and Copy/Paste Across Multiple Photos
- FR-112 Develop Auto-Sync Mode
- FR-113 Relative (Delta) and Absolute Multi-Photo Quick Develop
- FR-114 Match Total Exposure Across Selected Photos
- FR-115 Per-Photo Computed Batch Auto-Corrections, Batch Auto-Crop, and Batch AI Corrections

### NonFunctional Requirements

- NFR-1 Cached basic-tone Preview updates within 100 ms — Epic 3
- NFR-2 Import of 500 JPEGs by Add stays off the UI thread — Epic 1
- NFR-3 Shoot path works with the network off — Epics 1–4
- NFR-4 One SQLite database inside the Catalog folder, and a disposable preview cache — Epic 13
- NFR-5 Same source on macOS, Windows, and Linux — all epics, no platform-only MVP feature
- NFR-6 No account and no telemetry — all epics
- NFR-7 4.5:1 text contrast on the dark theme — Epic 2, when the Library labels are set
- NFR-8 95% line coverage on new domain packages — every epic that adds domain code

### Additional Requirements

- ADR-7: remove the 1920×1080 hard exit — Story 1.1
- ADR-6: domain functions stay free of Qt — every story that adds a service
- Empty states for Map, Book, Slideshow, Print, and Web until their epics — Story 2.1
- CI workflow running unit tests — Story 1.1, once the first domain tests exist

### UX Design Requirements

No UX document. Stories use the Module names from the PRD glossary.

### FR Coverage Map

- FR-1 Epic 1
- FR-2 Epic 1
- FR-3 Epic 1
- FR-4 Epic 1
- FR-5 Epic 1
- FR-6 Epic 1 (destination and rename), Epic 5 (Metadata and Keywords on Import)
- FR-7 Epic 1
- FR-8 Epic 1
- FR-9 Epic 2
- FR-10 Epic 5
- FR-11 Epic 2
- FR-12 Epic 5
- FR-13 Epic 5
- FR-14 Epic 2
- FR-15 Epic 2 (text, Rating, Flag, Color Label), Epic 5 (Keyword and date)
- FR-16 Epic 5
- FR-17 Epic 5
- FR-18 Epic 5
- FR-19 Epic 5
- FR-20 Epic 5
- FR-21 Epic 3
- FR-22 Epic 3
- FR-23 Epic 3
- FR-24 Epic 6
- FR-25 Epic 6
- FR-26 Epic 6
- FR-27 Epic 6
- FR-28 Epic 6
- FR-29 Epic 6
- FR-30 Epic 6
- FR-31 Epic 6
- FR-32 Epic 3 (History, Reset, before/after), Epic 6 (Snapshots, copy/paste)
- FR-33 Epic 6
- FR-34 Epic 3
- FR-35 Epic 4
- FR-36 Epic 4
- FR-37 Epic 4
- FR-38 Epic 7
- FR-39 Epic 7
- FR-40 Epic 9
- FR-41 Epic 9
- FR-42 Epic 8
- FR-43 Epic 8
- FR-44 Epic 8
- FR-45 Epic 8
- FR-46 Epic 9
- FR-47 Epic 10
- FR-48 Epic 11
- FR-49 Epic 11
- FR-50 Epic 12
- FR-51 Epic 13
- FR-52 Epic 13
- FR-53 Epic 13
- FR-54 Epic 13
- FR-55 Epic 14
- FR-56 Epic 14
- FR-57 Epic 15
- FR-80 Epic 23
- FR-81 Epic 23
- FR-82 Epic 23
- FR-83 Epic 23
- FR-84 Epic 23
- FR-85 Epic 23
- FR-86 Epic 24
- FR-87 Epic 24
- FR-88 Epic 24
- FR-89 Epic 24
- FR-90 Epic 24
- FR-91 Epic 24
- FR-92 Epic 24
- FR-93 Epic 24
- FR-94 Epic 25
- FR-95 Epic 25
- FR-96 Epic 25
- FR-97 Epic 25
- FR-98 Epic 25
- FR-99 Epic 26
- FR-100 Epic 26
- FR-101 Epic 26
- FR-102 Epic 26
- FR-103 Epic 26
- FR-104 Epic 26
- FR-105 Epic 27
- FR-106 Epic 27
- FR-107 Epic 27
- FR-108 Epic 27
- FR-109 Epic 27
- FR-110 Epic 28
- FR-111 Epic 28
- FR-112 Epic 28
- FR-113 Epic 28
- FR-114 Epic 28
- FR-115 Epic 28

## Epic List

1. Catalog and Import — a shoot lands in a Catalog and the Originals stay safe
2. Library culling — grid, loupe, folders, marks, and filters
3. Basic Develop — crop, white balance, tone, history, histogram
4. Export — client JPEGs and a TIFF, without ingesting them
5. Library organization — keywords, metadata, collections, stacks, virtual copies
6. Full Develop — the rest of the Classic panel set
7. Map — pins and geotag
8. Print and Slideshow — contact sheet and playback
9. Book and Web — PDF book and a static gallery
10. People — confirm faces when a detector exists
11. Catalog startup — ask, reopen the last Catalog, or open a pinned Catalog
12. Catalog required — the workspace opens only after a Catalog is current
13. Catalog package — one folder holds imported folders, index images, and that Catalog's settings
14. Library grid — the grid lists the open Catalog's index images and stays empty until some exist
15. Import index images — Import writes an index image for each Photo and the grid shows it
23. Configurable Auto-Cull on Import and Library — automatic selection by configurable criteria (eyes, smile, sharpness, exposure, framing, burst winner)
24. Complete End-to-End Develop Pipeline and Controls — full persistence, live preview, 12-stage rendering, and tools for every Develop panel
25. Automatic Image Corrections — deterministic scene-analyzed Auto Tone, Auto WB, Auto Presence, Auto Lens/CA, and Auto Upright
26. AI Image Correction and Enhancement Suite — local-first AI Auto-Develop/Relight, Semantic Masks, Portrait Retouch, AI Denoise/Sharpen, Dust Auto-Heal, and Adaptive Presets
27. Configurable Auto-Crop and Smart Framing — rule-based and subject/face/horizon-aware automatic cropping with straighten bounds
28. Multi-Photo Batch Image Manipulation and Sync — multi-selection, selective Sync, Auto-Sync, relative/absolute Quick Develop, Match Total Exposure, and per-photo computed Batch Auto/AI/Crop

## Epic 1: Catalog and Import

A Photographer can create a Catalog, bring a card in, and reopen the same Photos later without a changed Original.

### Story 1.1: Create and reopen a Catalog

As a Photographer,
I want to create a Catalog and see it again after a restart,
So that the shoot has a home before I import.

**Acceptance Criteria:**

**Given** no Catalog is open
**When** a Catalog is created at a chosen path
**Then** a single SQLite file exists there
**And** restarting the application reopens it without a merge into any other Catalog

**Given** a display smaller than 1920×1080
**When** the application starts
**Then** the window opens
**And** it does not exit because of screen size

**Given** the first domain tests in `src/catalog`
**When** CI runs
**Then** `python -m unittest discover -s tests` is the command
**And** those tests do not construct a Qt application

### Story 1.2: Import with a summary

As a Photographer,
I want Add, Copy, and Move with a count and size before commit,
So that I know what will happen to the card.

**Acceptance Criteria:**

**Given** a folder of JPEGs
**When** the selection changes in Import
**Then** the summary shows the selected count and byte size
**And** commit stays disabled while the selection is empty

**Given** Copy
**When** Import commits
**Then** new files exist at the destination and the source files remain

**Given** Add of 500 JPEGs
**When** Import runs
**Then** progress reports completed count
**And** the UI thread is not blocked on the file walk

**Given** Move
**When** the destination file exists and its size matches
**Then** the source file is removed
**And** a failed copy leaves the source in place

### Story 1.3: Skip duplicates

As a Photographer,
I want an Original that is already in the Catalog to be skipped unless I say otherwise,
So that a second copy of the card does not double the grid.

**Acceptance Criteria:**

**Given** a Photo whose Original hash is already in the Catalog
**When** Import scans it
**Then** the default action is skip
**And** skip does not create a Photo and does not change the existing Photo

**Given** the Photographer chooses to import the duplicate anyway
**When** Import commits
**Then** a second Photo is created

### Story 1.4: Missing Originals and sidecars

As a Photographer,
I want a missing file to stay visible, and Develop Settings to round-trip through a Sidecar,
So that the Catalog is not the only record and it is not a silent deletion.

**Acceptance Criteria:**

**Given** a Photo whose Original was removed outside DarkLab
**When** Library shows it
**Then** the Photo is marked missing
**And** relinking a file with the same hash clears that state and keeps Develop Settings

**Given** a Sidecar write
**When** the Original is hashed afterward
**Then** the hash is unchanged
**And** an unrelated tag that was already in the Sidecar is still there

**Given** that Sidecar and a new Catalog
**When** the same Original is imported
**Then** the Develop Settings from the Sidecar are on the new Photo

### Story 1.5: Back up the Catalog

As a Photographer,
I want a timestamped backup I can restore,
So that a bad quit does not cost the cull.

**Acceptance Criteria:**

**Given** a Catalog with Photos
**When** a backup is written and then restored
**Then** the restored Catalog has those Photos
**And** Original files were not deleted by the restore

**Given** the backup destination cannot be written
**When** backup runs
**Then** the open Catalog still opens and still has its Photos

### Story 1.6: Group Copy, Move, and Add

As a Photographer,
I want Copy, Move, and Add to read as one choice,
So that Add is not a separate command from the other ways a file enters the Catalog.

**Acceptance Criteria:**

**Given** the Import top bar
**When** it is shown
**Then** Copy, Move, and Add are one row, in that order
**And** Assisted Culling sits outside that row

**Given** Add is selected
**When** the bar is shown
**Then** the caption is visible under that row
**And** another mode hides the caption

### Story 1.7: A usable Import window

As a Photographer,
I want Import to show only the choice I am making,
So that presets, renaming, and metadata do not bury the files.

**Acceptance Criteria:**

**Given** Copy or Move
**When** Import opens
**Then** the side panel is a destination folder and a Choose Folder button
**And** the chosen folder is where the files are placed, in one folder

**Given** Add
**When** Import opens
**Then** the destination panel is hidden

**Given** the bottom bar
**When** Import opens
**Then** it has the summary, the duplicate choice, and Cancel plus the commit button
**And** it does not offer an import-preset manager

### Story 1.8: Separate the Import blocks

As a Photographer,
I want renaming, metadata, and the destination preset to read as separate blocks,
So that I can see which control belongs to which job.

**Acceptance Criteria:**

**Given** Import
**When** the window opens
**Then** File Renaming, Metadata, and Destination are three shaded blocks, in that order
**And** Destination shows the active preset and its folder

**Given** an existing destination preset
**When** a folder is chosen
**Then** that preset's folder changes
**And** the other destination presets remain

### Story 1.9: Keep the Import side panel inside its column

As a Photographer,
I want the Import side panel to stay inside its column,
So that I do not scroll sideways to reach renaming, metadata, or the destination.

**Acceptance Criteria:**

**Given** the Import window at its default size
**When** the side panel is shown
**Then** it has no horizontal scrollbar
**And** the settings content is no wider than the column

### Story 1.10: Remove index images

As a Photographer,
I want to remove an index image from the Catalog,
So that I can choose whether the Original file stays on disk.

**Acceptance Criteria:**

**Given** a selected index image
**When** Remove asks what to delete
**Then** one choice deletes only the index image
**And** the Original file stays on disk

**Given** the same question
**When** the Photographer also deletes the Original
**Then** that file is removed from disk
**And** the index image and the Photo row are gone

**Given** the Original cannot be deleted
**When** that choice runs
**Then** the Photo and its index image stay

### Story 1.11: Clear the Navigator after removal

As a Photographer,
I want the Navigator to drop a removed index image,
So that I do not keep looking at a photograph that has left the Catalog.

**Acceptance Criteria:**

**Given** the Navigator is showing a selected index image
**When** that index image is removed
**Then** the Navigator pixmap is cleared
**And** it says that no photograph is selected

### Story 1.12: Match index image size to the thumbnail slider

As a Photographer,
I want the index images to open at the Thumbnails slider size,
So that the grid matches the control I see.

**Acceptance Criteria:**

**Given** the Library opens with the Thumbnails slider at its starting position
**When** the grid is shown
**Then** the index image size is the size that position selects

**Given** the Library is open
**When** the Thumbnails slider moves
**Then** the index image size follows the new position

## Epic 2: Library culling

A Photographer can see the shoot, mark selects, and filter to them.

### Story 2.1: Grid, loupe, and honest empty Modules

As a Photographer,
I want a grid and a loupe, and a Module bar that matches Classic,
So that I can move through the shoot and see where later work will live.

**Acceptance Criteria:**

**Given** imported Photos
**When** a sort is chosen among capture time, filename, Import time, and Rating
**Then** the grid order follows that sort
**And** loupe shows the selected Photo

**Given** the Module bar
**When** the Photographer looks at it
**Then** the Modules are Library, Develop, Map, Book, Slideshow, Print, and Web, in that order
**And** Map, Book, Slideshow, Print, and Web show an empty state until their epic, not a control that pretends to work

### Story 2.2: Folders

As a Photographer,
I want the directories of my Originals as Folders,
So that the card I imported is the set I cull.

**Acceptance Criteria:**

**Given** Photos imported from a directory
**When** that Folder is selected
**Then** the grid shows those Photos
**And** the Folder is not a second copy of the files

**Given** the directory was renamed outside DarkLab
**When** Library refreshes
**Then** the Folder is marked missing until it is relinked

### Story 2.3: Ratings, flags, and labels

As a Photographer,
I want stars, a flag, and a color label,
So that selects survive a restart.

**Acceptance Criteria:**

**Given** a Photo in Library
**When** a Rating, Flag, or Color Label is set
**Then** the same marks are on that Photo in Develop
**And** they are still there after restart

### Story 2.4: Filter the cull

As a Photographer,
I want to filter by text, Rating, Flag, and Color Label,
So that the grid becomes the delivery set.

**Acceptance Criteria:**

**Given** a Folder with mixed Flags
**When** the filter is Pick
**Then** the grid count equals the Pick count in that Folder

**Given** an active filter
**When** the filter is cleared
**Then** the grid count returns to the Folder count

**Given** body labels on the dark theme
**When** contrast is measured
**Then** text against its background is at least 4.5:1

## Epic 3: Basic Develop

A Photographer can correct a select without touching the Original, and can undo.

### Story 3.1: Tone and white balance

As a Photographer,
I want white balance and the basic tone controls on a Preview,
So that the venue color and exposure are correct before I export.

**Acceptance Criteria:**

**Given** a Photo opened in Develop
**When** any basic control in FR-23 changes
**Then** Develop Settings change and the Original hash does not

**Given** a cached Preview
**When** exposure moves
**Then** the Preview updates within 100 ms on the NFR-1 reference machines
**And** the same settings are present after restart

**Given** as-shot white balance
**When** the Photographer then edits temperature
**Then** the edited value is what is stored

### Story 3.2: Crop

As a Photographer,
I want crop and straighten stored with the Photo,
So that Export matches what I framed.

**Acceptance Criteria:**

**Given** a locked aspect ratio
**When** the crop changes and the lock is turned off
**Then** both states are visible and the latest crop is the one in Develop Settings

**Given** a crop
**When** Reset is used
**Then** Develop Settings return to the Import state, including an empty crop

### Story 3.3: History and before/after

As a Photographer,
I want each change as a History Step and a before/after compare,
So that a bad correction is recoverable.

**Acceptance Criteria:**

**Given** two tone changes
**When** the older History Step is selected
**Then** Develop Settings match that step

**Given** before/after
**When** the Photographer toggles it
**Then** the Preview switches between Import settings and the current settings without writing a new step

### Story 3.4: Histogram and clipping

As a Photographer,
I want a histogram of the current Preview and a clipping overlay,
So that I can see blocked shadows before Export.

**Acceptance Criteria:**

**Given** a change to exposure
**When** the Preview updates
**Then** the histogram updates from that Preview

**Given** the clipping overlay
**When** it is turned off
**Then** Develop Settings are unchanged

## Epic 4: Export

A Photographer can write client files and prove the Originals were not the save target.

### Story 4.1: Export JPEG and TIFF

As a Photographer,
I want JPEG and TIFF renders at a chosen size and color space,
So that the client folder is the delivery.

**Acceptance Criteria:**

**Given** selected Photos that have Originals
**When** Export runs
**Then** the output count matches that selection
**And** a missing Original is skipped and named

**Given** a cropped Photo with tone changes
**When** the JPEG or TIFF is opened outside DarkLab
**Then** the crop and tone are in the file

### Story 4.2: Built-in JPEG Preset

As a Photographer,
I want a saved sRGB JPEG at a 2048 long edge,
So that I can repeat the usual delivery.

**Acceptance Criteria:**

**Given** the built-in Preset
**When** Export runs
**Then** the file is JPEG, sRGB, long edge 2048, and has no watermark

**Given** a Photographer-saved Preset
**When** it is chosen
**Then** format, size, color space, output sharpening, and watermark follow the saved values

### Story 4.3: Export does not ingest

As a Photographer,
I want Export to leave the Catalog and the Originals alone,
So that renders are not a second shoot unless I import them.

**Acceptance Criteria:**

**Given** hashes of the selected Originals and a Photo count
**When** Export finishes
**Then** the hashes match and the Photo count is unchanged

## Epic 5: Library organization

A Photographer can find Photos later by more than the folder they landed in.

### Story 5.1: Keywords

As a Photographer,
I want a Keyword hierarchy on Photos, including at Import,
So that a later filter is the wedding, not a scroll.

**Acceptance Criteria:**

**Given** a child Keyword
**When** it is assigned
**Then** the parent path is stored with it
**And** a Keyword filter returns that Photo

**Given** Keywords chosen in Import
**When** Import commits
**Then** the new Photos have those Keywords

### Story 5.2: Metadata

As a Photographer,
I want to read EXIF and edit IPTC,
So that captions exist for Book and Export.

**Acceptance Criteria:**

**Given** an Original with camera EXIF
**When** a caption is edited
**Then** the EXIF exposure values are unchanged
**And** the caption is available to Export and Book

### Story 5.3: Collections and smart collections

As a Photographer,
I want manual Collections and a Smart Collection from a filter,
So that a delivery set can outlive the Folder view.

**Acceptance Criteria:**

**Given** a Photo in two Collections
**When** it is removed from one
**Then** it remains in the other and the Original remains

**Given** a Smart Collection rule on Rating
**When** a Photo's Rating crosses the rule
**Then** membership changes without a manual drop

### Story 5.4: Stacks and virtual copies

As a Photographer,
I want bursts stacked and a second set of Develop Settings on the same Original,
So that the grid stays short and a black-and-white try does not replace the color edit.

**Acceptance Criteria:**

**Given** a Stack
**When** it is collapsed and then unstacked
**Then** collapse shows one Photo plus a count
**And** unstacking deletes nothing

**Given** a Virtual Copy
**When** its Develop Settings change
**Then** the source Photo's Develop Settings stay as they were
**And** both Photos share the Original hash

### Story 5.5: Compare, survey, and Quick Develop

As a Photographer,
I want to look at candidates together and apply a simple correction to the set,
So that culling and a first pass do not require a trip through every control.

**Acceptance Criteria:**

**Given** Compare
**When** a candidate and a select are chosen
**Then** both stay visible and neither is deleted by leaving the view

**Given** Survey
**When** a Photo is removed from the survey
**Then** it remains in the Catalog

**Given** Quick Develop on a selection that includes a missing Original
**When** exposure is applied
**Then** each present Photo gains one History Step
**And** the missing Photo is named and skipped

### Story 5.6: Filter by keyword and date

As a Photographer,
I want the Library filter to include Keyword and capture date,
So that the marks from this epic are usable in the grid.

**Acceptance Criteria:**

**Given** a Keyword and a capture-date range
**When** either filter is applied
**Then** the grid count matches the Photos in the current source that satisfy it

## Epic 6: Full Develop

A Photographer can finish a file with the Classic panel set, still without writing the Original.

### Story 6.1: Curve, HSL, and color grading

As a Photographer,
I want curve, HSL, and color grading,
So that color work is not stuck at the basic sliders.

**Acceptance Criteria:**

**Given** a point on the red curve, an HSL band, and a shadow grade
**When** they are edited and the Catalog is reopened
**Then** those values match
**And** Reset curve clears the curve and leaves basic tone unchanged

### Story 6.2: Detail, lens, transform, effects, and calibration

As a Photographer,
I want detail at 1:1, a lens profile when Lensfun has one, manual transform, vignette, grain, and calibration,
So that geometry and finish are part of the same Develop Settings.

**Acceptance Criteria:**

**Given** sharpening
**When** the Preview is at 1:1
**Then** the sharpening is visible there

**Given** no matching lens profile
**When** the lens panel opens
**Then** it says the profile is missing
**And** manual transform still saves

**Given** any control in this story
**When** it changes
**Then** the Original hash is unchanged

### Story 6.3: Masks

As a Photographer,
I want brush, linear, radial, color-range, and luminance-range Masks,
So that a local correction does not become a second application.

**Acceptance Criteria:**

**Given** a Mask with increased exposure
**When** the Preview is rendered
**Then** pixels outside the Mask and its falloff keep the unmasked exposure

**Given** no subject or sky detector
**When** Develop opens
**Then** those two tools are absent
**And** the other Mask tools still work

**Given** a deleted Mask
**When** the Preview renders
**Then** that Mask's effect is gone and the global Develop Settings remain

### Story 6.4: Healing

As a Photographer,
I want heal and clone strokes stored on the Photo,
So that a dust spot stays gone after Export and restart.

**Acceptance Criteria:**

**Given** a heal stroke
**When** the Catalog is reopened and the Photo is exported
**Then** the stroke is in the Preview and in the Export

**Given** the stroke is deleted
**When** the Preview renders
**Then** the spot is back and the Original hash never changed

### Story 6.5: Presets, snapshots, and copy settings

As a Photographer,
I want Presets, named Snapshots, and copy/paste of Develop Settings,
So that one reception look can be reused on purpose.

**Acceptance Criteria:**

**Given** a Preset saved without crop
**When** it is applied
**Then** it is one History Step
**And** the destination crop is unchanged

**Given** a Snapshot
**When** it is selected after later edits
**Then** Develop Settings match the Snapshot

**Given** copied Develop Settings
**When** they are pasted on another Photo
**Then** the destination gains one History Step and the source Photo is unchanged

## Epic 7: Map

A Photographer can see GPS Photos and put the rest on a place.

### Story 7.1: Pins from GPS

As a Photographer,
I want Photos that already have GPS to show on the Map,
So that the camera's locations are visible without retyping them.

**Acceptance Criteria:**

**Given** a source with mixed GPS
**When** Map opens and the network is available
**Then** the pin count equals the Photos that have GPS
**And** selecting a pin selects the Photo

**Given** the network is off
**When** Map opens
**Then** an offline empty state is shown
**And** Library, Develop, and Export still work

### Story 7.2: Geotag and tracklog

As a Photographer,
I want to drag a Photo onto a place, clear it, save the place, and match a tracklog,
So that reception frames without GPS still belong to the venue.

**Acceptance Criteria:**

**Given** a drag onto the map
**When** the Catalog restarts
**Then** the pin is there and the Sidecar contains the GPS

**Given** Clear
**When** it is confirmed
**Then** the pin is gone

**Given** a tracklog
**When** a Photo's capture time falls inside it
**Then** the coordinates are set
**And** a capture time outside the track is not assigned

## Epic 8: Print and Slideshow

A Photographer can hand a contact sheet to a couple and play the selects.

### Story 8.1: Print a layout

As a Photographer,
I want a single image, a contact sheet, or custom cells, sent to a printer or a JPEG,
So that a paper proof does not mean exporting a loose folder by hand.

**Acceptance Criteria:**

**Given** a contact sheet
**When** a JPEG of the layout is written
**Then** the cell count and margins match the on-screen page
**And** the file is the layout, not one uncropped Original

**Given** draft mode
**When** it is on
**Then** the page is labeled draft

### Story 8.2: Play and export a slideshow

As a Photographer,
I want timed playback with captions and optional music, and a video export,
So that a review night does not depend on another tool.

**Acceptance Criteria:**

**Given** a duration per slide
**When** playback runs
**Then** slides advance without input
**And** stop returns to the Slideshow Module with the Collection unchanged

**Given** a video export
**When** the file is measured
**Then** its duration matches the slide timings within one second
**And** Original hashes are unchanged

## Epic 9: Book and Web

A Photographer can leave with a PDF book and a folder that opens in a browser.

### Story 9.1: Book to PDF

As a Photographer,
I want pages from a Collection, with captions, exported to PDF,
So that a book is a file and not a checkout.

**Acceptance Criteria:**

**Given** a Book
**When** Photos are reordered in the Book only
**Then** the Collection order stays as it was

**Given** a caption edit in the Book
**When** the Photo is viewed in Library
**Then** the Metadata caption matches

**Given** PDF export
**When** the PDF is opened
**Then** the page count matches the Book
**And** Original hashes are unchanged

### Story 9.2: Static gallery

As a Photographer,
I want a Collection exported as HTML that needs no server,
So that a client can click through selects from a folder.

**Acceptance Criteria:**

**Given** an exported gallery
**When** the index file is opened in a browser with no network
**Then** every Photo that was in the Collection at export time is shown
**And** the page does not call DarkLab

## Epic 10: People

A Photographer can name a face when a detector is present, and the app still runs when it is not.

### Story 10.1: Confirm or reject a face

As a Photographer,
I want suggestions to stay suggestions until I confirm them,
So that a person filter is something I said, not something a model guessed.

**Acceptance Criteria:**

**Given** no face detector
**When** Library opens
**Then** the other Modules still work
**And** the people control states that detection is unavailable

**Given** a suggestion
**When** it is confirmed
**Then** a person filter returns that Photo

**Given** a rejected suggestion
**When** the same Photo is scanned again
**Then** that suggestion is not offered again for that Photo

## Epic 11: Catalog startup

A Photographer can decide which Catalog the next launch opens.

### Story 11.1: Save the startup choice

As a Photographer,
I want to choose ask, the most recent Catalog, or one pinned Catalog,
So that the next launch is the one I meant.

**Acceptance Criteria:**

**Given** Catalog Settings
**When** Ask is saved
**Then** the choice is still Ask after a restart

**Given** fixed mode and no existing file
**When** the Photographer confirms
**Then** the previous setting stays in place

**Given** a pinned Catalog
**When** a different Catalog is opened
**Then** the pinned path is unchanged

### Story 11.2: Launch follows the startup choice

As a Photographer,
I want the next launch to follow Catalog Settings,
So that I am asked, returned to the last Catalog, or returned to the pin.

**Acceptance Criteria:**

**Given** Ask
**When** DarkLab launches
**Then** Select Catalog is shown before the workspace

**Given** recent mode and an existing last Catalog
**When** DarkLab launches
**Then** that Catalog is current
**And** a missing last Catalog shows Select Catalog before the workspace

**Given** a pinned file that exists
**When** DarkLab launches
**Then** that file is current even if a different Catalog was opened last

**Given** a pinned file that is missing
**When** DarkLab launches
**Then** Select Catalog is shown before the workspace

## Epic 12: Catalog required

The workspace does not open until a Catalog is current.

### Story 12.1: Choose or quit before the workspace

As a Photographer,
I want DarkLab to require a Catalog the way Lightroom does,
So that I never edit in an empty window that has nowhere to put Photos.

**Acceptance Criteria:**

**Given** no Catalog can be resolved at launch
**When** DarkLab starts
**Then** Select Catalog is shown before the workspace
**And** Open and New are both available

**Given** Select Catalog
**When** Quit is chosen
**Then** DarkLab exits
**And** the workspace is not shown

**Given** the file chooser
**When** it is cancelled
**Then** Select Catalog stays open

## Epic 13: Catalog package

A Photographer can copy one Catalog folder and keep its imported folders, index images, and settings.

### Story 13.1: Store the Catalog in one folder

As a Photographer,
I want one Catalog folder to hold imported folders, index images, and that Catalog's settings,
So that copying the folder takes the shoot's DarkLab state with it.

**Acceptance Criteria:**

**Given** a new Catalog
**When** it is created
**Then** the path is a folder whose name ends in `.darklab`
**And** it contains the database, a preview directory, and a settings file
**And** creating it again does not remove what was stored

**Given** a folder path
**When** it is recorded
**Then** that path is listed once
**And** an empty path is refused
**And** another Catalog does not list it

**Given** index-image bytes for a Photo
**When** they are stored
**Then** they are read back from the preview directory
**And** removing that directory leaves the Catalog, its folders, and its settings usable

**Given** a Catalog setting
**When** it is saved
**Then** it is read back from that Catalog only
**And** invalid settings JSON is refused

**Given** a Catalog created earlier as a single database file
**When** it is opened
**Then** it still opens

**Given** Startup Mode
**When** a Catalog setting is saved
**Then** Startup Mode stays in the application config

## Epic 14: Library grid

The Library shows Photos only after they are in the open Catalog.

### Story 14.1: Build the grid from index images

As a Photographer,
I want a new Catalog to open with an empty Library,
So that I see only Photos I have imported into that Catalog.

**Acceptance Criteria:**

**Given** a new Catalog
**When** the Library opens
**Then** the grid and the filmstrip are empty

**Given** index images in the open Catalog
**When** the Library opens
**Then** the grid lists those index images in Photo id order
**And** files in the preview cache that are not index images are omitted

**Given** one Catalog with index images and another without
**When** the Photographer switches to the empty Catalog
**Then** the grid becomes empty

**Given** a disk folder that contains photographs
**When** the open Catalog has no index images
**Then** the Library does not show those photographs

## Epic 15: Import index images

Importing photographs leaves index images the Library can show.

### Story 15.1: Write an index image for each imported Photo

As a Photographer,
I want Import to put an index image in the open Catalog,
So that the Library grid shows the photographs I just imported.

**Acceptance Criteria:**

**Given** an open Catalog and selected photographs
**When** Add or Copy finishes
**Then** each resulting file has a Photo row and an index image
**And** importing the same path again does not add a second Photo

**Given** a file that cannot be read
**When** it is imported with files that can
**Then** it is skipped
**And** the readable files still get index images

**Given** the Import dialog closes
**When** the Library is showing the same Catalog
**Then** the grid lists the new index images

## Epic 23: Configurable Auto-Cull on Import and Library

Feature PRD: `https://github.com/fgalyasz/DarkLab/blob/main/_bmad-output/planning-artifacts/prds/prd-DarkLab-configurable-auto-cull/prd.md` (`FR-80`–`FR-85`, `ADR-10`, `ADR-16`)

A Photographer can automatically select imported Photos based on configurable criteria (eyes open, smile, sharpness, exposure health, framing, and burst grouping) during Import and in Library.

### Story 23.1: Configurable culling criteria model and presets

As a Photographer,
I want to configure Auto-Cull weights and minimum thresholds (sharpness, eyes open, smile, exposure, framing, burst settings) and choose or save a Culling Profile,
So that portrait shoots prioritize open eyes and smiles while action or landscape shoots prioritize sharpness and exposure.

**Acceptance Criteria:**

**Given** a Catalog
**When** a `CullCriteria` profile (`Portrait & Wedding`, `Event & Action`, `Landscape & Architecture`, or `Custom`) is saved to `settings.json` (`auto_cull` key)
**Then** reading `auto_cull` back returns the exact weights, thresholds, burst window, and `preserve_manual_marks` flag
**And** out-of-range weights or thresholds are clamped to `0..100`

**Cost-Effective Implementation Blueprint:**
- Target module: `src/culling/criteria.py`
- Key types/functions (≤10 lines each): `CullCriteria` frozen dataclass, `BUILT_IN_PROFILES`, `encode_criteria(criteria) -> dict`, `decode_criteria(raw) -> CullCriteria`, `load_cull_criteria(catalog) -> CullCriteria`, `save_cull_criteria(catalog, criteria) -> None`
- Unit test file: `tests/test_cull_criteria.py` (≥95% coverage)

### Story 23.2: Per-Photo quality metric extractor (sharpness, eyes, smile, exposure, framing, pHash)

As a Photographer,
I want DarkLab to evaluate sharpness, face/eye openness, smile/expression, exposure health, framing margin, and a perceptual hash for each Photo offline,
So that culling decisions are based on objective image signals without uploading files.

**Acceptance Criteria:**

**Given** a sharp portrait with open eyes and a blurred frame with closed eyes
**When** `extract_cull_metrics` runs on both images
**Then** the sharp portrait receives higher `sharpness_score`, `eyes_open_score`, and `all_eyes_open = True`
**And** a Photo with `face_count == 0` still receives valid `sharpness_score`, `exposure_score`, `framing_score`, and `perceptual_hash`
**And** Original bytes are never modified

**Cost-Effective Implementation Blueprint:**
- Target module: `src/culling/metrics.py`
- Key types/functions (≤10 lines each): `PhotoCullMetrics` frozen dataclass, `extract_cull_metrics(pixels: np.ndarray) -> PhotoCullMetrics`, `measure_sharpness(gray)`, `measure_exposure(gray)`, `compute_dhash(gray) -> str`, `detect_face_signals(gray, bgr)`
- Unit test file: `tests/test_cull_metrics.py` (≥95% coverage)

### Story 23.3: Burst grouping and weighted composite scorer

As a Photographer,
I want sequential burst shots grouped together and scored against my active `CullCriteria` weights,
So that the best frame in each burst is marked `Pick` and blinked or blurry frames are marked `Rejected`.

**Acceptance Criteria:**

**Given** cached `PhotoCullMetrics` for a shoot and a `CullCriteria` profile
**When** `evaluate_cull_batch` runs
**Then** Photos within `burst_time_window_sec` and `burst_hamming_max` form burst groups
**And** the top-scoring Photo in each burst above `pick_score_min` gets `pick = "accepted"`
**And** Photos failing hard defect rules (`all_eyes_open == False` when `reject_closed_eyes` is on, or `sharpness_score < reject_sharpness_floor`) get `pick = "rejected"`
**And** Photos with `face_count == 0` exclude eye/smile weights from the composite denominator

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/culling/burst.py`, `src/culling/scorer.py`
- Key functions (≤10 lines each): `hamming_distance(a, b) -> int`, `group_bursts(items, window_sec, max_hamming) -> list[list[int]]`, `compute_composite_score(metrics, criteria) -> int`, `decide_photo_marks(metrics, criteria, is_winner) -> dict[str, str]`
- Unit test file: `tests/test_cull_scorer.py` (≥95% coverage)

### Story 23.4: SQLite persistence for per-Photo cull metrics

As a Photographer,
I want computed quality metrics cached in `catalog.sqlite` by `photo_id` and `content_hash`,
So that adjusting Auto-Cull sliders re-ranks 500 Photos immediately without re-decoding Originals.

**Acceptance Criteria:**

**Given** an open Catalog and extracted `PhotoCullMetrics`
**When** `save_cull_metrics` writes them and `read_cull_metrics` reads them back
**Then** all metric fields round-trip accurately
**And** existing manual marks on Photos are preserved when `preserve_manual_marks` is `True`

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/catalog/schema_sql.py`, `src/catalog/cull_metrics_store.py`
- Key functions (≤10 lines each): `save_cull_metrics(catalog, photo_id, content_hash, metrics)`, `read_cull_metrics(catalog, photo_id) -> PhotoCullMetrics | None`, `apply_cull_decisions(catalog, decisions, preserve_manual)`
- Unit test file: `tests/test_cull_metrics_store.py` (≥95% coverage)

### Story 23.5: Import Assisted Culling and Library Auto-Cull UI integration

As a Photographer,
I want to configure and run Auto-Cull in the Import dialog (`Assisted Culling`) and from the Library toolbar (`Auto-Cull...`),
So that I can filter to picks during Import or auto-cull an existing Folder in Library with explainable score badges.

**Acceptance Criteria:**

**Given** `ImportDialog` in `Assisted Culling` mode or `LibraryBrowserPanel`
**When** the Photographer opens `Auto-Cull...`, adjusts criteria sliders, and applies
**Then** candidate/Catalog Photos receive suggested `pick` and `rating` marks off the UI thread with progress reporting
**And** each Photo shows an explainable score summary (`Composite`, `Sharpness`, `Eyes`, `Smile`, `Exposure`)

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/ui/dialogs/auto_cull_dialog.py`, `src/ui/dialogs/import_dialog.py`, `src/ui/panels/library_browser_panel.py`
- Unit test file: `tests/test_auto_cull_ui.py` (≥95% coverage on domain/controller glue)

## Epic 24: Complete End-to-End Develop Pipeline and Controls

Feature PRD: `https://github.com/fgalyasz/DarkLab/blob/main/_bmad-output/planning-artifacts/prds/prd-DarkLab-complete-develop-pipeline/prd.md` (`FR-86`–`FR-93`, `ADR-11`, `ADR-16`)

A Photographer can use every Develop panel and tool with live preview updates, full Catalog persistence, XMP sidecar round-trip, History steps, and identical Preview/Export rendering.

### Story 24.1: Canonical settings schema, full Basic live preview, B&W Treatment, and Reset/Previous

As a Photographer,
I want all Basic sliders, the `Color / B&W` Treatment toggle, `Previous`, and `Reset` to update the Preview live and persist in `develop_settings`,
So that no control in the Basic panel or bottom bar is inert.

**Acceptance Criteria:**

**Given** a Photo in Develop
**When** any slider in `TONE_KEYS` (`Highlights`, `Shadows`, `Whites`, `Blacks`, `Texture`, `Clarity`, `Dehaze`, `Vibrance`, `Saturation`, `Exposure`, `Contrast`, `Temp`, `Tint`) or `Treatment` (`Color` / `B&W`) changes
**Then** `_paint_preview()` updates immediately and the setting persists to `develop_settings`
**And** clicking `Reset` persists default settings and records a `"Reset"` History Step
**And** clicking `Previous` applies the previously edited Photo's settings as a `"Previous"` History Step

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/develop/settings_schema.py`, `src/imaging/treatment.py`, `src/ui/panels/develop_panel.py`
- Unit test file: `tests/test_develop_basic_complete.py` (≥95% coverage)

### Story 24.2: Parametric and Point Tone Curve (RGB, Red, Green, Blue)

As a Photographer,
I want both the Parametric region sliders (`Highlights`, `Lights`, `Darks`, `Shadows`) and interactive Point Curve (`RGB`, `R`, `G`, `B`) to shape image contrast and persist per Photo,
So that custom tonal curves round-trip through the Catalog, Preview, and Export.

**Acceptance Criteria:**

**Given** edited Parametric sliders and a control point added on the `Red` point curve
**When** the Preview renders, the Catalog restarts, and Export runs
**Then** both Preview and Export apply the 256-entry channel LUTs from `src/imaging/tone_curve.py`
**And** reopening the Photo restores the exact Parametric slider values and curve control points

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/develop/curve_settings.py`, `src/imaging/tone_curve.py`, `src/ui/widgets/tone_curve_widget.py`
- Unit test file: `tests/test_tone_curve.py` (≥95% coverage)

### Story 24.3: 8-Band Color Mixer (HSL) and 4-Way Color Grading Wheels

As a Photographer,
I want to adjust Hue, Saturation, and Luminance for each of the 8 color bands and grade Shadows, Midtones, Highlights, and Global color wheels,
So that selective color and split-toning work end-to-end in Preview and Export.

**Acceptance Criteria:**

**Given** clicking a color dot in `Color Mixer` and adjusting `Hue`, `Saturation`, `Luminance`, and dragging the `Shadows` and `Highlights` `ColorWheel`s with `Blending` and `Balance`
**When** settings are saved and rendered
**Then** each of the 8 bands stores its own `HSL_<Band>_Hue|Sat|Lum` keys
**And** `src/imaging/hsl_mixer.py` and `src/imaging/color_wheels.py` transform pixels identically in Preview and Export

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/develop/hsl_grading_settings.py`, `src/imaging/hsl_mixer.py`, `src/imaging/color_wheels.py`, `src/ui/widgets/color_wheel.py`
- Unit test file: `tests/test_hsl_and_grading.py` (≥95% coverage)

### Story 24.4: Detail panel (Sharpening & Noise Reduction) with unique keys and 1:1 preview

As a Photographer,
I want distinct, working Sharpening (`Amount`, `Radius`, `Detail`, `Masking`) and Noise Reduction (`Luminance`, `Luminance Detail`, `Luminance Contrast`, `Color`, `Color Detail`, `Smoothness`) sliders with a 1:1 zoom toggle,
So that high-ISO noise and fine edge sharpening are accurately previewed and exported.

**Acceptance Criteria:**

**Given** `SliderRow` controls in `detail_panel`
**When** `Luminance Detail`, `Color Detail`, and `Sharpening Detail` are adjusted
**Then** each slider writes its own unique key (`SharpAmount`, `SharpRadius`, `SharpDetail`, `SharpMasking`, `NrLuminance`, `NrLuminanceDetail`, `NrLuminanceContrast`, `NrColor`, `NrColorDetail`, `NrColorSmoothness`)
**And** `src/imaging/detail.py` applies bilateral/wavelet noise reduction and edge-masked sharpening in Preview and Export

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/develop/detail_settings.py`, `src/imaging/detail.py`, `src/ui/widgets/slider_row.py`, `src/ui/develop_sections.py`
- Unit test file: `tests/test_detail_pipeline.py` (≥95% coverage)

### Story 24.5: Lens Corrections, Perspective Transform, and Constrain Crop

As a Photographer,
I want profile/manual Lens Corrections (`Remove Chromatic Aberration`, `Enable Profile Corrections`, `Distortion`, `Vignetting`) and Perspective Transform (`Vertical`, `Horizontal`, `Rotate`, `Aspect`, `Scale`, `X Offset`, `Y Offset`, `Constrain Crop`),
So that lens geometry and architectural perspective render cleanly without black corner wedges.

**Acceptance Criteria:**

**Given** lens distortion/vignetting or perspective Transform sliders with `Constrain Crop` checked
**When** `src/imaging/lens_transform.py` renders the Photo
**Then** chromatic aberration, radial distortion, lens vignetting, and homography warp apply in order
**And** `Constrain Crop` insets the crop box so no blank border pixels remain

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/develop/lens_transform_settings.py`, `src/imaging/lens_transform.py`
- Unit test file: `tests/test_lens_transform.py` (≥95% coverage)

### Story 24.6: Post-Crop Vignetting, Film Grain, and Camera Calibration

As a Photographer,
I want Post-Crop Vignetting, deterministic Film Grain, and Calibration (`Shadows Tint`, `Red/Green/Blue Primary Hue & Saturation`),
So that creative finish and primary color calibration persist and render identically in Preview and Export.

**Acceptance Criteria:**

**Given** non-zero Vignette, Grain, and Calibration primary sliders
**When** the Photo is rendered in Preview and Export
**Then** `src/imaging/effects_calibration.py` applies primary matrix shifts, post-crop oval vignette with feather/roundness/highlight preservation, and deterministic grain seeded by `photo_id`

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/develop/effects_calibration_settings.py`, `src/imaging/effects_calibration.py`
- Unit test file: `tests/test_effects_calibration.py` (≥95% coverage)

### Story 24.7: Interactive Crop Overlay, Spot Heal/Clone, Red Eye, and Local Masks

As a Photographer,
I want the `Crop`, `Spot`, `Red Eye`, and `Mask` tool buttons to open interactive tools and store non-destructive local edits,
So that spot removal, red-eye correction, and regional masks (`Brush`, `Linear Gradient`, `Radial Gradient`, `Color Range`, `Luminance Range`) work in Preview and Export.

**Acceptance Criteria:**

**Given** a `HealStroke`, a `RedEyeStroke`, and a `Radial Gradient` `Mask` with local exposure `+50`
**When** the Photo is saved, reopened, and exported
**Then** `src/imaging/healing.py`, `src/imaging/red_eye.py`, and `src/imaging/masking.py` apply all three non-destructively
**And** deleting a stroke or mask restores the underlying pixels while the Original hash stays unchanged

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/develop/local_edits.py`, `src/imaging/healing.py`, `src/imaging/red_eye.py`, `src/imaging/masking.py`
- Unit test file: `tests/test_local_adjustments.py` (≥95% coverage)

### Story 24.8: Presets with Amount slider, persistent Snapshots & History, Copy/Paste, Soft Proofing, and unified 12-stage pipeline

As a Photographer,
I want working Develop Presets (with `Amount` scaling), persistent Snapshots and History in SQLite, `Copy...`/`Paste`, `Soft Proofing`, and the unified 12-stage `src/imaging/pipeline.py` wired into both `DevelopPanel` and `exporting/render.py`,
So that the entire Develop module operates as one cohesive, lossless system.

**Acceptance Criteria:**

**Given** a Photo edited across all Develop sections, a saved Snapshot, and a Preset applied at `Amount = 60%`
**When** DarkLab restarts and Exports the Photo
**Then** `photo_history` and `photo_snapshots` restore all History Steps and Snapshots
**And** `render_photo` and `DevelopPanel` both call `src/imaging/pipeline.py`

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/imaging/pipeline.py`, `src/develop/presets_store.py`, `src/catalog/history_snapshots_store.py`, `src/ui/panels/develop_panel.py`, `src/exporting/render.py`
- Unit test file: `tests/test_presets_snapshots_pipeline.py` (≥95% coverage)

## Epic 25: Automatic Image Corrections

Feature PRD: `https://github.com/fgalyasz/DarkLab/blob/main/_bmad-output/planning-artifacts/prds/prd-DarkLab-auto-corrections/prd.md` (`FR-94`–`FR-98`, `ADR-12`, `ADR-16`)

A Photographer can apply deterministic, scene-analyzed automatic corrections (Auto Tone, Auto WB, Auto Presence, Auto Lens/CA, and Auto Upright) with one click.

### Story 25.1: Scene-analyzed Auto Tone, Auto Presence, and Auto White Balance

As a Photographer,
I want one-click `Auto Tone` and `Auto White Balance` that analyze the image histogram and neutral illuminant to set optimal `Exposure`, `Contrast`, `Highlights`, `Shadows`, `Whites`, `Blacks`, `Vibrance`, `Clarity`, `Dehaze`, `Temp`, and `Tint`,
So that under/over-exposed or color-cast frames balance immediately into editable sliders.

**Acceptance Criteria:**

**Given** a dark, warm-cast image and a bright, clipped-highlight image
**When** `compute_auto_tone` and `compute_auto_wb` run
**Then** the dark image gets positive `Exposure`/`Shadows` and cooler `Temp`, while the bright image gets negative `Exposure`/`Highlights`
**And** all returned values are valid integers within each slider's legal range

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/develop/auto_tone.py`, `src/develop/auto_wb.py`
- Key functions (≤10 lines each): `compute_auto_tone(pixels, include_presence=True) -> dict[str, int]`, `compute_auto_wb(pixels) -> tuple[int, int]`
- Unit test file: `tests/test_auto_tone_wb.py` (≥95% coverage)

### Story 25.2: Auto Upright and Auto Horizon geometry (`Auto`, `Level`, `Vertical`, `Full`)

As a Photographer,
I want the Transform Upright buttons (`Off`, `Auto`, `Level`, `Vertical`, `Full`) to detect horizon tilt and vertical convergence automatically,
So that crooked horizons and leaning buildings straighten in one click.

**Acceptance Criteria:**

**Given** a synthetic image with a 6-degree tilted horizon and converging vertical lines
**When** `compute_upright(pixels, mode)` runs for `Level`, `Vertical`, `Full`, and `Auto`
**Then** `Level` sets `CropAngle` to counteract the tilt, `Vertical` sets `TransformVertical`, `Full` sets both, and `Off` resets upright keys to `0`

**Cost-Effective Implementation Blueprint:**
- Target module: `src/develop/auto_upright.py`
- Key functions (≤10 lines each): `detect_horizon_angle(gray) -> int`, `detect_vertical_tilt(gray) -> int`, `compute_upright(pixels, mode) -> dict[str, str]`
- Unit test file: `tests/test_auto_upright.py` (≥95% coverage)

### Story 25.3: Auto Lens Profile matching and Chromatic Aberration correction

As a Photographer,
I want DarkLab to match EXIF camera/lens metadata to lens correction parameters and automatically estimate lateral chromatic aberration,
So that lens distortion, peripheral vignette, and color fringing are corrected automatically.

**Acceptance Criteria:**

**Given** EXIF metadata and an image with red/blue edge fringing
**When** `compute_auto_lens(exif, pixels)` runs
**Then** it returns `RemoveCA = "1"`, matched lens profile name (or `"Manual — no matching profile"`), and calculated `LensDistortion` and `LensVignetting` values

**Cost-Effective Implementation Blueprint:**
- Target module: `src/develop/auto_lens.py`
- Unit test file: `tests/test_auto_lens.py` (≥95% coverage)

### Story 25.4: Develop, Quick Develop, and Import Auto-Correction UI integration

As a Photographer,
I want an `Auto` button in the Develop Basic panel, `Auto Tone` / `Auto WB` buttons in Library Quick Develop, and an optional `Apply Auto Tone on Import` checkbox,
So that automatic corrections are accessible at every stage of my workflow and record a single History Step.

**Acceptance Criteria:**

**Given** a Photo in Develop or Library
**When** the Photographer clicks `Auto`
**Then** Auto Tone, Auto WB, and (if enabled) Auto Presence update `develop_settings`, refresh the Preview/Histogram, and record one `"Auto Tone"` History Step

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/ui/develop_sections.py`, `src/ui/panels/develop_panel.py`, `src/ui/panels/library_browser_panel.py`
- Unit test file: `tests/test_auto_correction_ui.py` (≥95% coverage)

## Epic 26: AI Image Correction and Enhancement Suite

Feature PRD: `https://github.com/fgalyasz/DarkLab/blob/main/_bmad-output/planning-artifacts/prds/prd-DarkLab-ai-image-corrections/prd.md` (`FR-99`–`FR-104`, `ADR-13`, `ADR-16`)

A Photographer can apply local-first AI scene corrections, semantic masks, portrait retouching, AI denoise/deblur, automatic dust/blemish healing, and adaptive presets without touching Originals or requiring cloud uploads.

### Story 26.1: Local AI model registry and Semantic Masking (`Subject`, `Sky`, `Background`, `People-Parts`)

As a Photographer,
I want to generate editable AI semantic masks for `Subject`, `Sky`, `Background`, and `People` parts (`Facial Skin`, `Body Skin`, `Eyes`, `Teeth`, `Lips`, `Hair`, `Clothes`) offline,
So that local adjustments target semantic regions automatically.

**Acceptance Criteria:**

**Given** a portrait or landscape Photo
**When** `generate_semantic_mask(pixels, kind)` runs offline
**Then** it returns a normalized `0.0..1.0` alpha mask encoded into `Masks` in `develop_settings`
**And** `Background` equals the inverse of `Subject`
**And** Original bytes remain unchanged

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/ai/model_registry.py`, `src/ai/semantic_masks.py`
- Unit test file: `tests/test_ai_semantic_masks.py` (≥95% coverage)

### Story 26.2: AI Scene-Aware Auto-Develop and Subject Relight

As a Photographer,
I want `AI Auto-Develop` and `AI Relight` to classify the scene (`Portrait`, `Wedding`, `Landscape`, `Backlit`, `Night`, `Indoor`) and balance subject exposure against the background/sky,
So that backlit or tricky lighting scenes are corrected intelligently in one step.

**Acceptance Criteria:**

**Given** a backlit portrait where the subject is dark against a bright background
**When** `compute_ai_auto_develop(pixels, exif, strength=80)` runs
**Then** `AISceneType` is `"Backlit"` (or `"Portrait"`), global highlights are recovered, and a Subject mask lifts subject exposure/shadows as one `"AI Auto-Develop"` History Step

**Cost-Effective Implementation Blueprint:**
- Target module: `src/ai/scene_corrector.py`
- Unit test file: `tests/test_ai_scene_corrector.py` (≥95% coverage)

### Story 26.3: AI Portrait Retouch (Skin Smoothing, Eye Enhancer, Dark Circles, Teeth Whitening)

As a Photographer,
I want non-destructive AI portrait retouch controls (`AISkinSmooth`, `AISkinTexturePreserve`, `AIEyeClarity`, `AIEyeBrighten`, `AIDarkCircles`, `AITeethWhiten`, `AILipEnhance`),
So that portraits get natural, texture-preserving skin and eye enhancement inside Develop.

**Acceptance Criteria:**

**Given** a portrait Photo with `AISkinSmooth = 60` and `AIEyeClarity = 50`
**When** `apply_portrait_retouch` runs in the render pipeline
**Then** low-frequency skin blotches smooth out while high-frequency pore/hair detail is preserved according to `AISkinTexturePreserve`, and eye/teeth adjustments stay strictly inside their facial region masks

**Cost-Effective Implementation Blueprint:**
- Target module: `src/ai/portrait_retouch.py`
- Unit test file: `tests/test_ai_portrait_retouch.py` (≥95% coverage)

### Story 26.4: AI Denoise, AI Sharpen/Deblur Assist, and Sensor Dust/Blemish Auto-Heal

As a Photographer,
I want `AI Denoise`, `AI Sharpen / Deblur`, and one-click `Auto-Detect Dust & Spots`,
So that noisy high-ISO shots, slight softness, and sensor dust spots in skies are cleaned non-destructively.

**Acceptance Criteria:**

**Given** a noisy image with simulated sensor dust spots in the sky
**When** `apply_ai_denoise_sharpen` and `detect_dust_and_blemishes` run
**Then** chroma/luma noise drops while edges stay crisp, and detected dust spots are returned as editable `HealStroke` entries with clean source patch coordinates

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/ai/denoise_sharpen.py`, `src/ai/spot_detector.py`
- Unit test file: `tests/test_ai_denoise_and_spots.py` (≥95% coverage)

### Story 26.5: AI Adaptive Presets and Develop AI UI panels

As a Photographer,
I want built-in AI Adaptive Presets (`Adaptive: Portrait Pop`, `Adaptive: Sky Drama`, `Adaptive: Subject Warmth`, `Adaptive: Golden Hour`, `Adaptive: Clean Studio Skin`, `Adaptive: High-ISO Rescue`) and an `AI Corrections & Retouch` collapsible section in Develop,
So that applying an Adaptive Preset computes fresh masks per Photo and scales with the `Amount` slider.

**Acceptance Criteria:**

**Given** two different Photos and `Adaptive: Sky Drama` applied at `Amount = 120%`
**When** the preset is applied to each Photo
**Then** each Photo gets its own freshly segmented Sky mask and scaled tone adjustments as one History Step

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/ai/adaptive_presets.py`, `src/ui/develop_sections.py`, `src/ui/panels/develop_panel.py`
- Unit test file: `tests/test_ai_adaptive_presets.py` (≥95% coverage)

## Epic 27: Configurable Auto-Crop and Smart Framing

Feature PRD: `https://github.com/fgalyasz/DarkLab/blob/main/_bmad-output/planning-artifacts/prds/prd-DarkLab-configurable-auto-crop/prd.md` (`FR-105`–`FR-109`, `ADR-14`, `ADR-16`)

A Photographer can automatically crop Photos based on configurable aspect ratios, composition rules (Rule of Thirds, Golden Ratio, Center, Portrait Headroom, Horizon Split), subject/face margins, and straighten constraints.

### Story 27.1: Auto-Crop configuration model, aspect ratios, and presets

As a Photographer,
I want to configure Auto-Crop settings (aspect ratio, composition rule, headroom %, padding %, look-room bias, auto-level horizon, never-cut-faces) and choose from built-in or saved presets,
So that my framing preferences are reusable across shoots.

**Acceptance Criteria:**

**Given** an `AutoCropConfig` saved to the Catalog's `settings.json` (`auto_crop` key)
**When** it is loaded back
**Then** all fields round-trip accurately and `parse_aspect_ratio` resolves `"Original"`, `"4:5"`, `"1:1"`, `"3:2"`, `"16:9"`, and custom `"W:H"` ratios

**Cost-Effective Implementation Blueprint:**
- Target module: `src/develop/auto_crop_config.py`
- Unit test file: `tests/test_auto_crop_config.py` (≥95% coverage)

### Story 27.2: Subject, Face, Eye-Line, Gaze, and Saliency Anchor Detector

As a Photographer,
I want DarkLab to detect face boxes, eye-line midpoints, gaze direction, multi-person group bounds, and visual saliency anchors,
So that Auto-Crop knows where the subject and eyes are located in the frame.

**Acceptance Criteria:**

**Given** a portrait image and a non-portrait object image
**When** `detect_subject_anchor(pixels)` runs
**Then** it returns a `SubjectAnchor` with valid `bbox`, `focal_point`, `head_top_y`, `gaze_dir_x`, `face_boxes`, and `horizon_angle`

**Cost-Effective Implementation Blueprint:**
- Target module: `src/develop/auto_crop_anchors.py`
- Unit test file: `tests/test_auto_crop_anchors.py` (≥95% coverage)

### Story 27.3: Composition-Rule, Group-Safe, and Straighten-Constrained Crop Solver

As a Photographer,
I want a deterministic geometry solver that turns `SubjectAnchor` and `AutoCropConfig` into `CropSettings` inside the rotated image's valid inscribed area without cutting through any detected face,
So that Auto-Crop produces clean, rule-aligned framing with zero black rotation corners.

**Acceptance Criteria:**

**Given** image dimensions, a `SubjectAnchor` with two faces, `angle = 5`, `aspect_ratio = "4:5"`, and `composition_rule = "rule_of_thirds"`
**When** `solve_auto_crop` runs
**Then** the returned `CropSettings` lies strictly within the 5-degree rotated inscribed rectangle, encompasses both faces (`never_cut_faces=True`), matches the `4:5` aspect ratio, and places the focal anchor near the upper-third line

**Cost-Effective Implementation Blueprint:**
- Target module: `src/develop/auto_crop_solver.py`
- Unit test file: `tests/test_auto_crop_solver.py` (≥95% coverage)

### Story 27.4: Develop Crop panel Auto-Crop controls and History integration

As a Photographer,
I want an `Auto Crop` button and configuration controls (`Preset`, `Aspect Ratio`, `Rule`, `Headroom %`, `Padding %`, `Auto-Level`) inside the Develop `Crop` section,
So that one click frames the current Photo and records an `"Auto Crop"` History Step.

**Acceptance Criteria:**

**Given** a Photo in Develop
**When** the Photographer selects an Auto-Crop preset/rule and clicks `Auto Crop`
**Then** `CropLeft`, `CropTop`, `CropRight`, `CropBottom`, `CropAngle`, and `CropAspectLock` update immediately in the UI, Preview, Catalog, and History

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/ui/develop_sections.py`, `src/ui/crop_binding.py`, `src/ui/panels/develop_panel.py`
- Unit test file: `tests/test_auto_crop_ui.py` (≥95% coverage)

## Epic 28: Multi-Photo Batch Image Manipulation and Sync

Feature PRD: `https://github.com/fgalyasz/DarkLab/blob/main/_bmad-output/planning-artifacts/prds/prd-DarkLab-multi-photo-manipulation/prd.md` (`FR-110`–`FR-115`, `ADR-15`, `ADR-16`)

A Photographer can apply and synchronize Develop adjustments, relative Quick Develop steps, Match Total Exposure, Auto-Corrections, AI Enhancements, and Configurable Auto-Crop across multiple selected Photos in Library and Develop.

### Story 28.1: Multi-Photo selection (`Primary` + `Secondary`) in Filmstrip and Library Grid

As a Photographer,
I want `Cmd/Ctrl+Click`, `Shift+Click`, and `Cmd/Ctrl+A` multi-selection in both `GridImageWidget` and `FilmstripWidget` with a distinct Primary (most-selected) Photo,
So that I can target a set of Photos in Library or Develop.

**Acceptance Criteria:**

**Given** 6 Photos in `GridImageWidget` or `FilmstripWidget`
**When** the Photographer `Shift+Clicks` a range of 4 Photos and `Ctrl/Cmd+Clicks` a 5th
**Then** `selected_paths()` returns all 5 paths in order, `primary_path()` returns the active primary Photo, and switching from Library to Develop keeps the same multi-selection

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/ui/widgets/grid_image_widget.py`, `src/ui/widgets/filmstrip_widget.py`, `src/ui/main_window.py`
- Unit test file: `tests/test_multi_selection.py` (≥95% coverage)

### Story 28.2: Selective `Sync...` dialog, `Copy...`/`Paste` groups, and live `Auto-Sync` mode

As a Photographer,
I want a `Sync...` dialog to choose which of the 14 Develop setting groups to copy from the Primary Photo to all selected Photos, plus a live `Auto-Sync` toggle in Develop,
So that I can synchronize white balance and color grading across 30 shots without overwriting their individual crops.

**Acceptance Criteria:**

**Given** Primary Photo 1 (`Exposure = 40`, `CropLeft = 15`) and Secondary Photos 2 and 3 (`Exposure = 0`, `CropLeft = 5`)
**When** `sync_settings_to_photos` runs with `Basic Tone` checked and `Crop` unchecked
**Then** Photos 2 and 3 have `Exposure = "40"` and keep `CropLeft = "5"`, each gaining one `"Sync Settings"` History Step
**And** when `Auto-Sync` is checked in Develop, moving a slider on Photo 1 updates only that changed key across Photos 2 and 3 immediately

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/develop/sync_groups.py`, `src/ui/dialogs/sync_settings_dialog.py`, `src/ui/panels/develop_panel.py`
- Unit test file: `tests/test_sync_settings.py` (≥95% coverage)

### Story 28.3: Relative (Delta) and Absolute Multi-Photo Quick Develop and Match Total Exposure

As a Photographer,
I want Library `Quick Develop` to apply relative (`Δ`) or absolute adjustments across all selected Photos, and `Match Total Exposure` to normalize brightness across a sequence to match the Primary Photo,
So that multi-photo tonal adjustments preserve each frame's relative offset or equalize uneven lighting.

**Acceptance Criteria:**

**Given** Photo 1 (`Exposure = 10`) and Photo 2 (`Exposure = -20`) selected in Library
**When** `apply_relative_delta` applies `{"Exposure": 25}`
**Then** Photo 1 becomes `35` and Photo 2 becomes `5`, each with a `"Quick Develop"` History Step
**And** when `match_total_exposure` runs on a sequence with differing brightness, each secondary Photo's `Exposure` is adjusted to match the Primary Photo's target luminance

**Cost-Effective Implementation Blueprint:**
- Target module: `src/develop/batch_adjust.py`
- Unit test file: `tests/test_batch_adjust.py` (≥95% coverage)

### Story 28.4: Per-Photo computed Batch Processor (Batch Auto Tone, Auto WB, Auto Upright, Auto-Crop, and AI Corrections)

As a Photographer,
I want to run `Batch Auto Tone`, `Batch Auto WB`, `Batch Auto Upright`, `Batch Auto-Crop`, `Batch AI Auto-Develop`, `Batch AI Denoise`, or `Batch Adaptive Preset` across N selected Photos so each Photo is analyzed individually off the UI thread,
So that batch automation adapts to each frame's own subject, horizon, and histogram.

**Acceptance Criteria:**

**Given** 3 selected Photos with different subject positions and brightness, plus 1 Photo with a missing Original
**When** `run_batch_photo_operation` executes `Batch Auto-Crop` or `Batch Auto Tone`
**Then** each of the 3 present Photos receives its own individually computed settings and History Step, the 1 missing Original is skipped and named in `BatchResult.skipped`, and Original hashes are unchanged

**Cost-Effective Implementation Blueprint:**
- Target module: `src/develop/batch_processor.py`
- Unit test file: `tests/test_batch_processor.py` (≥95% coverage)

### Story 28.5: Library and Develop Batch Manipulation UI, Progress, and Context Menus

As a Photographer,
I want toolbar and context-menu actions in Library and Develop for `Sync...`, `Auto-Sync`, `Match Total Exposure`, `Batch Auto Tone`, `Batch Auto-Crop`, and `Batch AI Enhance` with a non-blocking progress/cancel bar,
So that all multi-photo operations are one click away in both modules.

**Acceptance Criteria:**

**Given** multiple Photos selected in `LibraryBrowserPanel` or `DevelopPanel`
**When** the Photographer triggers any batch action
**Then** the batch runs via `batch_processor.py`, updates thumbnails/previews upon completion, and shows a completion summary

**Cost-Effective Implementation Blueprint:**
- Target modules: `src/ui/panels/library_browser_panel.py`, `src/ui/panels/develop_panel.py`
- Unit test file: `tests/test_multi_photo_ui.py` (≥95% coverage)

