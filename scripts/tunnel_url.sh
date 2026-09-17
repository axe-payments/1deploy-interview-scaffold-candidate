#!/usr/bin/env bash
#
# Print the public URL of the running tunnel (waits up to ~30s for it to come up).
#
#   ./scripts/tunnel_url.sh              # whichever provider answers (labelled)
#   ./scripts/tunnel_url.sh cloudflared  # only cloudflared, fail if it is not up
#   ./scripts/tunnel_url.sh ngrok        # only ngrok, fail if it is not up
#
# Reads the providers' local APIs published on localhost by docker-compose.yml.
# Only needs bash + curl + python3.

set -euo pipefail

PROVIDER="${1:-any}"

cloudflared_url() {
  curl -sf http://localhost:2000/quicktunnel 2>/dev/null \
    | python3 -c 'import sys,json; h=json.load(sys.stdin).get("hostname",""); print("https://"+h if h else "")' 2>/dev/null || true
}
ngrok_url() {
  curl -sf http://localhost:4040/api/tunnels 2>/dev/null \
    | python3 -c 'import sys,json; t=[x["public_url"] for x in json.load(sys.stdin).get("tunnels",[]) if x.get("public_url","").startswith("https://")]; print(t[0] if t else "")' 2>/dev/null || true
}

for _ in $(seq 1 30); do
  case "$PROVIDER" in
    cloudflared) URL="$(cloudflared_url)"; [ -n "$URL" ] && { echo "$URL"; exit 0; } ;;
    ngrok)       URL="$(ngrok_url)";       [ -n "$URL" ] && { echo "$URL"; exit 0; } ;;
    any)
      C="$(cloudflared_url)"; N="$(ngrok_url)"
      if [ -n "$C$N" ]; then
        [ -n "$C" ] && echo "cloudflared: $C"
        [ -n "$N" ] && echo "ngrok:       $N"
        exit 0
      fi ;;
    *) echo "usage: $0 [cloudflared|ngrok]" >&2; exit 2 ;;
  esac
  sleep 1
done

echo "No public URL from '$PROVIDER' yet. Is the tunnel running? Start it with ./scripts/tunnel.sh${PROVIDER:+ }$( [ "$PROVIDER" = any ] || echo "$PROVIDER" )" >&2
exit 1
