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
import json
import requests
import random  # Temporary use, can be removed after connecting to Azure OpenAI

tasks = Blueprint('tasks', __name__)

@tasks.route('/')
@login_required
def all_tasks():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Filter conditions
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    
    # Build query
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
    
    # Filter conditions
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    
    # Build query - get tasks assigned to current user
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
    # Get list of assignable users
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
        
        # Process uploaded files
        if 'supporting_files' in request.files:
            files = request.files.getlist('supporting_files')
            for file in files:
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    unique_filename = str(uuid.uuid4()) + '_' + filename
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(file_path)
                    
                    # Create file record
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

@tasks.route('/api/verify', methods=['POST'])
@login_required
def api_verify_task():
    data = request.json
    title = data.get('title', '')
    business_goal = data.get('business_goal', '')
    
    if not title or not business_goal:
        return jsonify({
            'status': 'error',
            'message': 'Missing required fields'
        }), 400
    
    try:
        # Azure OpenAI API call
        # Configure your Azure OpenAI API key and endpoint here
        azure_api_key = os.environ.get('AZURE_OPENAI_API_KEY', '')
        azure_endpoint = os.environ.get('AZURE_OPENAI_ENDPOINT', '')
        azure_deployment_name = os.environ.get('AZURE_OPENAI_DEPLOYMENT_NAME', 'gpt-4o-mini')
        azure_api_version = os.environ.get('AZURE_OPENAI_API_VERSION', '2025-04-15')
        
        if azure_api_key and azure_endpoint:
            # Build API request
            url = f"{azure_endpoint}/openai/deployments/{azure_deployment_name}/chat/completions?api-version={azure_api_version}"
            headers = {
                "Content-Type": "application/json",
                "api-key": azure_api_key
            }
            
            # Build request content for Azure OpenAI
            payload = {
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are a senior data scientist and researcher at a large technology company. You are evaluating the clarity and feasibility of a new requirement. Please provide a clarity score (0-100) and a feasibility score (0-100), along with detailed feedback. Your feedback should identify any areas of ambiguity, suggest what additional information might be needed, and assess if the requirement is technically feasible with current technologies."
                    },
                    {
                        "role": "user",
                        "content": f"Please evaluate this requirement:\nTitle: {title}\nBusiness Goal: {business_goal}\n\nProvide your analysis in this JSON format:\n```json\n{{\"clarity_score\": (number 0-100), \"feasibility_score\": (number 0-100), \"feedback\": \"Your detailed feedback here\"}}\n```"
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 800,
                "n": 1
            }
            
            # Send request to Azure OpenAI
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                response_data = response.json()
                assistant_message = response_data['choices'][0]['message']['content']
                
                # Extract JSON part from response
                try:
                    # Find JSON formatted string
                    json_start = assistant_message.find('{')
                    json_end = assistant_message.rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        json_str = assistant_message[json_start:json_end]
                        result = json.loads(json_str)
                        
                        # Ensure all required fields are present
                        if all(k in result for k in ['clarity_score', 'feasibility_score', 'feedback']):
                            return jsonify(result)
                except Exception as e:
                    current_app.logger.error(f"Error parsing AI response: {str(e)}")
            
            # If Azure OpenAI call fails or parsing fails, return mock data
            current_app.logger.warning("Failed to get valid response from Azure OpenAI, using mock data")
        
        # Use mock data (when Azure OpenAI API is unavailable)
        # This part can be removed in actual deployment
        clarity_score = random.randint(65, 95)
        feasibility_score = random.randint(60, 90)
        
        feedback_templates = [
            "The requirement is generally clear but could benefit from more specific metrics for success. Consider defining key performance indicators (KPIs) that would demonstrate successful implementation. The feasibility is good, though implementation timeline might need adjustment based on available resources.",
            "Your business goal is well-defined, but the scope needs more precise boundaries. Try specifying which data sources will be used and exact time ranges. From a technical perspective, this is feasible but would require significant data processing capabilities.",
            "This requirement has good clarity in terms of the business objective, but lacks detail on technical requirements. The feasibility depends on data availability and quality. Please provide more information about existing data infrastructure and quality."
        ]
        
        return jsonify({
            'clarity_score': clarity_score,
            'feasibility_score': feasibility_score,
            'feedback': random.choice(feedback_templates)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error during verification: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'Internal server error during verification'
        }), 500

@tasks.route('/<int:task_id>/verify', methods=['POST'])
@login_required
def verify_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    # Should call Azure OpenAI API for verification
    # Using simple simulation for now
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