#!/usr/bin/env bash
# Render runs this script when it builds a new version of the site.
set -o errexit

pip install -r requirements.txt
python manage.py collectstatic --no-input
