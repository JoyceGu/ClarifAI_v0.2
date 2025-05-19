#!/bin/bash
# Local development startup script
# This script sets the appropriate environment variables for local development
# and starts the Flask development server on port 8000

export FLASK_ENV=development FLASK_APP=run.py DATABASE_URL="" && flask run --port=8000
