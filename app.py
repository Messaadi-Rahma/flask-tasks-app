import os
from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# Environment config
DATA_DIR = os.getenv('DATA_DIR', '/data')
TASKS_FILE = os.path.join(DATA_DIR, os.getenv('TASKS_FILENAME', 'tasks.json'))
SECRET_MESSAGE = os.getenv('SECRET_MESSAGE', 'No secret')
PORT = int(os.getenv('PORT', 5000))

@app.route('/')
def index():
    return f"DevOps Tasks API! Secret: {SECRET_MESSAGE}"

def save_tasks(tasks):
    try:
        with open(TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=2)
            f.flush()
            os.fsync(f.fileno())
        print(f"Saved to {TASKS_FILE}")
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

@app.route('/tasks', methods=['POST'])
def add_task():
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

@app.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(load_tasks())

if __name__ == '__main__':
    print(f"Using tasks file: {TASKS_FILE}")
    app.run(host='0.0.0.0', port=PORT, debug=True)