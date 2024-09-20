from flask_dance.contrib.google import make_google_blueprint
from flask_dance.contrib.google import google
from flask import Flask
from app.models.config import Config
from app.db.postgresdb import PostgresDB
from flask import redirect, url_for, current_app
from app.db.db_utils import close_db
import logging
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv
import os
from app.managers.job_manager import JobManager
from app.managers.user_manager import UserManager
from app.managers.processed_email_manager import ProcessedEmailManager
from app.managers.role_manager import RoleManager
from app.db.db_utils import get_db
from app.managers.update_schema_manager import UpdateSchemaManager
SYSTEM_USER_ID = 0
login_manager = LoginManager()
login_manager.login_view = 'user.login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    db = get_db()  # Use get_db to get the database connection
    user_manager = UserManager(db)
    
    # Retrieve the user using UserManager
    user_response = user_manager.get_user(user_id)
    
    if user_response.status == "success":
        # Return the user object if the response is successful
        return user_response.data["user"]
    else:
        # Return None if there was an error or no user found
        return None

def init_database():
    # Create instances of the managers with the system user ID
    db = get_db()
    role_manager = RoleManager(db)
    job_manager = JobManager(db)
    processed_email_manager = ProcessedEmailManager(db, user_id=SYSTEM_USER_ID)
    user_manager = UserManager(db)

    # Call the create_tables method for each manager
    user_manager.create_table()
    job_manager.create_table()
    processed_email_manager.create_table()
    role_manager.create_tables()

google_bp = make_google_blueprint(
    client_id="my-key-here",
    client_secret="my-secret-here",
    scope=["profile", "email"]
)

def update_schema():
    """
    The function `update_schema()` updates the database schema and logs a success message.
    """
    db = get_db()
    schema_updater = UpdateSchemaManager(db)
    schema_updater.update_schema()
    logger = logging.getLogger(__name__)
    logger.info("Database schema updated successfully.")
    

def create_flask_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    # Initialize the LoginManager with the app
    login_manager.init_app(app)
    login_manager.login_view = 'user.login'

    # Register blueprints
    from app.routes.user_routes import user_bp
    from app.routes.api.user_api_routes import user_api_bp
    from app.routes.jobs_routes import job_bp
    from app.routes.role_routes import role_bp
    from app.routes.api.role_api_routes import role_api_bp
    from app.routes.setup_routes import setup_bp
    from app.routes.admin_routes import admin_bp
    from app.routes.api.task_queue_api_routes import task_queue_bp
    
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(job_bp, url_prefix='/jobs')
    app.register_blueprint(role_bp, url_prefix='/roles')
    app.register_blueprint(role_api_bp, url_prefix='/api/roles')
    app.register_blueprint(user_api_bp, url_prefix='/api/users')
    app.register_blueprint(setup_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(task_queue_bp, url_prefix='/api/task_queue')
    # Teardown database connection
    app.teardown_appcontext(close_db)

    # Initialize the database with app context
    with app.app_context():
        init_database()
        update_schema()

    return app
