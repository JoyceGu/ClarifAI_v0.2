from app import db
from datetime import datetime
import enum

class TaskPriority(enum.Enum):
    LOW = 'low'
    MEDIUM = 'medium'
    HIGH = 'high'
    CRITICAL = 'critical'

class TaskStatus(enum.Enum):
    DRAFT = 'draft'
    PENDING = 'pending'
    VERIFIED = 'verified'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    REJECTED = 'rejected'

class OutputType(enum.Enum):
    REPORT = 'report'
    DASHBOARD = 'dashboard'
    API = 'api'
    MODEL = 'model'
    OTHER = 'other'

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    business_goal = db.Column(db.Text, nullable=True)
    priority = db.Column(db.Enum(TaskPriority), default=TaskPriority.MEDIUM)
    status = db.Column(db.Enum(TaskStatus), default=TaskStatus.DRAFT)
    output_type = db.Column(db.Enum(OutputType), default=OutputType.REPORT)
    deadline = db.Column(db.Date, nullable=True)
    
    # 关系
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 验证结果
    verification_result = db.Column(db.Text, nullable=True)
    
    # 任务关联的文件
    files = db.relationship('File', backref='task', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Task {self.id}: {self.title}>'
        
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'business_goal': self.business_goal,
            'priority': self.priority.value,
            'status': self.status.value,
            'output_type': self.output_type.value,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'creator_id': self.creator_id,
            'assignee_id': self.assignee_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        } 