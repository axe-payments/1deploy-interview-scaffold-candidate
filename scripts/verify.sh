#!/usr/bin/env bash
#
# Check that the stack is up and correctly seeded: /health, /docs, and the inventory counts
# (2 organisations, 4 departments, 12 devices on a fresh database).
#
#   ./scripts/verify.sh

source "$(dirname "$0")/_compose.sh"

APP="$(app_url)"

echo "== /health ($APP)"
curl -sS "$APP/health"; echo
echo "== /docs"
curl -sS -o /dev/null -w 'HTTP %{http_code}\n' "$APP/docs"
echo "== seed counts (expected on a fresh database: 2 / 4 / 12)"
# psql runs with the credentials the postgres container itself was started with.
compose exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "
  select '"'"'organisations'"'"', count(*) from organisations
  union all select '"'"'departments'"'"', count(*) from departments
  union all select '"'"'devices'"'"', count(*) from devices;"'

echo "== public URL (only when a tunnel profile is running)"
curl -sS "$APP/tunnel/"; echo
