import logging
from app.db.db_utils import get_db
from app.db.postgresdb import PostgresDB
from app.models.api_response import APIResponse


class RoleManager:
    def __init__(self):
        self.db: PostgresDB = get_db()
        self.logger = logging.getLogger(__name__)

    def create_tables(self) -> APIResponse:
        """Create the roles and user_roles tables if they don't exist."""
        self.logger.info("Creating roles and user_roles tables")

        create_roles_table_query = """
        CREATE TABLE IF NOT EXISTS roles (
            role_id SERIAL PRIMARY KEY,
            role_name VARCHAR(255) UNIQUE NOT NULL
        );
        """
        self.db.execute_query(create_roles_table_query)

        create_user_roles_table_query = """
        CREATE TABLE IF NOT EXISTS user_roles (
            user_id INTEGER REFERENCES users(user_id) ON DELETE CASCADE,
            role_id INTEGER REFERENCES roles(role_id) ON DELETE CASCADE,
            PRIMARY KEY (user_id, role_id)
        );
        """
        self.db.execute_query(create_user_roles_table_query)

        self.logger.info("Roles and user_roles tables created successfully")
        return APIResponse(status="success", message="Tables created successfully")

    def create_role(self, role_name) -> APIResponse:
        """Create a new role."""
        self.logger.info(f"Creating role: {role_name}")
        try:
            self.db.execute_query("INSERT INTO roles (role_name) VALUES (%s)", (role_name,))
            self.logger.info(f"Role '{role_name}' created successfully")
            return APIResponse(status="success", message=f"Role '{role_name}' created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create role '{role_name}': {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to create role '{role_name}'")

    def assign_role_to_user(self, user_id, role_name) -> APIResponse:
        """Assign a role to a user using role_name."""
        self.logger.info(f"Assigning role '{role_name}' to user with ID {user_id}")
        try:
            # Get the role_id for the given role_name
            role_id = self._get_role_id_by_name(role_name)
            if role_id:
                self.db.execute_query("INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)", (user_id, role_id))
                self.logger.info(f"Role '{role_name}' assigned to user with ID {user_id} successfully")
                return APIResponse(status="success", message=f"Role '{role_name}' assigned successfully")
            else:
                return APIResponse(status="failure", message=f"Role '{role_name}' does not exist")
        except Exception as e:
            self.logger.error(f"Failed to assign role '{role_name}' to user with ID {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to assign role '{role_name}'")

    def remove_role_from_user(self, user_id, role_name) -> APIResponse:
        """Remove a role from a user using role_name."""
        self.logger.info(f"Removing role '{role_name}' from user with ID {user_id}")
        try:
            # Get the role_id for the given role_name
            role_id = self._get_role_id_by_name(role_name)
            if role_id:
                self.db.execute_query("DELETE FROM user_roles WHERE user_id = %s AND role_id = %s", (user_id, role_id))
                self.logger.info(f"Role '{role_name}' removed from user with ID {user_id} successfully")
                return APIResponse(status="success", message=f"Role '{role_name}' removed successfully")
            else:
                return APIResponse(status="failure", message=f"Role '{role_name}' does not exist")
        except Exception as e:
            self.logger.error(f"Failed to remove role '{role_name}' from user with ID {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to remove role '{role_name}'")

    def get_user_roles(self, user_id) -> APIResponse:
        """Get all roles assigned to a user."""
        self.logger.info(f"Getting roles for user with ID {user_id}")
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
            self.logger.error(f"Failed to get roles for user with ID {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message="Failed to retrieve roles")

    def has_role(self, user_id, role_name) -> bool:
        """Check if a user has a specific role using role_name."""
        self.logger.info(f"Checking if user with ID {user_id} has role '{role_name}'")
        try:
            role_id = self._get_role_id_by_name(role_name)
            if role_id:
                result = self.db.fetch_one(
                    "SELECT COUNT(*) FROM user_roles WHERE user_id = %s AND role_id = %s", (user_id, role_id)
                )
                has_role = result[0] > 0
                self.logger.info(f"User with ID {user_id} {'has' if has_role else 'does not have'} role '{role_name}'")
                return has_role
            else:
                return False
        except Exception as e:
            self.logger.error(f"Failed to check role '{role_name}' for user with ID {user_id}: {str(e)}", exc_info=True)
            return False

    def get_all_roles(self) -> APIResponse:
        """Get all available roles."""
        self.logger.info("Getting all roles")
        try:
            roles = [row[0] for row in self.db.fetch_all("SELECT role_name FROM roles")]
            self.logger.info(f"Roles retrieved: {', '.join(roles)}")
            return APIResponse(status="success", message="Roles retrieved successfully", data=roles)
        except Exception as e:
            self.logger.error(f"Failed to get roles: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message="Failed to retrieve roles")

    def get_users_in_role(self, role_name) -> APIResponse:
        """Get all users assigned to a specific role."""
        self.logger.info(f"Getting users in role '{role_name}'")
        try:
            role_id = self._get_role_id_by_name(role_name)
            if role_id:
                query = """
                SELECT u.user_id, u.email
                FROM user_roles ur
                JOIN users u ON ur.user_id = u.user_id
                WHERE ur.role_id = %s
                """
                users = self.db.fetch_all(query, (role_id,))
                self.logger.info(f"Users retrieved for role '{role_name}'")
                return APIResponse(status="success", message="Users retrieved successfully", data=users)
            else:
                return APIResponse(status="failure", message=f"Role '{role_name}' does not exist")
        except Exception as e:
            self.logger.error(f"Failed to get users for role '{role_name}': {str(e)}", exc_info=True)
            return APIResponse(status="failure", message="Failed to retrieve users")

    def get_users_without_role(self) -> APIResponse:
        """Get all users without any assigned roles."""
        self.logger.info("Getting users without any role")
        try:
            query = """
            SELECT u.user_id, u.username
            FROM users u
            LEFT JOIN user_roles ur ON u.user_id = ur.user_id
            WHERE ur.role_id IS NULL
            """
            users = self.db.fetch_all(query)
            self.logger.info("Users without roles retrieved")
            return APIResponse(status="success", message="Users retrieved successfully", data=users)
        except Exception as e:
            self.logger.error(f"Failed to get users without role: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message="Failed to retrieve users")

    def update_role(self, old_role_name, new_role_name) -> APIResponse:
        """Update the name of a role."""
        self.logger.info(f"Updating role from '{old_role_name}' to '{new_role_name}'")
        try:
            role_id = self._get_role_id_by_name(old_role_name)
            if role_id:
                self.db.execute_query("UPDATE roles SET role_name = %s WHERE role_id = %s", (new_role_name, role_id))
                self.logger.info(f"Role '{old_role_name}' updated to '{new_role_name}' successfully")
                return APIResponse(status="success", message=f"Role '{old_role_name}' updated successfully")
            else:
                return APIResponse(status="failure", message=f"Role '{old_role_name}' does not exist")
        except Exception as e:
            self.logger.error(f"Failed to update role '{old_role_name}' to '{new_role_name}': {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to update role '{old_role_name}'")

    def delete_role(self, role_name) -> APIResponse:
        """Delete a role."""
        self.logger.info(f"Deleting role '{role_name}'")
        try:
            role_id = self._get_role_id_by_name(role_name)
            if role_id:
                # First, delete the role assignments from user_roles
                self.db.execute_query("DELETE FROM user_roles WHERE role_id = %s", (role_id,))
                # Then, delete the role itself
                self.db.execute_query("DELETE FROM roles WHERE role_id = %s", (role_id,))
                self.logger.info(f"Role '{role_name}' deleted successfully")
                return APIResponse(status="success", message=f"Role '{role_name}' deleted successfully")
            else:
                return APIResponse(status="failure", message=f"Role '{role_name}' does not exist")
        except Exception as e:
            self.logger.error(f"Failed to delete role '{role_name}': {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to delete role '{role_name}'")

    def get_role(self, role_name) -> APIResponse:
        """Get details of a role."""
        self.logger.info(f"Retrieving role '{role_name}'")
        try:
            role = self.db.fetch_one("SELECT role_id, role_name FROM roles WHERE role_name = %s", (role_name,))
            if role:
                self.logger.info(f"Role '{role_name}' retrieved successfully")
                return APIResponse(
                    status="success", message="Role retrieved successfully", data={"role_id": role[0], "role_name": role[1]}
                )
            else:
                return APIResponse(status="failure", message=f"Role '{role_name}' does not exist")
        except Exception as e:
            self.logger.error(f"Failed to retrieve role '{role_name}': {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to retrieve role '{role_name}'")

    def _get_role_id_by_name(self, role_name):
        """Helper function to get role_id by role_name."""
        role = self.db.fetch_one("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
        return role[0] if role else None
