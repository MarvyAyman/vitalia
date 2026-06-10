#!/usr/bin/env bash
# exit on error
set -o errexit

# Install project packages
pip install -r requirements.txt

# Collect static files for Django Admin layouts
python manage.py collectstatic --no-input

# Run database schema migrations
python manage.py migrate
