#!/bin/sh
set -e

# Applies pending migrations, then replaces the shell with gunicorn so it receives signals.
# Fine for a single replica; run `migrate` as a separate release step if you scale out.
python manage.py migrate --noinput

exec gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers "${WEB_CONCURRENCY:-2}" \
    --timeout 30 \
    --access-logfile - \
    --error-logfile -
