from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app, send_from_directory
from flask_login import login_required, current_user
from app.models import File
from app import db
import os
from werkzeug.utils import secure_filename
import uuid

files = Blueprint('files', __name__)

@files.route('/')
@login_required
def file_explorer():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # 获取所有文件
    files_list = File.query.order_by(
        File.uploaded_at.desc()
    ).paginate(page=page, per_page=per_page)
    
    return render_template('files/explorer.html', files=files_list)

@files.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        files = request.files.getlist('file')
        
        uploaded_files = []
        for file in files:
            if file.filename == '':
                continue
            
            if file:
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
                    uploader_id=current_user.id
                )
                db.session.add(file_record)
                uploaded_files.append(filename)
        
        if uploaded_files:
            db.session.commit()
            flash(f'Uploaded {len(uploaded_files)} files successfully', 'success')
            return redirect(url_for('files.file_explorer'))
    
    return render_template('files/upload.html')

@files.route('/<int:file_id>')
@login_required
def download_file(file_id):
    file = File.query.get_or_404(file_id)
    
    return send_from_directory(
        directory=current_app.config['UPLOAD_FOLDER'],
        path=file.filename,
        as_attachment=True,
        download_name=file.original_filename
    )

@files.route('/<int:file_id>/delete', methods=['POST'])
@login_required
def delete_file(file_id):
    file = File.query.get_or_404(file_id)
    
    try:
        # 删除物理文件
        os.remove(os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename))
    except Exception as e:
        # 文件可能已经不存在，记录错误但继续
        print(f"Error deleting file: {e}")
    
    # 删除数据库记录
    db.session.delete(file)
    db.session.commit()
    
    flash('File deleted successfully', 'success')
    return redirect(url_for('files.file_explorer')) 