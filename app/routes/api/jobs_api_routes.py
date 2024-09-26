
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required
from app.managers.job_manager import JobManager
from app.managers.user_manager import UserManager
from app.db.db_utils import get_db
from app.services.email_processor import EmailProcessor
from app.services.job_application_processor import JobApplicationProcessor
from app.services.task_queue import TaskQueue
from app.utils.decorators import role_required

jobs_api_bp = Blueprint('job_api', __name__)

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
    return api_response.to_dict()