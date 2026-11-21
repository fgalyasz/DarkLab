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
  --collect-data certifi \
  --add-data "docs/version.txt:docs" \
  --distpath "${dist}" \
  --workpath "${root}/build/pyinstaller" \
  main.py
/usr/libexec/PlistBuddy -c "Set :CFBundleShortVersionString ${app_version}" "${app}/Contents/Info.plist"
codesign --force --sign "${identity}" --keychain "${keychain}" "${app}"

staging="${dist}/dmg-staging"
background="${root}/dmg_background.png"
tmp_rw_dmg="${dist}/DarkLab.rw.dmg"
disk_device=""
cleanup_dmg() {
  if [[ -n "${disk_device}" ]]; then
    hdiutil detach "${disk_device}" -quiet >/dev/null 2>&1 || true
  fi
  rm -f "${tmp_rw_dmg}" >/dev/null 2>&1 || true
}
trap cleanup_dmg EXIT
rm -rf "${staging}"
mkdir -p "${staging}"
ditto "${app}" "${staging}/DarkLab.app"
ln -s "/Applications" "${staging}/Applications"
rm -f "${dmg}" "${tmp_rw_dmg}"
hdiutil create -volname DarkLab -srcfolder "${staging}" -ov -format UDRW "${tmp_rw_dmg}" >/dev/null
attach_output="$(hdiutil attach -readwrite -noverify -noautoopen "${tmp_rw_dmg}")"
disk_device="$(echo "${attach_output}" | awk '/^\/dev\// {print $1; exit}')"
mount_point="$(echo "${attach_output}" | awk 'BEGIN{mp=""} /\/Volumes\// {mp=$NF} END{print mp}')"
if [[ -f "${background}" ]]; then
  mkdir -p "${mount_point}/.background"
  cp "${background}" "${mount_point}/.background/background.png"
fi
osascript <<'EOF'
tell application "Finder"
  tell disk "DarkLab"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set bounds of container window to {200, 200, 940, 640}
    set viewOptions to icon view options of container window
    set arrangement of viewOptions to not arranged
    set icon size of viewOptions to 96
    set text size of viewOptions to 12
    try
      set position of item "DarkLab.app" of container window to {180, 160}
    end try
    try
      set position of item "Applications" of container window to {540, 160}
    end try
    try
      if exists file ".background:background.png" then
        set background picture of viewOptions to file ".background:background.png"
      end if
    end try
    close
    open
    update without registering applications
    delay 1
  end tell
end tell
EOF
sync
hdiutil detach "${disk_device}" -quiet
disk_device=""
hdiutil convert "${tmp_rw_dmg}" -format UDZO -ov -o "${dmg}" >/dev/null
rm -f "${tmp_rw_dmg}"
trap - EXIT
rm -rf "${staging}"
echo "OK: ${dmg}"
