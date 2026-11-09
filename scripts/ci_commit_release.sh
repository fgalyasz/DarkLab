#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

add_if_present() {
  local path="$1"
  if [[ -f "${path}" ]]; then
    git add -- "${path}"
  fi
}

if [[ "${1:-}" == "company" ]]; then
  cd "${TENPRINT_ROOT:?}"
else
  cd "${root}"
fi
git config user.name "fgalyasz"
git config user.email "fgalyasz@gmail.com"

if [[ "${1:-}" == "company" ]]; then
  add_if_present src/data/products.ts
else
  add_if_present VERSION
  add_if_present docs/version.txt
  add_if_present docs/appcast.xml
  add_if_present docs/index.html
fi

if git diff --cached --quiet; then
  echo "no release files to commit"
  exit 0
fi

version="$(tr -d ' \t\n\r' < "${root}/docs/version.txt")"
git commit -m "Release ${version} [skip ci]"
for attempt in 1 2 3; do
  git pull --rebase -X theirs origin main
  if git push origin HEAD:main; then
    exit 0
  fi
  sleep 2
done
exit 1
