from app.models.job_manager import JobManager
from app.db.postgresdb import db

def fetch_and_process_jobs():
    job_manager = JobManager(db)
    # Example: Fetch jobs from an external API or source
    job_manager.create_job("Example Job", "Example Job Description", "1000", "open")

if __name__ == '__main__':
    fetch_and_process_jobs()
