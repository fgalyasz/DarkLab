#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="darklab"
SITE_HOST="darklab-a4o.pages.dev"
PACKAGE_NAME="DarkLab"
GATEWAY="${ROOT}/.gateway-site"
version="$(tr -d ' \t\n\r' < "${ROOT}/docs/version.txt")"

[[ "${version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
tag="v${version}"
download_url="https://github.com/fgalyasz/DarkLab/releases/download/${tag}/${PACKAGE_NAME}.dmg"
gh release create "${tag}" "${ROOT}/dist/${PACKAGE_NAME}.dmg" \
  --repo fgalyasz/DarkLab \
  --title "${PACKAGE_NAME} ${version}" \
  --notes "macOS installer ${version}. Signed for the build and not notarized."
rm -rf "${GATEWAY}"
mkdir -p "${GATEWAY}"
cat > "${GATEWAY}/index.html" <<EOF
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>${PACKAGE_NAME} ${version}</title>
  <style>
    body { font-family: -apple-system, sans-serif; max-width: 36rem; margin: 4rem auto; padding: 0 1.25rem; color: #1c1917; }
    a { color: #9a3412; }
  </style>
</head>
<body>
  <h1>${PACKAGE_NAME}</h1>
  <p>Version ${version}</p>
  <p><a href="${download_url}">Download ${PACKAGE_NAME}.dmg</a></p>
  <p>This macOS image is signed for the build and is not notarized.</p>
</body>
</html>
EOF
npx --yes wrangler pages deploy "${GATEWAY}" --project-name "${PROJECT}"
echo "OK: https://${SITE_HOST} version ${version}"
