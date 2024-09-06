from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.jobs.forms import CreateJobForm, UpdateJobForm
from app.models.job_manager import JobManager
from app.db.postgresdb import PostgresDB
from app.db.utils import get_db
import markdown 
import logging

job_bp = Blueprint('jobs', __name__)


@job_bp.route('/jobs')
@login_required
def jobs():
    if current_user.is_authenticated:
        db = get_db()
        logging.info("Fetching all jobs")
        job_manager = JobManager(db, current_user.user_id)
        jobs = job_manager.fetch_all_jobs()
    else:
        return redirect(url_for('user.login', next=request.url))
    return render_template('jobs.html', jobs=jobs)

@job_bp.route('/create_job', methods=['GET', 'POST'])
@login_required
def create_job():
    form = CreateJobForm()
    logging.info("Create job form submitted")
    if form.validate_on_submit():
        db = get_db()
        job_manager = JobManager(db, current_user.user_id)
        job_manager.create_job(form.title.data, form.description.data, form.budget.data, form.status.data)
        flash('Job created successfully!', 'success')
        logging.info(f"Job created: {form.title.data}")
        return redirect(url_for('jobs.jobs'))
    return render_template('create_job.html', form=form)

@job_bp.route('/update_job/<int:job_id>', methods=['GET', 'POST'])
@login_required
def update_job(job_id):
    db = get_db()
    job_manager = JobManager(db, current_user.user_id)
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
    db = get_db()
    job_manager = JobManager(db, current_user.user_id)
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
def index():
    if current_user.is_authenticated:
        db = get_db()
        job_manager = JobManager(db, current_user.user_id)
        logging.info("Fetching all jobs for index page")
        jobs = job_manager.db.fetch_all('SELECT * FROM job_details WHERE user_id = %s ORDER BY email_date DESC', (current_user.user_id,))
        return render_template('jobs.html', jobs=jobs)
    else:
        return redirect(url_for('user.login', next=request.url))

@job_bp.route('/job/<job_id>')
@login_required
def job_detail(job_id):
    db = get_db()
    job_manager = JobManager(db, current_user.user_id)
    logging.info(f"Fetching job details for job: {job_id}")
    job = job_manager.read_job(job_id)
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

    return render_template('job_detail.html', job=job)
