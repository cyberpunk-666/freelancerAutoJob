
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

@jobs_api_bp.route('/fetch_jobs_from_email', methods=['POST'])
@login_required
def fetch_jobs_from_email():
    
    email_processor = EmailProcessor()
    api_response = email_processor.fetch_jobs_from_email(current_user.user_id)

    if api_response.status == "success":
        response_data = api_response.data
    else:
        response_data = {
            "error": api_response.message,
            "job_list": []  # Returning an empty list in case of failure
        }

    return jsonify(response_data)


@jobs_api_bp.route('/process_job/<int:job_id>', methods=['POST'])
@login_required
def process_job(job_id):
    job_manager = JobManager()
    job = job_manager.read_job(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404
    
    job_processor = JobApplicationProcessor()
    result = job_processor.process_job(job)
    return jsonify({"success": True, "result": result})

@jobs_api_bp.route('/', methods=['GET'])
@login_required
def get_jobs():
    job_manager = JobManager()
    jobs = job_manager.get_jobs_for_user(current_user.user_id)
    if jobs is None:
        return jsonify({"error": "No jobs found for the user"}), 404
    return jobs.to_dict()