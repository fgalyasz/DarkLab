#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}"
PACKAGE_NAME="DarkLab"
version="$(tr -d ' \t\n\r' < "${ROOT}/docs/version.txt")"
[[ "${version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
tag="v${version}"
upload_paths=()
while IFS= read -r path; do
  upload_paths+=("${path}")
done < <(python3 "${ROOT}/scripts/release_dist_paths.py")
if [[ "${#upload_paths[@]}" -eq 0 ]]; then
  echo "No release assets found under dist/"
  exit 1
fi
if gh release view "${tag}" --repo fgalyasz/DarkLab >/dev/null 2>&1; then
  gh release upload "${tag}" "${upload_paths[@]}" \
    --repo fgalyasz/DarkLab \
    --clobber
else
  notes="$(python3 -c "from src.release import downloads; print(downloads.release_notes('${version}'))")"
  gh release create "${tag}" "${upload_paths[@]}" \
    --repo fgalyasz/DarkLab \
    --title "${PACKAGE_NAME} ${version}" \
    --notes "${notes}"
fi
echo "OK: GitHub release ${tag}"
