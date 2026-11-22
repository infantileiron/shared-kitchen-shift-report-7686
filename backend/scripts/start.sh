#!/bin/sh
set -eu
python -m scripts.migrate
if [ "${SEED_DEMO:-true}" = true ]; then
  python -m scripts.seed_demo || echo 'Demo seeding failed' >&2
fi
exec uvicorn src.main:app --host 0.0.0.0 --port 8000
