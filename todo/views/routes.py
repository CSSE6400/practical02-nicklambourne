import sqlite3
from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
import datetime


api = Blueprint("api", __name__, url_prefix="/api/v1")


@api.route("/health")
def health():
    return jsonify({"status": "ok"})


@api.route("/todos", methods=["GET"])
def get_todos():
    todos = Todo.query.filter(
        Todo.completed.in_(
            (True,) if request.args.get("completed", None) else (True, False)
        ),
        Todo.deadline_at
        <= datetime.datetime.now()
        + datetime.timedelta(days=int(request.args.get("window", None)))
        if request.args.get("window", None)
        else Todo.deadline_at >= datetime.datetime.min,
    )

    result = []
    for todo in todos:
        result.append(todo.to_dict())
    return jsonify(result)


@api.route("/todos/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({"error": "Todo not found"}), 404
    return jsonify(todo.to_dict())


@api.route("/todos", methods=["POST"])
def create_todo():
    try:
        todo = Todo(**request.json)
        if "deadline_at" in request.json:
            todo.deadline_at = datetime.datetime.fromisoformat(request.json.get("deadline_at"))
        # Adds a new record to the database or will update an existing record
        db.session.add(todo)
        # Commits the changes to the database, this must be called for the changes to be saved
        db.session.commit()
        return jsonify(todo.to_dict()), 201
    except:
        return jsonify({f"error": "Invalid ToDo content: {error}"}), 400


@api.route("/todos/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({"error": "Todo not found"}), 404
    if request.json.get("id", None) and request.json.get("id", None) != todo_id:
        return jsonify({"error": "Cannot change ID of Todo"}), 400
    for field in request.json.keys():
        if field not in Todo.attribute_names(Todo):
            return jsonify({"error": "Invalid field name"}), 400
    todo.title = request.json.get("title", todo.title)
    todo.description = request.json.get("description", todo.description)
    todo.completed = request.json.get("completed", todo.completed)
    todo.deadline_at = request.json.get("deadline_at", todo.deadline_at)
    db.session.commit()

    return jsonify(todo.to_dict())


@api.route("/todos/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200
