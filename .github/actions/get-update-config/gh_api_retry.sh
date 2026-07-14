#!/usr/bin/env bash
# Shared helper for get-update-config. Source it: source "$GITHUB_ACTION_PATH/gh_api_retry.sh"
#
# Query the GitHub API with retry on transient failures. Prints the response body on
# success. Exit codes:
#   0  = ok (HTTP 200)
#   44 = not found (HTTP 404) — the resource is genuinely absent
#   1  = transient failure (429/5xx/network) after retries — caller must fail loud,
#        never assume the resource is absent
gh_api_retry() {
  local path="$1" attempt=1 max=3 out err
  while :; do
    if out=$(gh api "$path" 2>/tmp/gh_api_err); then
      printf '%s' "$out"
      return 0
    fi
    err=$(cat /tmp/gh_api_err)
    if printf '%s' "$err" | grep -q '(HTTP 404)'; then
      return 44
    fi
    if (( attempt >= max )); then
      echo "::error::gh api $path failed after $max attempts (non-404): $err" >&2
      return 1
    fi
    echo "::warning::gh api $path transient failure (attempt $attempt/$max), retrying: $err" >&2
    sleep $(( attempt * 2 ))
    (( ++attempt ))
  done
}
