from flask import Blueprint, jsonify, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.managers.role_manager import RoleManager
from app.db.postgresdb import PostgresDB
from app.db.db_utils import get_db
from app.utils.decorators import role_required

role_bp = Blueprint('roles', __name__)

@role_bp.route('/')
@login_required
@role_required('admin')
def roles():
    db = get_db()
    role_manager = RoleManager(db)
    roles = role_manager.get_all_roles()
    return render_template('roles.html', roles=roles)

# Create
@role_bp.route('/create_role', methods=['GET', 'POST'])
@login_required
def create_role():
    if request.method == 'POST':
        role_name = request.form['role_name']
        db = get_db()
        role_manager = RoleManager(db)
        if role_manager.create_role(role_name):
            flash('Role created successfully!', 'success')
        else:
            flash('Failed to create role.', 'error')
        return redirect(url_for('roles.roles'))
    return render_template('create_role.html')

# Read
@role_bp.route('/view_role/<int:role_id>')
@login_required
def view_role(role_id):
    db = get_db()
    role_manager = RoleManager(db)
    role = role_manager.get_role_by_id(role_id)
    if role:
        return render_template('view_role.html', role=role)
        return redirect(url_for('roles.roles'))

# Update
@role_bp.route('/update_role/<int:role_id>', methods=['GET', 'POST'])
@login_required
def update_role(role_id):
    db = get_db()
    role_manager = RoleManager(db)
    role = role_manager.get_role_by_id(role_id)
    if role:
        if request.method == 'POST':
            new_role_name = request.form['role_name']
            if role_manager.update_role(role_id, new_role_name):
                flash('Role updated successfully!', 'success')
            else:
                flash('Failed to update role.', 'error')
            return redirect(url_for('roles.roles'))
        return render_template('update_role.html', role=role)
    else:
        flash('Role not found.', 'error')
        return redirect(url_for('roles.roles'))

# Delete
@role_bp.route('/delete_role/<int:role_id>', methods=['POST'])
@login_required
def delete_role(role_id):
    db = get_db()
    role_manager = RoleManager(db)
    if role_manager.delete_role(role_id):
        flash('Role deleted successfully!', 'success')
    else:
        flash('Failed to delete role.', 'error')
    return redirect(url_for('roles.roles'))

@role_bp.route('/assign_role/<int:user_id>', methods=['GET', 'POST'])
@login_required
def assign_role(user_id):
    if request.method == 'POST':
        role_name = request.form['role_name']
        db = get_db()
        role_manager = RoleManager(db)
        if role_manager.assign_role_to_user(user_id, role_name):
            flash('Role assigned successfully!', 'success')
        else:
            flash('Failed to assign role.', 'error')
        return redirect(url_for('roles.roles'))
    db = get_db()
    role_manager = RoleManager(db)
    roles = role_manager.get_all_roles()
    return render_template('assign_role.html', user_id=user_id, roles=roles)

@role_bp.route('/remove_role/<int:user_id>/<role_name>', methods=['POST'])
@login_required
def remove_role(user_id, role_name):
    db = get_db()
    role_manager = RoleManager(db)
    if role_manager.remove_role_from_user(user_id, role_name):
        flash('Role removed successfully!', 'success')
    else:
        flash('Failed to remove role.', 'error')
    return redirect(url_for('roles.roles'))
