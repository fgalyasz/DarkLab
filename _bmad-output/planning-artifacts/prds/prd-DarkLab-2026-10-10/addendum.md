# Addendum: DarkLab

Depth that the PRD should not carry. The PRD remains the requirements source.

## Rejected alternatives

- **Fork darktable or digiKam.** Those projects already cover raw development and asset management. They also bring a different workflow, which is the problem this product exists to avoid. Contributing upstream would be a different project.
- **Rewrite the shell in Rust, C++, or a web UI before the catalog exists.** The committed application is already a PyQt6 window with an import dialog and a library grid. A new shell would spend the first months on nothing a photographer can cull. A faster imaging core can sit behind `src/imaging` later if NFR-1 fails in Python.
- **Adobe catalog and render compatibility as the promise.** `.lrcat` is undocumented and versioned by Adobe. Pixel match pulls in proprietary profiles and an unbounded color-science project. Both fail the "a stranger can trust the README" test.
- **Cloud sync in the first product.** It adds accounts, conflict, and a service to operate. The brief's user wants the opposite.
- **Blurb inside Book.** A commercial checkout is not an open-source workflow. Book exports PDF.

## Sidecar

XMP next to the Original. Standard fields carry rating, label, IPTC, and GPS. A `darklab` namespace carries Develop Settings that have no standard field, including curve points, masks, and healing strokes. The writer must leave unrelated tags in place. `pyexiv2` is the first library to test because it is already a dependency. If it fails the foreign-tag test, replace the library. Do not replace the requirement.

## Develop panel inventory

These are the Classic controls the later Develop epic has to cover. They are not extra requirements beyond FR-22 through FR-33.

- Crop and straighten: angle, aspect, aspect lock.
- Basic: treatment is color only in the first full Develop pass (black and white is the saturation end of HSL, not a separate mode), temperature, tint, exposure, contrast, highlights, shadows, whites, blacks, texture, clarity, dehaze, vibrance, saturation.
- Tone curve: parametric highlights, lights, darks, shadows; point curve for RGB and for each channel.
- HSL: hue, saturation, luminance for red, orange, yellow, green, aqua, blue, purple, magenta.
- Color grading: shadows, midtones, highlights, global; hue, saturation, luminance; blending and balance.
- Detail: sharpening amount, radius, detail, masking; noise reduction luminance and color with their detail and smoothness controls.
- Lens: enable profile, distortion, vignetting; manual distortion if the profile is missing.
- Transform: upright is out until a reliable line detector exists; manual vertical, horizontal, rotate, aspect, scale, X offset, Y offset are in.
- Effects: post-crop vignette amount, midpoint, roundness, feather, highlights; grain amount, size, roughness.
- Calibration: shadow tint; red, green, and blue hue and saturation.
- Masks: add, invert, duplicate, delete; brush, linear, radial, color range, luminance range; subject and sky only with a bundled detector.
- Healing: heal and clone.

Auto upright, HDR merge, panorama merge, and soft proof are not in the inventory. Soft proof can be a later Print concern. HDR and panorama are out of this PRD.

## Render path

Decode the Original with `rawpy` for RAW and Pillow for other stills. Apply Develop Settings in a fixed order: crop and rotate, white balance, exposure and tone, tone curve, HSL, color grading, detail, lens and transform, effects, calibration, then mask-local versions of the tone controls, then healing. Cache the Preview by Photo id plus a hash of Develop Settings. Export uses the same order. The UI never writes pixels back to the Original.

The committed tree does not implement this path yet. `main` reads images for the library grid and does not own a develop pipeline.

## Code map on main

- `main.py` starts the Qt application and currently refuses displays under 1920×1080. The PRD removes that refusal.
- `src/ui/main_window.py` hosts the panels that exist on `main`.
- `src/ui/dialogs/import_dialog.py` plus destination, rename, and IPTC preset dialogs are the Import shell.
- `src/ui/panels/library_browser_panel.py` is the grid.
- Develop, Print, Slideshow, and Web panels on `main` are not the Develop or output requirements. Treat them as replaceable shells.
- New domain code goes in `src/catalog`, `src/importing`, `src/develop`, `src/exporting`, and `src/imaging`, as the architecture document says.

## Map, lenses, faces

- Map tiles are an OSM-compatible HTTPS source chosen in the Map epic. No key in the default developer path unless the provider forces one.
- Lens profiles are Lensfun.
- Face, subject, and sky detectors are optional and unbundled until their license is compatible with MIT distribution of the app. The Modules must run without them.
