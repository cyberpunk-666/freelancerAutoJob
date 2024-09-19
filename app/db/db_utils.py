from flask import current_app, g
from app.db.postgresdb import PostgresDB
from app.models.config import Config

def get_db():
    if 'db' not in g:
        if hasattr(current_app, 'db'):
            g.db = current_app.db
        else:
            g.db = PostgresDB(Config.DB_HOST, Config.DB_NAME, Config.DB_USER, Config.DB_PASSWORD)

    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        
