#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
version_file="${root}/docs/version.txt"
current="1.0.0"
if [[ -f "${version_file}" ]]; then
  current="$(tr -d ' \t\n\r' < "${version_file}")"
fi
IFS=. read -r major minor patch <<< "${current}"
patch=$((patch + 1))
app_version="${major}.${minor}.${patch}"
printf '%s' "${app_version}" > "${version_file}"
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
  --collect-binaries pyexiv2 \
  --distpath "${dist}" \
  --workpath "${root}/build/pyinstaller" \
  main.py
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString ${app_version}" "${app}/Contents/Info.plist"
codesign --force --sign "${identity}" --keychain "${keychain}" "${app}"
rm -f "${dmg}"
hdiutil create -volname DarkLab -srcfolder "${app}" -ov -format UDZO "${dmg}"
echo "OK: ${dmg}"
