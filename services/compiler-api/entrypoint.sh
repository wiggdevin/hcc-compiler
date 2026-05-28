#!/bin/sh
# Seed /data/library.db from the baked image seed if it's missing OR
# the image's seed is newer than the volume copy. This keeps the volume's
# library.db in sync with whatever was baked into the latest deploy.
set -e

SEED=/data-seed/library.db
DEST=${LIBRARY_DB_PATH:-/data/library.db}

if [ -f "$SEED" ]; then
  if [ ! -f "$DEST" ] || [ "$SEED" -nt "$DEST" ]; then
    echo "[entrypoint] seeding $DEST from $SEED" >&2
    cp "$SEED" "$DEST"
  fi
fi

exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8080}"
