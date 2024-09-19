let currentRoleName = null;

// Load and display all roles
async function loadRoles() {
    try {
        const response = await fetch('/api/roles');
        if (!response.ok) {
            throw new Error('Failed to fetch roles');
        }
        const apiResponse = await response.json();
        
        if (apiResponse.status === 'success') {
            const roles = apiResponse.data;
            
            const roleListItems = document.getElementById('roleListItems');
            roleListItems.innerHTML = '';
            roles.forEach(roleName => {
                const li = document.createElement('li');
                li.textContent = roleName;
                li.onclick = () => selectRole(roleName);
                roleListItems.appendChild(li);
            });
        } else {
            throw new Error(apiResponse.message);
        }
    } catch (error) {
        console.error('Error loading roles:', error);
        alert('Failed to load roles. Please try again.');
    }
}

// Create a new role
async function createRole() {
    const newRoleName = document.getElementById('newRoleName').value.trim();
    if (newRoleName) {
        try {
            const response = await fetch('/api/roles', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: newRoleName }),
            });

            if (!response.ok) {
                throw new Error('Failed to create role');
            }

            const apiResponse = await response.json();

            if (apiResponse.status === 'success') {
                await loadRoles();
                document.getElementById('newRoleName').value = '';
            } else {
                throw new Error(apiResponse.message);
            }
        } catch (error) {
            console.error('Error creating role:', error);
            alert('Failed to create role. Please try again.');
        }
    }
}

// Select and display a role
async function selectRole(roleName) {
    currentRoleName = roleName;
    try {
        const response = await fetch(`/api/roles/${roleName}`);
        if (!response.ok) {
            throw new Error('Failed to fetch role details');
        }
        const apiResponse = await response.json();
        
        if (apiResponse.status === 'success') {
            document.getElementById('currentRoleName').textContent = roleName;
            document.getElementById('roleDetails').style.display = 'block';
            await loadUsersInRole(roleName);
            await loadFreeUsers(roleName);
        } else {
            throw new Error(apiResponse.message);
        }
    } catch (error) {
        console.error('Error selecting role:', error);
        alert('Failed to load role details. Please try again.');
    }
}

// Edit the selected role
async function editRole() {
    const newName = prompt('Enter new role name', currentRoleName);
    if (newName && newName !== currentRoleName) {
        try {
            const response = await fetch(`/api/roles/${currentRoleName}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: newName }),
            });
            if (!response.ok) {
                throw new Error('Failed to update role');
            }
            const apiResponse = await response.json();
            
            if (apiResponse.status === 'success') {
                await loadRoles();
                currentRoleName = newName;
                document.getElementById('currentRoleName').textContent = newName;
            } else {
                throw new Error(apiResponse.message);
            }
        } catch (error) {
            console.error('Error updating role:', error);
            alert('Failed to update role. Please try again.');
        }
    }
}

// Delete the selected role
async function deleteRole() {
    if (confirm('Are you sure you want to delete this role?')) {
        try {
            const response = await fetch(`/api/roles/${currentRoleName}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error('Failed to delete role');
            }
            const apiResponse = await response.json();
            
            if (apiResponse.status === 'success') {
                await loadRoles();
                document.getElementById('roleDetails').style.display = 'none';
                await loadFreeUsers();
            } else {
                throw new Error(apiResponse.message);
            }
        } catch (error) {
            console.error('Error deleting role:', error);
            alert('Failed to delete role. Please try again.');
        }
    }
}

// Load and display users in the selected role
async function loadUsersInRole(roleName) {
    try {
        const response = await fetch(`/api/roles/${roleName}/users`);
        if (!response.ok) {
            throw new Error('Failed to fetch users in role');
        }
        const apiResponse = await response.json();
        
        if (apiResponse.status === 'success') {
            const users = apiResponse.data;
            
            const usersInRole = document.getElementById('usersInRole');
            const roleUsersList = document.getElementById('roleUsersList');
            usersInRole.innerHTML = '';
            roleUsersList.innerHTML = '';
            
            users.forEach(user => {
                const li = document.createElement('li');
                li.textContent = `${user[1]}`;
                usersInRole.appendChild(li);

                const option = document.createElement('option');
                option.value = user[0];
                option.textContent = user[1];
                roleUsersList.appendChild(option);
            });
        } else {
            throw new Error(apiResponse.message);
        }
    } catch (error) {
        console.error('Error loading users in role:', error);
        alert('Failed to load users in role. Please try again.');
    }
}

async function loadFreeUsers(role = null) {
    try {
        // Fetch users not in any role
        const freeUserResponse = await fetch('/api/users/free');
        if (!freeUserResponse.ok) {
            throw new Error('Failed to fetch free users (unassigned)');
        }
        const freeUserApiResponse = await freeUserResponse.json();
        
        if (freeUserApiResponse.status === 'success') {
            const freeUserListElement = document.getElementById('freeUserList');
            freeUserListElement.innerHTML = '';

            freeUserApiResponse.data.users.forEach(user => {
                user = JSON.parse(user);
                const li = document.createElement('li');
                li.textContent = `${user.email}`;
                freeUserListElement.appendChild(li);
            });
        } else {
            throw new Error(freeUserApiResponse.message);
        }

        // If a role is specified, fetch users not assigned to that role
        if (role) {
            const freeUsersListResponse = await fetch(`/api/users/free?role=${role}`);
            if (!freeUsersListResponse.ok) {
                throw new Error(`Failed to fetch free users for role ${role}`);
            }
            const freeUsersListApiResponse = await freeUsersListResponse.json();

            if (freeUsersListApiResponse.status === 'success') {
                const freeUsersListElement = document.getElementById('freeUsersList');
                freeUsersListElement.innerHTML = '';

                freeUsersListApiResponse.data.users.forEach(user => {
                    user = JSON.parse(user);
                    const option = document.createElement('option');
                    option.value = user.user_id;
                    option.textContent = user.email;
                    freeUsersListElement.appendChild(option);
                });
            } else {
                throw new Error(freeUsersListApiResponse.message);
            }
        }
    } catch (error) {
        console.error('Error loading free users:', error);
        alert('Failed to load free users. Please try again.');
    }
}


// Add a user to the current role
async function addUserToRole() {
    const userId = document.getElementById('freeUsersList').value;
    if (userId) {
        try {
            const response = await fetch(`/api/roles/${currentRoleName}/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ userId }),
            });
            if (!response.ok) {
                throw new Error('Failed to add user to role');
            }
            const apiResponse = await response.json();
            
            if (apiResponse.status === 'success') {
                await loadUsersInRole(currentRoleName);
                await loadFreeUsers(currentRoleName);
            } else {
                throw new Error(apiResponse.message);
            }
        } catch (error) {
            console.error('Error adding user to role:', error);
            alert('Failed to add user to role. Please try again.');
        }
    }
}

// Remove a user from the current role
async function removeUserFromRole() {
    const userId = document.getElementById('roleUsersList').value;
    if (userId) {
        try {
            const response = await fetch(`/api/roles/${currentRoleName}/users/${userId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error('Failed to remove user from role');
            }
            const apiResponse = await response.json();
            
            if (apiResponse.status === 'success') {
                await loadUsersInRole(currentRoleName);
                await loadFreeUsers(currentRoleName);
            } else {
                throw new Error(apiResponse.message);
            }
        } catch (error) {
            console.error('Error removing user from role:', error);
            alert('Failed to remove user from role. Please try again.');
        }
    }
}

// Initial load
loadRoles();
loadFreeUsers();
