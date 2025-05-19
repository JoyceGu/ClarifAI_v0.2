#!/bin/bash
# Prepare Azure Deployment Package - Optimized Version

echo "======== Preparing Optimized Azure Deployment Package ========"

# Ensure directory exists
mkdir -p deployment

# Clean up old files
if [ -f "deployment/clarifai_app.zip" ]; then
    echo "Deleting old deployment package..."
    rm deployment/clarifai_app.zip
fi

# Create temporary deployment directory
echo "Preparing deployment files..."
TEMP_DIR="deployment/temp"
mkdir -p $TEMP_DIR

# Use rsync to exclude files listed in .deployignore
if [ -f ".deployignore" ]; then
    echo "Using .deployignore to exclude unnecessary files..."
    rsync -av --exclude-from='.deployignore' . $TEMP_DIR/
else
    # If .deployignore file doesn't exist, use basic copy
    echo "Warning: .deployignore file not found, copying only basic files..."
    cp -r app $TEMP_DIR/
    cp -r migrations $TEMP_DIR/
    cp requirements.txt $TEMP_DIR/
    cp config.py $TEMP_DIR/
    cp run.py $TEMP_DIR/
    cp web.config $TEMP_DIR/
    cp .env.example $TEMP_DIR/.env.example
fi

# Create simplified requirements.txt to speed up deployment
echo "Creating optimized requirements.txt..."
if command -v pip-compile &> /dev/null; then
    echo "# Automatically generated optimized dependencies" > $TEMP_DIR/requirements-optimized.txt
    pip-compile requirements.txt --output-file=- | grep -v '^#' | grep -v '^-e' >> $TEMP_DIR/requirements-optimized.txt
    # Replace original requirements.txt
    mv $TEMP_DIR/requirements-optimized.txt $TEMP_DIR/requirements.txt
else
    echo "Warning: pip-compile not installed, skipping dependency optimization"
fi

# Create .deployment file to optimize deployment process
cat > $TEMP_DIR/.deployment << 'EOF'
[config]
SCM_DO_BUILD_DURING_DEPLOYMENT=true
command = bash ./startup.sh
EOF

# Create optimized startup script
cat > $TEMP_DIR/startup.sh << 'EOF'
#!/bin/bash
# Post-deployment Initialization Script - Optimized Version

# Set up log file
LOG_FILE="startup_log.txt"
exec > >(tee -a $LOG_FILE) 2>&1

echo "=============== Starting Deployment Initialization [$(date)] ==============="

# Initialize environment
export FLASK_APP=run.py
export FLASK_ENV=production
export PYTHONUNBUFFERED=1

# Display environment details for debugging
echo "Python version: $(python --version)"
echo "Current directory: $(pwd)"
echo "Directory contents: $(ls -la)"

# Set Azure App Service environment variables to avoid slow Python build process
export SCM_DO_BUILD_DURING_DEPLOYMENT=true

# Check if requirements are installed
echo "Checking Python packages..."
pip list

# Verify database configuration
echo "Database URL: $DATABASE_URL"
if [ -z "$DATABASE_URL" ]; then
    echo "WARNING: DATABASE_URL is not set, this may cause issues!"
fi

echo "Initializing database..."
flask db upgrade || {
    echo "WARNING: Database migration failed. Continuing anyway..."
}

# Create initial test users (if they don't exist)
echo "Attempting to create initial test users..."
python << 'PYTHON_SCRIPT'
from app import create_app, db
from app.models.user import User, UserRole
from werkzeug.security import generate_password_hash
import sys
import traceback

try:
    print("Creating app context...")
    app = create_app('production')
    with app.app_context():
        print("Checking for existing users...")
        # Check if users already exist
        if User.query.count() == 0:
            print("No users found. Creating initial test users...")
            # Create PM user
            pm_user = User(
                email='pm@test.com',
                username='Product Manager',
                role=UserRole.PM
            )
            pm_user.password_hash = generate_password_hash('password123')
            
            # Create Researcher user
            researcher_user = User(
                email='researcher@test.com',
                username='Researcher',
                role=UserRole.RESEARCHER
            )
            researcher_user.password_hash = generate_password_hash('password123')
            
            db.session.add(pm_user)
            db.session.add(researcher_user)
            db.session.commit()
            print("Initial test users created successfully")
        else:
            print("Users already exist, skipping initial user creation")
except Exception as e:
    print(f"Error creating initial users: {str(e)}")
    traceback.print_exc()
PYTHON_SCRIPT

# Make the application correctly load Azure configuration
echo "Optimizing Azure service connection configuration..."
if [ -n "$WEBSITE_SITE_NAME" ]; then  # Check if running in Azure environment
    echo "Running in Azure environment, enabling application cache..."
    touch .skip-lock  # Avoid rebuilding each time
    
    # Create web.debug.config
    if [ ! -f "web.debug.config" ]; then
        cp web.config web.debug.config
    fi
fi

# Ensure gunicorn is available
if ! command -v gunicorn &> /dev/null; then
    echo "WARNING: gunicorn not found! Installing..."
    pip install gunicorn
fi

echo "Testing application startup..."
python -c "from app import create_app; app = create_app('production'); print('Application initialization test successful')" || {
    echo "ERROR: Application could not be initialized!"
}

echo "=============== Initialization Complete [$(date)] ==============="
echo "Startup script completed. The application should now be available."
EOF

# Make script executable
chmod +x $TEMP_DIR/startup.sh

# Create zip file
echo "Creating optimized deployment package..."
cd $TEMP_DIR
zip -r ../clarifai_app.zip ./* .deployment
cd ../..

# Calculate deployment package size
PACKAGE_SIZE=$(du -h deployment/clarifai_app.zip | cut -f1)

# Clean up temporary files
echo "Cleaning up temporary files..."
rm -rf $TEMP_DIR

echo "Deployment package created: $(pwd)/deployment/clarifai_app.zip (Size: $PACKAGE_SIZE)"
echo "Completed ✓" 