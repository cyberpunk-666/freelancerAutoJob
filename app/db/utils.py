from flask import current_app, g
from app.db.postgresdb import PostgresDB
from app.config.config import Config

def get_db():
    if 'db' not in g:
        if hasattr(current_app, 'db'):
            g.db = current_app.db
        else:
            # user_db_info = get_user_db_info() 
            g.db = PostgresDB(Config.DB_HOST, Config.DB_NAME, Config.DB_USER, Config.DB_PASSWORD)

    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()
        
def get_user_db_info():
    # Exemple : Cette fonction pourrait vérifier l'utilisateur actuel et retourner les infos de sa DB
    user_id = get_current_user_id()  # Récupère l'ID de l'utilisateur actuel
    # Logique pour récupérer les infos de connexion à la DB de l'utilisateur
    return {
        'host': 'localhost',
        'dbname': f'user_{user_id}_db',
        'user': 'db_user',
        'password': 'db_password'
    }
    
def get_current_user_id():
    return 1 
