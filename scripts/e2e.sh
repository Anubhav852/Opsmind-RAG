#!/usr/bin/env bash
API="${1:-http://localhost:8000}"
ORIGIN="${2:-http://localhost:5173}"
pass=0; fail=0
ok()  { echo "  PASS  $1"; pass=$((pass+1)); }
bad() { echo "  FAIL  $1  ($2)"; fail=$((fail+1)); }
req() { curl -s -o /tmp/e2e_body -w "%{http_code}" "$@"; }
js()  { python3 -c "import json; d=json.load(open('/tmp/e2e_body')); print($1)" 2>/dev/null; }
tok() { req -m 90 -X POST "$API/auth/token" -H 'content-type: application/json' -d "{\"user\":\"$1\",\"groups\":$2}" >/dev/null; js "d['token']"; }

echo "Target API: $API   Frontend origin: $ORIGIN"
read -r SVC TS TRUTH < <(python3 -c "import json; g=[x for x in map(json.loads,open('data/ground_truth.jsonl')) if x['split']=='test'][0]; print(g['alert_service'], g['alert_ts'], g['root_service'])")
echo "Test incident: alert on '$SVC' at $TS (true root service: $TRUTH)"

echo; echo "[1] Basics"
c=$(req -m 120 "$API/health"); [ "$c" = 200 ] && ok "health" || bad "health" "HTTP $c; cold start? wait 60s and retry"
c=$(req -X POST "$API/search" -H 'content-type: application/json' -d '{}'); { [ "$c" = 401 ] || [ "$c" = 403 ]; } && ok "request without token is rejected" || bad "no-token rejection" "HTTP $c"
hdr=$(curl -s -D - -o /dev/null -m 30 -X OPTIONS "$API/investigate" -H "Origin: $ORIGIN" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: authorization,content-type")
echo "$hdr" | grep -qi "access-control-allow-origin: $ORIGIN" && ok "CORS allows $ORIGIN" || bad "CORS allows $ORIGIN" "set CORS_ORIGINS on the API"

echo; echo "[2] Auth"
SRE=$(tok e2e-sre '["public","sre"]'); PUB=$(tok e2e-pub '["public"]')
if [ -z "$SRE" ]; then bad "token endpoint" "no token; DEMO_MODE=false gives 404 on purpose"; echo; echo "Stopping: the remaining tests need DEMO_MODE=true"; echo "Result: $pass passed, $fail failed"; exit 1; fi
ok "tokens issued"

echo; echo "[3] Retrieval (needs database + loaded data)"
c=$(req -m 180 -X POST "$API/search" -H "authorization: Bearer $SRE" -H 'content-type: application/json' -d "{\"query\":\"recent deploy or config change\",\"at\":\"$TS\"}")
if [ "$c" = 200 ]; then n=$(js "len(d)"); [ "${n:-0}" -gt 0 ] && ok "search returned $n events" || bad "search" "200 but empty: no data loaded in the database"; else bad "search" "HTTP $c (500 usually means no database)"; fi

echo; echo "[4] Investigation (needs LLM; can take 1-3 minutes)"
c=$(req -m 900 -X POST "$API/investigate" -H "authorization: Bearer $SRE" -H 'content-type: application/json' -d "{\"alert_service\":\"$SVC\",\"alert_ts\":\"$TS\"}")
ID=""
if [ "$c" = 200 ]; then
  st=$(js "d['status']"); svc=$(js "d['report']['root_cause_service']"); ID=$(js "d['id']")
  echo "        status=$st  model says '$svc'  truth='$TRUTH'"
  { [ "$st" = verified ] || [ "$st" = insufficient_evidence ]; } && ok "investigation completed ($st)" || bad "investigation" "unexpected status '$st'"
else bad "investigation" "HTTP $c (500 = missing LLM or database settings)"; fi

echo; echo "[5] Approval and permissions"
if [ -n "$ID" ]; then
  c=$(req -X POST "$API/investigations/$ID/approve" -H "authorization: Bearer $PUB"); [ "$c" = 403 ] && ok "non-sre user cannot approve" || bad "non-sre approve" "HTTP $c"
  c=$(req -X POST "$API/investigations/$ID/approve" -H "authorization: Bearer $SRE"); [ "$c" = 200 ] && ok "sre user can approve" || bad "sre approve" "HTTP $c"
  c=$(req -X POST "$API/investigations/$ID/approve" -H "authorization: Bearer $SRE"); [ "$c" = 404 ] && ok "second approval is rejected" || bad "double approve" "HTTP $c"
else echo "  skipped (no investigation id)"; fi

echo; echo "[6] Rate limit (30 requests per minute)"
RL=$(tok e2e-rl '["public","sre"]'); n429=0
for i in $(seq 1 40); do c=$(req -m 20 -X POST "$API/investigations/00000000-0000-0000-0000-000000000000/approve" -H "authorization: Bearer $RL"); [ "$c" = 429 ] && n429=$((n429+1)); done
[ "$n429" -gt 0 ] && ok "limiter answered 429 $n429 times" || bad "rate limit" "never hit 429; is Redis connected?"

echo; echo "Result: $pass passed, $fail failed"
[ "$fail" -eq 0 ]
