#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.smoke.milestone_one_shoot import run_milestone_one_shoot


def _configure_utf8_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8", errors="replace")


def main() -> int:
    _configure_utf8_stdout()
    work = Path(tempfile.mkdtemp(prefix="darklab-smoke-"))
    run_milestone_one_shoot(work)
    print("milestone smoke: import → flag → tone → export OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
