from flask import Flask
from app.config.config import Config
from app.db.postgresdb import PostgresDB
from flask import redirect, url_for, current_app
from app.db.utils import close_db
import logging
from flask_login import LoginManager, login_required, current_user
from dotenv import load_dotenv
import os
from app.models.job_manager import JobManager
from app.models.user_manager import UserManager
from app.models.processed_email_manager import ProcessedEmailManager
from app.db.utils import get_db

login_manager = LoginManager()
login_manager.login_view = 'user.login'
login_manager.login_message_category = 'info'
login_manager.login_message = 'Please log in to access this page.'

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    db = get_db()  # Use get_db to get the database connection
    user_manager = UserManager(db)
    return user_manager.get_user(user_id)

def init_database():
    """Initialize the database connection and create necessary tables."""
    # Load environment variables from .env file
    logger = logging.getLogger(__name__)
    load_dotenv()
    logging.info("Environment variables loaded from .env file.")

    # Initialize the PostgresDB instance
    try:
        db = get_db()
        logging.info("Database connection established successfully.")
    except Exception as e:
        logging.error(f"Failed to connect to the database: {e}")
        raise

    # Initialize the JobManager instance
    try:
        job_manager = JobManager(db)
        logging.info("JobManager instance created successfully.")
    except Exception as e:
        logging.error(f"Failed to create JobManager instance: {e}")
        raise

    # Create the job_manager table
    try:
        job_manager.create_table()
        logging.info("job_manager table ensured to exist.")
    except Exception as e:
        logging.error(f"Failed to create job_manager table: {e}")
        raise
    
    # initialize User instance
    try:
        user_manager = UserManager(db)
        logging.info("User instance created successfully.")
    except Exception as e:
        logging.error(f"Failed to create User instance: {e}")
        raise
    
    # create users table
    try:
        user_manager.create_table()
        logging.info("users table ensured to exist.")
    except Exception as e:
        logging.error(f"Failed to create users table: {e}")
        raise

    try:
        processed_email_manager = ProcessedEmailManager(db)
        logging.info("ProcessedEmailManager instance created successfully.")
    except Exception as e:
        logging.error(f"Failed to create ProcessedEmailManager instance: {e}")
        raise
    
    try:
        processed_email_manager.create_table()
        logging.info("processed_email_manager table ensured to exist.")
    except Exception as e:
        logging.error(f"Failed to create processed_email_manager table: {e}")
        raise
    
@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    db = get_db()  # Use get_db to get the database connection
    user_manager = UserManager(db)
    return user_manager.get_user(user_id)

def init_database():
    """Initialize the database connection and create necessary tables."""
    db = get_db()
    user_manager = UserManager(db)
    user_manager.create_table()
    logging.info("Database initialized and tables created successfully.")

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'RQaMw8Oy5Cch7Po9ANAnHud1r-MedSNduol_qFha44Y'

    # Initialize the LoginManager with the app
    login_manager.init_app(app)
    login_manager.login_view = 'user.login'

    # Register blueprints
    from app.user.routes import user_bp
    from app.jobs.routes import job_bp

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(job_bp, url_prefix='/jobs')

    # Teardown database connection
    app.teardown_appcontext(close_db)

    # Initialize the database with app context
    with app.app_context():
        init_database()

    return app
