#!/usr/bin/env bash
#
# Run pytest inside the running app container (no Python needed on your machine). No tests
# are supplied; this runs any you add. Extra arguments are passed to pytest:
#   ./scripts/test.sh -x -v

source "$(dirname "$0")/_compose.sh"

compose exec app python -m pytest "$@"
