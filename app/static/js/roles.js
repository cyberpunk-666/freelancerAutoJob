let currentRoleId = null;

// Load and display all roles
async function loadRoles() {
    try {
        const response = await fetch('/api/roles');
        if (!response.ok) {
            throw new Error('Failed to fetch roles');
        }
        const roles = await response.json();
        
        const roleList = document.getElementById('roleList');
        roleList.innerHTML = '';
        roles.forEach(role => {
            const li = document.createElement('li');
            li.textContent = role.name;
            li.onclick = () => selectRole(role.id);
            roleList.appendChild(li);
        });
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
            await loadRoles();
            document.getElementById('newRoleName').value = '';
        } catch (error) {
            console.error('Error creating role:', error);
            alert('Failed to create role. Please try again.');
        }
    }
}

// Select and display a role
async function selectRole(roleId) {
    currentRoleId = roleId;
    try {
        const response = await fetch(`/api/roles/${roleId}`);
        if (!response.ok) {
            throw new Error('Failed to fetch role details');
        }
        const role = await response.json();
        document.getElementById('currentRoleName').textContent = role.name;
        document.getElementById('roleDetails').style.display = 'block';
        await loadUsersInRole(roleId);
        await loadFreeUsers();
    } catch (error) {
        console.error('Error selecting role:', error);
        alert('Failed to load role details. Please try again.');
    }
}

// Edit the selected role
async function editRole() {
    const newName = prompt('Enter new role name', document.getElementById('currentRoleName').textContent);
    if (newName && newName !== document.getElementById('currentRoleName').textContent) {
        try {
            const response = await fetch(`/api/roles/${currentRoleId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: newName }),
            });
            if (!response.ok) {
                throw new Error('Failed to update role');
            }
            await loadRoles();
            document.getElementById('currentRoleName').textContent = newName;
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
            const response = await fetch(`/api/roles/${currentRoleId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error('Failed to delete role');
            }
            await loadRoles();
            document.getElementById('roleDetails').style.display = 'none';
            await loadFreeUsers();
        } catch (error) {
            console.error('Error deleting role:', error);
            alert('Failed to delete role. Please try again.');
        }
    }
}

// Load and display users in the selected role
async function loadUsersInRole(roleId) {
    try {
        const response = await fetch(`/api/roles/${roleId}/users`);
        if (!response.ok) {
            throw new Error('Failed to fetch users in role');
        }
        const users = await response.json();
        
        const usersInRole = document.getElementById('usersInRole');
        const roleUsersList = document.getElementById('roleUsersList');
        usersInRole.innerHTML = '';
        roleUsersList.innerHTML = '';
        
        users.forEach(user => {
            const li = document.createElement('li');
            li.textContent = `${user.name} (${user.email})`;
            usersInRole.appendChild(li);

            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.name;
            roleUsersList.appendChild(option);
        });
    } catch (error) {
        console.error('Error loading users in role:', error);
        alert('Failed to load users in role. Please try again.');
    }
}

// Load and display users not assigned to any role
async function loadFreeUsers() {
    try {
        const response = await fetch('/api/users/free');
        if (!response.ok) {
            throw new Error('Failed to fetch free users');
        }
        const freeUsers = await response.json();
        
        const freeUserList = document.getElementById('freeUserList');
        const freeUsersList = document.getElementById('freeUsersList');
        freeUserList.innerHTML = '';
        freeUsersList.innerHTML = '';
        
        freeUsers.forEach(user => {
            const li = document.createElement('li');
            li.textContent = `${user.name} (${user.email})`;
            freeUserList.appendChild(li);

            const option = document.createElement('option');
            option.value = user.id;
            option.textContent = user.name;
            freeUsersList.appendChild(option);
        });
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
            const response = await fetch(`/api/roles/${currentRoleId}/users`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ userId }),
            });
            if (!response.ok) {
                throw new Error('Failed to add user to role');
            }
            await loadUsersInRole(currentRoleId);
            await loadFreeUsers();
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
            const response = await fetch(`/api/roles/${currentRoleId}/users/${userId}`, {
                method: 'DELETE',
            });
            if (!response.ok) {
                throw new Error('Failed to remove user from role');
            }
            await loadUsersInRole(currentRoleId);
            await loadFreeUsers();
        } catch (error) {
            console.error('Error removing user from role:', error);
            alert('Failed to remove user from role. Please try again.');
        }
    }
}

// Initial load
loadRoles();
loadFreeUsers();
