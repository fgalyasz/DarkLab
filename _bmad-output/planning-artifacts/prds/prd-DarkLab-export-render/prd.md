---
title: DarkLab Export renders JPEG and TIFF
status: final
created: 2026-10-30
updated: 2026-10-30
extends: prd-DarkLab-2026-10-10
parent_issue: 17
story_issue: 18
---

# PRD: Export renders JPEG and TIFF

## 0. Document Purpose

This PRD adds FR-66 through FR-69. It realizes FR-35, FR-36, and FR-37 for the first milestone and the empty state of story 19.3. It replaces the Library "Export..." button that copied index images.

## 1. Vision

The Photographer selects the keepers, picks a Preset, and gets files in a folder that look like the Develop Preview. The Originals and the Catalog stay as they were.

## 2. Features

### 2.1 Render

#### FR-66: Export renders selected Photos

Export renders each selected Photo from its Original with its stored crop and tone, at the Preset's format and long edge, into the chosen folder.

**Consequences (testable):**
- The output count equals the number of selected Photos that still have an Original.
- A Photo whose Original is missing is skipped and named in the result. A Photo that fails to render is named with the reason, and the others still export.
- The file is JPEG or TIFF as the Preset says, sRGB, and its long edge is the Preset's long edge. A long edge of 0 keeps the full size.
- The crop and Exposure and Contrast stored for the Photo are in the file, using the same geometry and tone function as the Preview.
- Two Photos with the same file name get different output names. Existing files are not overwritten.

### 2.2 Presets

#### FR-67: Built-in and saved Presets

**Consequences (testable):**
- The built-in Preset is JPEG, sRGB, long edge 2048, no sharpening, no watermark.
- A saved Preset keeps its name, format, long edge, color space, output sharpening, and watermark text, and Export follows those values after a restart.
- Saving under the built-in name is refused. Saving under an existing saved name replaces it.
- sRGB is the only color space in this milestone. A stored Preset naming another color space is ignored.

### 2.3 Not ingesting

#### FR-68: Export leaves the Catalog and Originals alone

**Consequences (testable):**
- Original hashes and the Catalog Photo count are the same before and after Export.
- Rendered files are not added to the Catalog.

### 2.4 Honest empty state

#### FR-69: Export says why it cannot run

**Consequences (testable):**
- The Export dialog disables its commit button and shows a plain reason when no Photo is selected, when no selected Photo has an Original, or when no folder is chosen.
- When some selected Photos have no Original, the dialog says how many will be skipped.

## 3. Non-Goals

- Color spaces other than sRGB, which need bundled ICC profiles.
- Writing metadata, IPTC, or keywords into the output.
- Export of white balance, highlights, shadows, whites, blacks, and the other Develop controls whose Preview is not implemented yet.
- Adding the rendered files to the Catalog (FR-37 forbids it).

## 4. Open Questions

None for this change.
