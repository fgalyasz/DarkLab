#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PYTHONPATH="${ROOT}"
PROJECT="darklab"
SITE_HOST="darklab-a4o.pages.dev"
GATEWAY="${ROOT}/.gateway-site"
version="$(tr -d ' \t\n\r' < "${ROOT}/docs/version.txt")"
WRANGLER_BIN="${ROOT}/../TenPrintSoftware/node_modules/.bin/wrangler"

[[ "${version}" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]
bash "${ROOT}/scripts/ci_publish_github_release.sh"
rm -rf "${GATEWAY}"
python3 "${ROOT}/scripts/render_gateway_site.py" "${version}" "${GATEWAY}"
if [[ -x "${WRANGLER_BIN}" ]]; then
  deploy_cmd=("${WRANGLER_BIN}" pages deploy "${GATEWAY}" --project-name "${PROJECT}")
else
  deploy_cmd=(npx --yes wrangler@4.127.1 pages deploy "${GATEWAY}" --project-name "${PROJECT}")
fi
if [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  "${deploy_cmd[@]}"
else
  env -u CLOUDFLARE_API_TOKEN "${deploy_cmd[@]}"
fi
echo "OK: https://${SITE_HOST} version ${version}"
