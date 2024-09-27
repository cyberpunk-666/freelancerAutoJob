import json
import os
from flask_dance.contrib.google import google
from flask import app, current_app, flash
from flask import Blueprint, render_template, redirect, url_for, flash, session, request, session
from flask_login import login_user, logout_user
from app.forms.user_forms import UpdateProfileForm, RegistrationForm, LoginForm, ResetPasswordForm
from flask import url_for
from app.managers.user_manager import UserManager
from app.db.db_utils import get_db
from flask_login import current_user
from flask_login import login_required, current_user
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.managers.user_preferences_manager import UserPreferencesManager

csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address)

user_bp = Blueprint('user', __name__)
user_api_bp = Blueprint('user_api', __name__)

@user_bp.route('/signup', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def signup():
    form = RegistrationForm()
    if form.validate_on_submit():
        user_manager = UserManager()
        if user_manager.sign_up(form.email.data, form.password.data):
            flash('Account created successfully! Please check your email to verify your account.', 'success')
            return redirect(url_for('user.login'))
        else:
            flash('Sign-up failed. Email might already be registered.', 'danger')
    return render_template('user/signup.html', form=form)


@user_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user_manager = UserManager()  # Initialize UserManager with the db instance
        
        # Login attempt
        login_response = user_manager.login(form.email.data, form.password.data)
        
        if login_response.status == "success":
            # Retrieve usern
            user_response = user_manager.get_user(login_response.data["user_id"])
            
            if user_response.status == "success":
                user = user_response.data["user"]
                login_user(user)
                flash(login_response.message, 'success')
                return redirect(url_for('jobs.index'))
            else:
                flash(user_response.message, 'danger')
        else:
            flash(login_response.message, 'danger')
    
    return render_template('user/login.html', form=form)




@user_bp.route('/logout')
def logout():
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('user.login'))

@user_bp.route('/profile', methods=['GET'])
@login_required
def profile_get():
    form = UpdateProfileForm()
    user_manager = UserManager()
    get_user_response = user_manager.get_user_profile(current_user.user_id)
    if get_user_response.status == "success":
        user = get_user_response.data["user"]
        form.email.data = user[1]
        form.gemini_api_key.data = user[2]
    else:
        flash(get_user_response.message, 'danger')
    return render_template('user/profile.html', form=form)


@user_bp.route('/profile', methods=['POST'])
@login_required
def profile_post():
    form = UpdateProfileForm()
    if not form.validate_on_submit():
        # Print or log form errors for debugging
        print(form.errors)
        for field, errors in form.errors.items():
            for error in errors:
                print(f"Field: {field}, Error: {error}")
                
        flash('Please correct the errors in the form.', 'danger')
    else:
        user_manager = UserManager()
        user_manager.update_user(current_user.user_id, data={
            'email': form.email.data,
            'gemini_api_key': form.gemini_api_key.data
        })
        flash('Profile updated successfully!', 'success')
    return render_template('user/profile.html', form=form)

@user_bp.route('/verify-email/<token>', methods=['GET'])
@login_required
def verify_email(token):
    user_manager = UserManager()
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
        user_manager = UserManager()
        if user_manager.reset_password(form.email.data, form.new_password.data):
            flash('Password reset successful! Please log in with your new password.', 'success')
            return redirect(url_for('user.login'))
        else:
            flash('Password reset failed. Please try again.', 'danger')
    return render_template('user/reset_password.html', form=form)

@user_bp.route('/google-login')
def google_login():
    if not google.authorized:
        return redirect(url_for('google.login'))
    resp = google.get('/oauth2/v1/userinfo')
    if resp.ok:
        user_info = resp.json()
        google_id = user_info['id']
        email = user_info['email']
        user_manager = UserManager()
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
    

@user_bp.route('/preferences', methods=['GET', 'POST'])
@login_required
def preferences():
    user_preferences_manager = UserPreferencesManager()
    if request.method == 'POST':
        # Handle form submission
        for pref_key, pref_value in request.form.items():
            set_preference_response = user_preferences_manager.set_preference(current_user.user_id, pref_key, pref_value)
            if not set_preference_response.status == "success":
                flash(set_preference_response.message, 'danger')
                break  # Exit the loop if there's an error
        else:  # This else belongs to the for loop (it runs if the loop completes without a break)
            flash('Preferences updated successfully', 'success')
        
        # Redirect to GET after POST (Post/Redirect/Get pattern)
        return redirect(url_for('user.preferences'))

    # Fetch user preferences (for both GET and after POST)
    get_preferences_response = user_preferences_manager.get_preferences(current_user.user_id)
    user_preferences = get_preferences_response.data if get_preferences_response.status == "success" else {}

    # Load and process the JSON configuration
    try:
        app = current_app._get_current_object()
        with app.app_context():
            config_file_path = os.path.join(current_app.root_path, 'static', 'config', 'preferences.json')
            with open(config_file_path, 'r') as config_file:
                preferences_config = json.load(config_file)
    except Exception as e:
        flash(f'Error loading preferences configuration: {str(e)}', 'danger')
        return render_template('user/preferences.html', user_preferences=user_preferences, preferences_by_category={})
    # Organize preferences by category
    preferences_by_category = {}
    for pref in preferences_config['preferences']:
        category = pref.get('category', 'General')
        if category not in preferences_by_category:
            preferences_by_category[category] = []
        preferences_by_category[category].append(pref)

    return render_template('user/preferences.html', 
        preferences_by_category=preferences_by_category, 
        user_preferences=user_preferences)