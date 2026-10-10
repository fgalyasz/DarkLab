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
