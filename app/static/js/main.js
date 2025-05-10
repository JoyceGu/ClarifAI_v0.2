// 在文档加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 自动关闭提示消息
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const closeButton = alert.querySelector('.btn-close');
            if (closeButton) {
                closeButton.click();
            }
        }, 5000);
    });
    
    // 任务详情页中添加nl2br功能
    const businessGoalEl = document.querySelector('.business-goal-content');
    if (businessGoalEl) {
        businessGoalEl.innerHTML = nl2br(businessGoalEl.textContent);
    }
    
    // 初始化任何Bootstrap工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
});

// 文本转HTML功能（nl2br）
function nl2br(str) {
    if (typeof str === 'undefined' || str === null) {
        return '';
    }
    return (str + '').replace(/(\r\n|\n\r|\r|\n)/g, '<br>');
}

// AJAX表单提交（支持)
function submitFormWithAjax(formId, successCallback) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const formData = new FormData(form);
        const url = form.getAttribute('action');
        const method = form.getAttribute('method') || 'POST';
        
        fetch(url, {
            method: method,
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (typeof successCallback === 'function') {
                successCallback(data);
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
    });
} 