#!/usr/bin/env bash
# Render runs this script every time the site starts.
#
# The free Render plan has no persistent disk, so without DATABASE_URL the
# SQLite database lives only while the instance runs. That's why the
# database is created and filled with demo data on every start: the demo
# always has fresh deadlines and resets itself after visitors' changes.
set -o errexit

python manage.py migrate --no-input
python manage.py seed_demo_data
exec gunicorn config.wsgi:application \
    --bind "0.0.0.0:${PORT:-10000}" \
    --workers "${WEB_CONCURRENCY:-2}"
