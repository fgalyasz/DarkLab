# Addendum — Auto-update implementation blueprint

## Config keys

- `updates.check_on_startup` (bool, default `true`)
- `updates.skipped_version` (str, default `""`)

## Domain files (no Qt)

| File | Symbols |
| --- | --- |
| `src/release/versioning.py` | `read_version_text`, `parse_semver`, `is_newer`, `resolve_version_file`, `app_version` |
| `src/release/update_check.py` | `ReleaseInfo`, `UpdateCheckError`, `latest_api_url`, `parse_release_payload`, `fetch_latest_release`, `platform_asset_name`, `select_asset`, `should_offer_update` |
| `src/release/update_download.py` | `download_release_asset` |
| `src/release/update_apply.py` | `is_frozen_app`, `install_root`, `apply_update`, `open_downloaded_installer` |

## UI files

| File | Role |
| --- | --- |
| `src/ui/update_controller.py` | `UpdateController` — startup + manual check, worker thread |
| `src/ui/dialogs/update_dialog.py` | Offer Update / Later / Skip |
| `src/ui/main_window.py` | Help menu; wire controller |

## Build

All three packagers pass `--add-data` so `docs/version.txt` lands in the frozen bundle at `docs/version.txt`.

## Unit tests

`tests/test_auto_update.py` — versioning, payload parse, offer rules, asset select, download to temp with fake opener, apply path selection for frozen vs not. Target ≥95% on new domain modules.
