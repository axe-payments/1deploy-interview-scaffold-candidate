#!/usr/bin/env bash
#
# Run the test-suite inside the running app container (no Python needed on your machine).
# Extra arguments are passed to pytest:  ./scripts/test.sh -k inbound -v
#
# Tests use a throwaway SQLite database and a fake Slack transport; they never touch
# Postgres or Slack.

source "$(dirname "$0")/_compose.sh"

compose exec app python -m pytest "$@"
