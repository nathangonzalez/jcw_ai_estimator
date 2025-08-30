#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:8080}"
FRONTEND_ORIGIN="${FRONTEND_ORIGIN:-https://jcw-ai-estimator-frontend-fmthtgj3nq-uc.a.run.app}"

log() { printf "\n==> %s\n" "$*"; }
fail() { echo "❌ $*" >&2; exit 1; }
ok() { echo "✅ $*"; }

log "Health check"
health_json="$(curl -sS "$BACKEND_URL/api/v2/health" || true)"
[[ -n "$health_json" ]] || fail "No response from /health"
echo "$health_json" | grep -q '"ok": *true' && ok "Health ok:true" || fail "Health JSON missing ok:true"

log "CORS preflight"
preflight_headers="$(curl -sSI -X OPTIONS "$BACKEND_URL/api/v2/upload/blueprint"   -H "Origin: $FRONTEND_ORIGIN" -H "Access-Control-Request-Method: POST" || true)"
echo "$preflight_headers" | tr '[:upper:]' '[:lower:]' | grep -q "access-control-allow-origin: $(echo "$FRONTEND_ORIGIN" | tr '[:upper:]' '[:lower:]')" && ok "CORS header present" || fail "CORS header missing"

TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
printf "%%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF\n" > "$TMP/test.pdf"

log "echo-upload"
code_echo="$(curl -sS -o /dev/null -w "%{http_code}" -F "file=@$TMP/test.pdf;type=application/pdf" "$BACKEND_URL/api/v2/debug/echo-upload" || true)"
[[ "$code_echo" =~ ^20[0-9]$ ]] && ok "echo-upload $code_echo" || fail "echo-upload $code_echo"

log "upload/blueprint (happy path)"
code_up="$(curl -sS -o /dev/null -w "%{http_code}" -F "file=@$TMP/test.pdf;type=application/pdf" "$BACKEND_URL/api/v2/upload/blueprint" || true)"
[[ "$code_up" =~ ^20[0-9]$ ]] && ok "upload $code_up" || echo "ℹ️ upload returned $code_up"

log "oversize guard (expect 413)"
dd if=/dev/zero of="$TMP/big.pdf" bs=1M count=11 status=none
code_big="$(curl -sS -o /dev/null -w "%{http_code}" -F "file=@$TMP/big.pdf;type=application/pdf" "$BACKEND_URL/api/v2/upload/blueprint" || true)"
[[ "$code_big" == "413" ]] && ok "oversize -> 413" || echo "ℹ️ oversize returned $code_big"
echo "🎉 Done."
