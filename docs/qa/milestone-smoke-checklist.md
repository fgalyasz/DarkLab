# Milestone one-shoot smoke (story 18.2)

Proves NFR-5 for the milestone-1 path: **Import → Flag → basic tone → Export JPEG**, with ADR-2 catalog layout unchanged.

## Automated

From the repo root, with `requirements.txt` installed:

```bash
python scripts/milestone_smoke.py
```

CI should run this on macOS, Linux, and Windows before the unit suite. The prepared `tests.yml` matrix (ubuntu-24.04, macos-latest, windows-latest) could not be pushed from the cloud token without the `workflow` scope; apply that change on a machine that can update workflows.

## Manual on each OS

1. Install Python 3.12 and `pip install -r requirements.txt` (macOS: `brew install inih` for pyexiv2).
2. Run `python scripts/milestone_smoke.py` and expect `milestone smoke: import → flag → tone → export OK`.
3. Optional: `python -m unittest tests.test_milestone_shoot` with `QT_QPA_PLATFORM=offscreen`.

The script does not start the GUI and does not change Originals on disk.
