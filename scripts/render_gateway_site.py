from __future__ import annotations

import sys
from pathlib import Path

from src.release import downloads

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: render_gateway_site.py <version> <gateway_dir>", file=sys.stderr)
        return 1
    version = sys.argv[1].strip()
    gateway = Path(sys.argv[2])
    dist = ROOT / "dist"
    present = {name: (dist / name).is_file() for _, name in downloads.PLATFORM_ASSETS}
    assets = downloads.platforms_for_paths(present)
    gateway.mkdir(parents=True, exist_ok=True)
    (gateway / "index.html").write_text(
        downloads.gateway_html(version, assets),
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
