from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_id, email, is_active=True):
        self.id = user_id  # Flask-Login expects `id` attribute for `get_id`
        self.email = email
        self.active = is_active

    def is_active(self):
        """Return whether the user is active."""
        return self.active
