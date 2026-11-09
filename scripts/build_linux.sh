#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version="$(tr -d ' \t\n\r' < "${root}/docs/version.txt")"
dist="${root}/dist"
bundle="${dist}/DarkLab"
archive="${dist}/DarkLab-linux-x86_64.tar.gz"

cd "${root}"
python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller \
  --noconfirm \
  --windowed \
  --name DarkLab \
  --collect-binaries pyexiv2 \
  --distpath "${dist}" \
  --workpath "${root}/build/pyinstaller" \
  main.py
rm -f "${archive}"
tar czf "${archive}" -C "${dist}" DarkLab
echo "OK: ${archive} (version ${version})"
