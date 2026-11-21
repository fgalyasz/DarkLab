# Addendum — Cost-effective implementation blueprint

## Target files

- `scripts/build_dmg.sh` — replace single-folder UDZO create with staging + Applications symlink + UDRW layout + UDZO convert.
- `tests/test_startup.py` — assert script contains Applications symlink and icon position for Applications.
- `CHANGELOG.md` — user-visible installer note.

## Script contracts

Keep bump/sign/PyInstaller steps unchanged. After codesign:

1. `staging="${dist}/dmg-staging"`; wipe and mkdir.
2. `ditto "${app}" "${staging}/DarkLab.app"`.
3. `ln -s "/Applications" "${staging}/Applications"`.
4. Create UDRW from staging, attach readwrite, run Finder AppleScript (app at `{180,160}`, Applications at `{540,160}`), detach, convert UDZO to `${dmg}`.

## Unit tests

- `test_build_dmg_links_applications` — script text contains `ln -s "/Applications"` and `item "Applications"`.
- `test_build_dmg_uses_tenprint_background` — script references `dmg_background.png` and `.background/background.png`; repo root has that PNG.
- Existing `test_build_dmg_collects_pyexiv2_binaries` stays green.
