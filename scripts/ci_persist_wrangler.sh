#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${GH_TOKEN:-}" ]]; then
  echo "GH_TOKEN / ACTIONS_PUSH_TOKEN missing; skip Cloudflare login persist."
  exit 0
fi

if [[ "$(uname -s)" == "Darwin" ]]; then
  cfg="${HOME}/Library/Preferences/.wrangler/config/default.toml"
else
  cfg="${HOME}/.config/.wrangler/config/default.toml"
fi

if [[ ! -s "${cfg}" ]] || ! grep -q "oauth_token" "${cfg}"; then
  echo "No wrangler oauth config to persist."
  exit 0
fi

force="${1:-}"
before="${RUNNER_TEMP:-/tmp}/wrangler-before.toml"
if [[ "${force}" != "force" && -f "${before}" ]] && cmp -s "${cfg}" "${before}"; then
  echo "Cloudflare login unchanged; skip persist."
  exit 0
fi

enc="$(PASS="${GH_TOKEN}" openssl enc -aes-256-cbc -pbkdf2 -salt -base64 -A -pass env:PASS -in "${cfg}")"
gh variable set WRANGLER_CONFIG_ENC --repo fgalyasz/TenPrintSoftware --body "${enc}"
for repo in TenPrintSoftware DarkLab SnappyZones SessionGuard WalkAway MarkSweep 8bitEmu; do
  gh secret set WRANGLER_CONFIG --repo "fgalyasz/${repo}" < "${cfg}"
done
echo "Persisted refreshed Cloudflare wrangler login to WRANGLER_CONFIG_ENC + WRANGLER_CONFIG."
