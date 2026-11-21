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

try_source() {
  local name="$1"
  echo "Trying Cloudflare login from ${name}"
  if ! grep -q "oauth_token" "${cfg}"; then
    return 1
  fi
  chmod 600 "${cfg}"
  if grep -q "expiration_time" "${cfg}"; then
    echo "  expiration_time=$(grep -E '^expiration_time' "${cfg}" | head -1 | cut -d= -f2- | tr -d ' \"')"
  fi
  if [[ -n "${RUNNER_TEMP:-}" ]]; then
    cp "${cfg}" "${RUNNER_TEMP}/wrangler-before.toml"
  fi
  if auth_works; then
    echo "wrangler whoami OK via ${name}"
    return 0
  fi
  echo "  whoami failed via ${name}"
  return 1
}

ok=0
if write_cfg_from_secret && try_source "WRANGLER_CONFIG"; then
  ok=1
elif write_cfg_from_enc && try_source "WRANGLER_CONFIG_ENC"; then
  ok=1
fi

if [[ "${ok}" -eq 1 ]]; then
  script_dir="$(cd "$(dirname "$0")" && pwd)"
  if [[ -x "${script_dir}/ci_persist_wrangler.sh" ]]; then
    "${script_dir}/ci_persist_wrangler.sh" || true
  fi
  exit 0
fi

echo "::error::Cloudflare wrangler oauth expired and could not be refreshed."
echo "::error::Run DarkLab Actions → Refresh Cloudflare login → Run workflow,"
echo "::error::open the device URL from the job log, enter the code, approve."
echo "::error::That workflow persists oauth and dispatches catalogue publish."
cat /tmp/wrangler-whoami.txt >&2 || true
exit 1
