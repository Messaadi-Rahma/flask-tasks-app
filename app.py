import os
import json
from flask import (
    Flask, request, jsonify, render_template,
    redirect, url_for, session, flash
)
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

# 🔹 Enable Prometheus monitoring (auto exposes /metrics)
metrics = PrometheusMetrics(app)

# Environment config
DATA_DIR = os.getenv('DATA_DIR', '/data')         # use PVC mount path
TASKS_FILE = os.path.join(DATA_DIR, os.getenv('TASKS_FILENAME', 'tasks.json'))
SECRET_MESSAGE = os.getenv('SECRET_MESSAGE', 'No secret')
PORT = int(os.getenv('PORT', 5000))
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-change-me')

# Dummy user credentials
USERS = {"admin": "1234"}

# -----------------------
# Helpers
# -----------------------
def save_tasks(tasks):
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        return True
    except Exception as e:
        print(f"Save failed: {e}")
        return False

def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    try:
        with open(TASKS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

# -----------------------
# Pages (UI)
# -----------------------
@app.route('/')
def index():
    return redirect(url_for('home_page'))

@app.route('/home')
def home_page():
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('tasks_page'))
        else:
            flash("Invalid username or password")

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/tasks', methods=['GET'])
def tasks_page():
    if 'user' not in session:
        return redirect(url_for('login'))
    tasks = load_tasks()
    return render_template('tasks.html', tasks=tasks)

@app.route('/add', methods=['POST'])
def add_task_web():
    if 'user' not in session:
        return redirect(url_for('login'))

    title = request.form.get('task')
    if title:
        tasks = load_tasks()
        new_id = max((t['id'] for t in tasks), default=0) + 1
        tasks.append({"id": new_id, "title": title})
        save_tasks(tasks)

    return redirect(url_for('tasks_page'))

@app.route('/delete/<int:task_id>', methods=['POST'])
def delete_task_web(task_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    tasks = [t for t in load_tasks() if t['id'] != task_id]
    save_tasks(tasks)
    return redirect(url_for('tasks_page'))

# -----------------------
# API (JSON endpoints)
# -----------------------
@app.route('/api/tasks', methods=['GET'])
def api_get_tasks():
    return jsonify(load_tasks())

@app.route('/api/tasks', methods=['POST'])
def api_add_task():
    if not request.is_json:
        return jsonify({"error": "JSON required"}), 400

    data = request.get_json()
    if not data.get('title'):
        return jsonify({"error": "Title required"}), 400

    tasks = load_tasks()
    new_id = max((task['id'] for task in tasks), default=0) + 1
    new_task = {"id": new_id, "title": data['title']}
    tasks.append(new_task)

    if not save_tasks(tasks):
        return jsonify({"error": "Failed to save"}), 500

    return jsonify(new_task), 201

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def api_delete_task(task_id):
    tasks = [t for t in load_tasks() if t['id'] != task_id]
    if not save_tasks(tasks):
        return jsonify({"error": "Failed to delete"}), 500
    return '', 204

# -----------------------
if __name__ == '__main__':
    print(f"Using tasks file: {TASKS_FILE}")
    app.run(host='0.0.0.0', port=PORT, debug=True)
