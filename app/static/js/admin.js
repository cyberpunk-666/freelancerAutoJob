// Fetch users and roles from the server
fetch('/admin/data')
    .then(response => response.json())
    .then(data => {
        populateUserList(data.users);
        populateRoleList(data.roles);
    })
    .catch(error => console.error('Error fetching data:', error));

// Populate user list
function populateUserList(users) {
    const userList = document.getElementById('userList');
    users.forEach(user => {
        const li = document.createElement('li');
        li.textContent = user;
        userList.appendChild(li);
    });
}

// Populate role list
function populateRoleList(roles) {
    const roleList = document.getElementById('roleList');
    roles.forEach(role => {
        const li = document.createElement('li');
        li.textContent = role;
        roleList.appendChild(li);
    });
}
