document.addEventListener('DOMContentLoaded', function () {
    // Logic for ajax Select
    const ajaxSelects = document.querySelectorAll('select[data-url]');
    ajaxSelects.forEach(select => {
        const url = select.dataset.url;
        fetch(url)
            .then(response => response.json())
            .then(data => {
                select.innerHTML = ''; // Clear loading option
                data.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item;
                    option.textContent = item;
                    select.appendChild(option);
                });
                select.value = select.dataset.selected;
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                select.innerHTML = '<option value="">Error loading data</option>';
            });
    });
});


let stickyStatus = null

function showConnectionStatus(message, newStatus, task_count = null, timeout = null) {
    const connectionStatus = document.getElementById('connection-status');
    const loadingIconContainer = document.getElementById('loading-icon-container');
    const loadingIcon = document.getElementById('loading-icon-status');
    const taskCountSpan = document.getElementById('task-count');
    const messageSpan = document.getElementById('status-message');

    // Function to update the status bar content
    function updateStatusBar(msg, status, task_count) {
        // Update the task count
        taskCountSpan.textContent = task_count;

        // Update the message
        messageSpan.textContent = msg;

        // Set the appropriate class based on the status
        connectionStatus.className = 'alert';
        if (status === 'loading') {
            timeout = 0;
            connectionStatus.classList.add('alert-info');
            loadingIconContainer.style.display = 'block';
        } else if (status === 'success') {
            timeout = timeout || 3000;
            connectionStatus.classList.add('alert-success');
            loadingIconContainer.style.display = 'block';
        } else if (status === 'error') {
            timeout = timeout || 3000;
            connectionStatus.classList.add('alert-danger');
            loadingIconContainer.style.display = 'none';
        }

        // Show the connection status only if there are tasks
        if (task_count > 0) {
            taskCountSpan.style.display = 'block';
            connectionStatus.style.display = 'flex';
        } else {
            taskCountSpan.style.display = 'none';
            connectionStatus.style.display = 'none';
        }
    }

    // If timeout is 0, update the sticky status
    if (!timeout) {
        task_count = task_count || 0;
        stickyStatus = { message, newStatus, task_count };
    } else if (stickyStatus) {
        task_count = stickyStatus.task_count;
    } else {
        task_count = 0;
    }
    updateStatusBar(message, newStatus, task_count);

    // If a timeout is specified, show the message temporarily
    if (timeout > 0) {
        setTimeout(() => {
            // If there's a sticky status, show it after the timeout
            if (stickyStatus) {
                updateStatusBar(stickyStatus.message, stickyStatus.newStatus, stickyStatus.task_count);
            } else {
                connectionStatus.style.display = 'none';
            }
        }, timeout);
    }
}

function updateTaskCount(count) {
    const taskCountSpan = document.querySelector('#connection-status .task-count');
    if (taskCountSpan) {
        taskCountSpan.textContent = String(count);
    }

    // Update the sticky status if it exists
    if (stickyStatus) {
        stickyStatus.task_count = count;

        if (count > 0) {
            // Show the status if there are tasks, regardless of its current visibility
            showConnectionStatus(stickyStatus.message, stickyStatus.newStatus, count);
        } else {
            // Hide the status if there are no tasks
            document.getElementById('connection-status').style.display = 'none';
        }
    }
}


function updateTaskCount(count) {
    const taskCountSpan = document.querySelector('#connection-status .task-count');
    if (taskCountSpan) {
        taskCountSpan.textContent = String(count);
    }

    // Update the sticky status if it exists
    if (stickyStatus) {
        stickyStatus.task_count = count;

        if (count > 0) {
            // Show the status if there are tasks, regardless of its current visibility
            showConnectionStatus(stickyStatus.message, stickyStatus.newStatus, count);
        } else {
            // Hide the status if there are no tasks
            document.getElementById('connection-status').style.display = 'none';
        }
    }
}



function hideConnectionStatus() {
    const connectionStatus = document.getElementById('connection-status');
    const taskCount = document.getElementById('task-count');
    const loadingIcon = document.getElementById('loading-icon');

    connectionStatus.style.display = 'none';
    taskCount.style.display = 'none';
    loadingIcon.style.display = 'none';
}

function showLoadingIcon() {
    const loadingIcon = document.getElementById('loading-icon');
    loadingIcon.style.display = 'flex';
    // Force a reflow
    void loadingIcon.offsetHeight;
}

function hideLoadingIcon() {
    document.getElementById('loading-icon').style.display = 'none';
}

