#!/usr/bin/env bash
set -euo pipefail

if [[ "$(uname -s)" == "Darwin" ]]; then
  cfg="${HOME}/Library/Preferences/.wrangler/config/default.toml"
else
  cfg="${HOME}/.config/.wrangler/config/default.toml"
fi

if [[ ! -s "${cfg}" ]] || ! grep -q "oauth_token" "${cfg}"; then
  echo "No local wrangler login found at ${cfg}"
  echo "Run first: npx wrangler@4.127.1 login"
  exit 1
fi

if ! command -v gh >/dev/null; then
  echo "GitHub CLI (gh) required."
  exit 1
fi

echo "Pushing wrangler oauth login to GitHub Actions secrets..."
for repo in TenPrintSoftware DarkLab SnappyZones SessionGuard WalkAway MarkSweep 8bitEmu; do
  gh secret set WRANGLER_CONFIG --repo "fgalyasz/${repo}" < "${cfg}"
  echo "  WRANGLER_CONFIG → fgalyasz/${repo}"
done

if [[ -n "${ACTIONS_PUSH_TOKEN:-}" ]]; then
  enc="$(PASS="${ACTIONS_PUSH_TOKEN}" openssl enc -aes-256-cbc -pbkdf2 -salt -base64 -A -pass env:PASS -in "${cfg}")"
  GH_TOKEN="${ACTIONS_PUSH_TOKEN}" gh variable set WRANGLER_CONFIG_ENC --repo fgalyasz/TenPrintSoftware --body "${enc}"
  echo "  WRANGLER_CONFIG_ENC → fgalyasz/TenPrintSoftware"
else
  echo "ACTIONS_PUSH_TOKEN unset locally — WRANGLER_CONFIG secrets are enough for CI restore."
fi

echo "OK. Next: GitHub → DarkLab → Actions → Publish company catalogue → Run workflow"
