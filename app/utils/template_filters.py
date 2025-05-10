from flask import Blueprint, Markup
import datetime

filters_bp = Blueprint('filters', __name__)

@filters_bp.app_template_filter('nl2br')
def nl2br(value):
    """将换行符转换为HTML <br> 标签"""
    if not value:
        return ''
    return Markup(value.replace('\n', '<br>'))

@filters_bp.app_template_filter('format_date')
def format_date(value, format='%Y-%m-%d'):
    """格式化日期"""
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.datetime.strptime(value, '%Y-%m-%d')
        except ValueError:
            return value
    return value.strftime(format)

@filters_bp.app_template_filter('format_datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M'):
    """格式化日期时间"""
    if not value:
        return ''
    if isinstance(value, str):
        try:
            value = datetime.datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime(format)

@filters_bp.app_template_filter('file_size_format')
def file_size_format(size_in_bytes):
    """将字节转换为可读格式"""
    if not size_in_bytes:
        return '0 B'
    
    size = float(size_in_bytes)
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024 