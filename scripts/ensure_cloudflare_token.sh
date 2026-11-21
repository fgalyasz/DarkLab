#!/usr/bin/env bash
# Clear an empty CLOUDFLARE_API_TOKEN so wrangler can use restored oauth config.
# Do not promote oauth_token to CLOUDFLARE_API_TOKEN — Cloudflare rejects that (9109).
if [[ -z "${CLOUDFLARE_API_TOKEN:-}" ]]; then
  unset CLOUDFLARE_API_TOKEN || true
fi
