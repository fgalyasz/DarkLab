#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: $(basename "$0") <issue-number-or-url> <status>" >&2
  echo "Status: Todo | In Progress | Done" >&2
  exit 1
}

if [[ $# -lt 2 ]]; then
  usage
fi

raw="$1"
status="$2"
root="$(cd "$(dirname "$0")/.." && pwd)"
meta="${root}/docs/pdlc/project.json"

if [[ ! -f "${meta}" ]]; then
  echo "ERROR: missing ${meta}. Run scripts/pdlc_seed_github.py first." >&2
  exit 1
fi

owner="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["owner"])' "${meta}")"
project_number="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["project_number"])' "${meta}")"
repo="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["repo"])' "${meta}")"

case "${status}" in
  Todo|"In Progress"|Done) ;;
  *)
    echo "ERROR: unknown status: ${status}" >&2
    usage
    ;;
esac

if [[ "${raw}" =~ ^https:// ]]; then
  url="${raw}"
else
  url="https://github.com/${repo}/issues/${raw}"
fi

add_output="$(gh project item-add "${project_number}" --owner "${owner}" --url "${url}" 2>&1)" || {
  if [[ "${add_output}" != *"already exists"* ]]; then
    echo "${add_output}" >&2
    exit 1
  fi
}
gh project item-edit "${project_number}" --owner "${owner}" --url "${url}" --field Status --value "${status}" >/dev/null
echo "Project ${project_number}: ${url} -> ${status}"
