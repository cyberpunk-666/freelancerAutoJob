import logging
from app.utils.api_response import APIResponse
class RoleManager:
    def __init__(self, db):
        self.db = db
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
            self.db.execute_query(
                "INSERT INTO roles (role_name) VALUES (%s)",
                (role_name,)
            )
            self.logger.info(f"Role '{role_name}' created successfully")
            return APIResponse(status="success", message=f"Role '{role_name}' created successfully")
        except Exception as e:
            self.logger.error(f"Failed to create role '{role_name}': {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to create role '{role_name}'")

    def assign_role_to_user(self, user_id, role_name) -> APIResponse:
        """Assign a role to a user."""
        self.logger.info(f"Assigning role '{role_name}' to user with ID {user_id}")
        try:
            # Get the role_id for the given role_name
            role_id = self.db.fetch_one("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
            if role_id:
                role_id = role_id[0]
                self.db.execute_query(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (user_id, role_id)
                )
                self.logger.info(f"Role '{role_name}' assigned to user with ID {user_id} successfully")
                return APIResponse(status="success", message=f"Role '{role_name}' assigned successfully")
            else:
                self.logger.error(f"Role '{role_name}' does not exist")
                return APIResponse(status="failure", message=f"Role '{role_name}' does not exist")
        except Exception as e:
            self.logger.error(f"Failed to assign role '{role_name}' to user with ID {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message=f"Failed to assign role '{role_name}'")

    def remove_role_from_user(self, user_id, role_name) -> APIResponse:
        """Remove a role from a user."""
        self.logger.info(f"Removing role '{role_name}' from user with ID {user_id}")
        try:
            # Get the role_id for the given role_name
            role_id = self.db.fetch_one("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
            if role_id:
                role_id = role_id[0]
                self.db.execute_query(
                    "DELETE FROM user_roles WHERE user_id = %s AND role_id = %s",
                    (user_id, role_id)
                )
                self.logger.info(f"Role '{role_name}' removed from user with ID {user_id} successfully")
                return APIResponse(status="success", message=f"Role '{role_name}' removed successfully")
            else:
                self.logger.error(f"Role '{role_name}' does not exist")
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

    def has_role(self, user_id, role_name) -> APIResponse:
        """Check if a user has a specific role."""
        self.logger.info(f"Checking if user with ID {user_id} has role '{role_name}'")
        try:
            role_id = self.db.fetch_one("SELECT role_id FROM roles WHERE role_name = %s", (role_name,))
            if role_id:
                role_id = role_id[0]
                result = self.db.fetch_one(
                    "SELECT COUNT(*) FROM user_roles WHERE user_id = %s AND role_id = %s",
                    (user_id, role_id)
                )
                has_role = result[0] > 0
                self.logger.info(f"User with ID {user_id} {'has' if has_role else 'does not have'} role '{role_name}'")
                return APIResponse(status="success", message="Role check successful", data={"has_role": has_role})
            else:
                self.logger.error(f"Role '{role_name}' does not exist")
                return APIResponse(status="failure", message=f"Role '{role_name}' does not exist")
        except Exception as e:
            self.logger.error(f"Failed to check role '{role_name}' for user with ID {user_id}: {str(e)}", exc_info=True)
            return APIResponse(status="failure", message="Failed to check role")
