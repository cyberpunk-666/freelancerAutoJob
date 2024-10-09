from datetime import datetime
import logging
import os
from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_required
from app.managers.job_manager import JobManager
from app.managers.user_manager import UserManager
from app.db.db_utils import get_db
from app.managers.user_preferences_manager import UserPreferencesManager
from app.models.api_response import APIResponse
from app.services.email_processor import EmailProcessor
from app.services.job_application_processor import JobApplicationProcessor
from app.services.task_queue import TaskQueue
from app.utils.decorators import role_required

jobs_api_bp = Blueprint('jobs_api', __name__)


@jobs_api_bp.route('/', methods=['GET'])
@login_required
def get_jobs():
    job_manager = JobManager()
    # Get paging parameters from request arguments with defaults
    page = request.args.get('page', default=1, type=int)
    page_size = request.args.get('page_size', default=10, type=int)

    # Fetch the paginated jobs
    jobs_response = job_manager.get_jobs_for_user(current_user.user_id, page=page, page_size=page_size)

    return jobs_response.to_dict()


@jobs_api_bp.route('/freelancer_jobs', methods=['GET'])
@login_required
def fetch_freelancer_jobs():
    job_manager = JobManager()
    api_response = job_manager.fetch_and_store_jobs()
    config_file_path = os.path.join(current_app.root_path, 'static', 'config', 'preferences.json')

    user_preferences_manager = UserPreferencesManager(config_file_path)
    preferences_response = user_preferences_manager.get_preferences_values(current_user.user_id)
    user_preferences = preferences_response.data if preferences_response.status == "success" else {}
    auto_process_jobs = user_preferences["auto_process_jobs"]
    user_id = current_user.user_id
    job_id = None
    if auto_process_jobs and api_response.status == "success":
        jobs_fetched = api_response.data
        task_queue = TaskQueue()
        for job in jobs_fetched:
            job_id = job["job_id"]
            task_queue.add_task(user_id, "process_job", {"job_id": job_id})

    return api_response.to_dict()


@jobs_api_bp.route('/poll-updates', methods=['GET'])
@login_required
def poll_updates():
    job_manager = JobManager()
    logging.info("Polling for job updates")

    last_sync = request.args.get('last_sync', None)
    if not last_sync:
        return APIResponse(status="error", message="Missing last_sync parameter", data=None).to_dict(), 400

    # Convert string to timestamp
    try:
        last_sync_dt = datetime.fromisoformat(last_sync)
    except ValueError:
        return APIResponse(status="error", message="Invalid last_sync format", data=None).to_dict(), 400

    api_response = job_manager.poll_updates_for_user(current_user.user_id, last_sync_dt)
    return api_response.to_dict()


@jobs_api_bp.route('/jobs', methods=['GET'])
@login_required
def get_jobs_for_user():
    job_manager = JobManager()

    # Get DataTables parameters
    draw = request.args.get('draw', type=int)
    start = request.args.get('start', type=int)
    length = request.args.get('length', type=int)
    search_value = request.args.get('search[value]', '')

    # Get sorting information
    order_column_index = request.args.get('order[0][column]', type=int)
    order_direction = request.args.get('order[0][dir]', 'desc')  # Default to descending if not provided

    # Dynamically get column information
    columns = []
    searchable_columns = []
    i = 0
    while f'columns[{i}][data]' in request.args:
        column_data = request.args.get(f'columns[{i}][data]')
        if not column_data:
            i += 1
            continue
        column_searchable = request.args.get(f'columns[{i}][searchable]') == 'true'
        columns.append({'data': column_data})
        if column_searchable:
            searchable_columns.append(column_data)
        i += 1

    # Set default sort column if no order is specified
    if order_column_index is None:
        sort_column = 'created_at' if 'created_at' in [col['data'] for col in columns] else columns[0]['data']
    else:
        sort_column = columns[order_column_index]['data'] if order_column_index < len(columns) else 'created_at'

    # Fetch jobs using the updated method
    jobs_response = job_manager.get_jobs_for_user(
        user_id=current_user.user_id,
        start=start,
        length=length,
        sort_column=sort_column,
        sort_order=order_direction.upper(),
        search_value=search_value,
        columns=columns,
        searchable_columns=searchable_columns,
    )

    if jobs_response.status == "failure":
        return jsonify({"error": jobs_response.message}), 404

    # Prepare DataTables response format
    response_data = {
        "draw": draw,
        "recordsTotal": jobs_response.data['recordsTotal'],
        "recordsFiltered": jobs_response.data['recordsFiltered'],
        "data": jobs_response.data['jobs'],
    }

    return jsonify(response_data)
