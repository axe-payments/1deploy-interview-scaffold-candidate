#!/usr/bin/env bash
#
# Post ONE example heartbeat to the running app, then look for the receipt in the app logs.
#
#   ./scripts/send_heartbeat.sh                       # the shared example (ns-fin-01)
#   ./scripts/send_heartbeat.sh hb-sup-02             # another device id from the fixture
#   URL=https://<tunnel>/inbound/heartbeat/ ./scripts/send_heartbeat.sh
#
# Only needs bash + curl.

set -euo pipefail

URL="${URL:-http://localhost:${APP_PORT:-8000}/inbound/heartbeat/}"
DEVICE="${1:-ns-fin-01}"

# Derive the department/organisation for the chosen device from the fixture.
read -r ORG DEPT < <(python3 - "$DEVICE" <<'PY'
import json, sys
data = json.load(open("fixtures/fleet-v1.json"))
device = next((d for d in data["devices"] if d["id"] == sys.argv[1]), None)
if device is None:
    sys.exit(f"unknown device id {sys.argv[1]!r}; see fixtures/fleet-v1.json")
dept = next(d for d in data["departments"] if d["id"] == device["department_id"])
print(dept["organisation_id"], dept["id"])
PY
)

NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
PAYLOAD=$(printf '{"organisation_id":"%s","department_id":"%s","device_id":"%s","sent_at":"%s","last_upload_at":"%s"}' \
  "$ORG" "$DEPT" "$DEVICE" "$NOW" "$NOW")

echo "POST $URL"
echo "  $PAYLOAD"
echo
curl -sS -w '\nHTTP %{http_code}\n' -X POST "$URL" -H "Content-Type: application/json" -d "$PAYLOAD"
echo
echo "Now look for 'Heartbeat received' in the app logs (docker compose --env-file env.local logs -f app)."
