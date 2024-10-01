import os
from flask import Blueprint, current_app, request
from flask_login import current_user, login_required
from app.managers.user_preferences_manager import UserPreferencesManager
from app.models.user import User
from app.managers.user_manager import UserManager
from app.db.db_utils import get_db
from app.utils.decorators import role_required
from app.models.api_response import APIResponse
user_api_bp = Blueprint('user_api', __name__, url_prefix='/api/users')

@user_api_bp.route('/', methods=['GET'])
@login_required
@role_required('admin')
def get_all_users():
    user_manager = UserManager()
    # Get filter parameters from request
    show_inactive = request.args.get('show_inactive', 'false').lower() == 'true'
    users_response = user_manager.get_all_users(show_inactive)
    return users_response.to_dict()

@user_api_bp.route('/<int:user_id>', methods=['GET'])
@login_required
@role_required('admin')
def get_user(user_id):
    user_manager = UserManager()
    user_response = user_manager.get_user(user_id)
    # verify if the data type is User
    if isinstance(user_response.data["user"], User):
        user_response.data["user"] = user_response.data["user"].toJson()
    return user_response.to_dict()

@user_api_bp.route('/search', methods=['GET'])
@login_required
@role_required('admin')
def search_users():
    query = request.args.get('q', '')
    user_manager = UserManager()
    search_response = user_manager.search_users(query)
    return search_response.to_dict()

@user_api_bp.route('/', methods=['POST'])
@login_required
@role_required('admin')
def create_user():
    data = request.json
    user_manager = UserManager()
    create_response = user_manager.create_user(data)
    return create_response.to_dict()

@user_api_bp.route('/<int:user_id>', methods=['PUT'])
@login_required
@role_required('admin')
def update_user(user_id):
    data = request.json
    user_manager = UserManager()
    update_response = user_manager.update_user(user_id, data)
    return update_response.to_dict()

@user_api_bp.route('/<int:user_id>', methods=['DELETE'])
@login_required
@role_required('admin')
def delete_user(user_id):
    user_manager = UserManager()
    delete_response = user_manager.delete_user(user_id)
    return delete_response.to_dict()

@user_api_bp.route('/<int:user_id>/roles', methods=['GET'])
@login_required
@role_required('admin')
def get_user_roles(user_id):
    user_manager = UserManager()
    roles_response = user_manager.get_user_roles(user_id)
    return roles_response.to_dict()

@user_api_bp.route('/free', methods=['GET'])
@login_required
@role_required('admin')
def get_free_users_by_role():
    user_manager = UserManager()
    role_name = request.args.get('role')  # Fetch the role name from the query parameter
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)

    free_users_response = user_manager.get_free_users_by_role(role_name=role_name, page=page, page_size=page_size)
   
    return free_users_response.to_dict()



@user_api_bp.route('/preferences', methods=['POST'])
@login_required
def preferences() -> APIResponse:
    config_file_path = os.path.join(current_app.root_path, 'static', 'config', 'preferences.json')

    user_preferences_manager = UserPreferencesManager(config_file_path)
    if request.method == 'POST':
        # Get JSON data from the request
        preferences_data = request.json

        if not preferences_data:
            return APIResponse(status="error", message="No preference data received").to_dict()

        # Handle form submission
        for pref_key, pref_value in preferences_data.items():
            set_preference_response = user_preferences_manager.set_preference(current_user.user_id, pref_key, pref_value)
            if set_preference_response.status != "success":
                return set_preference_response.to_dict()

        return APIResponse(status="success", message="Preferences updated successfully").to_dict()
