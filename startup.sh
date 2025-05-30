#!/bin/bash
# startup.sh - Azure Web App startup script for ClarifAI application

echo "Starting ClarifAI application setup..."

# Set Python path to include application directory
export PYTHONPATH=$PYTHONPATH:/home/site/wwwroot

# Set environment variable for Flask
export FLASK_APP=run.py
export FLASK_ENV=production

# Database migration
echo "Running database migrations if needed..."
if [ -d "migrations" ]; then
    python -m flask db upgrade
    if [ $? -ne 0 ]; then
        echo "WARNING: Database migration may have failed. Continuing anyway..."
    else
        echo "Database migration completed successfully."
    fi
else
    echo "No migrations directory found. Skipping database migration."
fi

# Initialize users if required (only run if specified via env var)
if [ "$INIT_USERS" = "true" ]; then
    echo "Initializing default users..."
    python init_users.py
fi

echo "Starting the application server..."
# Use run:app to match your project structure (run.py imports and creates app)
gunicorn --bind=0.0.0.0:8000 --workers=4 --timeout=600 --access-logfile="-" --error-logfile="-" run:app
