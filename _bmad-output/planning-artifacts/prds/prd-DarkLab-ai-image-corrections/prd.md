---
title: DarkLab AI Image Correction and Enhancement Suite
status: final
created: 2026-11-11
updated: 2026-11-11
extends: prd-DarkLab-2026-10-10
epic: 26
parent_issue: 122
story_issues: [123, 124, 125, 126, 127]
---

# PRD: AI Image Correction and Enhancement Suite

## 0. Document Purpose

This PRD adds FR-99 through FR-104 and expands Epic 17 (`AI assist (local-first)`). It specifies DarkLab's local-first AI image correction and enhancement features: **AI Scene-Aware Auto-Develop & Relight**, **AI Semantic Masks (Subject, Sky, Background, People-parts)**, **AI Portrait Retouch (Skin, Eyes, Teeth, Dark Circles)**, **AI Denoise & Sharpen/Deblur Assist**, **AI Sensor Dust & Blemish Auto-Heal**, and **AI Adaptive Presets**. All AI features run locally by default (`ADR-8`), never alter Original bytes (`ADR-3`), and produce editable non-destructive Develop Settings, Masks, and Heal strokes.

## 1. Vision

Photographers want the speed of modern AI photo enhancers without sacrificing Lightroom Classic's non-destructive slider/mask control or uploading client wedding photos to a cloud server. DarkLab's AI corrections run on-device, classify the scene and subjects, and translate every AI enhancement into inspectable, editable Develop Settings, semantic Masks, and local adjustments that render identically in Preview and Export.

## 2. Features

### 2.1 AI Scene-Aware Auto-Develop, Relight, and Semantic Masking

#### FR-99: AI Scene-Aware Auto-Develop and Subject Relight

When the Photographer invokes `AI Auto-Develop` or `AI Relight`, DarkLab classifies the scene (`Portrait`, `Group / Wedding`, `Landscape`, `Architecture`, `Night / Low-Light`, `Backlit / High-Dynamic-Range`, `Indoor Event`) and applies scene-calibrated global tone/color adjustments plus an automatic Subject vs. Background relight balance.

**Consequences (testable):**
- For a backlit portrait, `AI Auto-Develop` lifts subject exposure/shadows via a Subject mask while recovering background/sky highlights.
- The detected scene label (`AISceneType`) and strength (`AIAutoStrength`, `0..100`) are stored in `develop_settings` and recorded as one `"AI Auto-Develop"` History Step.
- Works 100% offline using the local inference adapter (`src/ai/scene_corrector.py`).

#### FR-100: AI Semantic Masking (Subject, Sky, Background, and People-Parts)

In the Develop Mask panel, the Photographer can generate AI masks for `Subject`, `Sky`, `Background`, and `People` parts (`Facial Skin`, `Body Skin`, `Eyes / Iris`, `Eyebrows`, `Lips`, `Teeth`, `Hair`, `Clothes`).

**Consequences (testable):**
- Each AI mask produces an editable soft-feathered alpha mask (`Masks` entry in `develop_settings`) that can be refined with Add/Subtract Brush or Range intersections and inverted or deleted.
- Deleting the mask removes its effect cleanly; Original files remain unchanged.

### 2.2 AI Portrait Retouch, AI Denoise/Sharpen, AI Dust Auto-Heal, and Adaptive Presets

#### FR-101: AI Portrait Retouch (Skin Smoothing, Eye Enhancer, Teeth Whitening)

The Develop `AI Retouch` section provides dedicated portrait sliders (`AISkinSmooth`, `AISkinTexturePreserve`, `AIEyeClarity`, `AIEyeBrighten`, `AIDarkCircles`, `AITeethWhiten`, `AILipEnhance`) scoped automatically to detected facial regions.

**Consequences (testable):**
- `AISkinSmooth` uses frequency-separation / edge-preserving smoothing on facial skin masks so pores and fine hair texture are preserved rather than plastic-blurred.
- `AIEyeClarity` and `AITeethWhiten` adjust local clarity, exposure, and yellow-cast desaturation strictly inside eye/sclera/iris and teeth masks.
- If no face is present on the Photo, the panel states `"No face detected"` and leaves pixels unchanged.

#### FR-102: AI Denoise and AI Sharpen / Motion Deblur Assist

The `Detail` panel includes `AI Denoise` (`AIDenoiseAmount` `0..100`) and `AI Sharpen / Deblur` (`AISharpenAmount` `0..100`, mode `Lens | Motion | Smart`), which analyze EXIF ISO and local noise/blur kernels to compute optimal edge-preserving luminance/chroma denoise and deconvolution sharpening.

**Consequences (testable):**
- High-ISO frames receive chroma speck removal and structure-preserving luma smoothing without destroying fine eyelashes or fabric edges.
- Both Preview (including 1:1 view) and Export execute the same `src/ai/denoise_sharpen.py` pass in the canonical render pipeline.

#### FR-103: AI Sensor Dust and Blemish Auto-Heal

Clicking `Auto-Detect Dust & Spots` in the Spot/Healing tool scans uniform sky/backdrop regions for sensor dust spots and facial skin regions for transient blemishes, generating editable non-destructive `HealStrokes`.

**Consequences (testable):**
- Each detected spot is added as a standard `HealStroke` with an automatically matched clean source patch.
- The Photographer can delete any individual auto-generated stroke or clear all auto-strokes in one click.

#### FR-104: AI Adaptive Presets with Amount Scaling

DarkLab ships built-in AI Adaptive Presets (`Adaptive: Portrait Pop`, `Adaptive: Sky Drama`, `Adaptive: Subject Warmth`, `Adaptive: Golden Hour`, `Adaptive: Clean Studio Skin`, `Adaptive: High-ISO Rescue`) that compute fresh semantic masks on the target Photo and apply preset local + global adjustments scaled by the `PresetAmount` slider (`0..200%`).

**Consequences (testable):**
- Applying an Adaptive Preset on Photo A and Photo B computes Photo-specific masks for A and B rather than copying static mask pixel coordinates from A to B.
- Applying an Adaptive Preset records a single History Step.

## 3. Non-Goals

- Cloud-mandatory generative fill or text-to-image synthesis that invents objects not present in the Original photograph.

## 4. Open Questions

None.
