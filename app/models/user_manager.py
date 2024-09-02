import hashlib
import hmac
import os
from datetime import datetime

class UserManager:
    def __init__(self, db):
        self.db = db

    def create_users_table(self):
        """Create the users table if it doesn't exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            user_id SERIAL PRIMARY KEY,
            email VARCHAR(255) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        self.db.execute_query(create_table_query)

    def hash_password(self, password):
        """Hash a password for storing."""
        salt = os.urandom(16)
        pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return salt + pwdhash

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
            return True
        except Exception as e:
            return False

    def login(self, email, password):
        """Authenticate a user based on email and password."""
        query = "SELECT user_id, password_hash FROM users WHERE email = %s"
        result = self.db.fetch_one(query, (email,))
        if result:
            user_id, stored_password_hash = result
            if self.verify_password(bytes.fromhex(stored_password_hash), password):
                return True, user_id
            else:
                return False, None
        else:
            return False, None

    def reset_password(self, email, new_password):
        """Reset a user's password."""
        password_hash = self.hash_password(new_password)
        try:
            self.db.execute_query(
                "UPDATE users SET password_hash = %s WHERE email = %s",
                (password_hash.hex(), email)
            )
            return True
        except Exception as e:
            return False
