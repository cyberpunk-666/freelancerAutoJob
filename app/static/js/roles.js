// Sample data for roles and users
let roles = ['Admin', 'Editor', 'Viewer'];
let users = ['john@example.com', 'jane@example.com', 'bob@example.com'];

// Populate role list
const roleList = document.getElementById('roleList');
roles.forEach(role => {
    const li = document.createElement('li');
    li.textContent = role;
    li.addEventListener('click', () => editRole(role));
    roleList.appendChild(li);
});

// Populate user list
const userList = document.getElementById('userList');
users.forEach(user => {
    const option = document.createElement('option');
    option.value = user;
    option.textContent = user;
    userList.appendChild(option);
});

// Populate role select
const roleSelect = document.getElementById('roleSelect');
roles.forEach(role => {
    const option = document.createElement('option');
    option.value = role;
    option.textContent = role;
    roleSelect.appendChild(option);
});

// Create a new role
function createRole() {
    const newRoleName = document.getElementById('newRoleName').value.trim();
    if (newRoleName) {
        roles.push(newRoleName);
        const li = document.createElement('li');
        li.textContent = newRoleName;
        li.addEventListener('click', () => editRole(newRoleName));
        roleList.appendChild(li);

        const option = document.createElement('option');
        option.value = newRoleName;
        option.textContent = newRoleName;
        roleSelect.appendChild(option);

        document.getElementById('newRoleName').value = '';
    }
}

// Edit a role
function editRole(role) {
    const newRoleName = prompt('Enter new role name', role);
    if (newRoleName && newRoleName !== role) {
        const index = roles.indexOf(role);
        roles[index] = newRoleName;
        roleSelect.querySelectorAll('option')[index + 1].textContent = newRoleName;
    }
}

// Assign a role to a user
function assignRole() {
    const user = userList.value;
    const role = roleSelect.value;
    // Here, you can call a function or make an API request to associate the selected role with the selected user
    console.log(`Assigning role "${role}" to user "${user}"`);
}
