#!/usr/bin/env bash
set -euo pipefail

# Wait for the database (simple loop; sync app, no extra deps).
echo "Waiting for database ${DB_HOST:-db}:${DB_PORT:-5432}…"
python - <<'PY'
import os, time, socket
host, port = os.getenv("DB_HOST","db"), int(os.getenv("DB_PORT","5432"))
for _ in range(60):
    try:
        socket.create_connection((host, port), timeout=2).close(); break
    except OSError:
        time.sleep(2)
else:
    raise SystemExit("Database not reachable")
PY

python manage.py migrate --noinput
python manage.py collectstatic --noinput

# Optional one-shot seed of the reference project (idempotent). Off by default.
if [ "${SEED_ON_START:-0}" = "1" ]; then
  python manage.py seed_prdc || true
fi

exec gunicorn config.wsgi:application \
     --bind 0.0.0.0:8000 \
     --workers "${GUNICORN_WORKERS:-3}" \
     --threads "${GUNICORN_THREADS:-2}" \
     --worker-class sync \
     --timeout "${GUNICORN_TIMEOUT:-120}" \
     --access-logfile - --error-logfile -
