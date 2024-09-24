from app.db.postgresdb import PostgresDB
from app.models.config import Config

current_db = None

def get_db():
    if not current_db:
        current_db = PostgresDB(Config.DB_HOST, Config.DB_NAME, Config.DB_USER, Config.DB_PASSWORD)

    return current_db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        
