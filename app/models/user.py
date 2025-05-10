from app import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime
import enum

class UserRole(enum.Enum):
    ADMIN = 'admin'
    PM = 'pm'
    RESEARCHER = 'researcher'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    username = db.Column(db.String(80), nullable=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.Enum(UserRole), default=UserRole.RESEARCHER)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # 关系
    tasks_created = db.relationship('Task', backref='creator', lazy='dynamic',
                                   foreign_keys='Task.creator_id')
    tasks_assigned = db.relationship('Task', backref='assignee', lazy='dynamic',
                                    foreign_keys='Task.assignee_id')
    
    def __init__(self, email, password, role=UserRole.RESEARCHER, username=None):
        self.email = email
        self.password = password
        self.role = role
        self.username = username or email.split('@')[0]
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
        
    @password.setter
    def password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.email}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) 