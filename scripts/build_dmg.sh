#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
identity="DarkLab Local"
keychain="${HOME}/Library/Keychains/darklab-signing.keychain-db"
dist="${root}/dist"
app="${dist}/DarkLab.app"
dmg="${dist}/DarkLab.dmg"

cd "${root}"
python3 -m pip install -r requirements.txt pyinstaller
python3 -m PyInstaller \
  --noconfirm \
  --windowed \
  --name DarkLab \
  --distpath "${dist}" \
  --workpath "${root}/build/pyinstaller" \
  main.py
codesign --force --sign "${identity}" --keychain "${keychain}" "${app}"
rm -f "${dmg}"
hdiutil create -volname DarkLab -srcfolder "${app}" -ov -format UDZO "${dmg}"
echo "OK: ${dmg}"
