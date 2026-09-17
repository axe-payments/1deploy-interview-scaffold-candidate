#!/usr/bin/env bash
#
# Start the app WITH a public tunnel so the interviewer can send heartbeats to it.
#
#   ./scripts/tunnel.sh              # cloudflared quick tunnel (default; no account needed)
#   ./scripts/tunnel.sh ngrok        # ngrok (needs NGROK_AUTHTOKEN in env.local)
#
# Runs in the foreground like `docker compose up`. Once it is up, run
# ./scripts/tunnel_url.sh in another terminal to print the public URL, and send that
# URL to the interviewer. Only the app port (8000) is exposed; never the database.

source "$(dirname "$0")/_compose.sh"

PROVIDER="${1:-cloudflared}"
case "$PROVIDER" in
  cloudflared) PROFILE="tunnel" ;;
  ngrok)
    PROFILE="ngrok"
    if [ -z "$(env_value NGROK_AUTHTOKEN)" ]; then
      echo "NGROK_AUTHTOKEN is blank in env.local. Set it, or use the default cloudflared tunnel:" >&2
      echo "  ./scripts/tunnel.sh" >&2
      exit 1
    fi
    ;;
  *) echo "usage: $0 [cloudflared|ngrok]" >&2; exit 2 ;;
esac

echo "Starting the app with the '$PROVIDER' tunnel. In another terminal run:"
echo "  ./scripts/tunnel_url.sh $PROVIDER"
echo
compose --profile "$PROFILE" up --build
