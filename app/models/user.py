from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_id, email, password_hash, active, google_id=None):
        self.user_id = user_id
        self.email = email
        self.password_hash = password_hash
        self.active = active
        self.google_id = google_id
        return self.active

    def is_active(self):
        """Return whether the user is active."""

