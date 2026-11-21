#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}"
PROJECT="darklab"
SITE_HOST="darklab-a4o.pages.dev"
PACKAGE_NAME="DarkLab"
GATEWAY="${ROOT}/.gateway-site"
version="$(tr -d ' \t\n\r' < "${ROOT}/docs/version.txt")"
WRANGLER_BIN="${ROOT}/../TenPrintSoftware/node_modules/.bin/wrangler"

[[ "${version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
tag="v${version}"
upload_paths=()
while IFS= read -r path; do
  upload_paths+=("${path}")
done < <(python3 "${ROOT}/scripts/release_dist_paths.py")
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
rm -rf "${GATEWAY}"
python3 "${ROOT}/scripts/render_gateway_site.py" "${version}" "${GATEWAY}"
if [[ -x "${WRANGLER_BIN}" ]]; then
  env -u CLOUDFLARE_API_TOKEN "${WRANGLER_BIN}" pages deploy "${GATEWAY}" --project-name "${PROJECT}"
else
  env -u CLOUDFLARE_API_TOKEN npx --yes wrangler@4.127.1 pages deploy "${GATEWAY}" --project-name "${PROJECT}"
fi
echo "OK: https://${SITE_HOST} version ${version}"
