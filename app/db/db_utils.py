from app.db.postgresdb import PostgresDB
from app.models.config import Config

current_db = None

def get_db():
    global current_db
    if not current_db:
        current_db = PostgresDB(Config.DB_HOST, Config.DB_NAME, Config.DB_USER, Config.DB_PASSWORD)

    return current_db

def close_db(e=None):
    global current_db 
    if current_db is not None:
        current_db.close()
        current_db = None
        
