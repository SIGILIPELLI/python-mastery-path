#!/bin/bash
# Push a status update to the owner's WhatsApp via the running bridge.
# Usage: ./notify.sh "message text"   (or pipe: echo "msg" | ./notify.sh)
# Exits 0 on success; non-zero (with a note on stderr) if the bridge is down.
set -euo pipefail
PORT=$(node -e "console.log(require('$(dirname "$0")/config.json').port)" 2>/dev/null || echo 8787)
if [ $# -gt 0 ]; then MSG="$*"; else MSG="$(cat)"; fi
if [ -z "$MSG" ]; then echo "notify.sh: empty message" >&2; exit 2; fi
if ! curl -sf --max-time 15 -X POST --data-binary "$MSG" "http://127.0.0.1:${PORT}/send" >/dev/null; then
  echo "notify.sh: WhatsApp bridge not reachable on port ${PORT} (is it running?)" >&2
  exit 1
fi
