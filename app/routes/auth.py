from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db
from datetime import datetime
from app.utils.forms import LoginForm
from werkzeug.urls import url_parse

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.verify_password(form.password.data):
            flash('Invalid email or password', 'danger')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        # 更新最后登录时间
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        
        return redirect(next_page)
    
    # 示例账号
    test_accounts = [
        {'role': 'PM', 'email': 'pm@test.com', 'password': 'password123'},
        {'role': 'Researcher', 'email': 'researcher@test.com', 'password': 'password123'}
    ]
    
    return render_template('auth/login.html', form=form, test_accounts=test_accounts)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

# 注册功能可选，暂不实现 