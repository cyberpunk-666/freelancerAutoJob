from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.forms.jobs_forms import CreateJobForm, UpdateJobForm
from app.managers.job_manager import JobManager
from app.db.postgresdb import PostgresDB
from app.db.db_utils import get_db
import markdown 
import logging
from flask import jsonify, request
from app.services.email_processor import EmailProcessor
from app.services.task_queue import TaskQueue
from app.models.api_response import APIResponse
from app.managers.role_manager import RoleManager
from datetime import date

job_bp = Blueprint('jobs', __name__)


@job_bp.route('/create_job', methods=['GET', 'POST'])
@login_required
def create_job():
    form = CreateJobForm()
    logging.info("Create job form submitted")
    if form.validate_on_submit():
        job_manager = JobManager()
        job_manager.create_job(form.title.data, form.description.data, form.budget.data, form.status.data)
        flash('Job created successfully!', 'success')
        logging.info(f"Job created: {form.title.data}")
        return redirect(url_for('jobs.jobs'))
    return render_template('create_job.html', form=form)

@job_bp.route('/update_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def update_job(job_id):
    job_manager = JobManager()
    logging.info(f"Updating job: {job_id}")
    job = job_manager.read_job(job_id)
    if job is None:
        flash('Job not found or you do not have permission to edit it.', 'error')
        return redirect(url_for('jobs.jobs'))
    form = UpdateJobForm(obj=job)
    if form.validate_on_submit():
        job_manager.update_job(job_id, {'title': form.title.data, 'description': form.description.data, 'budget': form.budget.data, 'status': form.status.data})
        flash('Job updated successfully!', 'success')
        logging.info(f"Job updated: {job_id}")
        return redirect(url_for('jobs.jobs'))
    return render_template('update_job.html', form=form, job_id=job_id)

@job_bp.route('/delete_job/<int:job_id>', methods=['POST'])
@login_required
def delete_job(job_id):
    job_manager = JobManager()
    logging.info(f"Deleting job: {job_id}")
    job = job_manager.read_job(job_id)
    if job is None:
        flash('Job not found or you do not have permission to delete it.', 'error')
        return redirect(url_for('jobs.jobs'))
    job_manager.delete_job(job_id)
    logging.info(f"Job deleted: {job_id}")
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('jobs.jobs'))

@job_bp.route('/')
@login_required
def jobs():
    logging.info("Fetching all jobs")
    job_manager = JobManager()
    jobs_answer = job_manager.get_jobs_for_user(current_user.user_id)
    if jobs_answer.status == "success":
        logging.info("Jobs fetched successfully")
        jobs = jobs_answer.data
    else:
        logging.warning(f"Failed to fetch jobs: {jobs_answer.message}")
        jobs = []

    return render_template('job/jobs.html', jobs=jobs)


@job_bp.route('/job/<job_id>')
@login_required
def job_detail(job_id):
    job_manager = JobManager()
    logging.info(f"Fetching job details for job: {job_id}")
    api_response = job_manager.get_job_by_id(job_id)
    job = api_response.data if api_response.status == "success" else None
    if job is None:
        logging.warning(f"Job not found or unauthorized access: {job_id}")
        return f"Job with ID {job_id} not found.", 404

    gemini_results = job.get('gemini_results', {})

    if 'generate_detailed_steps' in gemini_results:
        gemini_results['generate_detailed_steps'] = gemini_results['generate_detailed_steps']
        if 'steps' in gemini_results['generate_detailed_steps']:
            for step in gemini_results['generate_detailed_steps']['steps']:
                step['description'] = markdown.markdown(step['description'])

    if 'generate_application_letter' in gemini_results:
        gemini_results['generate_application_letter'] = gemini_results['generate_application_letter']
        if 'introduction' in gemini_results['generate_application_letter']:
            gemini_results['generate_application_letter']['introduction'] = markdown.markdown(gemini_results['generate_application_letter']['introduction'])
        if 'fit' in gemini_results['generate_application_letter']:
            gemini_results['generate_application_letter']['fit'] = markdown.markdown(gemini_results['generate_application_letter']['fit'])

    return render_template('job/job_detail.html', job=job)
