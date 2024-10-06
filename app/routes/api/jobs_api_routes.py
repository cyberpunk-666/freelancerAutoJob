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
    jobs = job_manager.get_jobs_for_user(current_user.user_id)
    if jobs is None:
        return jsonify({"error": "No jobs found for the user"}), 404
    return jobs.to_dict()


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
