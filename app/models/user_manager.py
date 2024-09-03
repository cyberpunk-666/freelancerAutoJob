import hashlib
import hmac
import os
from datetime import datetime
import logging
from app.models.user import User
from flask_login import UserMixin
class UserManager(UserMixin):
    def __init__(self, db):
        self.db = db
        self.logger = logging.getLogger(__name__)

    def create_table(self):
        """Create the users table if it doesn't exist."""
        self.logger.info("Creating users table")
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN DEFAULT TRUE
        );
        """
        self.db.execute_query(create_table_query)
        self.logger.info("Users table created successfully")


    def hash_password(self, password):
        """Hash a password for storing."""
        salt = os.urandom(16)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt + pwdhash

        self.logger.info(f"Attempting to sign up user: {email}")
    def verify_password(self, stored_password, provided_password):
        """Verify a stored password against one provided by user."""
        salt = stored_password[:16]
        stored_pwdhash = stored_password[16:]
        pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return hmac.compare_digest(stored_pwdhash, pwdhash)

    def sign_up(self, email, password):
        """Create a new user account with a hashed password."""
        password_hash = self.hash_password(password)
        try:
            self.db.execute_query(
                "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
                (email, password_hash.hex())
            )
            self.logger.info(f"User signed up successfully: {email}")
            return True
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
