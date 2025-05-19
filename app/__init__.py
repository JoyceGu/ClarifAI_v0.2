from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config
import os
import logging

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page'
login_manager.login_message_category = 'info'

# 自定义Azure服务扩展
azure_insights_middleware = None
app_insights_tracer = None
entra_id_provider = None  # 将在create_app中初始化

def get_entra_id_provider():
    """获取Entra ID提供者实例，避免循环引用问题"""
    global entra_id_provider
    return entra_id_provider

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    if hasattr(config[config_name], 'init_app'):
        config[config_name].init_app(app)
    
    # 确保上传文件夹存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # 注册模板过滤器
    from app.utils.template_filters import filters_bp
    app.register_blueprint(filters_bp)
    
    # 注册蓝图
    from app.routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.routes.tasks import tasks as tasks_blueprint
    app.register_blueprint(tasks_blueprint, url_prefix='/tasks')
    
    from app.routes.files import files as files_blueprint
    app.register_blueprint(files_blueprint, url_prefix='/files')
    
    # 添加错误处理器
    from app.routes.errors import errors as errors_blueprint
    app.register_blueprint(errors_blueprint)
    
    # 根据环境初始化Azure服务
    init_azure_services(app)
    
    return app

def init_azure_services(app):
    """根据环境初始化Azure服务"""
    # 初始化Azure Application Insights
    if app.config.get('APPLICATIONINSIGHTS_CONNECTION_STRING'):
        try:
            # 在需要时才导入，避免循环依赖问题
            try:
                from opencensus.ext.azure.log_exporter import AzureLogHandler
                from opencensus.ext.azure.trace_exporter import AzureExporter
                from opencensus.ext.flask.flask_middleware import FlaskMiddleware
                from opencensus.trace.samplers import ProbabilitySampler
                from opencensus.trace.tracer import Tracer
                
                # 设置Azure Application Insights日志处理器
                azure_handler = AzureLogHandler(
                    connection_string=app.config['APPLICATIONINSIGHTS_CONNECTION_STRING']
                )
                azure_handler.setLevel(logging.INFO)
                app.logger.addHandler(azure_handler)
                
                # 设置Azure Application Insights分布式追踪
                global azure_insights_middleware, app_insights_tracer
                azure_insights_middleware = FlaskMiddleware(
                    app,
                    exporter=AzureExporter(connection_string=app.config['APPLICATIONINSIGHTS_CONNECTION_STRING']),
                    sampler=ProbabilitySampler(rate=1.0),
                )
                app_insights_tracer = Tracer(
                    exporter=AzureExporter(connection_string=app.config['APPLICATIONINSIGHTS_CONNECTION_STRING']),
                    sampler=ProbabilitySampler(rate=1.0),
                )
                
                app.logger.info("Azure Application Insights initialized")
            except ImportError:
                app.logger.warning("Azure Application Insights dependencies not installed, skipping initialization")
        except Exception as e:
            app.logger.error(f"Azure Application Insights initialization failed: {str(e)}")
    
    # 初始化Microsoft Entra ID
    if app.config.get('ENTRA_CLIENT_ID') and app.config.get('ENTRA_CLIENT_SECRET'):
        try:
            # 避免在应用启动时导入azure_auth，以防止循环引用
            from app.utils.azure_auth import EntraIDAuthProvider
            global entra_id_provider
            
            try:
                entra_id_provider = EntraIDAuthProvider(app)
                app.logger.info("Microsoft Entra ID integration initialized")
            except Exception as e:
                app.logger.error(f"Microsoft Entra ID initialization failed: {str(e)}")
                entra_id_provider = None
        except ImportError:
            app.logger.warning("Microsoft Entra ID dependencies not installed, skipping initialization")
    
    # 初始化Azure Storage（仅在生产模式下使用）
    if app.config.get('USE_AZURE_STORAGE') and app.config.get('AZURE_STORAGE_CONNECTION_STRING'):
        try:
            # 同样，这里延迟导入避免循环依赖
            try:
                from app.utils.azure_storage import init_blob_service
                init_blob_service(app)
                app.logger.info("Azure Blob Storage initialized")
            except Exception as e:
                app.logger.error(f"Azure Blob Storage initialization failed: {str(e)}")
        except ImportError:
            app.logger.warning("Azure Blob Storage dependencies not installed, skipping initialization")

# 避免循环导入
from app.models.user import User
from app.models.task import Task
from app.models.file import File 