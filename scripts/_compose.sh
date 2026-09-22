#!/usr/bin/env bash
# Shared helper: run docker compose with env.local. Sourced by the other scripts.
#
# Every docker compose command (up, exec, logs, down ...) must be given --env-file env.local,
# because Compose re-reads it each time to fill in the ${...} values in docker-compose.yml.

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [ ! -f env.local ]; then
  echo "env.local not found. Create it first:  cp env.example env.local  (then fill it in)" >&2
  exit 1
fi

compose() {
  docker compose --env-file env.local "$@"
}

# Effective value of one setting, with the same precedence Compose uses for ${...}
# interpolation: a variable that is SET in your shell wins even when it is empty (Compose
# then applies its own :- default), otherwise env.local, otherwise empty. Callers apply
# the same defaults as docker-compose.yml.
env_value() {
  if [ -n "${!1+set}" ]; then
    printf '%s\n' "${!1}"
  else
    grep -E "^$1=" env.local | head -1 | cut -d= -f2- || true
  fi
}

# Host URL of the running app, taken from the container's actual published port so it can
# never disagree with what Compose started. Falls back to the configured port when the
# stack is not running.
app_url() {
  local mapping port
  mapping="$(compose port app 8000 2>/dev/null | tail -1 || true)"
  port="${mapping##*:}"
  if [ -z "$port" ]; then port="$(env_value APP_PORT)"; port="${port:-8000}"; fi
  printf 'http://localhost:%s\n' "$port"
}
