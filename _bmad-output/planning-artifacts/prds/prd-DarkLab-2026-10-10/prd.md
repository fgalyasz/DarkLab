---
title: DarkLab
status: final
created: 2026-10-10
updated: 2026-10-10
---

# PRD: DarkLab

## 0. Document Purpose

This PRD is the requirements source for DarkLab's product, UX, architecture, and epics. It builds on the brief at `_bmad-output/planning-artifacts/briefs/brief-DarkLab-2026-10-10/brief.md`. Technical mechanism, rejected alternatives, and the Classic panel inventory live in `addendum.md`. Glossary terms are used verbatim. Functional requirements use stable `FR-` ids. Inferences are tagged `[ASSUMPTION]` and indexed in section 9.

## 1. Vision

DarkLab is a free, open-source, local-first desktop application that lets a photographer finish work the way Lightroom Classic taught them to finish it. They import a shoot into a Catalog, cull in Library, correct in Develop, and hand the result out through Export, Print, Book, Slideshow, or Web. Map holds location. The seven Modules stay in that Classic order because the order is the product.

What DarkLab sells is that sequence without a subscription and without an account. Originals stay files on disk. Develop Settings are instructions. Export writes a new file.

DarkLab does not promise to be Adobe. It will not read a Lightroom catalog, ship Adobe profiles, or treat a pixel match to Classic as the definition of done. A photographer who needs Adobe's rendering still needs Adobe. A photographer who needs Adobe's workflow on their own disk is who this is for.

## 2. Target User

### 2.1 Jobs To Be Done

- Bring a card or a folder in, know what was copied, and trust that the camera files are still the camera files.
- Cull a shoot with ratings, flags, labels, and filters without developing every frame first.
- Correct a selected Photo non-destructively and see the same correction after a restart.
- Deliver JPEGs, a print, a book PDF, a slideshow, or a static gallery from the same Catalog.
- Find a Photo later by folder, collection, keyword, or place.

### 2.2 Non-Users (v1)

- A studio that needs two people in the same Catalog at the same time.
- A photographer whose delivery requirement is an Adobe catalog or Adobe's camera profiles.
- Someone who wants a phone or browser editor as the primary surface.

### 2.3 Key User Journeys

- **UJ-1. Anna imports the wedding card before she sleeps.**
  - **Persona + context:** Anna, a solo wedding photographer, is back at the laptop with one card and a client delivery tomorrow.
  - **Entry state:** DarkLab is open on a Catalog she already uses. She has not signed in, because there is no account.
  - **Path:** She chooses Import, points at the card, leaves Copy selected, sees the photo count and size, and confirms. Duplicates from an earlier partial copy are listed before anything is written.
  - **Climax:** The Library grid shows the new shoot, and the card files are still intact.
  - **Resolution:** She is in Library on the imported folder, ready to cull.
  - **Edge case:** If a destination disk is short on space, Import stops before copying and tells her how many Photos did not land. Nothing half-written is presented as a successful Import.

- **UJ-2. Anna culls to the selects.**
  - **Persona + context:** Same night, same Catalog, about two hundred frames.
  - **Entry state:** Library, imported folder.
  - **Path:** She moves through loupe, sets a Flag and a Rating, filters to the flagged Photos, and rejects the rest.
  - **Climax:** The filter shows only the Photos she intends to deliver.
  - **Resolution:** The selection is still there after she quits and reopens.
  - **Edge case:** A Photo whose Original is missing shows as missing and can be relinked. It does not silently disappear from the count.

- **UJ-3. Anna corrects the selects.**
  - **Persona + context:** She has a filtered set and a consistent white balance from the venue.
  - **Entry state:** A Photo open in Develop.
  - **Path:** She sets white balance and basic tone, crops, checks the histogram, and steps back through History when a move is wrong.
  - **Climax:** The Preview matches the correction she wants, and Reset returns to the imported look.
  - **Resolution:** She leaves Develop. The next open shows the same Develop Settings.
  - **Edge case:** Pasting Develop Settings onto a Photo does not change that Photo's Original bytes.

- **UJ-4. Anna exports the client JPEGs.**
  - **Persona + context:** Delivery is sRGB JPEGs at a long edge she always uses.
  - **Entry state:** Filtered selects in Library.
  - **Path:** She exports with a saved preset, watches progress, and opens the destination folder.
  - **Climax:** The folder contains one rendered file per selected Photo, and a hash of each Original matches the pre-export hash.
  - **Resolution:** She can export again without creating a second Catalog entry for the JPEG unless she imports it on purpose.

- **UJ-5. Anna drops the reception set on the Map.**
  - Anna, later in the week, opens Map, sees Photos that already have GPS, and drags the rest onto the venue. The Library filter can then use that place.

- **UJ-6. Anna prints a contact sheet for the couple.**
  - Anna opens Print on a Collection, picks a contact-sheet layout, and writes a JPEG of the pages. The Originals are unchanged.

## 3. Glossary

- **Photographer** — The person using DarkLab. One person per Catalog session.
- **Catalog** — The local database of Photos, organization, and Develop Settings. One Catalog is one SQLite file plus its preview cache and backups.
- **Photo** — A Catalog record that points at one Original and holds Develop Settings, Metadata, and organization. A Photo is not the file.
- **Original** — The image file on disk that a Photo references. Develop and Export do not write pixels into it.
- **Develop Settings** — The non-destructive instruction set for one Photo or Virtual Copy.
- **Preview** — A generated image of a Photo with Develop Settings applied. Previews are a cache.
- **Module** — A top-level work surface. The Modules are Library, Develop, Map, Book, Slideshow, Print, and Web.
- **Library** — The Module for browsing, culling, and organizing Photos.
- **Develop** — The Module for editing Develop Settings on one Photo.
- **Map** — The Module for seeing and assigning location.
- **Book** — The Module for a multi-page layout exported as PDF.
- **Slideshow** — The Module for timed playback of a Collection.
- **Print** — The Module for page layouts sent to a printer or a JPEG.
- **Web** — The Module for a static HTML gallery.
- **Import** — The dialog that creates Photos from files on disk. Not a Module.
- **Export** — The action that renders new files from Photos. Not a Module.
- **Folder** — A Catalog view of a directory that contains Originals.
- **Collection** — An ordered set of Photos that does not move Originals.
- **Smart Collection** — A Collection whose membership is a saved filter.
- **Keyword** — A hierarchical word attached to a Photo.
- **Metadata** — EXIF read from the Original, plus IPTC fields the Photographer can edit.
- **Rating** — Zero to five stars on a Photo.
- **Flag** — Pick, reject, or unflagged.
- **Color Label** — One of red, yellow, green, blue, purple, or none.
- **Stack** — A collapse of several Photos under one visible Photo in the grid.
- **Virtual Copy** — A second Photo that shares an Original and has its own Develop Settings.
- **History Step** — One recorded change to Develop Settings, in order, that can be selected again.
- **Snapshot** — A named copy of Develop Settings.
- **Preset** — A named, reusable subset of Develop Settings or of Export options.
- **Mask** — A region that limits which pixels a subset of Develop Settings affects.
- **Sidecar** — An XMP file next to the Original that stores Develop Settings and editable Metadata.

## 4. Features

### 4.1 Catalog

**Description:** The Photographer creates a Catalog, opens it later, and can keep more than one. The Catalog references Originals. It does not become the only copy of those files unless Import copied them. Realizes UJ-1 and UJ-2.

**Functional Requirements:**

#### FR-1: Catalog lifecycle

The Photographer can create a Catalog, open an existing Catalog, and switch Catalogs. Develop Settings and organization from the opened Catalog come back as they were saved.

**Consequences (testable):**
- Creating a Catalog produces one SQLite file the Photographer can copy to another disk.
- Quitting and reopening restores the last Folder, filter, and selected Photo.
- Switching Catalogs does not merge Photos between them.
- Startup choice is FR-48 and FR-49 in `prd-DarkLab-catalog-startup`.

#### FR-2: Original references

A Photo stores the path of its Original and a content hash. A missing Original is shown as missing. The Photographer can relink it to a file with the same hash or confirm a different file.

**Consequences (testable):**
- Deleting the Original outside DarkLab leaves the Photo in the Catalog, marked missing.
- Relinking to the same hash clears the missing state and keeps Develop Settings.
- Relinking to a different file requires an explicit confirmation.

#### FR-3: Catalog backup

The Photographer can write a timestamped backup of the Catalog and restore from one.

**Consequences (testable):**
- Restore replaces the Catalog database and does not delete Originals.
- A failed backup leaves the current Catalog usable.

#### FR-4: Sidecar round-trip

Develop Settings and editable Metadata can be written to a Sidecar and read back. Writing a Sidecar does not change Original pixels.

**Consequences (testable):**
- The Original's hash is unchanged after a Sidecar write.
- Reading the Sidecar on a second Catalog import of the same Original restores those Develop Settings. [ASSUMPTION: Sidecar is XMP, including a DarkLab namespace for settings that have no standard XMP field.]

### 4.2 Import

**Description:** Import creates Photos from a folder or a card. The Photographer sees count and size before the copy starts. Realizes UJ-1.

**Functional Requirements:**

#### FR-5: Add, Copy, and Move

The Photographer can Import by Add (reference files in place), Copy, or Move.

**Consequences (testable):**
- Add does not write a second image file.
- Copy writes new files at the destination and leaves the source in place.
- Move removes a source file only after the destination file exists and its size matches.

#### FR-6: Import organization

During Import the Photographer can set the destination, a rename pattern, Metadata to apply, and Keywords to apply.

**Consequences (testable):**
- The destination and rename pattern are visible before commit.
- Applied Keywords and Metadata are on the new Photos after Import, not only in the dialog.

**Out of Scope:**
- Keyword and Metadata apply on Import ships with FR-16 and FR-17. The first milestone still has destination and rename.

#### FR-7: Pre-commit summary

Import shows how many Photos are selected and how many bytes will be copied before the Photographer commits.

**Consequences (testable):**
- The summary changes when the selection changes.
- Commit is unavailable when the selection is empty.

#### FR-8: Duplicates

Import detects an Original that is already in the Catalog by hash and asks the Photographer to skip it or import it again as another Photo.

**Consequences (testable):**
- The default action is skip.
- Skip does not create a second Photo and does not modify the existing Photo.

### 4.3 Library

**Description:** Library is where a shoot is culled and, later, organized. Realizes UJ-2.

**Functional Requirements:**

#### FR-9: Grid and loupe

The Photographer can browse Photos as a grid and open one Photo in loupe.

**Consequences (testable):**
- Grid order is stable for a chosen sort (capture time, filename, Import time, Rating).
- Loupe shows the same Photo the grid selection has.

#### FR-10: Compare and survey

The Photographer can compare two Photos and survey several.

**Consequences (testable):**
- Compare keeps one candidate and one select.
- Survey removes a Photo from the view without deleting it from the Catalog.

#### FR-11: Folders

Library shows Folders for directories that contain Originals. Selecting a Folder shows its Photos.

**Consequences (testable):**
- A Folder is not a copy of the files.
- Renaming a directory outside DarkLab marks the Folder missing until it is relinked.

#### FR-12: Collections

The Photographer can create Collections and collection sets and can add or remove Photos without moving Originals.

**Consequences (testable):**
- A Photo can be in more than one Collection.
- Removing a Photo from a Collection does not delete the Original or the Photo.

#### FR-13: Smart Collections

The Photographer can save a filter as a Smart Collection. Membership updates when Photo fields change.

**Consequences (testable):**
- Raising a Rating into the rule adds the Photo without a manual drop.
- Editing the rule changes membership.

#### FR-14: Cull marks

The Photographer can set Rating, Flag, and Color Label on a Photo from Library and from Develop.

**Consequences (testable):**
- Marks persist across restart.
- Marks are per Photo, including per Virtual Copy.

#### FR-15: Filter

The Photographer can filter the current source by text, Rating, Flag, Color Label, Keyword, and capture date.

**Consequences (testable):**
- The grid count matches the filter.
- Clearing the filter restores the source count.
- The first milestone filter is text, Rating, Flag, and Color Label. Keyword and date ship with FR-16 and FR-17.

#### FR-16: Keywords

The Photographer can create a Keyword hierarchy and assign Keywords to Photos.

**Consequences (testable):**
- Assigning a child Keyword records the parent path.
- A Keyword filter matches the Photo.

#### FR-17: Metadata

Library shows EXIF from the Original and lets the Photographer edit IPTC fields. Editable fields can be written to the Sidecar.

**Consequences (testable):**
- EXIF from the camera is not overwritten by an IPTC edit.
- A caption entered in Library is the caption Export and Book can read.

#### FR-18: Stacks

The Photographer can stack Photos and expand or collapse the Stack in the grid.

**Consequences (testable):**
- Collapse shows one Photo and a count.
- Unstacking does not delete Photos.

#### FR-19: Virtual Copies

The Photographer can make a Virtual Copy, develop it independently, and delete the copy without deleting the Original.

**Consequences (testable):**
- The copy shares the Original path and hash.
- Changing the copy's Develop Settings does not change the source Photo.

#### FR-20: Quick Develop

From Library the Photographer can apply a limited set of Develop Settings (white balance, exposure, contrast, and a Preset) to the selection.

**Consequences (testable):**
- The change is a History Step on each affected Photo.
- Photos that are missing their Original are skipped and named in the result.

### 4.4 Develop

**Description:** Develop edits one Photo's Develop Settings and shows a Preview. The panel inventory and control ranges live in `addendum.md`. Realizes UJ-3.

**Functional Requirements:**

#### FR-21: Non-destructive edit

Every Develop control writes Develop Settings. None of them writes Original pixels.

**Consequences (testable):**
- The Original hash is identical before and after any Develop control, History navigation, or Reset.
- Reset restores the Develop Settings captured at Import.

#### FR-22: Crop and straighten

The Photographer can crop, rotate, and straighten. The crop is part of Develop Settings.

**Consequences (testable):**
- The Preview is the cropped view.
- Export uses the same crop.
- Aspect-ratio lock is visible and reversible.

#### FR-23: Basic tone and white balance

The Photographer can set white balance (temperature, tint, as-shot, auto) and basic tone: exposure, contrast, highlights, shadows, whites, blacks, texture, clarity, dehaze, vibrance, and saturation.

**Consequences (testable):**
- Moving exposure changes the Preview and the histogram.
- Auto white balance sets temperature and tint from the Original and remains an editable value.
- Values survive restart.

#### FR-24: Tone curve

The Photographer can edit a parametric tone curve and a point curve on the combined channel and on red, green, and blue.

**Consequences (testable):**
- A curve point round-trips through the Catalog and the Sidecar.
- Reset curve clears curve points and leaves basic tone as it was.

#### FR-25: HSL

The Photographer can adjust hue, saturation, and luminance per color band.

**Consequences (testable):**
- A band adjustment changes the Preview.
- Settings round-trip.

#### FR-26: Color grading

The Photographer can grade shadows, midtones, and highlights independently, plus a global grade.

**Consequences (testable):**
- Each region has hue and saturation (and luminance where the Classic control has it).
- Settings round-trip.

#### FR-27: Detail

The Photographer can set sharpening and noise reduction, with a preview that shows the effect at 1:1.

**Consequences (testable):**
- Sharpening is visible at 1:1 and is not only a fit-to-screen approximation.
- Settings round-trip.

#### FR-28: Lens corrections and transform

The Photographer can enable profile lens corrections and manual transform (vertical, horizontal, rotate, aspect, scale, offset).

**Consequences (testable):**
- When no lens profile matches, the panel says so and manual transform still works. [ASSUMPTION: profiles come from Lensfun, not from Adobe's lens-profile package.]
- Settings round-trip.

#### FR-29: Effects and calibration

The Photographer can set vignette and grain, and can adjust calibration primaries.

**Consequences (testable):**
- Settings affect the Preview and Export the same way.
- Settings round-trip.

#### FR-30: Masks

The Photographer can limit a subset of Develop Settings with a Mask: brush, linear gradient, radial gradient, color range, and luminance range. Subject and sky Masks are available when a detector is bundled.

**Consequences (testable):**
- A Mask does not change pixels outside its region beyond the documented falloff.
- Deleting a Mask removes its effect and keeps the global Develop Settings.
- DarkLab runs without a subject or sky detector; those two tools are absent rather than failing silently. [ASSUMPTION: no detector is bundled in the first Develop milestone.]

#### FR-31: Healing

The Photographer can remove a spot with a heal or clone stroke stored in Develop Settings.

**Consequences (testable):**
- A stroke survives restart and Export.
- Deleting the stroke restores the underlying Preview.

#### FR-32: History and versions

The Photographer can walk History Steps, store a Snapshot, compare before and after, and copy or paste Develop Settings between Photos.

**Consequences (testable):**
- Selecting an older History Step restores those Develop Settings.
- Paste appends a History Step on the destination and does not change the source.
- The first milestone requires History and before/after. Snapshots and copy/paste ship in Epic 6 and remain part of FR-32.

#### FR-33: Develop Presets

The Photographer can save, apply, and delete a Develop Preset.

**Consequences (testable):**
- Applying a Preset is one History Step.
- A Preset does not contain the Photo's crop unless the Photographer included crop when saving.

#### FR-34: Histogram

Develop shows a histogram of the current Preview, and the Photographer can see clipping in the Preview.

**Consequences (testable):**
- The histogram updates when basic tone changes.
- Clipping highlight can be turned on and off without changing Develop Settings.

### 4.5 Export

**Description:** Export renders new files. Realizes UJ-4.

**Functional Requirements:**

#### FR-35: Render an Export

The Photographer can Export one or more Photos to JPEG or TIFF at a chosen color space, long edge, and output location.

**Consequences (testable):**
- The output count equals the number of Photos that still have an Original.
- Missing Originals are skipped and listed.
- JPEG and TIFF open in an external viewer and reflect crop and Develop Settings.

#### FR-36: Export Presets

The Photographer can save and reuse Export settings as a Preset.

**Consequences (testable):**
- Re-running a Preset uses the saved format, size, color space, sharpening-for-output, and watermark choice.
- The first milestone includes one built-in JPEG Preset (sRGB, long edge 2048, no watermark).

#### FR-37: Export does not ingest

Export does not modify Originals and does not add the rendered files to the Catalog.

**Consequences (testable):**
- Original hashes match before and after Export.
- Catalog Photo count is unchanged by Export.

### 4.6 Map

**Description:** Map shows Photos that have a location and lets the Photographer assign one. Realizes UJ-5.

**Functional Requirements:**

#### FR-38: Pins

Map shows a pin for each Photo in the current source that has GPS Metadata. Selecting a pin selects the Photo.

**Consequences (testable):**
- A Photo with no GPS does not get a pin.
- The pin count equals the number of Photos in the source with GPS.

#### FR-39: Assign location

The Photographer can drag a Photo onto the map, clear its location, save a named place, and match a tracklog by capture time.

**Consequences (testable):**
- An assigned location is written to the Sidecar as GPS and is visible after restart.
- Clear removes the pin.
- A tracklog match sets coordinates only when the capture time falls inside the track. [ASSUMPTION: the base map is OpenStreetMap-compatible tiles. Import, Library, Develop, and Export do not require the network. Map degrades to an empty state offline.]

### 4.7 Book

**Description:** Book lays out a Collection into pages. Realizes a delivery job, not a store.

**Functional Requirements:**

#### FR-40: Page layout

The Photographer can build a Book from a Collection with page templates, photo frames, and captions taken from Metadata.

**Consequences (testable):**
- Reordering Photos in the Book does not reorder the Collection unless the Photographer asks.
- A caption edit in the Book updates the Photo Metadata.

#### FR-41: Book PDF

The Photographer can Export the Book to a multi-page PDF.

**Consequences (testable):**
- Page count in the PDF matches the Book.
- Original hashes are unchanged.

**Out of Scope:**
- Ordering a printed book from Blurb or any other vendor.

### 4.8 Slideshow

**Functional Requirements:**

#### FR-42: Playback

The Photographer can play a Slideshow from a Collection with per-slide duration, captions, and an optional music file.

**Consequences (testable):**
- Playback advances without user input at the chosen duration.
- Stopping returns to the Slideshow Module with the Collection intact.

#### FR-43: Slideshow video

The Photographer can Export the Slideshow to a video file.

**Consequences (testable):**
- The video duration matches the slide timings within one second.
- Original hashes are unchanged.

### 4.9 Print

**Description:** Realizes UJ-6.

**Functional Requirements:**

#### FR-44: Print layouts

The Photographer can lay out a single image, a contact sheet, or a custom set of cells, with margins and captions.

**Consequences (testable):**
- The on-screen page matches the cell count and margins.
- Draft mode is labeled as draft and is not the only quality.

#### FR-45: Print output

The Photographer can send the layout to a printer or write it to a JPEG.

**Consequences (testable):**
- JPEG output uses the layout, not a single uncropped Original.
- Original hashes are unchanged.

### 4.10 Web

**Functional Requirements:**

#### FR-46: Static gallery

The Photographer can Export a Collection as a folder of HTML, CSS, and images that opens in a browser without a server.

**Consequences (testable):**
- Opening the index file shows every Photo that was in the Collection at export time.
- The gallery does not call DarkLab or an account service.
- Original hashes are unchanged.

### 4.11 People

**Functional Requirements:**

#### FR-47: Face confirmation

The Photographer can review suggested faces, confirm a person, reject a suggestion, and filter Library by person.

**Consequences (testable):**
- A suggestion is not a confirmed person until the Photographer confirms it.
- Rejecting a suggestion keeps it from returning as the same suggestion for that Photo.
- DarkLab's other Modules run if no face detector is installed. [ASSUMPTION: the first shipments do not bundle a face detector.]

## 5. Non-Goals (Explicit)

- Reading or writing a Lightroom `.lrcat` catalog, or converting Adobe develop XML as a compatibility promise.
- Pixel-identical rendering against Lightroom Classic, or shipping Adobe camera profiles, lens profiles, or color lookup tables.
- Lightroom cloud sync, a mobile app, or an account.
- Tethered capture.
- Binary compatibility with Adobe plugins.
- Blurb or other print-vendor checkout inside Book.
- Generative fill, generative remove, or any control that invents pixels the Original did not contain. Healing in FR-31 copies or blends existing pixels.
- Multi-user editing of one Catalog.
- A video editor. Slideshow video export is a rendered sequence of stills.
- Using the Lightroom name or Adobe's icons in the product.

## 6. MVP Scope

The first public milestone is UJ-1 through UJ-4. It is an experience slice: one shoot goes from card to client JPEG.

### 6.1 In Scope

- FR-1, FR-2, FR-3, FR-4
- FR-5, FR-7, FR-8, and the destination plus rename parts of FR-6
- FR-9, FR-11, FR-14
- FR-15 for text, Rating, Flag, and Color Label
- FR-21, FR-22, FR-23, FR-34
- FR-32 for History, Reset, and before/after
- FR-35, FR-36 (one built-in JPEG Preset), FR-37
- The seven Module buttons exist. Map, Book, Slideshow, Print, and Web may be empty states that name the later epic.

### 6.2 Out of Scope for MVP

- FR-10, FR-12, FR-13, FR-16, FR-17, FR-18, FR-19, FR-20 — organization beyond folders and cull marks.
- FR-6 keyword and Metadata apply — waits for FR-16 and FR-17.
- FR-24 through FR-31, FR-33, and the rest of FR-32 — full Develop.
- FR-38 through FR-47 — Map, Book, Slideshow, Print, Web, people.
- Each deferred FR stays in this PRD. It is the product, not a maybe.

## 7. Success Metrics

**Primary**

- **SM-1:** A fixture shoot of 200 mixed RAW and JPEG files completes UJ-1 through UJ-4, and every Original hash is unchanged. Validates FR-4, FR-5, FR-21, FR-35, FR-37.
- **SM-2:** After quit and reopen, Develop Settings and cull marks match the pre-quit Catalog for that fixture. Validates FR-1, FR-14, FR-23.

**Secondary**

- **SM-3:** Five photographers who have used Classic can name which Module they would open to cull, to develop, and to print, with no tour. Validates the Module set. This is a moderated check, not a growth metric.

**Counter-metrics (do not optimize)**

- **SM-C1:** Delta-E or other pixel distance to Lightroom Classic is not a release gate. Counterbalances the temptation to turn SM-1 into an Adobe-matching project.
- **SM-C2:** Account creation, sync, and online-only features are not success. Counterbalances SM-3 if familiarity is ever pursued by cloning the cloud product.

## 8. Open Questions

1. Which XMP library writes the DarkLab namespace without stripping unrelated tags already in a Sidecar? `pyexiv2` is already a dependency. The choice is an implementation detail as long as FR-4's consequences hold.
2. Map tiles: which OSM-compatible provider, and whether a packaged offline style is required for the Map epic. Not a blocker for the MVP.
3. Subject, sky, and face detectors: model license and whether they are optional downloads. FR-30 and FR-47 already allow shipping without them.
4. Compare and survey (FR-10) versus masks (FR-30): both are post-MVP. The epic order in `epics.md` puts organization and full Develop before Map. Revisit only if a photographer study shows culling, not tone, is the adoption wall.

## 9. Assumptions Index

- Section 4.1, FR-4 — Sidecar format is XMP plus a DarkLab namespace.
- Section 4.4, FR-28 — Lens profiles come from Lensfun.
- Section 4.4, FR-30 — No subject or sky detector in the first Develop milestone.
- Section 4.6, FR-39 — Map uses OSM-compatible tiles and is the only MVP-adjacent feature that needs a network. MVP itself does not include Map.
- Section 4.11, FR-47 — No face detector in the first shipments.
- Brief and section 2 — One primary persona, English UI first, MIT license, solo maintainer. [ASSUMPTION: the UI language of the first milestone is English.]
- Section 6 — Empty states for unfinished Modules are acceptable in the first milestone.

## 10. Cross-Cutting NFRs

- **NFR-1:** After a Preview is cached, a basic-tone slider on a 24-megapixel Photo updates that Preview within 100 ms on an Apple M1 or a 2020 Intel laptop with 16 GB of RAM. Validates the Develop loop in FR-23.
- **NFR-2:** Import of 500 JPEGs by Add does not block the UI thread. Progress shows the count completed. Validates FR-5 and FR-7.
- **NFR-3:** Import, Library, Develop, and Export function with the network disabled. Validates the local-first promise. Map may show an offline empty state.
- **NFR-4:** The Catalog database is one SQLite file. Previews are a cache that can be deleted and rebuilt.
- **NFR-5:** The same source builds and runs on macOS, Windows, and Linux. A platform-specific feature is off by default rather than breaking the others.
- **NFR-6:** No account, no telemetry, and no phone-home check is required to Import, edit, or Export.
- **NFR-7:** Text on the dark theme meets a 4.5:1 contrast ratio against its background for body labels.
- **NFR-8:** New domain packages (`src/catalog`, `src/importing`, `src/develop`, `src/exporting`, `src/imaging`) ship at or above 95% line coverage.

## 11. Platform and Information Architecture

DarkLab is a desktop application. [ASSUMPTION: the shell stays PyQt6, which is already the committed UI.] There is no web app and no mobile client in this PRD.

The window has a Module bar with Library, Develop, Map, Book, Slideshow, Print, and Web, in that order. Import is under File and as a shortcut, not as an eighth Module. Export is an action from Library and Develop. The Photographer always has one active Catalog.

A hard block below 1920×1080 is out. The window may warn on a small display. It still opens. The committed `main.py` currently exits below that size; removing that exit is part of making the shell match this section.

## 12. Constraints and Guardrails

- **Privacy:** Photos and the Catalog stay on disk the Photographer chose. No analytics exception.
- **Licensing:** MIT for DarkLab's code. Third-party lens data, map tiles, and optional detectors must be compatible with that distribution. Adobe's proprietary profiles are not bundled.
- **Trademark:** The product name is DarkLab. Documentation may say "Lightroom Classic workflow" in a descriptive sentence. The UI does not use Adobe's marks or icons.
- **Cost:** The first milestone has no paid service and no API key in the default path.

## 13. Risks

- **Render quality.** Photographers may reject a correct workflow because the Preview looks unlike Classic. Mitigation: SM-C1 keeps this from becoming a secret second product, and the brief states the limit in the README so the comparison is honest.
- **Scope.** Forty-seven functional requirements will bury a solo maintainer if the MVP is not enforced. Mitigation: section 6 is the only first milestone, and epics after Export do not start as the default implementation target.
- **Sidecar damage.** A bad XMP write can strip another application's tags. Mitigation: FR-4 is in the first milestone, and a writer that strips an unrelated tag already in the Sidecar fails FR-4. Catalog persistence alone does not satisfy FR-4. Open question 1 is which library passes that test, not whether the test can wait.
