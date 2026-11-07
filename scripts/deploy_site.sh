#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT="darklab"
SITE_HOST="darklab-a4o.pages.dev"
PACKAGE_NAME="DarkLab"
GATEWAY="${ROOT}/.gateway-site"
version="$(tr -d ' \t\n\r' < "${ROOT}/docs/version.txt")"

[[ "${version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
rm -rf "${GATEWAY}"
mkdir -p "${GATEWAY}"
cp "${ROOT}/dist/${PACKAGE_NAME}.dmg" "${GATEWAY}/"
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
  <p><a href="./${PACKAGE_NAME}.dmg">Download ${PACKAGE_NAME}.dmg</a></p>
  <p>This macOS image is signed for the build and is not notarized.</p>
</body>
</html>
EOF
npx --yes wrangler pages deploy "${GATEWAY}" --project-name "${PROJECT}"
echo "OK: https://${SITE_HOST} version ${version}"
