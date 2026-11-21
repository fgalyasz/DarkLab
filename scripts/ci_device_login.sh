#!/usr/bin/env bash
set -euo pipefail

wrangler_bin="${WRANGLER_BIN:-}"
if [[ -z "${wrangler_bin}" || ! -x "${wrangler_bin}" ]]; then
  wrangler_bin="npx"
fi

log="/tmp/wrangler-device-login.log"
rm -f "${log}"
unset CLOUDFLARE_API_TOKEN || true

echo "Starting wrangler device login (approve in browser within 5 minutes)..."
if [[ "${wrangler_bin}" == "npx" ]]; then
  stdbuf -oL -eL env -u CLOUDFLARE_API_TOKEN npx --yes wrangler@4.127.1 login --device --browser=false 2>&1 | tee "${log}" &
else
  stdbuf -oL -eL env -u CLOUDFLARE_API_TOKEN "${wrangler_bin}" login --device --browser=false 2>&1 | tee "${log}" &
fi
pid=$!

deadline=$((SECONDS + 360))
printed=0
while kill -0 "${pid}" 2>/dev/null; do
  if [[ "${printed}" -eq 0 && -f "${log}" ]]; then
    if grep -q "oauth2/device/verify" "${log}" && grep -Eq '^[[:space:]]*[A-Za-z0-9_-]{6,}[[:space:]]*$' "${log}"; then
      url="$(grep -Eo 'https://dash\.cloudflare\.com/oauth2/device/verify' "${log}" | head -1)"
      code="$(grep -Eo '^[[:space:]]*[A-Za-z0-9_-]{6,}[[:space:]]*$' "${log}" | head -1 | tr -d '[:space:]')"
      echo "::notice title=Cloudflare device login::Open ${url} and enter code ${code}"
      if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
        {
          echo "## Cloudflare device login"
          echo ""
          echo "1. Open: ${url}"
          echo "2. Enter code: \`${code}\`"
          echo "3. Approve Wrangler"
        } >> "${GITHUB_STEP_SUMMARY}"
      fi
      printed=1
    fi
  fi
  if [[ "${SECONDS}" -ge "${deadline}" ]]; then
    kill "${pid}" 2>/dev/null || true
    echo "::error::Device login timed out after 6 minutes."
    exit 1
  fi
  sleep 2
done

wait "${pid}"
status=$?
if [[ "${status}" -ne 0 ]]; then
  echo "::error::wrangler login --device failed (exit ${status})."
  exit "${status}"
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  cfg="${HOME}/Library/Preferences/.wrangler/config/default.toml"
else
  cfg="${HOME}/.config/.wrangler/config/default.toml"
fi
if [[ ! -s "${cfg}" ]] || ! grep -q "oauth_token" "${cfg}"; then
  echo "::error::Login finished but oauth config missing at ${cfg}"
  exit 1
fi
echo "Device login OK."
