from flask import Blueprint, render_template, redirect, url_for, flash
from app.jobs.forms import CreateJobForm, UpdateJobForm
from app.models.job_manager import JobManager
from app.db.postgresdb import PostgresDB
from app.db.utils import get_db
import markdown 

job_bp = Blueprint('jobs', __name__)


@job_bp.route('/jobs')
def jobs():
    db = get_db()
    job_manager = JobManager(db)
    jobs = job_manager.fetch_all_jobs()
    return render_template('jobs.html', jobs=jobs)

@job_bp.route('/create_job', methods=['GET', 'POST'])
def create_job():
    form = CreateJobForm()
    if form.validate_on_submit():
        db = get_db()
        job_manager = JobManager(db)        
        job_manager.create_job(form.title.data, form.description.data, form.budget.data, form.status.data)
        flash('Job created successfully!', 'success')
        return redirect(url_for('jobs.jobs'))
    return render_template('create_job.html', form=form)

@job_bp.route('/update_job/<int:job_id>', methods=['GET', 'POST'])
def update_job(job_id):
    db = get_db()
    job_manager = JobManager(db)    
    job = job_manager.fetch_all_jobs()[0]  # Replace this with a specific job fetch logic
    form = UpdateJobForm(obj=job)
    if form.validate_on_submit():
        job_manager.update_job(job_id, form.title.data, form.description.data, form.budget.data, form.status.data)
        flash('Job updated successfully!', 'success')
        return redirect(url_for('jobs.jobs'))
    return render_template('update_job.html', form=form, job_id=job_id)

@job_bp.route('/delete_job/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    db = get_db()
    job_manager = JobManager(db)    
    job_manager.delete_job(job_id)
    flash('Job deleted successfully!', 'success')
    return redirect(url_for('jobs.jobs'))

@job_bp.route('/')
def index():
    db = get_db()
    job_manager = JobManager(db)   
    jobs = job_manager.db.fetch_all('SELECT * FROM job_details ORDER BY email_date DESC')
    return render_template('jobs.html', jobs=jobs)

@job_bp.route('/job/<job_id>')
def job_detail(job_id):
    db = get_db()
    job_manager = JobManager(db)   
    job = job_manager.read_job(job_id)
    if job is None:
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