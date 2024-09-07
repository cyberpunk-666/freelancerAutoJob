document.addEventListener("DOMContentLoaded", function () {
    const fetchJobsBtn = document.getElementById("fetch-jobs-btn");
    const processJobsBtn = document.getElementById("process-jobs-btn");
    const jobsModal = document.getElementById("jobs-modal");
    const jobsList = document.getElementById("jobs-list");

    // Fetch jobs and show modal
    fetchJobsBtn.addEventListener("click", function () {
        // Changed to use POST method
        fetch("/jobs/fetch_jobs", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            }
        })
        .then(response => response.json())
        .then(data => {
            // Clear the current job list
            jobsList.innerHTML = '';

            // Add fetched jobs to the modal list
            data.forEach(job => {
                const listItem = document.createElement('li');
                listItem.innerHTML = `
                    <input type="checkbox" class="job-checkbox" data-job-id="${job.job_id}">
                    ${job.job_title}
                `;
                jobsList.appendChild(listItem);
            });

            // Show the modal
            $('#jobs-modal').modal('show');
        });
    });

    // Process selected jobs
    processJobsBtn.addEventListener("click", function () {
        const selectedJobs = [];
        document.querySelectorAll(".job-checkbox:checked").forEach(checkbox => {
            selectedJobs.push(checkbox.getAttribute('data-job-id'));
        });

        if (selectedJobs.length === 0) {
            alert("Please select at least one job to process.");
            return;
        }

        // Send the selected jobs to the server to process
        fetch("/jobs/process", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ selected_jobs: selectedJobs })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Update the UI with the new jobs (add them to the job list with gray color)
                data.processed_jobs.forEach(job => {
                    const jobElement = document.createElement('div');
                    jobElement.classList.add('job-item', 'pending-job');
                    jobElement.innerHTML = `
                        <h3>${job.job_title}</h3>
                        <p>Status: ${job.status}</p>
                    `;
                    document.querySelector('.container').appendChild(jobElement);
                });

                // Close the modal
                $('#jobs-modal').modal('hide');
            } else {
                alert("Error: " + data.message);
            }
        });
    });
});
