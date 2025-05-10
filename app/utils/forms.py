from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, DateField, MultipleFileField
from wtforms.validators import DataRequired, Email, Length, ValidationError
from app.models import TaskPriority, OutputType
from flask_wtf.file import FileField, FileAllowed
from datetime import date

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class TaskForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=5, max=200)])
    business_goal = TextAreaField('Business Goal and Data Scope')
    priority = SelectField('Priority', choices=[
        (TaskPriority.LOW.value, 'Low'),
        (TaskPriority.MEDIUM.value, 'Medium'),
        (TaskPriority.HIGH.value, 'High'),
        (TaskPriority.CRITICAL.value, 'Critical')
    ], validators=[DataRequired()], coerce=str)
    output_type = SelectField('Expected Output', choices=[
        (OutputType.REPORT.value, 'Report'),
        (OutputType.DASHBOARD.value, 'Dashboard'),
        (OutputType.API.value, 'API'),
        (OutputType.MODEL.value, 'Model'),
        (OutputType.OTHER.value, 'Other')
    ], validators=[DataRequired()], coerce=str)
    deadline = DateField('Deadline', format='%Y-%m-%d', validators=[DataRequired()])
    assignee_id = SelectField('Assign To', coerce=int)
    supporting_files = MultipleFileField('Supporting Files')
    submit = SubmitField('Submit')
    
    def validate_deadline(self, field):
        if field.data < date.today():
            raise ValidationError('Deadline cannot be in the past.') 