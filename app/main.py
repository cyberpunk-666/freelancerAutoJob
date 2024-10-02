from datetime import datetime
import threading

from flask_login import login_required
from app import create_flask_app
from flask import Blueprint, render_template, redirect, url_for, flash
import logging
from app.managers.currency_convertion_manager import CurrencyConversionManager
from app.managers.messages_handler import MessageHandler
from app.models.config import setup_logging
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix
import os
from app.managers.job_manager import JobManager
from app.services.task_queue import TaskQueue
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


# Custom filter for formatting datetime
def format_datetime(value, format='%Y-%m-%d'):
    if isinstance(value, datetime):
        return value.strftime(format)
    return value  # Handle if value is not a datetime


# Register the filter in Flask
app.jinja_env.filters['datetime'] = format_datetime
task_queue = TaskQueue()
task_queue.register_callback("process_job", None)


@app.template_filter('truncate_title')
def truncate_title_filter(title, max_length=50):
    return (title[: max_length - 3] + '...') if len(title) > max_length else title


@app.context_processor
def inject_role_manager():
    role_manager = RoleManager()
    return dict(role_manager=role_manager)


@app.route('/api/get_options/<field_key>', methods=['get'])
@login_required
def get_options(field_key):
    if field_key == "currency":
        currency_conversion = CurrencyConversionManager()
        currencies = currency_conversion.get_available_currencies()
        return currencies


@app.route('/')
def root():
    user_manager = UserManager()

    # Check if the system is initialized
    init_response = user_manager.system_initialized()

    if init_response.status != "success":
        # If there was an error checking initialization status, render an error page
        return render_template(
            'pages/error.html', message="Failed to check system initialization status. Please try again later."
        )

    if not init_response.data["initialized"]:
        # If the system is not initialized, redirect to the initial setup
        return redirect(url_for('setup.initial_setup_get'))
    else:
        # If the system is initialized, redirect to the jobs index as before
        return redirect(url_for('jobs.jobs'))


if __name__ == '__main__':
    app.logger.info("Starting app...")
    # Run the app
    if os.getenv('FLASK_ENV') == 'development':
        # Run the app in debug mode
        port = os.getenv('WEB_API_FLASK_PORT', 5000)
        app.run(ssl_context=('cert.pem', 'key_unencrypted.pem'), debug=True, use_reloader=False, port=port)
    else:
        app.run(debug=False)
