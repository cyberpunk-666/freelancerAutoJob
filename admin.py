from flask import Flask, render_template
from job_details import JobDetails
from app.db.postgresdb import PostgresDB
from datetime import datetime
import os
from dotenv import load_dotenv
import json
import markdown 
# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)

# Database configuration
db_config = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

# Initialize the PostgresDB instance
db = PostgresDB(**db_config)

# Initialize the JobDetails instance
job_details = JobDetails(db)

@app.route('/')
def index():
    """Display all job entries."""
    conn = db
    jobs = job_details.db.fetch_all('SELECT * FROM job_details ORDER BY email_date DESC')
    return render_template('jobs.html', jobs=jobs)

@app.route('/job/<job_id>')
def job_detail(job_id):
    """Display the details of a specific job."""
    job = job_details.read_job(job_id)
    if job is None:
        return f"Job with ID {job_id} not found.", 404

    # Parse and process JSON fields if they exist
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
        if 'approach' in gemini_results['generate_application_letter']:
            gemini_results['generate_application_letter']['approach'] = markdown.markdown(gemini_results['generate_application_letter']['approach'])
        if 'closing' in gemini_results['generate_application_letter']:
            gemini_results['generate_application_letter']['closing'] = markdown.markdown(gemini_results['generate_application_letter']['closing'])

    job['gemini_results'] = gemini_results

    return render_template('job_detail.html', job=job)

if __name__ == '__main__':
    app.run(debug=True)
