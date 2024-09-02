from flask import Flask
from app.config.config import Config
from app.db.postgresdb import PostgresDB
from flask import redirect, url_for

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from app.user.routes import user_bp
    from app.jobs.routes import job_bp

    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(job_bp, url_prefix='/jobs')


    return app
