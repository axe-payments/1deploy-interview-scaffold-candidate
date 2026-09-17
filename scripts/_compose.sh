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
# interpolation: a variable exported in your shell wins, then env.local, else empty.
env_value() {
  local exported="${!1:-}"
  if [ -n "$exported" ]; then
    printf '%s\n' "$exported"
  else
    grep -E "^$1=" env.local | head -1 | cut -d= -f2- || true
  fi
}
