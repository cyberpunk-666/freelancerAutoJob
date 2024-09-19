from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.managers.user_manager import UserManager
from app.managers.role_manager import RoleManager
from app.db.db_utils import get_db
from werkzeug.security import generate_password_hash
import re

setup_bp = Blueprint('setup', __name__)

@setup_bp.route('/initial-setup', methods=['GET'])
def initial_setup_get():
    db = get_db()
    user_manager = UserManager(db)

    # Check if the system is already initialized
    init_response = user_manager.system_initialized()
    if init_response.status != "success":
        return render_template('error.html', message="Failed to check system initialization status. Please try again later.")
    
    if init_response.data["initialized"]:
        # If the system is already initialized, redirect to the jobs index
        return redirect(url_for('jobs.index'))

    return render_template('setup.html')


@setup_bp.route('/initial-setup', methods=['POST'])
def initial_setup_post():
    db = get_db()
    user_manager = UserManager(db)
    role_manager = RoleManager(db)

    # Check if the system is already initialized
    init_response = user_manager.system_initialized()
    if init_response.status != "success":
        return render_template('error.html', message="Failed to check system initialization status. Please try again later.")
    
    if init_response.data["initialized"]:
        # If the system is already initialized, redirect to the jobs index
        return redirect(url_for('jobs.index'))

    # Form validation
    email = request.form.get('email')
    password = request.form.get('password')
    confirm_password = request.form.get('confirm_password')

    if not email or not password or not confirm_password:
        flash('All fields are required.', 'error')
        return render_template('setup.html'), 400

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        flash('Invalid email address.', 'error')
        return render_template('setup.html'), 400

    if password != confirm_password:
        flash('Passwords do not match.', 'error')
        return render_template('setup.html'), 400

    if len(password) < 8:
        flash('Password must be at least 8 characters long.', 'error')
        return render_template('setup.html'), 400

    # Create admin role
    admin_role_response = role_manager.create_role('admin')
    if admin_role_response.status != "success":
        flash(admin_role_response.message, 'error')
        return render_template('setup.html'), 500

    # Create admin user
    admin_user_response = user_manager.create_user(
        email=email,
        password=password,
        is_active=True
    )
    if admin_user_response.status != "success":
        flash(admin_user_response.message, 'error')
        return render_template('setup.html'), 500

    # Assign admin role to the user
    assign_role_response = role_manager.assign_role_to_user(
        admin_user_response.data['user_id'],
        'admin'
    )
    if assign_role_response.status != "success":
        flash(assign_role_response.message, 'error')
        return render_template('setup.html'), 500

    flash('Initial setup completed successfully. You can now log in.', 'success')
    return redirect(url_for('user.login'))
