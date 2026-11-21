#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  return 0 2>/dev/null || exit 0
fi
unset CLOUDFLARE_API_TOKEN || true

cfg=""
for candidate in \
  "${HOME}/Library/Preferences/.wrangler/config/default.toml" \
  "${HOME}/.config/.wrangler/config/default.toml" \
  "${HOME}/.wrangler/config/default.toml"
do
  if [[ -s "${candidate}" ]]; then
    cfg="${candidate}"
    break
  fi
done
if [[ -z "${cfg}" ]]; then
  echo "ensure_cloudflare_token: no wrangler config found" >&2
  return 1 2>/dev/null || exit 1
fi

token="$(
  python3 - "${cfg}" <<'PY'
import re, sys
from pathlib import Path
text = Path(sys.argv[1]).read_text()
match = re.search(r'oauth_token\s*=\s*"([^"]+)"', text)
if not match:
    match = re.search(r"oauth_token\s*=\s*'([^']+)'", text)
print(match.group(1) if match else "")
PY
)"
if [[ -z "${token}" ]]; then
  echo "ensure_cloudflare_token: oauth_token missing in ${cfg}" >&2
  return 1 2>/dev/null || exit 1
fi
export CLOUDFLARE_API_TOKEN="${token}"
echo "ensure_cloudflare_token: exported oauth_token as CLOUDFLARE_API_TOKEN"
