from flask_dance.contrib.google import google
from flask import flash
from flask import Blueprint, render_template, redirect, url_for, flash, session, request, session
from flask_login import login_user, logout_user
from app.user.forms import RegistrationForm, LoginForm, ResetPasswordForm
from app.utils.email_sender import EmailSender
from flask import url_for
from app.models.user_manager import UserManager
from app.db.postgresdb import PostgresDB
from app.db.utils import get_db
from flask_login import current_user
from flask_login import login_required, current_user
from app.user.forms import UpdateProfileForm
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

user_bp = Blueprint('user', __name__)

@user_bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        db = get_db()
        user_manager = UserManager(db)
        if user_manager.sign_up(form.email.data, form.password.data):
            flash('Account created successfully! Please check your email to verify your account.', 'success')
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
                return redirect(url_for('jobs.index'))
        flash('Login failed. Check your credentials.', 'danger')
    return render_template('login.html', form=form)


@user_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('user.login'))

@user_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = UpdateProfileForm()
    if form.validate_on_submit():
        if form.current_password.data:
            if form.new_password.data:
                db = get_db()  # Get the database instance
                user_manager = UserManager(db)                 
                if user_manager.check_password(current_user.id, form.current_password.data):
                    user_manager.update_password(current_user.id, form.new_password.data)
                    flash('Your profile has been updated.', 'success')
                    return redirect(url_for('user.profile'))                                                 
                else:
                    flash('Current password is incorrect.', 'danger')
                    return render_template('profile.html', form=form)
            else:
                flash('Please enter a new password.', 'danger')
                return render_template('profile.html', form=form)
        else:
            flash('Please enter your current password to update your profile.', 'danger')
            return render_template('profile.html', form=form)

    elif request.method == 'GET':
        form.email.data = current_user.email
    else:
        flash('Please correct the errors in the form.', 'danger')
    return render_template('profile.html', form=form)


@user_bp.route('/verify-email/<token>', methods=['GET'])
@login_required
def verify_email(token):
    db = get_db()
    user_manager = UserManager(db)
    email = request.args.get('email')
    if user_manager.verify_email(email, token):
        flash('Email verified successfully! You can now log in.', 'success')
    else:
        flash('Email verification failed. Please try again or contact support.', 'danger')
    return redirect(url_for('user.login'))

@user_bp.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        db = get_db()
        user_manager = UserManager(db)
        if user_manager.reset_password(form.email.data, form.new_password.data):
            flash('Password reset successful! Please log in with your new password.', 'success')
            return redirect(url_for('user.login'))
        else:
            flash('Password reset failed. Please try again.', 'danger')
    return render_template('reset_password.html', form=form)

@user_bp.route('/google-login')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    resp = google.get('/oauth2/v1/userinfo')
    if resp.ok:
        user_info = resp.json()
        google_id = user_info['id']
        email = user_info['email']
        db = get_db()
        user_manager = UserManager(db)
        user = user_manager.get_or_create_user_by_google_id(google_id, email)
        if user:
            login_user(user)
            flash('Logged in successfully via Google.', 'success')
            return redirect(url_for('jobs.index'))
        else:
            flash('Failed to log in via Google. Please try again.', 'danger')
            return redirect(url_for('user.login'))
    else:
        flash('Failed to get user info from Google.', 'danger')
        return redirect(url_for('user.login'))
