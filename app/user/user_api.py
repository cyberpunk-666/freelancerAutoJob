from flask import Blueprint, request
from flask_login import login_required
from app.models.user_manager import UserManager
from app.db.utils import get_db
from app.decorators import role_required

user_api_bp = Blueprint('user_api', __name__, url_prefix='/api/users')

@user_api_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def get_all_users():
    db = get_db()
    user_manager = UserManager(db)
    users_response = user_manager.get_all_users()
    return users_response.to_dict()

@user_api_bp.route('/<int:user_id>', methods=['GET'])
@login_required
@role_required('admin')
def get_user(user_id):
    db = get_db()
    user_manager = UserManager(db)
    user_response = user_manager.get_user(user_id)
    return user_response.to_dict()

@user_api_bp.route('/search', methods=['GET'])
@login_required
@role_required('admin')
def search_users():
    query = request.args.get('q', '')
    db = get_db()
    user_manager = UserManager(db)
    search_response = user_manager.search_users(query)
    return search_response.to_dict()

@user_api_bp.route('/', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    data = request.json
    db = get_db()
    user_manager = UserManager(db)
    create_response = user_manager.create_user(data)
    return create_response.to_dict()

@user_api_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_user(user_id):
    data = request.json
    db = get_db()
    user_manager = UserManager(db)
    update_response = user_manager.update_user(user_id, data)
    return update_response.to_dict()

@user_api_bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_user(user_id):
    db = get_db()
    user_manager = UserManager(db)
    delete_response = user_manager.delete_user(user_id)
    return delete_response.to_dict()

@user_api_bp.route('/<int:user_id>/roles', methods=['GET'])
@login_required
@role_required('admin')
def get_user_roles(user_id):
    db = get_db()
    user_manager = UserManager(db)
    roles_response = user_manager.get_user_roles(user_id)
    return roles_response.to_dict()

@user_api_bp.route('/free', methods=['GET'])
@login_required
@role_required('admin')
def get_free_users():
    db = get_db()
    user_manager = UserManager(db)
    free_users_response = user_manager.get_free_users()
    return free_users_response.to_dict()