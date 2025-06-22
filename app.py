from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

TASKS_FILE = "tasks.json"


@app.route('/')
def index():
    return "Bienvenue sur l’API des tâches DevOps ! Utilisez /tasks pour interagir."


# Charger les tâches depuis le fichier JSON
def load_tasks():
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r") as f:
        return json.load(f)

# Sauvegarder les tâches
def save_tasks(tasks):
    with open(TASKS_FILE, "w") as f:
        json.dump(tasks, f, indent=4)

# GET: récupérer toutes les tâches
@app.route("/tasks", methods=["GET"])
def get_tasks():
    tasks = load_tasks()
    return jsonify(tasks)

# POST: ajouter une nouvelle tâche
@app.route("/tasks", methods=["POST"])
def add_task():
    data = request.json
    tasks = load_tasks()
    new_id = tasks[-1]["id"] + 1 if tasks else 1
    new_task = {"id": new_id, "title": data["title"]}
    tasks.append(new_task)
    save_tasks(tasks)
    return jsonify(new_task), 201

# DELETE: supprimer une tâche par ID
@app.route("/tasks/<int:task_id>", methods=["DELETE"])
def delete_task(task_id):
    tasks = load_tasks()
    tasks = [t for t in tasks if t["id"] != task_id]
    save_tasks(tasks)
    return jsonify({"message": f"Task {task_id} deleted"})
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
