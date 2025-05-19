#!/bin/bash
echo "Starting minimal app..."
export PYTHONUNBUFFERED=1 
export FLASK_APP=minimal_app.py
export FLASK_ENV=production

python --version
ls -la
echo "Dependencies installed:"
pip list

exec gunicorn --bind=0.0.0.0 --timeout=600 --log-level=debug minimal_app:app
