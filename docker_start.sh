#!/usr/bin/env bash
set -e

echo "[startup] Starting bgutil PO token server on port 4416..."
npx bgutil-ytdlp-pot-provider serve &

# Wait up to 30 s for the bgutil server to accept connections
MAX_WAIT=30
WAITED=0
until curl -sf http://localhost:4416/ > /dev/null 2>&1 || [ "$WAITED" -ge "$MAX_WAIT" ]; do
    sleep 1
    WAITED=$((WAITED + 1))
done

if [ "$WAITED" -ge "$MAX_WAIT" ]; then
    echo "[startup] WARNING: bgutil server did not respond within ${MAX_WAIT}s, continuing anyway..."
else
    echo "[startup] bgutil server is ready (${WAITED}s)."
fi

echo "[startup] Starting gunicorn..."
exec gunicorn server:app --workers 1 --threads 4 --timeout 120
