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
from app.utils.crypto import Crypto
from app.utils.api_response import APIResponse
class UserManager(UserMixin):
    def __init__(self, db):
        self.db = db
        self.email_sender = EmailSender()
        self.logger = logging.getLogger(__name__)

    def create_table(self) -> APIResponse:
        """Create the users table if it doesn't exist."""
        try:
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255),
                    is_active BOOLEAN DEFAULT TRUE,
                    email_verified BOOLEAN DEFAULT FALSE,
                    verification_token VARCHAR(255),
                    google_id VARCHAR(255),
                    last_login TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            self.logger.info("Users table created successfully")
            return APIResponse(status="success", message="Users table created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create users table: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to create users table: {str(e)}")
        
    def hash_password(self, password) -> APIResponse:
        """Hash the provided password."""
        try:
            hashed_password = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
            verify_password_response = self.verify_password(hashed_password, password)
            self.logger.info("Password hashed successfully")
            return APIResponse(status="success", message="Password hashed successfully", data={"hashed_password": hashed_password})
        except Exception as e:
            self.logger.error(f"Failed to hash password: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to hash password: {str(e)}")


    def verify_password(self, hashed_password, password) -> APIResponse:
        """Verify the provided password against the hashed password."""
        try:
            if bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8")):
                self.logger.info("Password verified successfully")
                return APIResponse(status="success", message="Password verified successfully")
            else:
                self.logger.warning("Password verification failed")
                return APIResponse(status="failure", message="Password verification failed")
        except Exception as e:
            self.logger.error(f"Failed to verify password: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to verify password: {str(e)}")

    def sign_up(self, email, password) -> APIResponse:
        """Create a new user account with a hashed password."""
        try:
            hash_password_response = self.hash_password(password)
            if hash_password_response.status == "success":
                password_hash = hash_password_response.data["hashed_password"]
                verification_token = secrets.token_urlsafe(32)

                self.db.execute_query(
                    "INSERT INTO users (email, password_hash, verification_token) VALUES (%s, %s, %s)",
                    (email, password_hash, verification_token)
                )

                verification_link = url_for('user.verify_email', token=verification_token, _external=True)

                email_html = render_template(
                    'verification_email.html',
                    user_name=email,
                    verification_link=verification_link
                )

                email_text = render_template(
                    'verification_email.txt',
                    user_name=email,
                    verification_link=verification_link
                )

                email_sent = self.email_sender.send_email(
                    recipient=email,
                    subject="Verify your email",
                    html_body=email_html,
                    text_body=email_text
                )

                if email_sent:
                    self.logger.info(f"User signed up successfully and verification email sent: {email}")
                    return APIResponse(status="success", message="User signed up and verification email sent")
                else:
                    self.logger.error(f"User signed up but failed to send verification email: {email}")
                    return APIResponse(status="failure", message="User signed up but failed to send verification email")
            else:
                return hash_password_response
        except Exception as e:
            self.logger.error(f"Sign up failed for {email}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Sign up failed for {email}: {str(e)}")

        except Exception as e:
            self.logger.error(f"Sign up failed for {email}: {str(e)}", exc_info=True)
            return False
        
    def get_user(self, user_id) -> APIResponse:
        """Retrieve a user's information by user_id and return a User object."""
        self.logger.info(f"Retrieving user with ID: {user_id}")
        try:
            query = "SELECT user_id, email, is_active FROM users WHERE user_id = %s"
            result = self.db.fetch_one(query, (user_id,))
            if result:
                user = User(user_id=result[0], email=result[1], is_active=result[2])
                self.logger.info(f"User retrieved successfully: {user.email}")
                return APIResponse(status="success", message="User retrieved successfully", data={"user": user})
            else:
                self.logger.warning(f"User with ID {user_id} not found")
                return APIResponse(status="failure", message="User not found")
        except Exception as e:
            self.logger.error(f"Failed to retrieve user with ID {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve user with ID {user_id}: {str(e)}")
        
    def login(self, email, password) -> APIResponse:
        """Authenticate a user based on email, password, active status, and email verification."""
        self.logger.info(f"Login attempt for user: {email}")
        
        try:
            query = "SELECT user_id, password_hash, is_active, email_verified FROM users WHERE email = %s"
            result = self.db.fetch_one(query, (email,))
            
            if result:
                user_id, stored_password_hash, is_active, email_verified = result
                if not is_active:
                    self.logger.warning(f"Login failed for {email}: account is inactive")
                    return APIResponse(status="failure", message="Account is inactive")
                
                if not email_verified:
                    self.logger.warning(f"Login failed for {email}: email not verified")
                    return APIResponse(status="failure", message="Email not verified")

                verify_password_response = self.verify_password(stored_password_hash, password)
                if verify_password_response.status == "success":
                    self.logger.info(f"Login successful for user: {email}")
                    return APIResponse(status="success", message="Login successful", data={"user_id": user_id})
                else:
                    self.logger.warning(f"Invalid password for user: {email}")
                    return APIResponse(status="failure", message="Invalid password")
            else:
                self.logger.warning(f"User with email {email} not found")
                return APIResponse(status="failure", message="User not found")
        except Exception as e:
            self.logger.error(f"Login failed for {email}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Login failed for {email}: {str(e)}")

    def reset_password(self, email, new_password) -> APIResponse:
        """Reset a user's password."""
        self.logger.info(f"Password reset attempt for user: {email}")
        try:
            hash_password_response = self.hash_password(new_password)
            if hash_password_response.status == "success":
                password_hash = hash_password_response.data["hashed_password"]
                self.db.execute_query(
                    "UPDATE users SET password_hash = %s WHERE email = %s",
                    (password_hash, email)
                )
                self.logger.info(f"Password reset successful for user: {email}")
                return APIResponse(status="success", message="Password reset successful")
            else:
                return hash_password_response
        except Exception as e:
            self.logger.error(f"Password reset failed for {email}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Password reset failed for {email}: {str(e)}")

    def get_all_users(self, active_only=True) -> APIResponse:
        """Retrieve all users, optionally filtering by active status."""
        self.logger.info(f"Retrieving {'active' if active_only else 'all'} users")
        try:
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
            return APIResponse(status="success", message="Users retrieved successfully", data={"users": users})
        except Exception as e:
            self.logger.error(f"Failed to retrieve users: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve users: {str(e)}")
                

    def activate_user(self, user_id) -> APIResponse:
        """Activate a user account."""
        self.logger.info(f"Activating user with ID {user_id}")
        try:
            data = {"is_active": True}
            condition = {"user_id": user_id}
            self.db.update_object("users", data, condition)
            self.logger.info(f"User with ID {user_id} activated successfully")
            return APIResponse(status="success", message="User activated successfully")
        except Exception as e:
            self.logger.error(f"Failed to activate user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to activate user {user_id}: {str(e)}")

    def deactivate_user(self, user_id) -> APIResponse:
        """Deactivate a user account."""
        self.logger.info(f"Deactivating user with ID {user_id}")
        try:
            data = {"is_active": False}
            condition = {"user_id": user_id}
            self.db.update_object("users", data, condition)
            self.logger.info(f"User with ID {user_id} deactivated successfully")
            return APIResponse(status="success", message="User deactivated successfully")
        except Exception as e:
            self.logger.error(f"Failed to deactivate user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to deactivate user {user_id}: {str(e)}")

    def delete_inactive_user(self, user_id) -> APIResponse:
        """Delete a user account only if it's inactive."""
        self.logger.info(f"Attempting to delete inactive user with ID {user_id}")
        try:
            condition = {"user_id": user_id, "is_active": False}
            self.db.delete_object("users", condition)
            self.logger.info(f"Inactive user with ID {user_id} deleted successfully")
            return APIResponse(status="success", message="Inactive user deleted successfully")
        except Exception as e:
            self.logger.error(f"Failed to delete user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to delete user {user_id}: {str(e)}")

    def check_password(self, user_id, password) -> APIResponse:
        """Check if the provided password matches the user's password."""
        self.logger.info(f"Checking password for user with ID {user_id}")
        user_response = self.get_user(user_id)
        if user_response.status == "success":
            user = user_response.data["user"]
            email = user.email
            password_hash_response = self.get_password_hash(email)
            if password_hash_response.status == "success":
                password_hash = password_hash_response.data["password_hash"]
                verify_password_response = self.verify_password(password_hash, password)
                if verify_password_response.status == "success":
                    self.logger.info(f"Password match for user with ID {user_id}")
                    return APIResponse(status="success", message="Password match")
                else:
                    self.logger.warning(f"Password mismatch for user with ID {user_id}")
                    return APIResponse(status="failure", message="Password mismatch")
            else:
                self.logger.warning(f"Password hash not found for user with ID {user_id}")
                return APIResponse(status="failure", message="Password hash not found")
        else:
            self.logger.warning(f"User with ID {user_id} not found")
            return APIResponse(status="failure", message="User not found")

    def update_password(self, user_id, new_password) -> APIResponse:
        """Update a user's password."""
        self.logger.info(f"Updating password for user with ID {user_id}")
        hash_password_response = self.hash_password(new_password)
        if hash_password_response.status == "success":
            try:
                data = {"password_hash": hash_password_response.data["hashed_password"]}
                condition = {"user_id": user_id}
                self.db.update_object("users", data, condition)
                self.logger.info(f"Password updated successfully for user with ID {user_id}")
                return APIResponse(status="success", message="Password updated successfully")
            except Exception as e:
                self.logger.error(f"Failed to update password for user {user_id}: {str(e)}", exc_info=True)
                return APIResponse(status="failure", message=f"Failed to update password for user {user_id}: {str(e)}")
        else:
            return hash_password_response

    def verify_email(self, email, token) -> APIResponse:
        """Verify user's email using the provided token."""
        try:
            result = self.db.fetch_one("SELECT user_id FROM users WHERE email = %s AND verification_token = %s", (email, token))
            if result:
                user_id = result[0]
                data = {"email_verified": True, "verification_token": None}
                condition = {"user_id": user_id}
                self.db.update_object("users", data, condition)
                self.logger.info(f"Email verified successfully for user: {email}")
                return APIResponse(status="success", message="Email verified successfully")
            else:
                self.logger.warning(f"Invalid verification attempt for email: {email}")
                return APIResponse(status="failure", message="Invalid verification attempt")
        except Exception as e:
            self.logger.error(f"Email verification failed for {email}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Email verification failed for {email}: {str(e)}")

    def get_or_create_user_by_google_id(self, google_id, email) -> APIResponse:
        """Get or create a user by Google ID."""
        try:
            result = self.db.fetch_one("SELECT * FROM users WHERE google_id = %s", (google_id,))
            if result:
                user = UserManager(*result)
                return APIResponse(status="success", message="User found", data={"user": user})
            else:
                self.db.execute_query("INSERT INTO users (google_id, email, email_verified) VALUES (%s, %s, TRUE)", (google_id, email))
                user = self.get_user_by_email(email)
                if user:
                    return APIResponse(status="success", message="User created", data={"user": user})
                else:
                    return APIResponse(status="failure", message="Failed to create user")
        except Exception as e:
            self.logger.error(f"Error getting or creating user by Google ID: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Error getting or creating user by Google ID: {str(e)}")

    def get_password_hash(self, email) -> APIResponse:
        """Retrieve the password hash for a given email."""
        self.logger.info(f"Retrieving password hash for email {email}")
        try:
            cursor = self.db.cursor()
            cursor.execute("SELECT password_hash FROM users WHERE email = %s", (email,))
            result = cursor.fetchone()
            if result:
                password_hash = result[0]
                self.logger.info(f"Password hash retrieved for email {email}")
                return APIResponse(status="success", message="Password hash retrieved", data={"password_hash": password_hash})
            else:
                self.logger.warning(f"No user found with email {email}")
                return APIResponse(status="failure", message="User not found")
        except Exception as e:
            self.logger.error(f"Failed to retrieve password hash: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve password hash: {str(e)}")
        
    def encrypt_sensible_data(self):
        crypto = Crypto()
        
        # Implement encryption logic here

    def update_last_login(self, user_id) -> APIResponse:
        """Update the last_login timestamp for a user."""
        self.logger.info(f"Updating last login for user with ID {user_id}")
        try:
            data = {"last_login": "CURRENT_TIMESTAMP"}
            condition = {"user_id": user_id}
            self.db.update_object("users", data, condition)
            self.logger.info(f"Last login updated successfully for user with ID {user_id}")
            return APIResponse(status="success", message="Last login updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update last login for user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to update last login for user {user_id}: {str(e)}")
        
    def get_users(self) -> APIResponse:
        """Retrieve all users."""
        self.logger.info("Retrieving all users")
        try:
            users = []
            results = self.db.fetch_all("SELECT * FROM users")
            for result in results:
                user = UserManager(*result)
                users.append(user)
            self.logger.info(f"Retrieved {len(users)} users successfully")
            return APIResponse(status="success", message="Users retrieved successfully", data={"users": users})
        except Exception as e:
            self.logger.error(f"Failed to retrieve users: {str(e)}")
            return APIResponse(status="failure", message=f"Failed to retrieve users: {str(e)}")

    def get_user_by_email(self, email) -> APIResponse:
        """Retrieve a user by email."""
        self.logger.info(f"Retrieving user with email {email}")
        try:
            result = self.db.fetch_one("SELECT * FROM users WHERE email = %s", (email,))
            if result:
                user = UserManager(*result)
                self.logger.info(f"User with email {email} retrieved successfully")
                return APIResponse(status="success", message="User retrieved successfully", data={"user": user})
            else:
                self.logger.warning(f"User with email {email} not found")
                return APIResponse(status="failure", message="User not found")
        except Exception as e:
            self.logger.error(f"Failed to retrieve user with email {email}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve user with email {email}: {str(e)}")

    def user_has_role(self, user_id, role_name) -> APIResponse:
        """Check if a user has a specific role."""
        self.logger.info(f"Checking if user {user_id} has role {role_name}")
        try:
            query = """
                SELECT 1 FROM user_roles ur
                JOIN roles r ON ur.role_id = r.role_id
                WHERE ur.user_id = %s AND r.role_name = %s
            """
            result = self.db.fetch_one(query, (user_id, role_name))
            if result:
                self.logger.info(f"User {user_id} has role {role_name}")
                return APIResponse(status="success", message="User has the specified role", data={"has_role": True})
            else:
                self.logger.info(f"User {user_id} does not have role {role_name}")
                return APIResponse(status="success", message="User does not have the specified role", data={"has_role": False})
        except Exception as e:
            self.logger.error(f"Failed to check role for user {user_id}: {str(e)}", exc_info=True)
            return

    def system_initialized(self) -> APIResponse:
        """Check if the system has been initialized with any users or roles."""
        self.logger.info("Checking if the system has been initialized")
        try:
            user_count = self.db.fetch_one("SELECT COUNT(*) FROM users")[0]
            role_count = self.db.fetch_one("SELECT COUNT(*) FROM roles")[0]
            
            is_initialized = user_count > 0 and role_count > 0
            
            if is_initialized:
                self.logger.info("System has been initialized")
            else:
                self.logger.info("System has not been initialized")
            
            return APIResponse(
                status="success",
                message="System initialization check completed",
                data={"initialized": is_initialized}
            )
        except Exception as e:
            self.logger.error(f"Failed to check system initialization: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to check system initialization: {str(e)}")

    def create_user(self, email, password, is_active=True):
        self.logger.info(f"Creating new user with email {email}")
        try:
            hash_password_response = self.hash_password(password)
            if hash_password_response.status == "success":
                
                password_hash = hash_password_response.data["hashed_password"]
                user_id = self.db.execute_query(
                    "INSERT INTO users (email, password_hash, email_verified) VALUES (%s, %s, %s) RETURNING user_id",
                    (email, password_hash, True)
                )

                self.logger.info(f"User created successfully")
                return APIResponse(status="success", message="User created successfully", data={"user_id": user_id})
            else:
                return hash_password_response
        except Exception as e:
            self.db.rollback()
            self.logger.error(f"Failed to create user: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to create user: {str(e)}")

    def search_users(self, query, page=1, page_size=10):
        self.logger.info(f"Searching for users with query: {query}")
        try:
            offset = (page - 1) * page_size
            users = []
            results = self.db.fetch_all(
                "SELECT * FROM users WHERE email LIKE %s OR username LIKE %s LIMIT %s OFFSET %s",
                (f"%{query}%", f"%{query}%", page_size, offset)
            )
            for result in results:
                user = UserManager(*result)
                users.append(user)
            self.logger.info(f"Found {len(users)} users matching the search query")
            return APIResponse(status="success", message="Users retrieved successfully", data={"users": users})
        except Exception as e:
            self.logger.error(f"Failed to search users: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to search users: {str(e)}")
        
    def update_user(self, user_id, data):
        self.logger.info(f"Updating user with ID {user_id}")
        try:
            condition = {"user_id": user_id}
            self.db.update_object("users", data, condition)
            self.logger.info(f"User with ID {user_id} updated successfully")
            return APIResponse(status="success", message="User updated successfully")
        except Exception as e:
            self.logger.error(f"Failed to update user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to update user {user_id}: {str(e)}")
        
    def delete_user(self, user_id):
        self.logger.info(f"Deleting user with ID {user_id}")
        try:
            condition = {"user_id": user_id}
            self.db.delete_object("users", condition)
            self.logger.info(f"User with ID {user_id} deleted successfully")
            return APIResponse(status="success", message="User deleted successfully")
        except Exception as e:
            self.logger.error(f"Failed to delete user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to delete user {user_id}: {str(e)}")
        
    def get_user_roles(self, user_id):
        self.logger.info(f"Retrieving roles for user with ID {user_id}")
        try:
            query = """
                SELECT r.role_name
                FROM user_roles ur
                JOIN roles r ON ur.role_id = r.role_id
                WHERE ur.user_id = %s
            """
            roles = [row[0] for row in self.db.fetch_all(query, (user_id,))]
            self.logger.info(f"Roles retrieved for user with ID {user_id}: {', '.join(roles)}")
            return APIResponse(status="success", message="Roles retrieved successfully", data=roles)
        except Exception as e:
            self.logger.error(f"Failed to retrieve roles for user {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve roles for user {user_id}: {str(e)}")
        
    def get_free_users(self, page=1, page_size=10):
        self.logger.info("Retrieving free users")
        try:
            offset = (page - 1) * page_size
            users = []
            results = self.db.fetch_all(
                "SELECT * FROM users WHERE user_id NOT IN (SELECT user_id FROM user_roles) LIMIT %s OFFSET %s",
                (page_size, offset)
            )
            for result in results:
                user = UserManager(*result)
                users.append(user)
            self.logger.info(f"Retrieved {len(users)} free users successfully")
            return APIResponse(status="success", message="Free users retrieved successfully", data={"users": users})
        except Exception as e:
            self.logger.error(f"Failed to retrieve free users: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve free users: {str(e)}")