import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    
    # 数据库配置 - 简化为SQLite，避免PostgreSQL连接问题
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'clarifai.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # 上传文件配置
    # 本地上传配置（开发环境）
    UPLOAD_FOLDER = os.path.join(basedir, 'app', 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    
    # Azure Blob Storage（生产环境）- 改为可选
    AZURE_STORAGE_CONNECTION_STRING = os.environ.get('AZURE_STORAGE_CONNECTION_STRING', '')
    AZURE_STORAGE_CONTAINER_NAME = os.environ.get('AZURE_STORAGE_CONTAINER_NAME', 'file-uploads')
    
    # Azure OpenAI配置 - 改为可选
    AZURE_OPENAI_API_KEY = os.environ.get('AZURE_OPENAI_API_KEY', '')
    AZURE_OPENAI_ENDPOINT = os.environ.get('AZURE_OPENAI_ENDPOINT', '')
    AZURE_OPENAI_DEPLOYMENT_NAME = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini')
    AZURE_OPENAI_API_VERSION = os.environ.get('AZURE_OPENAI_API_VERSION', '2025-04-15')
    
    # Azure Application Insights - 改为可选
    APPLICATIONINSIGHTS_CONNECTION_STRING = os.environ.get('APPLICATIONINSIGHTS_CONNECTION_STRING', '')
    APPLICATIONINSIGHTS_ROLE_NAME = os.environ.get('APPLICATIONINSIGHTS_ROLE_NAME', 'clarifai-webapp')
    
    # Azure Key Vault - 改为可选
    AZURE_KEY_VAULT_URL = os.environ.get('AZURE_KEY_VAULT_URL', '')
    
    # Microsoft Entra ID配置 - 改为可选
    ENTRA_CLIENT_ID = os.environ.get('ENTRA_CLIENT_ID', '')
    ENTRA_CLIENT_SECRET = os.environ.get('ENTRA_CLIENT_SECRET', '')
    ENTRA_TENANT_ID = os.environ.get('ENTRA_TENANT_ID', '')
    ENTRA_AUTHORITY = os.environ.get('ENTRA_AUTHORITY', '')
    ENTRA_REDIRECT_PATH = os.environ.get('ENTRA_REDIRECT_PATH', '/auth/callback')
    ENTRA_SCOPE = os.environ.get('ENTRA_SCOPE', 'user.read')
    
    # 日志配置
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'false').lower() == 'true'
    
    @classmethod
    def init_app(cls, app):
        """基础配置初始化"""
        pass

class DevelopmentConfig(Config):
    DEBUG = True
    # 本地环境优先使用本地文件系统存储
    USE_AZURE_STORAGE = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'test.db')
    WTF_CSRF_ENABLED = False
    USE_AZURE_STORAGE = False

class ProductionConfig(Config):
    # 生产环境配置
    DEBUG = False
    TESTING = False
    # 临时禁用Azure Storage，让应用先能启动
    USE_AZURE_STORAGE = False
    
    # SSL配置
    SSL_REDIRECT = os.environ.get('SSL_REDIRECT', 'false').lower() == 'true'
    
    # 代理服务器配置 (如果在反向代理后面运行)
    PREFERRED_URL_SCHEME = 'https'
    
    @classmethod
    def init_app(cls, app):
        # 生产环境特定初始化
        Config.init_app(app)
        
        # 日志配置 - 输出到stdout以便由Azure捕获
        if cls.LOG_TO_STDOUT:
            import logging
            from logging import StreamHandler
            file_handler = StreamHandler()
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)
            
        # 如果应用在代理服务器后面
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
} 