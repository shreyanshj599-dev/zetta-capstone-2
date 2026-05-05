#!/usr/bin/env bash
# verify.sh — golden-path smoke test for the lead enrichment service.
#
# Boots the stack (if not already up), POSTs a known-cooperative URL,
# polls /api/enrich/{job_id} until succeeded or fails out, and asserts
# the resulting CompanyFacts have non-trivial content.
#
# Exit 0 = the prep doc's "verify.sh prints OK" criterion is met.

set -euo pipefail

API="${API:-http://localhost:8000}"
TARGET="${TARGET:-https://anthropic.com}"
TIMEOUT="${TIMEOUT:-90}"   # seconds to wait for job to finish

echo "verify: API=$API target=$TARGET timeout=${TIMEOUT}s"

# 1. Ensure stack is up.
if ! curl -sf "$API/health" >/dev/null; then
  echo "verify: backend not responding; bringing stack up"
  docker compose up -d
  for i in $(seq 1 30); do
    if curl -sf "$API/health" >/dev/null; then break; fi
    sleep 2
  done
  curl -sf "$API/health" >/dev/null || { echo "verify: backend never came up"; exit 1; }
fi

# 2. Submit enrichment.
JOB_ID=$(curl -sf -X POST "$API/api/enrich" \
  -H 'content-type: application/json' \
  -d "{\"url\":\"$TARGET\"}" | python -c 'import sys, json; print(json.load(sys.stdin)["id"])')
echo "verify: submitted job=$JOB_ID"

# 3. Poll.
deadline=$((SECONDS + TIMEOUT))
while [ $SECONDS -lt $deadline ]; do
  RESP=$(curl -sf "$API/api/enrich/$JOB_ID")
  STATUS=$(echo "$RESP" | python -c 'import sys, json; print(json.load(sys.stdin)["status"])')
  case "$STATUS" in
    succeeded)
      echo "verify: succeeded"
      echo "$RESP" | python -m json.tool
      # 4. Sanity-assert: we got a non-empty industry and tech stack.
      echo "$RESP" | python -c '
import sys, json
d = json.load(sys.stdin)
c = d["company"]
assert c is not None, "no company payload"
assert c["industry"], "industry empty"
assert len(c["tech_stack"]) > 0, "tech_stack empty"
print("verify: OK")
'
      exit 0
      ;;
    failed)
      echo "verify: FAILED"
      echo "$RESP" | python -m json.tool
      exit 1
      ;;
    queued|running)
      echo "verify: status=$STATUS, polling..."
      sleep 3
      ;;
    *)
      echo "verify: unexpected status: $STATUS"
      exit 1
      ;;
  esac
done

echo "verify: TIMEOUT after ${TIMEOUT}s"
exit 1
