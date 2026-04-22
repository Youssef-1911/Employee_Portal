#!/usr/bin/env bash
# infra/run_sast_webhook.sh
# Runs Semgrep against the repo and POSTs the SARIF output to ThreatGPT.
# Usage: ./run_sast_webhook.sh

set -e

# ── Config ─────────────────────────────────────────────────────────────────
# Set these before running, or export them in your shell
THREATGPT_WEBHOOK_URL="${THREATGPT_WEBHOOK_URL:-http://localhost:8000/api/webhooks/sast}"
THREATGPT_PROJECT_ID="${THREATGPT_PROJECT_ID:-}"       # your ThreatGPT project UUID
THREATGPT_API_KEY="${THREATGPT_API_KEY:-}"             # if your webhook requires auth
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUTPUT_FILE="/tmp/semgrep_results.sarif.json"

echo "=========================================="
echo "  ThreatGPT SAST Webhook Runner"
echo "=========================================="
echo "Repo:    $REPO_ROOT"
echo "Webhook: $THREATGPT_WEBHOOK_URL"
echo ""

# ── Step 1: Run Semgrep ────────────────────────────────────────────────────
echo "[1/3] Running Semgrep..."

semgrep \
  --config "$REPO_ROOT/infra/.semgrep.yml" \
  --sarif \
  --output "$OUTPUT_FILE" \
  "$REPO_ROOT" \
  || true   # semgrep exits non-zero when findings exist — continue anyway

if [ ! -f "$OUTPUT_FILE" ]; then
  echo "ERROR: Semgrep did not produce output at $OUTPUT_FILE"
  exit 1
fi

FINDING_COUNT=$(python3 -c "
import json, sys
data = json.load(open('$OUTPUT_FILE'))
print(len(data['runs'][0]['results']))
" 2>/dev/null || echo "unknown")

echo "    Semgrep complete. Findings: $FINDING_COUNT"
echo "    Output: $OUTPUT_FILE"
echo ""

# ── Step 2: Optionally inject project ID into the SARIF ───────────────────
if [ -n "$THREATGPT_PROJECT_ID" ]; then
  echo "[2/3] Injecting project ID into SARIF..."
  python3 - <<EOF
import json

with open("$OUTPUT_FILE") as f:
    sarif = json.load(f)

# Add project ID as a custom property in the run
sarif["runs"][0]["properties"] = sarif["runs"][0].get("properties", {})
sarif["runs"][0]["properties"]["threatgpt_project_id"] = "$THREATGPT_PROJECT_ID"

with open("$OUTPUT_FILE", "w") as f:
    json.dump(sarif, f, indent=2)

print("    Project ID injected.")
EOF
else
  echo "[2/3] Skipping project ID injection (THREATGPT_PROJECT_ID not set)"
fi
echo ""

# ── Step 3: POST to ThreatGPT webhook ─────────────────────────────────────
echo "[3/3] Sending SARIF to ThreatGPT webhook..."

CURL_ARGS=(
  -s
  -o /tmp/webhook_response.json
  -w "%{http_code}"
  -X POST
  "$THREATGPT_WEBHOOK_URL"
  -H "Content-Type: application/json"
)

# Add auth header if API key is set
if [ -n "$THREATGPT_API_KEY" ]; then
  CURL_ARGS+=(-H "X-API-Key: $THREATGPT_API_KEY")
fi

CURL_ARGS+=(--data-binary "@$OUTPUT_FILE")

HTTP_STATUS=$(curl "${CURL_ARGS[@]}")

echo ""
echo "    HTTP Status: $HTTP_STATUS"
echo "    Response:"
cat /tmp/webhook_response.json 2>/dev/null || echo "(no response body)"
echo ""

if [[ "$HTTP_STATUS" == 2* ]]; then
  echo "✅ SARIF successfully sent to ThreatGPT."
  echo "   Check your project in ThreatGPT — new SAST evidence should appear."
else
  echo "❌ Webhook returned HTTP $HTTP_STATUS."
  echo "   Check THREATGPT_WEBHOOK_URL and that your ThreatGPT instance is running."
  exit 1
fi

echo ""
echo "=========================================="
echo "  Done."
echo "=========================================="
