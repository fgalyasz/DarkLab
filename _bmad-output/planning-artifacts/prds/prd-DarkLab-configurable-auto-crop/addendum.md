# Addendum: Configurable Auto-Crop and Smart Framing

## 1. Architecture & Package Placement

- `src/develop/auto_crop_config.py` — `AutoCropConfig` dataclass, aspect-ratio parser (`parse_aspect_ratio`), built-in presets, and Catalog `settings.json` persistence.
- `src/develop/auto_crop_anchors.py` — `SubjectAnchor` dataclass (`bbox`, `focal_point`, `head_top_y`, `gaze_dir_x`, `face_boxes`, `horizon_angle`) extracted from OpenCV face/eye detector + spectral saliency + horizon detector.
- `src/develop/auto_crop_solver.py` — Pure geometry solver `solve_auto_crop(size: tuple[int, int], anchor: SubjectAnchor, config: AutoCropConfig) -> CropSettings`:
  1. Computes inscribed axis-aligned safe rectangle for `angle` ($\cos|\theta| / \sin|\theta|$ largest inscribed rectangle constraint).
  2. Computes minimum crop height/width required to encompass `anchor.bbox` + `padding_pct` + `headroom_pct` (and all `face_boxes` when `never_cut_faces` is `True`).
  3. Fits target `aspect_ratio` window within the inscribed safe rectangle.
  4. Positions window so `anchor.focal_point` lands on the target grid line (`1/3`, `0.382` Golden Ratio, or `0.5` Center), clamped to the inscribed safe bounds.
  5. Converts pixel rectangle `(x0, y0, x1, y1)` on the rotated canvas to `CropSettings(left, top, right, bottom, angle, locked=True)`.

## 2. Cost-Effective Model Implementation Blueprint

- Story 27.1: `src/develop/auto_crop_config.py` + presets & JSON persistence + `tests/test_auto_crop_config.py`
- Story 27.2: `src/develop/auto_crop_anchors.py` (face/eye/group/saliency anchor detector) + `tests/test_auto_crop_anchors.py`
- Story 27.3: `src/develop/auto_crop_solver.py` (composition rules, aspect ratio, group-face safety, rotated inscribed bounds) + `tests/test_auto_crop_solver.py`
- Story 27.4: Wire `Auto Crop` controls into Develop `crop_panel` and `CropBinding` + `tests/test_auto_crop_ui.py`
