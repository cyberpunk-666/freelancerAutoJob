from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, user_id, email, is_active):
        self.user_id = user_id
        self.email = email
        self.is_active = is_active

    def is_active(self):
        """Return whether the user is active."""
        return self.is_active

    def get_id(self):
        """Return the user_id as the unique identifier for Flask-Login."""
        return str(self.user_id)

    def has_role(self, role_name):
        # We'll implement this method using your existing database structure
        from app.db.utils import get_db
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            SELECT 1 FROM user_roles ur
            JOIN roles r ON ur.role_id = r.id
            WHERE ur.user_id = ? AND r.name = ?
        """, (self.user_id, role_name))
        return cursor.fetchone() is not None

    @staticmethod
    def get(user_id):
        from app.db.utils import get_db
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT id, email, is_active FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        if user_data:
            return User(user_data['id'], user_data['email'], user_data['is_active'])
        return None
