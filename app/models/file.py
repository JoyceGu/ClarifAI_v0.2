from app import db
from datetime import datetime
import os
from flask import current_app

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_type = db.Column(db.String(100), nullable=False)
    
    # 关系
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id'), nullable=True)
    
    # 时间戳
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<File {self.id}: {self.original_filename}>'
    
    @property
    def full_path(self):
        return os.path.join(current_app.config['UPLOAD_FOLDER'], self.file_path)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'uploaded_at': self.uploaded_at.isoformat(),
            'uploader_id': self.uploader_id,
            'task_id': self.task_id
        } 