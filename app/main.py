import threading
from app import create_app
from flask import Blueprint, render_template, redirect, url_for, flash
import logging
from app.config.config import setup_logging
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from app.models.job_manager import JobManager
from app.utils.job_queue import JobQueue
from app.utils.job_application_processor import JobApplicationProcessor

setup_logging()
app = create_app()

Talisman(app, content_security_policy=None)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

@app.route('/')
def root():
    return redirect(url_for('jobs.index'))

if __name__ == '__main__':
    app.logger.info("Starting app...")
    # Run the app
    if os.getenv('FLASK_ENV') == 'development':
        queue_url = os.getenv('AWS_SQS_QUEUE_URL')
        # Create job queue and processor
        job_queue = JobQueue(queue_url)
        # job_manager = JobManager()
        # job_processor = JobApplicationProcessor()

        # # Start background thread for processing queued jobs
        # def process_queued_jobs():
        #     job_processor.process_job_from_queue(job_queue)

        # background_thread = threading.Thread(target=process_queued_jobs, daemon=True)
        # background_thread.start()

        # Run the app in debug mode
        app.run(ssl_context=('cert.pem', 'key_unencrypted.pem'), debug=True, use_reloader=False)
    else:
        app.run(debug=False)
