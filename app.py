import os
from flask import Flask, request, jsonify
import json
from prometheus_flask_exporter import PrometheusMetrics
import threading
import time

app = Flask(__name__)

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app, group_by='endpoint')

# Add custom metrics
REQUEST_COUNT = metrics.counter(
    'flask_http_request_count_total', 
    'Total HTTP Requests',
    labels={'method': lambda: request.method, 
            'endpoint': lambda: request.endpoint,
            'status': lambda r: r.status_code}
)

REQUEST_LATENCY = metrics.histogram(
    'flask_http_request_duration_seconds',
    'HTTP Request Latency',
    labels={'endpoint': lambda: request.endpoint}
)

CPU_USAGE = metrics.gauge('flask_cpu_usage_percent', 'CPU Usage Percent')
MEMORY_USAGE = metrics.gauge('flask_memory_usage_bytes', 'Memory Usage in Bytes')

# Environment config
DATA_DIR = os.getenv('DATA_DIR', '/data')
TASKS_FILE = os.path.join(DATA_DIR, os.getenv('TASKS_FILENAME', 'tasks.json'))
SECRET_MESSAGE = os.getenv('SECRET_MESSAGE', 'No secret')
PORT = int(os.getenv('PORT', 5000))
METRICS_PORT = int(os.getenv('METRICS_PORT', 5001))

def monitor_resources():
    """Background thread to monitor system resources"""
    while True:
        CPU_USAGE.set(psutil.cpu_percent())
        MEMORY_USAGE.set(psutil.Process().memory_info().rss)
        time.sleep(5)

@app.route('/')
def index():
    return f"DevOps Tasks API! Secret: {SECRET_MESSAGE}"

def save_tasks(tasks):
    try:
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
    except Exception as e:
        print(f"Load failed: {e}")
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
    
    # Start resource monitoring thread
    threading.Thread(target=monitor_resources, daemon=True).start()
    
    # Start metrics server on separate port
    metrics.start_http_server(METRICS_PORT)
    
    # Start main app
    app.run(host='0.0.0.0', port=PORT)