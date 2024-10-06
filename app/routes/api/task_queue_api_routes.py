from flask import Blueprint

from app.utils.decorators import role_required
from flask import render_template
from flask import render_template

from app.services.task_queue import TaskQueue
from flask_login import current_user, login_required
from flask import request


task_queue_bp = Blueprint('task_queue', __name__)


@task_queue_bp.route('/add_task', methods=['POST'])
@login_required
def add_task():
    task_queue = TaskQueue()
    user_id = current_user.user_id  # You can also fetch user_id from request.json if needed

    # Parse the incoming JSON payload
    data = request.get_json()  # This is where JSON data will be parsed

    if not data:
        return {'error': 'Invalid or missing JSON payload'}, 400

    # Extract task data from the JSON payload
    task_data = data.get('task_data')
    task_type = data.get('type')

    if not task_data or not task_type:
        return {'error': 'Missing task data or task type'}, 400

    # Check if the type is registred with get_callback_names
    if task_type not in task_queue.get_callback_names():
        return {'error': 'Invalid task type'}, 400

    # Process the task
    response = task_queue.add_task(user_id, task_type, task_data)

    return response.to_dict(), 200


@task_queue_bp.route('/get_tasks')
@login_required
def get_tasks():
    task_queue = TaskQueue()
    response = task_queue.get_tasks(current_user.user_id)
    return response.to_dict()


@task_queue_bp.route('/has_task')
@login_required
def has_task_for_user():
    task_queue = TaskQueue()
    response = task_queue.has_task_for_user(current_user.user_id)
    return response.to_dict()


@task_queue_bp.route('/task_count')
@login_required
def task_count_for_user():
    task_queue = TaskQueue()
    response = task_queue.get_task_count_for_user(current_user.user_id)
    return response.to_dict()
