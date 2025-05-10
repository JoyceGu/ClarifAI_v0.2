from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from app.models import Task, TaskPriority, TaskStatus, OutputType, User
from app.utils.forms import TaskForm
from app import db
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from app.models import File
import uuid

tasks = Blueprint('tasks', __name__)

@tasks.route('/')
@login_required
def all_tasks():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 过滤条件
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    
    # 构建查询
    query = Task.query
    
    if status_filter:
        query = query.filter(Task.status == TaskStatus(status_filter))
    
    if priority_filter:
        query = query.filter(Task.priority == TaskPriority(priority_filter))
    
    tasks_list = query.order_by(Task.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('tasks/all_tasks.html', 
                           tasks=tasks_list,
                           statuses=TaskStatus,
                           priorities=TaskPriority)

@tasks.route('/my-tasks')
@login_required
def my_tasks():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # 过滤条件
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    
    # 构建查询 - 获取分配给当前用户的任务
    query = Task.query.filter_by(assignee_id=current_user.id)
    
    if status_filter:
        query = query.filter(Task.status == TaskStatus(status_filter))
    
    if priority_filter:
        query = query.filter(Task.priority == TaskPriority(priority_filter))
    
    tasks_list = query.order_by(Task.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('tasks/my_tasks.html', 
                           tasks=tasks_list,
                           statuses=TaskStatus,
                           priorities=TaskPriority)

@tasks.route('/create', methods=['GET', 'POST'])
@login_required
def create_task():
    form = TaskForm()
    # 获取可分配的用户列表
    form.assignee_id.choices = [(0, 'Unassigned')] + [
        (u.id, u.username) for u in User.query.order_by(User.username).all()
    ]
    
    if form.validate_on_submit():
        task = Task(
            title=form.title.data,
            business_goal=form.business_goal.data,
            priority=form.priority.data,
            output_type=form.output_type.data,
            deadline=form.deadline.data,
            creator_id=current_user.id,
            status=TaskStatus.DRAFT
        )
        
        if form.assignee_id.data > 0:
            task.assignee_id = form.assignee_id.data
        
        db.session.add(task)
        db.session.commit()
        
        # 处理上传文件
        if 'supporting_files' in request.files:
            files = request.files.getlist('supporting_files')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = str(uuid.uuid4()) + '_' + filename
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    
                    # 创建文件记录
                    file_record = File(
                        filename=unique_filename,
                        original_filename=filename,
                        file_path=unique_filename,
                        file_size=os.path.getsize(file_path),
                        file_type=file.content_type,
                        uploader_id=current_user.id,
                        task_id=task.id
                    )
                    db.session.add(file_record)
            
            db.session.commit()
        
        flash('Task created successfully', 'success')
        return redirect(url_for('tasks.view_task', task_id=task.id))
    
    return render_template('tasks/create_task.html', 
                           form=form, 
                           priorities=TaskPriority,
                           output_types=OutputType)

@tasks.route('/<int:task_id>')
@login_required
def view_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    return render_template('tasks/view_task.html', task=task)

@tasks.route('/<int:task_id>/verify', methods=['POST'])
@login_required
def verify_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # 这里应该调用Azure OpenAI API进行验证
    # 暂时使用简单模拟
    verification_result = "Task verification completed. The requirement is clear and feasible."
    
    task.verification_result = verification_result
    task.status = TaskStatus.VERIFIED
    db.session.commit()
    
    return jsonify({
        'status': 'success',
        'result': verification_result
    })

@tasks.route('/<int:task_id>/submit', methods=['POST'])
@login_required
def submit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if task.status == TaskStatus.DRAFT or task.status == TaskStatus.VERIFIED:
        task.status = TaskStatus.PENDING
        db.session.commit()
        flash('Task submitted successfully', 'success')
    else:
        flash('Cannot submit task in current status', 'danger')
    
    return redirect(url_for('tasks.view_task', task_id=task.id))

@tasks.route('/<int:task_id>/update-status', methods=['POST'])
@login_required
def update_task_status(task_id):
    task = Task.query.get_or_404(task_id)
    new_status = request.form.get('status')
    
    if new_status and new_status in [s.value for s in TaskStatus]:
        task.status = TaskStatus(new_status)
        db.session.commit()
        flash('Task status updated', 'success')
    else:
        flash('Invalid status', 'danger')
    
    return redirect(url_for('tasks.view_task', task_id=task.id)) 