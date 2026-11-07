#!/usr/bin/env bash
set -euo pipefail

basename="${1:?keychain basename}"
identity_name="${2:?identity name}"
sparkle_dir="${3:-}"

: "${CODESIGN_P12_BASE64:?}"
: "${CODESIGN_P12_PASSWORD:?}"
: "${CODESIGN_KEYCHAIN_PASSWORD:?}"

keychain="${HOME}/Library/Keychains/${basename}.keychain-db"
work="${RUNNER_TEMP:-$(mktemp -d)}"
p12="${work}/identity.p12"
mkdir -p "$(dirname "$keychain")"
printf '%s' "${CODESIGN_P12_BASE64}" | base64 -D > "${p12}"
security create-keychain -p "${CODESIGN_KEYCHAIN_PASSWORD}" "${keychain}"
security set-keychain-settings -lut 21600 "${keychain}"
security unlock-keychain -p "${CODESIGN_KEYCHAIN_PASSWORD}" "${keychain}"
security import "${p12}" \
  -k "${keychain}" \
  -P "${CODESIGN_P12_PASSWORD}" \
  -A \
  -T /usr/bin/codesign \
  -T /usr/bin/security
security list-keychains -d user -s "${keychain}" "${HOME}/Library/Keychains/login.keychain-db"
security set-key-partition-list \
  -S apple-tool:,apple:,codesign: \
  -s \
  -k "${CODESIGN_KEYCHAIN_PASSWORD}" \
  "${keychain}" >/dev/null || true
rm -f "${p12}"
security find-identity -v -p codesigning "${keychain}"
security find-identity -v -p codesigning "${keychain}" | grep -F "\"${identity_name}\"" >/dev/null

if [[ -n "${sparkle_dir}" && -n "${SPARKLE_EDDSA_PRIVATE_KEY:-}" ]]; then
  mkdir -p "${sparkle_dir}"
  printf '%s' "${SPARKLE_EDDSA_PRIVATE_KEY}" > "${sparkle_dir}/sparkle_eddsa"
  chmod 600 "${sparkle_dir}/sparkle_eddsa"
fi
