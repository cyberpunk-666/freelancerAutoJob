from flask_wtf import FlaskForm
from wtforms import ValidationError
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length
import re

DISPOSABLE_DOMAINS = [
    'tempmail.com', 'throwawaymail.com', '10minutemail.com', 'guerrillamail.com',
    'mailinator.com', 'yopmail.com', 'getairmail.com', 'fakeinbox.com'
]

def validate_email(form, field):
    email = field.data
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(pattern, email):
        raise ValidationError('Invalid email format.')
    
    domain = email.split('@')[1]
    if domain in DISPOSABLE_DOMAINS:
        raise ValidationError('Disposable email addresses are not allowed.')
    
def validate_password_complexity(form, field):
    password = field.data
    if not re.search(r'[A-Z]', password):
        raise ValidationError('Password must contain at least one uppercase letter.')
    if not re.search(r'[a-z]', password):
        raise ValidationError('Password must contain at least one lowercase letter.')
    if not re.search(r'\d', password):
        raise ValidationError('Password must contain at least one number.')
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        raise ValidationError('Password must contain at least one special character.')

class RegistrationForm(FlaskForm):
    """Form for users to create a new account."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long'),
        validate_password_complexity
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    """Form for users to log in."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class ResetPasswordForm(FlaskForm):
    """Form for users to reset their password."""
    email = StringField('Email', validators=[DataRequired(), Email()])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')
    
class UpdateProfileForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Update Profile')
    gemini_api_key = StringField('Gemini API Key')

    def validate(self, extra_validators=None, **kwargs):
        # Custom validation logic here
        # For example, you could check if the current password matches the user's actual password
        initial_validation = super(UpdateProfileForm, self).validate(extra_validators=extra_validators, **kwargs)
        return initial_validation
