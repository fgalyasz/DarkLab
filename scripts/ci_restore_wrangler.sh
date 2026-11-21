#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "::error::ACTIONS_PUSH_TOKEN / GH_TOKEN required to restore Cloudflare login."
  exit 1
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  cfg_dir="${HOME}/Library/Preferences/.wrangler/config"
else
  cfg_dir="${HOME}/.config/.wrangler/config"
fi
mkdir -p "${cfg_dir}"
cfg="${cfg_dir}/default.toml"
wrangler_bin="${WRANGLER_BIN:-}"
if [[ -z "${wrangler_bin}" ]]; then
  sibling="$(cd "$(dirname "$0")/../.." && pwd)/TenPrintSoftware/node_modules/.bin/wrangler"
  if [[ -x "${sibling}" ]]; then
    wrangler_bin="${sibling}"
  else
    wrangler_bin="npx"
  fi
fi

write_cfg_from_enc() {
  local enc
  enc="$(gh variable get WRANGLER_CONFIG_ENC --repo fgalyasz/TenPrintSoftware 2>/dev/null || true)"
  [[ -n "${enc}" ]] || return 1
  printf '%s' "${enc}" | PASS="${GH_TOKEN}" openssl enc -d -aes-256-cbc -pbkdf2 -base64 -A -pass env:PASS > "${cfg}" 2>/dev/null
  [[ -s "${cfg}" ]] && grep -q "oauth_token" "${cfg}"
}

write_cfg_from_secret() {
  [[ -n "${WRANGLER_CONFIG:-}" ]] || return 1
  printf '%s\n' "${WRANGLER_CONFIG}" > "${cfg}"
  [[ -s "${cfg}" ]] && grep -q "oauth_token" "${cfg}"
}

auth_works() {
  if [[ "${wrangler_bin}" == "npx" ]]; then
    env -u CLOUDFLARE_API_TOKEN npx --yes wrangler@4.127.1 whoami >/tmp/wrangler-whoami.txt 2>&1
  else
    env -u CLOUDFLARE_API_TOKEN "${wrangler_bin}" whoami >/tmp/wrangler-whoami.txt 2>&1
  fi
}

restored=""
if write_cfg_from_enc; then
  restored="WRANGLER_CONFIG_ENC"
elif write_cfg_from_secret; then
  restored="WRANGLER_CONFIG"
else
  echo "::error::No WRANGLER_CONFIG_ENC or WRANGLER_CONFIG with oauth_token."
  exit 1
fi
chmod 600 "${cfg}"
if grep -q "expiration_time" "${cfg}"; then
  echo "Restored ${restored}; expiration_time=$(grep -E '^expiration_time' "${cfg}" | head -1 | cut -d= -f2- | tr -d ' \"')"
else
  echo "Restored ${restored}; no expiration_time field"
fi
if auth_works; then
  echo "wrangler whoami OK"
  if [[ -n "${RUNNER_TEMP:-}" ]]; then
    cp "${cfg}" "${RUNNER_TEMP}/wrangler-before.toml"
  fi
  exit 0
fi
echo "Primary restore failed whoami; trying alternate source..."
if [[ "${restored}" == "WRANGLER_CONFIG_ENC" ]] && write_cfg_from_secret; then
  restored="WRANGLER_CONFIG"
  chmod 600 "${cfg}"
  if auth_works; then
    echo "wrangler whoami OK via ${restored}"
    if [[ -n "${RUNNER_TEMP:-}" ]]; then
      cp "${cfg}" "${RUNNER_TEMP}/wrangler-before.toml"
    fi
    exit 0
  fi
fi
echo "::error::Cloudflare wrangler oauth is expired or revoked (whoami failed)."
echo "::error::FOUNDER ACTION: create a Cloudflare API token (Account → Pages → Edit) and set DarkLab secret CLOUDFLARE_API_TOKEN,"
echo "::error::or run 'wrangler login' locally and refresh WRANGLER_CONFIG / WRANGLER_CONFIG_ENC."
cat /tmp/wrangler-whoami.txt >&2 || true
exit 1
