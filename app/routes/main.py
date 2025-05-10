from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app.models import Task, TaskStatus

main = Blueprint('main', __name__)

@main.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))

@main.route('/dashboard')
@login_required
def dashboard():
    # 获取用户任务统计
    tasks_created = Task.query.filter_by(creator_id=current_user.id).count()
    tasks_assigned = Task.query.filter_by(assignee_id=current_user.id).count()
    tasks_pending = Task.query.filter_by(
        assignee_id=current_user.id, 
        status=TaskStatus.PENDING
    ).count()
    tasks_in_progress = Task.query.filter_by(
        assignee_id=current_user.id, 
        status=TaskStatus.IN_PROGRESS
    ).count()
    
    # 获取用户最近的任务
    recent_tasks = Task.query.filter(
        (Task.creator_id == current_user.id) | (Task.assignee_id == current_user.id)
    ).order_by(Task.updated_at.desc()).limit(5).all()
    
    stats = {
        'tasks_created': tasks_created,
        'tasks_assigned': tasks_assigned,
        'tasks_pending': tasks_pending,
        'tasks_in_progress': tasks_in_progress
    }
    
    return render_template('main/dashboard.html', 
                           stats=stats, 
                           recent_tasks=recent_tasks) 