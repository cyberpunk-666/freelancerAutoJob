// Function to get all users
async function getAllUsers(params) {
    try {
        const queryString = new URLSearchParams(params).toString();
        const response = await fetch(`/api/users?${queryString}`);
        if (!response.ok) {
            throw new Error('Failed to fetch users');
        }
        const data = await response.json();
        if (data.status == "success") {
            return data.data.users;
        } else {
            throw new Error(data.message || 'Failed to fetch users');
        }
    } catch (error) {
        console.error('Error fetching users:', error);
        throw error;
    }
}

// Function to get a specific user
async function getUser(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch user');
        }
        const data = await response.json();
        if (data.status == "success") {
            return data.data;
        } else {
            throw new Error(data.message || 'Failed to fetch user');
        }
    } catch (error) {
        console.error('Error fetching user:', error);
        throw error;
    }
}

// Function to search users
async function searchUsers(query) {
    try {
        let params = new URLSearchParams(query).toString()
        const response = await fetch(`/api/users/search?${params}`);
        if (!response.ok) {
            throw new Error('Failed to search users');
        }
        const data = await response.json();
        if (data.status == "success") {
            return data.data["users"];
        } else {
            throw new Error(data.message || 'Failed to search users');
        }
    } catch (error) {
        console.error('Error searching users:', error);
        throw error;
    }
}

// Function to create a new user
async function createUser(userData) {
    try {
        const response = await fetch('/api/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData),
        });
        if (!response.ok) {
            throw new Error('Failed to create user');
        }
        const data = await response.json();
        if (data.status == "success") {
            return data.data;
        } else {
            throw new Error(data.message || 'Failed to create user');
        }
    } catch (error) {
        console.error('Error creating user:', error);
        throw error;
    }
}

// Function to update a user
async function updateUser(userId, userData) {
    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(userData),
        });
        if (!response.ok) {
            throw new Error('Failed to update user');
        }
        const data = await response.json();
        if (data.status == "success") {
            return data.data;
        } else {
            throw new Error(data.message || 'Failed to update user');
        }
    } catch (error) {
        console.error('Error updating user:', error);
        throw error;
    }
}

// Function to delete a user
async function deleteUser(userId) {
    try {
        const response = await fetch(`/api/users/${userId}`, {
            method: 'DELETE',
        });
        if (!response.ok) {
            throw new Error('Failed to delete user');
        }
        const data = await response.json();
        if (data.status == "success") {
            return data.data;
        } else {
            throw new Error(data.message || 'Failed to delete user');
        }
    } catch (error) {
        console.error('Error deleting user:', error);
        throw error;
    }
}

// Function to get user roles
async function getUserRoles(userId) {
    try {
        const response = await fetch(`/api/users/${userId}/roles`);
        if (!response.ok) {
            throw new Error('Failed to fetch user roles');
        }
        const data = await response.json();
        if (data.status == "success") {
            return data.data;
        } else {
            throw new Error(data.message || 'Failed to fetch user roles');
        }
    } catch (error) {
        console.error('Error fetching user roles:', error);
        throw error;
    }
}
