from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=False)
    password_hash = db.Column(db.String(128), nullable=True)  # 对于Entra ID用户可以为空
    
    # 用户详细信息
    first_name = db.Column(db.String(50), nullable=True)
    last_name = db.Column(db.String(50), nullable=True)
    role = db.Column(db.String(20), default='user')
    
    # Microsoft Entra ID相关
    is_entra_user = db.Column(db.Boolean, default=False)
    entra_user_id = db.Column(db.String(128), unique=True, nullable=True)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # 关系
    created_tasks = db.relationship('Task', foreign_keys='Task.creator_id', backref='creator', lazy='dynamic')
    assigned_tasks = db.relationship('Task', foreign_keys='Task.assignee_id', backref='assignee', lazy='dynamic')
    uploaded_files = db.relationship('File', backref='uploader', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        if self.is_entra_user:
            # Entra ID用户不做本地密码验证
            return False
        return check_password_hash(self.password_hash, password)
        
    def __repr__(self):
        return f'<User {self.username}>'

# 剩余模型保持原样
class TaskPriority(str, enum.Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'
    
    def __str__(self):
        return self.value

class TaskStatus(str, enum.Enum):
    DRAFT = 'draft'
    VERIFIED = 'verified'
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    REVIEW = 'review'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'
    
    def __str__(self):
        return self.value
        
class OutputType(str, enum.Enum):
    REPORT = 'report'
    DASHBOARD = 'dashboard'
    API = 'api'
    MODEL = 'model'
    OTHER = 'other'
    
    def __str__(self):
        return self.value

class Task(db.Model):
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    business_goal = db.Column(db.Text, nullable=True)
    priority = db.Column(db.String(20), nullable=False, default=TaskPriority.MEDIUM)
    status = db.Column(db.String(20), nullable=False, default=TaskStatus.DRAFT)
    output_type = db.Column(db.String(20), nullable=False, default=OutputType.REPORT)
    
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    deadline = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    verification_result = db.Column(db.Text, nullable=True)
    
    files = db.relationship('File', backref='task', lazy='dynamic')
    
    def __repr__(self):
        return f'<Task {self.title}>'
        
class File(db.Model):
    __tablename__ = 'files'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    original_filename = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(100), nullable=False)
    
    uploader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    
    upload_time = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Azure Blob Storage相关字段
    is_blob = db.Column(db.Boolean, default=False)
    blob_url = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<File {self.original_filename}>' 