#!/usr/bin/env python
from flask import Flask, jsonify
import os

app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({
        "status": "success",
        "message": "简单的测试应用正在运行"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"})

@app.route('/info')
def info():
    return jsonify({
        "python_version": os.popen('python --version').read().strip(),
        "current_directory": os.getcwd(),
        "files": os.popen('ls -la').read().split('\n')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True) 