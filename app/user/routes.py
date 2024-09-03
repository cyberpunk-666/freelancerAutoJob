from flask import Blueprint, render_template, redirect, url_for, flash, session
from flask_login import login_user, logout_user
from app.user.forms import RegistrationForm, LoginForm, ResetPasswordForm
from app.models.user_manager import UserManager
from app.db.postgresdb import PostgresDB
from app.db.utils import get_db  # Import the get_db function
from flask_login import current_user

user_bp = Blueprint('user', __name__)

@user_bp.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegistrationForm(meta="ss")
    if form.validate_on_submit():
        db = get_db()  # Get the database instance
        user_manager = UserManager(db)  # Initialize User with the db instance
        if user_manager.sign_up(form.email.data, form.password.data):
            flash('Account created successfully! Please log in.', 'success')
            return redirect(url_for('user.login'))
        else:
            flash('Sign-up failed. Email might already be registered.', 'danger')
    return render_template('signup.html', form=form)

@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db = get_db()  # Get the database instance
        user_manager = UserManager(db)  # Initialize UserManager with the db instance
        success, user_id = user_manager.login(form.email.data, form.password.data)
        if success:
            user = user_manager.get_user(user_id)  # Retrieve the User instance
            if user:
                login_user(user)
                flash('Login successful!', 'success')
                return redirect(url_for('user.dashboard'))
        flash('Login failed. Check your credentials.', 'danger')
    return render_template('login.html', form=form)



@user_bp.route('/dashboard')
def dashboard():
    if current_user.is_authenticated:
        return f"Welcome {current_user.email}! This is your dashboard."
    else:
        flash('Please log in to access the dashboard.', 'warning')
        return redirect(url_for('user.login'))


@user_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('user.login'))

@user_bp.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        db = get_db()  # Get the database instance
        user_manager = UserManager(db)  # Initialize User with the db instance
        if user_manager.reset_password(form.email.data, form.new_password.data):
            flash('Password reset successful! Please log in with your new password.', 'success')
            return redirect(url_for('user.login'))
        else:
            flash('Password reset failed. Please try again.', 'danger')
    return render_template('reset_password.html', form=form)
