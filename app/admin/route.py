from flask import Blueprint, jsonify
from app.models.user_manager import UserManager
from app.models.role_manager import RoleManager
from app.db.postgresdb import PostgresDB
from app.db.utils import get_db
from flask_login import login_required, current_user
from app.utils.api_response import APIResponse
admin_bp = Blueprint('admin', __name__)

from app.utils.api_response import APIResponse

@admin_bp.route('/admin/data', methods=['GET'])
@login_required
def get_admin_data():
    db = get_db()
    user_manager = UserManager(db)
    role_manager = RoleManager(db)

    try:
        users = [user.email for user in user_manager.get_all_users()]
        roles = [role.name for role in role_manager.get_all_roles()]

        return APIResponse(
            status="success",
            message="Admin data fetched successfully",
            data={"users": users, "roles": roles}
        ).to_json()

    except Exception as e:
        return APIResponse(
            status="failure",
            message=str(e),
            data=None
        ).to_json()
