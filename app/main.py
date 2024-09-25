import threading
from app import create_flask_app
from flask import Blueprint, render_template, redirect, url_for, flash
import logging
from app.models.config import setup_logging
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from app.managers.job_manager import JobManager
from app.services.task_queue import TaskQueue
from app.services.job_application_processor import JobApplicationProcessor
from app.managers.user_manager import UserManager
from app.managers.role_manager import RoleManager
from app.db.db_utils import get_db
from app.models.user import User
import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, 'to_dict'):
            return obj.to_dict()
        return super().default(obj)

setup_logging()
app = create_flask_app()
app.json_encoder = CustomJSONEncoder
Talisman(app, content_security_policy=None)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

task_queue = TaskQueue()
task_queue.register_callback("fetch_email", None)
task_queue.register_callback('process_single_email', None)
task_queue.register_callback('scrape_job_details', None)

@app.context_processor
def inject_role_manager():
    role_manager = RoleManager()
    return dict(role_manager=role_manager)

@app.route('/')
def root():
    user_manager = UserManager()
    
    # Check if the system is initialized
    init_response = user_manager.system_initialized()
    
    if init_response.status != "success":
        # If there was an error checking initialization status, render an error page
        return render_template('error.html', message="Failed to check system initialization status. Please try again later.")
    
    if not init_response.data["initialized"]:
        # If the system is not initialized, redirect to the initial setup
        return redirect(url_for('setup.initial_setup_get'))
    else:
        # If the system is initialized, redirect to the jobs index as before
        return redirect(url_for('jobs.index'))


if __name__ == '__main__':
    app.logger.info("Starting app...")
    # Run the app
    if os.getenv('FLASK_ENV') == 'development':
        # Run the app in debug mode
        port = os.getenv('WEB_API_FLASK_PORT', 5000)
        app.run(ssl_context=('cert.pem', 'key_unencrypted.pem'), debug=True, use_reloader=False, port=port)
    else:
        app.run(debug=False)
