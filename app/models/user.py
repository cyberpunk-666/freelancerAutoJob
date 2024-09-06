from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_id, email, is_active, google_id=None):
        self.user_id = user_id
        self.email = email
        self.is_active = is_active
        self.google_id = google_id

    def is_active(self):
        """Return whether the user is active."""

    def get_id(self):
        """Return the user_id as the unique identifier for Flask-Login."""
        return str(self.user_id) 