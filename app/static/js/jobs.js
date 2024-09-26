document.addEventListener('DOMContentLoaded', function() {
    // Fetch jobs related elements
    const fetchJobsBtn = document.getElementById('fetch-jobs-btn');
    const connectionStatus = document.getElementById('connection-status');
    const errorMessage = document.getElementById('error-message');

    // Fetch jobs from the API
    async function fetchJobs() {
        try {
            const response = await fetch('/api/jobs/freelancer_jobs');
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }

            const apiResponse = await response.json();

            if (apiResponse.status === "success") {
                const jobs = apiResponse.data;
                connectionStatus.style.display = 'block';

                if (jobs.jobs_fetched === 0) {
                    connectionStatus.textContent = 'No new jobs available.';
                    connectionStatus.className = 'alert alert-info';
                } else {
                    connectionStatus.textContent = 'Jobs fetched successfully. Refreshing page...';
                    connectionStatus.className = 'alert alert-success';
                    setTimeout(() => window.location.reload(), 1500);
                }
            } else {
                throw new Error(apiResponse.message || 'Failed to retrieve jobs.');
            }
        } catch (error) {
            console.error('Error fetching jobs:', error);
            connectionStatus.textContent = `Error fetching jobs: ${error.message}`;
            connectionStatus.className = 'alert alert-danger';
            connectionStatus.style.display = 'block';
        }
    }

    if (fetchJobsBtn) {
        fetchJobsBtn.addEventListener('click', fetchJobs);
    }

    $(document).ready(function() {
        $('table').DataTable({
            "order": [], // Initialize without default ordering
            "columnDefs": [{ "orderable": false, "targets": 0 }] // Disable sorting for the first column (checkbox)
        });

        // Checkbox management
        const selectAll = document.getElementById('select-all');
        const jobCheckboxes = document.querySelectorAll('.job-checkbox');
        const actionMenu = document.getElementById('action-menu');
        const actionButton = actionMenu.querySelector('button');
        const processSelected = document.getElementById('process-selected');
        const deleteSelected = document.getElementById('delete-selected');

        function updateActionMenu() {
            const checkedBoxes = document.querySelectorAll('.job-checkbox:checked');
            actionButton.disabled = checkedBoxes.length === 0;
        }

        if (selectAll) {
            selectAll.addEventListener('change', function() {
                jobCheckboxes.forEach(checkbox => checkbox.checked = this.checked);
                updateActionMenu();
            });
        }

        jobCheckboxes.forEach(checkbox => {
            checkbox.addEventListener('change', updateActionMenu);
        });

        if (processSelected) {
            processSelected.addEventListener('click', function(e) {
                e.preventDefault();
                const selectedJobs = Array.from(document.querySelectorAll('.job-checkbox:checked'))
                    .map(checkbox => checkbox.dataset.jobId);
                console.log('Processing jobs:', selectedJobs);
                // Add your logic to process the selected jobs
            });
        }

        if (deleteSelected) {
            deleteSelected.addEventListener('click', function(e) {
                e.preventDefault();
                const selectedJobs = Array.from(document.querySelectorAll('.job-checkbox:checked'))
                    .map(checkbox => checkbox.dataset.jobId);
                console.log('Deleting jobs:', selectedJobs);
                // Add your logic to delete the selected jobs
            });
        }
    });
});
