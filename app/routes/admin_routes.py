from flask import Blueprint, jsonify
from app.managers.user_manager import UserManager
from app.managers.role_manager import RoleManager
from app.db.postgresdb import PostgresDB
from app.db.db_utils import get_db
from flask_login import login_required, current_user

admin_bp = Blueprint('admin', __name__)

from app.models.api_response import APIResponse
from flask import render_template
from app.utils.decorators import role_required


@admin_bp.route('/dashboard')
@role_required('admin')
def dashboard():
    return render_template('admin/admin_dashboard.html')


@admin_bp.route('/users')
@role_required('admin')
def users():
    user_manager = UserManager()
    users_answer = user_manager.get_all_users()
    if users_answer.status != "success":
        return render_template('error.html', error=users_answer.message)
    users = users_answer.data["users"]
    return render_template('admin/admin_users.html', users=users)


@admin_bp.route('/roles')
@role_required('admin')
def roles():
    return render_template('admin/admin_roles.html')


@admin_bp.route('/data', methods=['GET'])
@role_required('admin')
@login_required
def get_admin_data():
    user_manager = UserManager()
    role_manager = RoleManager()

    try:
        users = [user.email for user in user_manager.get_all_users()]
        roles = [role.name for role in role_manager.get_all_roles()]

        return APIResponse(
            status="success", message="Admin data fetched successfully", data={"users": users, "roles": roles}
        ).to_json()

    except Exception as e:
        return APIResponse(status="failure", message=str(e), data=None).to_json()
