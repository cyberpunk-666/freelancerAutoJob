from flask import Blueprint, request
from flask_login import login_required
from app.managers.user_manager import UserManager
from app.db.db_utils import get_db
from app.managers.role_manager import RoleManager
from app.utils.decorators import role_required

role_api_bp = Blueprint('role_api', __name__)

@role_api_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def get_roles():
    role_manager = RoleManager()
    roles_response = role_manager.get_all_roles()
    return roles_response.to_dict()

@role_api_bp.route('/', methods=['POST'])
@login_required
@role_required('admin')
def create_role_api():
    data = request.json
    role_name = data.get('name')
    role_manager = RoleManager()
    new_role_response = role_manager.create_role(role_name)
    return new_role_response.to_dict()

@role_api_bp.route('/<string:role_name>', methods=['GET'])
@login_required
@role_required('admin')
def get_role(role_name):
    role_manager = RoleManager()
    role_response = role_manager.get_role(role_name)
    return role_response.to_dict()

@role_api_bp.route('/<string:role_name>', methods=['PUT'])
@login_required
@role_required('admin')
def update_role_api(role_name):
    data = request.json
    new_role_name = data.get('name')
    role_manager = RoleManager()
    updated_role_response = role_manager.update_role(role_name, new_role_name)
    return updated_role_response.to_dict()

@role_api_bp.route('/<string:role_name>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_role_api(role_name):
    role_manager = RoleManager()
    delete_response = role_manager.delete_role(role_name)
    return delete_response.to_dict()

@role_api_bp.route('/<string:role_name>/users', methods=['GET'])
@login_required
@role_required('admin')
def get_users_in_role(role_name):
    role_manager = RoleManager()
    users_response = role_manager.get_users_in_role(role_name)
    return users_response.to_dict()

@role_api_bp.route('/<string:role_name>/users', methods=['POST'])
@login_required
@role_required('admin')
def add_user_to_role(role_name):
    data = request.json
    user_id = data.get('userId')
    role_manager = RoleManager()
    assign_response = role_manager.assign_role_to_user(user_id, role_name)
    return assign_response.to_dict()

@role_api_bp.route('/<string:role_name>/users/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def remove_user_from_role(role_name, user_id):
    role_manager = RoleManager()
    remove_response = role_manager.remove_role_from_user(user_id, role_name)
    return remove_response.to_dict()

@role_api_bp.route('/users/free', methods=['GET'])
@login_required
@role_required('admin')
def get_free_users():
    role_manager = RoleManager()
    users_response = role_manager.get_users_without_role()
    return users_response.to_dict()
