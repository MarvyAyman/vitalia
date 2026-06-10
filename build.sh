#!/usr/bin/env bash
# exit on error
set -o errexit

# Install packages
pip install -r requirements.txt

# Collect Static files
python manage.py collectstatic --no-input

# Run migrations
python manage.py migrate