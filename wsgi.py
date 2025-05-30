"""
WSGI entry point for Azure App Service deployment
"""
import os
import sys

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app

# Create Flask application instance with production config for Azure
config_name = os.environ.get('FLASK_CONFIG') or 'production'
app = create_app(config_name)

if __name__ == "__main__":
    app.run() 