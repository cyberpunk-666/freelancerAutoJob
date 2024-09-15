from functools import wraps
from flask import abort
from flask_login import current_user, login_required
from app.models.user_manager import UserManager
from app.db.utils import get_db

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            db = get_db()
            user_manager = UserManager(db)
            
            # Check if the system is initialized
            init_response = user_manager.system_initialized()
            if init_response.status == "success" and not init_response.data["initialized"]:
                # If the system is not initialized, allow access
                return f(*args, **kwargs)
            
            # If the system is initialized, check for the role
            response = user_manager.user_has_role(current_user.get_id(), role_name)
            if response.status == "success" and response.data["has_role"]:
                return f(*args, **kwargs)
            else:
                abort(403)
        return decorated_function
    return decorator
