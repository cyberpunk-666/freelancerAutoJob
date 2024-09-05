import hashlib
import hmac
import os
import re
from datetime import datetime
import logging
from app.models.user import User
from flask_login import UserMixin
from flask import url_for, render_template
from app.utils.email_sender import EmailSender
import secrets
import bcrypt
class UserManager(UserMixin):
    def __init__(self, db):
        self.db = db
        self.email_sender = EmailSender()
        self.logger = logging.getLogger(__name__)

    def create_table(self):
        """Create the users table if it doesn't exist."""
        self.logger.info("Creating users table")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            verification_token VARCHAR(64),  -- Add the verification_token column
            email_verified BOOLEAN DEFAULT FALSE, -- Add email verification status
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
        """
        self.db.execute_query(create_table_query)
        self.logger.info("Users table created successfully")



    def hash_password(self, password):
        """Hash a password for storing."""
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def verify_password(self, stored_password, provided_password):
        """Verify a stored password against one provided by user."""
        return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password)


    def sign_up(self, email, password):
        """Create a new user account with a hashed password."""
        password_hash = self.hash_password(password)
        verification_token = secrets.token_urlsafe(32)  # Generate a unique token for email verification
        try:
            # Insert user into the database
            self.db.execute_query(
                "INSERT INTO users (email, password_hash, verification_token) VALUES (%s, %s, %s)",
                (email, password_hash.hex(), verification_token)
            )

            # Generate the verification link
            verification_link = url_for('user.verify_email', token=verification_token, _external=True)

            # Load the HTML email template and replace placeholders
            email_html = render_template(
                'app/models/processed_email_manager.py',  # Assuming the template is in templates/email/verification_email.html
                user_name=email,  # Replace with actual user's name if available
                verification_link=verification_link
            )

            # Send the email using the email sender utility
            email_sent = self.email_sender.send_email(
                to=email,
                subject="Verify your email",
                html_body=email_html  # Send the HTML content
            )

            if email_sent:
                self.logger.info(f"User signed up successfully and verification email sent: {email}")
                return True
            else:
                self.logger.error(f"User signed up but failed to send verification email: {email}")
                return False

        except Exception as e:
            self.logger.error(f"Sign up failed for {email}: {str(e)}", exc_info=True)
            return False



    def login(self, email, password):
        """Authenticate a user based on email, password, and active status."""
        self.logger.info(f"Login attempt for user: {email}")
        query = "SELECT user_id, password_hash, is_active FROM users WHERE email = %s"
        result = self.db.fetch_one(query, (email,))
        
        if result:
            user_id, stored_password_hash, is_active = result
            if not is_active:
                self.logger.warning(f"Login failed for {email}: account is inactive")
                return False, None
            
            if self.verify_password(bytes.fromhex(stored_password_hash), password):
                return True, user_id
            else:
                return False, None
        else:
            return False, None


    def reset_password(self, email, new_password):
        """Reset a user's password."""
        self.logger.info(f"Password reset attempt for user: {email}")
        password_hash = self.hash_password(new_password)
        try:
            self.db.execute_query(
                "UPDATE users SET password_hash = %s WHERE email = %s",
                (password_hash.hex(), email)
            )
            return True
            self.logger.info(f"Password reset successful for user: {email}")
        except Exception as e:
            self.logger.error(f"Password reset failed for {email}: {str(e)}")
            return False

    def get_user(self, user_id):
        """Retrieve a user's information by user_id and return a User object."""
        self.logger.info(f"Retrieving user with ID: {user_id}")
        query = "SELECT user_id, email, is_active FROM users WHERE user_id = %s"
        result = self.db.fetch_one(query, (user_id,))
        if result:
            user = User(user_id=result[0], email=result[1], is_active=result[2])
            self.logger.info(f"User retrieved successfully: {user.email}")
            return user
        else:
            self.logger.warning(f"User with ID {user_id} not found")
            return None


    def get_all_users(self, active_only=True):
        """Retrieve all users, optionally filtering by active status."""
        self.logger.info(f"Retrieving {'active' if active_only else 'all'} users")
        if active_only:
            query = "SELECT user_id, email, created_at FROM users WHERE is_active = TRUE"
        else:
            query = "SELECT user_id, email, created_at FROM users"
            
        results = self.db.fetch_all(query)
        users = [
            {
                'user_id': row[0],
                'email': row[1],
                'created_at': row[2]
            } for row in results
        ]
        self.logger.info(f"Retrieved {len(users)} users successfully")
        return users

    def activate_user(self, user_id):
        """Activate a user account."""
        self.logger.info(f"Activating user with ID {user_id}")
        try:
            self.db.execute_query(
                "UPDATE users SET is_active = TRUE WHERE user_id = %s",
                (user_id,)
            )
            self.logger.info(f"User with ID {user_id} activated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to activate user {user_id}: {str(e)}", exc_info=True)
            return False

    def deactivate_user(self, user_id):
        """Deactivate a user account."""
        self.logger.info(f"Deactivating user with ID {user_id}")
        try:
            self.db.execute_query(
                "UPDATE users SET is_active = FALSE WHERE user_id = %s",
                (user_id,)
            )
            self.logger.info(f"User with ID {user_id} deactivated successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to deactivate user {user_id}: {str(e)}", exc_info=True)
            return False

    def delete_inactive_user(self, user_id):
        """Delete a user account only if it's inactive."""
        self.logger.info(f"Attempting to delete inactive user with ID {user_id}")
        try:
            # Ensure the user is inactive before deletion
            query = "DELETE FROM users WHERE user_id = %s AND is_active = FALSE"
            self.db.execute_query(query, (user_id,))
            self.logger.info(f"Inactive user with ID {user_id} deleted successfully")
            return True
        except Exception as e:
            self.logger.error(f"Failed to delete user {user_id}: {str(e)}", exc_info=True)
            return False

    def check_password(self, user_id, password):
        """Check if the provided password matches the user's password."""
        self.logger.info(f"Checking password for user with ID {user_id}")
        query = "SELECT password_hash FROM users WHERE user_id = %s"
        result = self.db.fetch_one(query, (user_id, ))
        if result:
            stored_password_hash = result[0]
            if self.verify_password(bytes.fromhex(stored_password_hash), password):
                self.logger.info(f"Password match for user with ID {user_id}")
                return True
            else:
                self.logger.warning(f"Password mismatch for user with ID {user_id}")
                return False
        else:
            self.logger.warning(f"User with ID {user_id} not found")
            return False

    def update_password(self, user_id, new_password):
        """Update a user's password."""
        self.logger.info(f"Updating password for user with ID {user_id}")
        password_hash = self.hash_password(new_password)
        try:
            self.db.execute_query(
                "UPDATE users SET password_hash = %s WHERE user_id = %s",
                (password_hash.hex(), user_id)
            )
            self.logger.info(f"Password updated successfully for user with ID {user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to update password for user {user_id}: {str(e)}", exc_info=True)
            return False

    def verify_email(self, email, token):
        """Verify user's email using the provided token."""
        try:
            result = self.db.fetch_one(
                "SELECT user_id FROM users WHERE email = %s AND verification_token = %s",
                (email, token)
            )
            if result:
                self.db.execute_query("UPDATE users SET email_verified = TRUE, verification_token = NULL WHERE user_id = %s", (result[0],))
                self.logger.info(f"Email verified successfully for user: {email}")
                return True
            else:
                self.logger.warning(f"Invalid verification attempt for email: {email}")
                return False
        except Exception as e:
            self.logger.error(f"Email verification failed for {email}: {str(e)}", exc_info=True)
            return False
