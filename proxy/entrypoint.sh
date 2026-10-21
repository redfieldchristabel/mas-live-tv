#!/bin/sh
set -e

# Chromium needs a writable home and --no-sandbox in containers
export HOME=/tmp
mkdir -p /tmp/chrome-proxy-profile

# First refresh runs in the background so the proxy is up immediately;
# playlists serve whatever is in the mounted channels.json until tokens land.
python3 /app/proxy.py &
PROXY_PID=$!

# Give chromium a moment, then let the proxy's refresh loop take over.
wait $PROXY_PID
