from flask_login import UserMixin
import json

"""
This class represents a user in the system.
It inherits from UserMixin, which is a class provided by Flask-Login for handling user authentication.
"""
class User(UserMixin):
    def __init__(self, user_id, email, is_active = True, email_verified = True, last_login = None):
        self.user_id = user_id
        self.email = email
        self.is_active = is_active
        self.email_verified = email_verified
        self.last_login = last_login

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)

    def is_active(self):
        """Return whether the user is active."""
        return self.is_active

    def get_id(self):
        """Return the user_id as the unique identifier for Flask-Login."""
        return str(self.user_id)

