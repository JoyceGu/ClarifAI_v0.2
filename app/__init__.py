from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from config import config
import os

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
bcrypt = Bcrypt()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 确保上传文件夹存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    
    # 注册模板过滤器
    from app.utils.template_filters import filters_bp
    app.register_blueprint(filters_bp)
    
    # 注册蓝图
    from app.routes.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.routes.tasks import tasks as tasks_blueprint
    app.register_blueprint(tasks_blueprint, url_prefix='/tasks')
    
    from app.routes.files import files as files_blueprint
    app.register_blueprint(files_blueprint, url_prefix='/files')
    
    # 添加错误处理器
    from app.routes.errors import errors as errors_blueprint
    app.register_blueprint(errors_blueprint)
    
    return app 