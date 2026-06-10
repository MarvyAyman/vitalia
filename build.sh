#!/usr/bin/env bash
# exit on error
set -o errexit

# Install project packages
pip install -r requirements.txt

# Clear out any stale compiled static asset files
python manage.py collectstatic --no-input

# Force a clean, verified database schema migration stamp
python manage.py migrate --no-input

# Create your admin credentials safely
python manage.py create_admin
