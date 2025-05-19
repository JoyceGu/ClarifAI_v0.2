import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'clarifai.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload configuration
    # Local upload configuration (development environment)
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Azure Blob Storage (production environment)
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING')
    AZURE_STORAGE_CONTAINER_NAME = os.environ.get('AZURE_STORAGE_CONTAINER_NAME', 'file-uploads')
    
    # Azure OpenAI configuration
    AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY', '')
    AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT', '')
    AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini')
    AZURE_OPENAI_API_VERSION = os.environ.get('AZURE_OPENAI_API_VERSION', '2025-04-15')
    
    # Azure Application Insights
    APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING')
    APPLICATIONINSIGHTS_ROLE_NAME = os.environ.get('APPLICATIONINSIGHTS_ROLE_NAME', 'clarifai-webapp')
    
    # Azure Key Vault
    AZURE_KEY_VAULT_URL = os.environ.get('AZURE_KEY_VAULT_URL')
    
    # Microsoft Entra ID configuration
    ENTRA_CLIENT_ID = os.environ.get('ENTRA_CLIENT_ID')
    ENTRA_CLIENT_SECRET = os.environ.get('ENTRA_CLIENT_SECRET')
    ENTRA_TENANT_ID = os.environ.get('ENTRA_TENANT_ID')
    ENTRA_AUTHORITY = os.environ.get('ENTRA_AUTHORITY', 
                                  f"https://login.microsoftonline.com/{os.environ.get('ENTRA_TENANT_ID')}")
    ENTRA_REDIRECT_PATH = os.environ.get('ENTRA_REDIRECT_PATH', '/auth/callback')
    ENTRA_SCOPE = os.environ.get('ENTRA_SCOPE', 'user.read')
    
    # Logging configuration
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() == 'true'
    
    @classmethod
    def init_app(cls, app):
        """Base configuration initialization"""
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    # Local environment prioritizes local file system storage
    USE_AZURE_STORAGE = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'test.db')
    WTF_CSRF_ENABLED = False
    USE_AZURE_STORAGE = False

class ProductionConfig(Config):
    # Production environment configuration
    DEBUG = False
    TESTING = False
    USE_AZURE_STORAGE = True
    
    # SSL configuration
    SSL_REDIRECT = os.environ.get('SSL_REDIRECT', 'false').lower() == 'true'
    
    # Proxy server configuration (if running behind a reverse proxy)
    PREFERRED_URL_SCHEME = 'https'
    
    @classmethod
    def init_app(cls, app):
        # Production environment specific initialization
        Config.init_app(app)
        
        # Logging configuration - output to stdout for Azure to capture
        if cls.LOG_TO_STDOUT:
            import logging
            from logging import StreamHandler
            file_handler = StreamHandler()
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
        # If the application is behind a proxy server
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 