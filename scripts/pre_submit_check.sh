#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-industrial-iot-alert-triage:latest}"
HOST_PORT="${HOST_PORT:-}"
INFERENCE_HOST_PORT="${INFERENCE_HOST_PORT:-}"

find_free_port() {
  local preferred="${1:-0}"
  python - "$preferred" <<'PY'
import socket
import sys

preferred = int(sys.argv[1])
candidates = [preferred] if preferred > 0 else []
candidates.extend(range(18000, 18200))

for port in candidates:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(("127.0.0.1", port))
            print(port)
            raise SystemExit(0)
        except OSError:
            continue

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
    sock.bind(("127.0.0.1", 0))
    print(sock.getsockname()[1])
PY
}

if [[ -z "$HOST_PORT" ]]; then
  HOST_PORT="$(find_free_port 18000)"
fi

if [[ -z "$INFERENCE_HOST_PORT" ]]; then
  INFERENCE_HOST_PORT="$(find_free_port 18001)"
fi

if [[ "$INFERENCE_HOST_PORT" == "$HOST_PORT" ]]; then
  INFERENCE_HOST_PORT="$(find_free_port $((HOST_PORT + 1)))"
fi

log() {
  printf '%s\n' "$*"
}

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

log "Step 1/5: docker build"
docker build -t "$IMAGE_NAME" "$REPO_DIR" >/tmp/openenv_docker_build.log 2>&1 || {
  cat /tmp/openenv_docker_build.log >&2
  fail "docker build failed"
}
log "PASS: docker build"

log "Step 2/5: run container + /health"
CID="$(docker run -d -p "${HOST_PORT}:8000" "$IMAGE_NAME")"
cleanup() {
  docker rm -f "$CID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

HEALTH_CODE="000"
for _ in $(seq 1 45); do
  HEALTH_CODE="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${HOST_PORT}/health" || true)"
  if [[ "$HEALTH_CODE" == "200" ]]; then
    break
  fi
  sleep 1
done
[[ "$HEALTH_CODE" == "200" ]] || fail "/health returned ${HEALTH_CODE}"
log "PASS: /health returns 200"

log "Step 3/5: /reset endpoint"
RESET_CODE="$(curl -s -o /tmp/openenv_reset_check.json -w '%{http_code}' -X POST -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:${HOST_PORT}/reset" || true)"
[[ "$RESET_CODE" == "200" ]] || fail "/reset returned ${RESET_CODE}"
python - <<'PY'
import json
with open('/tmp/openenv_reset_check.json', 'r', encoding='utf-8') as f:
    payload = json.load(f)
assert 'observation' in payload, 'missing observation in /reset payload'
assert 'done' in payload, 'missing done in /reset payload'
assert 'reward' in payload, 'missing reward in /reset payload'
PY
log "PASS: /reset returns valid payload"

log "Step 4/5: openenv validate"
cd "$REPO_DIR"
./.venv/bin/openenv validate >/tmp/openenv_validate.log 2>&1 || {
  cat /tmp/openenv_validate.log >&2
  fail "openenv validate failed"
}
log "PASS: openenv validate"

log "Step 5/5: baseline inference smoke"
export API_BASE_URL="${API_BASE_URL:-https://api.openai.com/v1}"
export MODEL_NAME="${MODEL_NAME:-gpt-4.1-mini}"
# Allow smoke run without real key; script still executes deterministic fallback path.
export OPENAI_API_KEY="${OPENAI_API_KEY:-dummy-key}"
export INFERENCE_MODE="single"
export HOST_PORT="$INFERENCE_HOST_PORT"
./.venv/bin/python inference.py >/tmp/openenv_inference.log 2>&1 || {
  cat /tmp/openenv_inference.log >&2
  fail "inference.py failed"
}
grep -q '^\[START\]' /tmp/openenv_inference.log || fail "missing [START] log"
grep -q '^\[STEP\]' /tmp/openenv_inference.log || fail "missing [STEP] log"
grep -q '^\[END\]' /tmp/openenv_inference.log || fail "missing [END] log"
log "PASS: inference smoke and structured logs"

log "All checks passed."
