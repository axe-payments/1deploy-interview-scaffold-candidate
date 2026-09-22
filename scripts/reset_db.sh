#!/usr/bin/env bash
#
# DESTRUCTIVE. Deletes this project's local Postgres volume and recreates it, so the
# next start rebuilds the schema and reseeds the 2 / 4 / 12 inventory. Any rows or tables
# you added are gone. You do not need it for model changes (a changed model's table is
# rebuilt on restart, see app/schema.py); it is for starting over from nothing.
#
# Only this Compose project's containers and volume are removed, nothing else in Docker.
#
#   ./scripts/reset_db.sh

source "$(dirname "$0")/_compose.sh"

echo "This deletes the local interview database (volume '$(basename "$ROOT")_pgdata')"
echo "including anything you added to it. The app and other containers are stopped too."
read -r -p "Type 'reset' to continue: " ANSWER
[ "$ANSWER" = "reset" ] || { echo "Aborted."; exit 1; }

compose down --volumes --remove-orphans
echo
echo "Done. Start again with:  docker compose --env-file env.local up --build"
echo "(the schema is recreated and the inventory reseeded on startup)"
