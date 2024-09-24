const fetchJobsBtn = document.getElementById('fetch-jobs-btn');
const cancelFetchBtn = document.getElementById('cancel-fetch-btn');
const connectionStatus = document.getElementById('connection-status');
const errorMessage = document.getElementById('error-message');
const jobsTable = document.getElementById('jobsTable').getElementsByTagName('tbody')[0];
let pollingTimer = null;

window.onload = async function() {
    try {
        const has_task = await checkUserQueue();
        console.log('has_task:', has_task);
        if (has_task === true) {
            console.log("Start Fetching Jobs");
            startFetchingJobs();
        } else if (has_task === false) {
            console.log("No tasks in queue");
        } else {
            console.log("Error checking user queue");
        }
    } catch (error) {
        console.error('Error in window.onload:', error);
    }
};


fetchJobsBtn.addEventListener('click', fetchJobsBtnClicked);
cancelFetchBtn.addEventListener('click', stopFetchingJobs);

async function checkUserQueue() {
    try {
        const response = await fetch('/api/task_queue/has_task');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        console.log('Server response:', data);

        if (data.status === 'success') {
            if (data.data && data.data.message_id) {
                // A task was found for the user
                return true;
            } else {
                // No tasks found for the user
                return false;
            }
        } else {
            console.error('Error checking user queue:', data.message);
            return null;
        }
    } catch (error) {
        console.error('Error checking user queue:', error);
        return null;
    }
}


async function startFetchingJobs() {
    connectionStatus.textContent = 'Fetching jobs...';
    connectionStatus.className = 'alert alert-info';
    connectionStatus.style.display = 'block';
    fetchJobsBtn.style.display = 'none';
    cancelFetchBtn.style.display = 'inline-block';

    pollingTimer = setInterval(fetchJobs, 10000); // Poll every 20 seconds
}

async function fetchJobsBtnClicked() {
    has_task = await checkUserQueue();
    if(has_task){
        connectionStatus.textContent = 'There is already task in the queue.';
        connectionStatus.className = 'alert alert-warning';
        return;   
    }
    stopFetchingJobs();
    addFetchEmailsTask();        
    startFetchingJobs();
}

function stopFetchingJobs() {
    clearInterval(pollingTimer);
    pollingTimer = null;

    connectionStatus.textContent = 'Job fetching stopped.';
    connectionStatus.className = 'alert alert-warning';
    cancelFetchBtn.style.display = 'none';
    fetchJobsBtn.style.display = 'inline-block';
}

async function fetchJobs() {
    try {
        const response = await fetch('/api/jobs/');
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const apiResponse = await response.json();

        // Check if the response status is "success"
        if (apiResponse.status === "success") {
            const jobs = apiResponse.data;
            jobs.forEach(addJobToTable);

            if (jobs.length === 0) {
                connectionStatus.textContent = 'No new jobs available.';
                connectionStatus.className = 'alert alert-info';
            }
        } else {
            // If status is "failure", show the error message
            throw new Error(apiResponse.message || 'Failed to retrieve jobs.');
        }
    } catch (error) {
        console.error('Error fetching jobs:', error);

        // Stop fetching jobs when an error occurs
        stopFetchingJobs();

        // Update the UI to reflect the error
        connectionStatus.textContent = `Error fetching jobs: ${error.message}`;
        connectionStatus.className = 'alert alert-danger';
    }
}


function addJobToTable(job) {
    const row = jobsTable.insertRow();
    row.innerHTML = `
        <td><a href="/jobs/${job.id}">${job.title}</a></td>
        <td>${job.budget}</td>
        <td>${job.email_date}</td>
        <td class="job-status" data-status="${job.status}">${job.status}</td>
    `;
    updateJobStatus(row.querySelector('.job-status'));
}

function updateJobStatus(statusElement) {
    const status = statusElement.dataset.status;
    switch (status.toLowerCase()) {
        case 'new':
            statusElement.style.color = 'blue';
            break;
        case 'in progress':
            statusElement.style.color = 'orange';
            break;
        case 'completed':
            statusElement.style.color = 'green';
            break;
        case 'cancelled':
            statusElement.style.color = 'red';
            break;
        default:
            statusElement.style.color = 'black';
    }
}


async function addFetchEmailsTask() {
    const taskData = {
        num_messages_to_read: 10
    };

    try {
        const response = await fetch('/api/task_queue/add_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                type: "fetch_email_jobs",
                task_data: taskData
            }),
        });

        if (!response.ok) {
            throw new Error('Network response was not ok');
        }

        const result = await response.json();
        console.log('Task added successfully:', result);
        return result;
    } catch (error) {
        console.error('Error adding task:', error);
        throw error;
    }
}


// Stop listening when the page is about to be unloaded
window.addEventListener('beforeunload', stopFetchingJobs);
