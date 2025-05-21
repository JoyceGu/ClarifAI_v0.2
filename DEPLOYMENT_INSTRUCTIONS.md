# ClarifAI Deployment Guide

This document provides detailed steps for deploying the ClarifAI application to Azure.

## Fixing Local Development Issues

The `ModuleNotFoundError: No module named 'psycopg2'` error you encountered when running the application locally has been resolved. This occurred because the .env file configured a PostgreSQL database connection, but PostgreSQL was not properly set up in the local environment.

### Development Environment Configuration

When developing locally, ensure:

1. **Clear or modify the DATABASE_URL environment variable**
   ```bash
   # Run the application with empty database URL to use SQLite
   export DATABASE_URL="" && export FLASK_ENV=development && flask run --port=8000
   ```

2. **Or create a .env.development file**
   ```
   # Flask application configuration - development environment
   FLASK_ENV=development
   # Comment out DATABASE_URL to use SQLite
   # DATABASE_URL=postgresql://...
   ```

### Using Quick Start Script

To simplify the local development process, we have created a quick start script:

```bash
# Give execution permissions to the script
chmod +x run_local.sh

# Run the application
./run_local.sh
```

This script automatically sets the correct environment variables and starts the application.

### Common Problem Solutions

1. **Database Connection Errors**:
   If you encounter errors like `could not translate host name "your-azure-postgres-server.postgres.database.azure.com" to address`, it means the database URL in the .env file is still being used. Solution:
   
   ```bash
   # Edit the .env file to comment out the database URL
   sed -i.bak 's/^DATABASE_URL=/#DATABASE_URL=/' .env
   
   # Or use the run_local.sh script
   ./run_local.sh
   ```

2. **SQLite Database Initialization**:
   If you need to reset or initialize the local SQLite database:
   
   ```bash
   export FLASK_APP=run.py FLASK_ENV=development
   flask db upgrade
   python init_users.py  # Optional, creates test users
   ```

## Azure Deployment Process

We have optimized the deployment process to address slow build times. Below are the complete deployment steps:

### 1. Pre-deployment Preparation

1. **Ensure Azure CLI is installed and configured**
   ```bash
   az --version
   az login
   ```

2. **Create a production environment configuration file**
   Create a .env.production file with the following content:
   ```
   # Flask application configuration - production environment
   FLASK_ENV=production
   DATABASE_URL=mssql+pymssql://username:password@server.database.windows.net:1433/dbname
   USE_AZURE_STORAGE=true
   # ...other Azure configurations...
   ```

### 2. Create Azure Resources

Run the optimized deployment script to create the required Azure resources:

```bash
./deploy_to_azure.sh
```

Note the resource names and information output by the script, including:
- Resource Group
- App Name
- SQL Server
- Storage Account
- App Service URL

### 3. Create Deployment Package

Use the optimized script to create the deployment package:

```bash
./prepare_deploy_package.sh
```

### 4. Deploy the Application

Use the following command to deploy the application:

```bash
# Use the resource group and application name from the script output
RESOURCE_GROUP="resource group name from script output"
APP_NAME="app name from script output"

# Deploy to production environment
az webapp deploy --resource-group $RESOURCE_GROUP --name $APP_NAME --src-path deployment/clarifai_app.zip --type zip
```

Or use deployment slots for zero-downtime deployment:

```bash
# Deploy to staging environment
az webapp deploy --resource-group $RESOURCE_GROUP --name $APP_NAME --src-path deployment/clarifai_app.zip --type zip --slot staging

# After verifying the staging environment is functioning correctly, swap to production
az webapp deployment slot swap --resource-group $RESOURCE_GROUP --name $APP_NAME --slot staging --target-slot production
```

### 5. Configure Azure Services

1. **Azure OpenAI Configuration**
   ```bash
   az webapp config appsettings set \
       --name $APP_NAME \
       --resource-group $RESOURCE_GROUP \
       --settings \
       AZURE_OPENAI_API_KEY="your-api-key" \
       AZURE_OPENAI_ENDPOINT="https://your-resource-name.openai.azure.com/" \
       AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4o-mini" \
       AZURE_OPENAI_API_VERSION="2025-04-15"
   ```

2. **Microsoft Entra ID Configuration**
   ```bash
   az webapp config appsettings set \
       --name $APP_NAME \
       --resource-group $RESOURCE_GROUP \
       --settings \
       ENTRA_CLIENT_ID="your-client-id" \
       ENTRA_CLIENT_SECRET="your-client-secret" \
       ENTRA_TENANT_ID="your-tenant-id" \
       ENTRA_REDIRECT_PATH="/auth/callback"
   ```

### 6. Monitor Deployment

Use the following commands to view deployment logs and status:

```bash
# Check deployment status
az webapp deployment list --name $APP_NAME --resource-group $RESOURCE_GROUP

# View application logs
az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP

# View application settings
az webapp config appsettings list --name $APP_NAME --resource-group $RESOURCE_GROUP
```

### 7. Access the Application

After deployment is complete, you can access the application at the following URL:

```
https://<app-name>.azurewebsites.net
```

## Deployment Optimization Summary

To address slow deployment issues, we made the following optimizations:

1. **Reduce Deployment Package Size**
   - Created a .deployignore file to exclude unnecessary files
   - Used rsync to filter out unwanted files

2. **Optimize Build Process**
   - Created a .deployment file to configure build parameters
   - Set SCM_DO_BUILD_DURING_DEPLOYMENT=true
   - Added build optimization configurations

3. **Improve App Service Performance**
   - Upgraded the App Service Plan from F1 free tier to B1 Basic tier
   - Enabled local cache functionality
   - Created deployment slots for zero-downtime deployment

4. **Enhance Deployment and Startup Scripts**
   - Optimized the startup script, added logging
   - Added environment detection to automatically adapt to different environments

For more deployment information, refer to the "Azure Deployment Guide" and "Deployment Optimization" sections in the README.md file. 