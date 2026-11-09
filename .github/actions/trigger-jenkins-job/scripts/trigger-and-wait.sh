#!/usr/bin/env bash
set -euo pipefail

: "${JENKINS_URL:?JENKINS_URL is required}"
: "${JENKINS_USER:?JENKINS_USER is required}"
: "${JENKINS_TOKEN:?JENKINS_TOKEN is required}"
: "${JOB:?JOB is required}"
: "${GITHUB_OUTPUT:?GITHUB_OUTPUT is required}"
PARAMETERS="${PARAMETERS:-}"
[[ -z "$PARAMETERS" ]] && PARAMETERS='{}'
POLL_INTERVAL_SECONDS="${POLL_INTERVAL_SECONDS:-60}"
TIMEOUT_MINUTES="${TIMEOUT_MINUTES:-280}"
MAX_CONSECUTIVE_ERRORS=10

BUILD_URL=""
FINISHED=false

output() { echo "$1=$2" >> "$GITHUB_OUTPUT"; }

fail() {
  echo "::error::$1"
  output result failure
  output failure_reason "$1"
  FINISHED=true
  exit 1
}

jenkins() {
  curl -sS --fail-with-body --max-time 60 \
    -K <(printf 'user = "%s:%s"\n' "$JENKINS_USER" "$JENKINS_TOKEN") "$@"
}

stop_build() {
  [[ -n "$BUILD_URL" ]] || return 0
  echo "::warning::Stopping Jenkins build $BUILD_URL"
  jenkins -X POST -o /dev/null "${BUILD_URL}stop" || echo "::warning::Could not stop $BUILD_URL"
}

on_signal() {
  if [[ "$FINISHED" != "true" ]]; then
    stop_build
    output result failure
    output failure_reason "Cancelled while waiting for the Jenkins build"
  fi
  exit 1
}
trap on_signal INT TERM

[[ "$POLL_INTERVAL_SECONDS" =~ ^[1-9][0-9]*$ ]] || fail "poll_interval_seconds must be a positive integer, got '$POLL_INTERVAL_SECONDS'"
[[ "$TIMEOUT_MINUTES" =~ ^[1-9][0-9]*$ ]] || fail "timeout_minutes must be a positive integer, got '$TIMEOUT_MINUTES'"
jq -e 'type == "object"' <<< "$PARAMETERS" > /dev/null 2>&1 || fail "parameters must be a JSON object"

JENKINS_URL="${JENKINS_URL%/}"
JOB_PATH=$(jq -rn --arg job "${JOB#/}" '$job | split("/") | map(select(. != "") | "job/" + @uri) | join("/")')
JOB_URL="$JENKINS_URL/$JOB_PATH"
FORM=$(jq -r 'to_entries | map("\(.key | @uri)=\(.value | tostring | @uri)") | join("&")' <<< "$PARAMETERS")
DEADLINE=$(( $(date +%s) + TIMEOUT_MINUTES * 60 ))

echo "::notice::Triggering $JOB with parameters $(jq -c . <<< "$PARAMETERS")"

HEADERS=$(mktemp)
BODY=$(mktemp)
trap 'rm -f "$HEADERS" "$BODY" "$BODY.err"' EXIT
# Jenkins explains a rejected request in an HTML page; keep the part that names the cause.
jenkins_reason() {
  [[ -s "$BODY" ]] || return 0
  local reason
  reason=$(grep -oiE "is missing the [A-Za-z/]+ permission|No valid crumb was included in the request" "$BODY" | head -n 1)
  [[ -n "$reason" ]] || reason=$(grep -oiE "<title>[^<]*</title>" "$BODY" | sed 's/<[^>]*>//g' | head -n 1)
  [[ -n "$reason" ]] && printf ' (%s)' "$reason"
  return 0
}

if ! response=$(jenkins -X POST -D "$HEADERS" -o "$BODY" --data "$FORM" "$JOB_URL/buildWithParameters" 2>&1); then
  fail "Could not trigger $JOB: $response$(jenkins_reason)"
fi

QUEUE_URL=$(grep -i '^location:' "$HEADERS" | tail -n 1 | awk '{print $2}' | tr -d '\r')
[[ -n "$QUEUE_URL" ]] || fail "Jenkins accepted the trigger for $JOB but returned no queue location"
QUEUE_URL="${QUEUE_URL%/}/"
echo "Queued: $QUEUE_URL"

# Fetches a Jenkins JSON endpoint into $BODY. Returns 0 on success, 1 on a transient error and 2 once
# MAX_CONSECUTIVE_ERRORS failures have happened in a row.
errors=0
poll() {
  if jenkins -o "$BODY" "$1" 2> "$BODY.err"; then
    errors=0
    return 0
  fi
  ((++errors))
  echo "::warning::Jenkins poll failed ($errors/$MAX_CONSECUTIVE_ERRORS): $(cat "$BODY.err")"
  (( errors < MAX_CONSECUTIVE_ERRORS )) || return 2
  return 1
}

while [[ -z "$BUILD_URL" ]]; do
  if (( $(date +%s) >= DEADLINE )); then
    queue_id=$(basename "$QUEUE_URL")
    jenkins -X POST -o /dev/null "$JENKINS_URL/queue/cancelItem?id=$queue_id" || true
    fail "Timed out after ${TIMEOUT_MINUTES}m waiting for $JOB to leave the Jenkins queue"
  fi

  rc=0
  poll "${QUEUE_URL}api/json" || rc=$?
  if (( rc == 2 )); then
    fail "Lost contact with Jenkins while waiting for the queue item $QUEUE_URL"
  elif (( rc == 0 )); then
    item=$(cat "$BODY")
    if [[ "$(jq -r '.cancelled // false' <<< "$item")" == "true" ]]; then
      fail "The queued build of $JOB was cancelled in Jenkins"
    fi
    BUILD_URL=$(jq -r '.executable.url // empty' <<< "$item")
    if [[ -n "$BUILD_URL" ]]; then
      BUILD_URL="${BUILD_URL%/}/"
      output build_url "$BUILD_URL"
      output build_number "$(jq -r '.executable.number' <<< "$item")"
      echo "::notice::Jenkins build started: $BUILD_URL"
      break
    fi
    echo "Waiting in Jenkins queue: $(jq -r '.why // "pending"' <<< "$item")"
  fi
  sleep "$POLL_INTERVAL_SECONDS"
done

while true; do
  if (( $(date +%s) >= DEADLINE )); then
    stop_build
    fail "Timed out after ${TIMEOUT_MINUTES}m waiting for $BUILD_URL"
  fi

  rc=0
  poll "${BUILD_URL}api/json?tree=building,result,duration" || rc=$?
  if (( rc == 2 )); then
    fail "Lost contact with Jenkins while waiting for $BUILD_URL"
  elif (( rc == 0 )); then
    build=$(cat "$BODY")
    building=$(jq -r '.building' <<< "$build")
    result=$(jq -r '.result // empty' <<< "$build")
    if [[ "$building" == "false" && -n "$result" ]]; then
      output jenkins_result "$result"
      FINISHED=true
      if [[ "$result" == "SUCCESS" ]]; then
        echo "::notice::Jenkins build succeeded: $BUILD_URL"
        output result success
        output failure_reason ""
        exit 0
      fi
      fail "Jenkins build finished with $result: $BUILD_URL"
    fi
    echo "Building: $BUILD_URL"
  fi
  sleep "$POLL_INTERVAL_SECONDS"
done
