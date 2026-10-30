---
title: DarkLab crop and straighten
status: final
created: 2026-10-30
updated: 2026-10-30
extends: prd-DarkLab-2026-10-10
parent_issue: 12
story_issue: 14
---

# PRD: Crop and straighten

## 0. Document Purpose

This PRD adds FR-64 and FR-65. It realizes FR-22 for the first milestone: a crop and a straighten angle live in the Photo's Develop Settings, show in the Preview, and are the geometry Export uses.

## 1. Vision

A Photographer frames a shot once in Develop. The same frame is what the Preview shows, what the Catalog remembers, and what Export renders.

## 2. Features

### 2.1 Crop and straighten as Develop Settings

#### FR-64: Crop is stored with the Photo

The Crop section of Develop has Left, Top, Right, and Bottom (percent of that side trimmed), Angle (whole degrees, straighten), and an Aspect lock.

**Consequences (testable):**
- Changing a crop control writes `CropLeft`, `CropTop`, `CropRight`, `CropBottom`, `CropAngle`, and `CropAspectLock` to the Photo's Develop Settings. An empty crop stores zeros and an unlocked lock, never a missing key.
- Showing the Photo in Develop after a restart sets every crop control to its stored value. A stored value that is not a whole number is ignored and the default is shown.
- With the Aspect lock on, a crop edge change keeps the cropped area at the aspect ratio of the Original. Turning the lock off keeps the latest crop and shows the lock as off.
- Reset returns every crop control to the empty crop and the lock to off.
- The Preview is the cropped view. The Original file and its content hash are unchanged.

#### FR-65: Crop geometry is shared

One function turns an image size and a crop into a pixel box on the rotated canvas. Preview and Export both call it.

**Consequences (testable):**
- An empty crop returns the full image.
- A crop never returns a box narrower or shorter than one pixel.
- A non-zero Angle rotates the image about its centre and grows the canvas to hold the whole rotated image before the box applies.

## 3. Non-Goals

- A draggable crop overlay on the Preview.
- Fixed ratio presets such as 3:2 or 16:9. The lock keeps the Original ratio only.
- Filling the corners that straightening exposes. They stay black unless the crop trims them.
- Perspective Transform, which stays in the Transform section.

## 4. Open Questions

None for this change.
