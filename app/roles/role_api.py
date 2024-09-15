from flask import Blueprint, request
from flask_login import login_required
from app.models.user_manager import UserManager
from app.db.utils import get_db
from app.models.role_manager import RoleManager
from app.decorators import role_required

role_api_bp = Blueprint('role_api', __name__)
@role_api_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def get_roles():
    db = get_db()
    role_manager = RoleManager(db)
    roles_response = role_manager.get_all_roles()
    return roles_response.to_dict()

@role_api_bp.route('/', methods=['POST'])
@login_required
@role_required('admin')
def create_role_api():
    data = request.json
    role_name = data.get('name')
    db = get_db()
    role_manager = RoleManager(db)
    new_role_response = role_manager.create_role(role_name)
    return new_role_response.to_dict()

@role_api_bp.route('/<int:role_id>', methods=['GET'])
@login_required
@role_required('admin')
def get_role(role_id):
    db = get_db()
    role_manager = RoleManager(db)
    role_response = role_manager.get_role_by_id(role_id)
    return role_response.to_dict()

@role_api_bp.route('/<int:role_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_role_api(role_id):
    data = request.json
    new_role_name = data.get('name')
    db = get_db()
    role_manager = RoleManager(db)
    updated_role_response = role_manager.update_role(role_id, new_role_name)
    return updated_role_response.to_dict()

@role_api_bp.route('/<int:role_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_role_api(role_id):
    db = get_db()
    role_manager = RoleManager(db)
    delete_response = role_manager.delete_role(role_id)
    return delete_response.to_dict()

@role_api_bp.route('/<int:role_id>/users', methods=['GET'])
@login_required
@role_required('admin')
def get_users_in_role(role_id):
    db = get_db()
    role_manager = RoleManager(db)
    users_response = role_manager.get_users_in_role(role_id)
    return users_response.to_dict()

@role_api_bp.route('/<int:role_id>/users', methods=['POST'])
@login_required
@role_required('admin')
def add_user_to_role(role_id):
    data = request.json
    user_id = data.get('userId')
    db = get_db()
    role_manager = RoleManager(db)
    assign_response = role_manager.assign_role_to_user(user_id, role_id)
    return assign_response.to_dict()

@role_api_bp.route('/<int:role_id>/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def remove_user_from_role(role_id, user_id):
    db = get_db()
    role_manager = RoleManager(db)
    remove_response = role_manager.remove_role_from_user(user_id, role_id)
    return remove_response.to_dict()

@role_api_bp.route('/users/free', methods=['GET'])
@login_required
@role_required('admin')
def get_free_users():
    db = get_db()
    role_manager = RoleManager(db)
    users_response = role_manager.get_users_without_role()
    return users_response.to_dict()
