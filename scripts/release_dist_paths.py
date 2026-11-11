from __future__ import annotations

import sys
from pathlib import Path

from src.release import downloads

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    dist = ROOT / "dist"
    present = {name: (dist / name).is_file() for _, name in downloads.PLATFORM_ASSETS}
    if not present.get(downloads.MAC_ASSET):
        print("missing required macOS installer", file=sys.stderr)
        return 1
    for _, name in downloads.PLATFORM_ASSETS:
        if present.get(name):
            print(dist / name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
