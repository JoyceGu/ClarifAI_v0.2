# ClarifAI - Intelligent Task Management Platform

ClarifAI is a Python Flask-based task management platform integrated with Azure OpenAI, providing task submission, validation, assignment, and tracking features.

## Core Features

1. **User Authentication System**
   - Login/Registration
   - Integration with Microsoft Entra ID (Azure AD)

2. **Task Management**
   - Submit new tasks/requirements
   - Assign tasks to team members
   - Track tasks assigned to yourself
   - View task history

3. **Intelligent Task Validation**
   - Use Azure OpenAI to validate task clarity and feasibility
   - Check for similar cases (via Knowledge Base API)

4. **File Management**
   - File upload/storage
   - File explorer and management interface

## Technology Stack

- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript (Bootstrap)
- **Database**: SQLite (development), PostgreSQL (production)
- **Authentication**: Flask-Login (local), Microsoft Entra ID (Azure deployment)
- **AI Integration**: Azure OpenAI
- **Cloud Deployment**: Azure App Service

## Azure Services Used

This application leverages the following Azure services:

- **Azure App Service**: Hosts the web application.
- **Azure SQL Database**: Stores production data.
- **Azure Blob Storage**: Stores uploaded files and documents.
- **Azure OpenAI Service**: Provides AI-powered task validation and analysis.
- **Microsoft Entra ID (Azure AD)**: Provides secure authentication and single sign-on.
- **Azure Key Vault**: Securely stores secrets and connection strings.
- **Azure Application Insights**: Monitors application health and logs.
- **App Service Plan**: Defines the compute resources for the web app.

## Installation Guide

1. Clone the repository

```bash
git clone [repository-url]
cd ClarifAI_v0.2
```

2. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # MacOS/Linux
# or
venv\Scripts\activate  # Windows
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Initialize the database

```bash
flask db init
flask db migrate
flask db upgrade
```

5. Run the application

```bash
flask run --port=8000
```

6. Access the application in your browser

```
http://localhost:8000
```

## Project Structure

```
ClarifAI/
├── app/
│   ├── __init__.py
│   ├── models/
│   ├── routes/
│   ├── static/
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   ├── templates/
│   └── utils/
├── migrations/
├── instance/
├── venv/
├── .gitignore
├── config.py
├── requirements.txt
└── README.md
```

## Azure Deployment Guide

### Prerequisites

1. Azure account
2. Azure CLI installed
3. Project configured locally

### Deployment Steps

#### 1. Configure Azure Services

Run the provided deployment script to create required Azure resources:

```bash
# Ensure the script is executable
chmod +x deploy_to_azure.sh
# Run the deployment script
./deploy_to_azure.sh
```

This script will automatically create the following Azure resources:
- Resource Group
- Azure SQL Server and Database
- Azure Blob Storage
- Application Insights
- Azure Key Vault
- App Service Plan
- Web App
- Azure OpenAI
- Microsoft Entra ID

#### 2. Prepare the Deployment Package

Run the following command to create the deployment package:

```bash
# Ensure the script is executable
chmod +x prepare_deploy_package.sh
# Create the deployment package
./prepare_deploy_package.sh
```

#### 3. Deploy the Application

```bash
# Replace with your resource group and app name
RESOURCE_GROUP="clarifai-resources"
APP_NAME="clarifai-app"

# Deploy to Azure
az webapp deployment source config-zip --resource-group $RESOURCE_GROUP --name $APP_NAME --src deployment/clarifai_app.zip
```

#### 4. Configure Azure OpenAI and Microsoft Entra ID

1. **Azure OpenAI Configuration**

   Create an Azure OpenAI resource in the Azure Portal, then update the app settings:
   
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

   Register a new application in Entra ID (Azure AD) via the Azure Portal, then update the app settings:
   
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

#### 5. Complete Deployment

After deployment, you can access your app at the Azure Web App URL:

```
https://clarifai-app.azurewebsites.net
```

#### 6. Post-Deployment Operations

1. Run database migrations (automatically executed in the startup script)
2. Monitor application performance via Azure Portal

### Troubleshooting

1. **View application logs**:
   ```bash
   az webapp log tail --name $APP_NAME --resource-group $RESOURCE_GROUP
   ```

2. **Check deployment status**:
   ```bash
   az webapp deployment list --name $APP_NAME --resource-group $RESOURCE_GROUP
   ```

3. **Restart the application**:
   ```bash
   az webapp restart --name $APP_NAME --resource-group $RESOURCE_GROUP
   ```

### Deployment Optimization

If experiencing slow deployment times, consider the following optimizations:

1. **Reduce deployment package size**:
   - Exclude unnecessary files using a `.deployignore` file
   - Remove static assets that can be served from a CDN
   - Use `.gitignore` patterns to exclude test files and development-only dependencies

2. **Optimize dependencies**:
   - Review and remove unused packages from `requirements.txt`
   - Use `pip-compile` to create a pinned requirements file to speed up installation
   - Consider using a custom Docker container with pre-installed dependencies

3. **Optimize App Service Plan**:
   - Upgrade from F1 free tier to a B1 or higher tier for faster deployments
   - Enable local cache for the App Service to reduce cold starts
   - Use deployment slots for zero-downtime deployments

4. **Enable build optimization**:
   - Set `SCM_DO_BUILD_DURING_DEPLOYMENT=true` in App Service configuration
   - Create a custom deployment script in `.deployment` file
   - Leverage Azure DevOps pipelines for more control over the build process

5. **Monitor deployment performance**:
   - Use the Azure CLI to get detailed deployment logs:
     ```bash
     az webapp log download --resource-group $RESOURCE_GROUP --name $APP_NAME
     ```
   - Check for timeout issues or resource constraints during deployment

## Roadmap

1. Basic features (authentication, task management, file upload)
2. Azure OpenAI integration
3. Microsoft Entra ID integration
4. Knowledge Base API integration
5. Azure deployment configuration

## Test Accounts

- PM: pm@test.com / password123
- Researcher: researcher@test.com / password123 