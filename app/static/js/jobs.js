document.addEventListener('DOMContentLoaded', function () {
    const fetchJobsBtn = document.getElementById('fetch-jobs-btn');
    let jobsTable;

    function initializeDataTable() {
        $('#jobsTable').DataTable({
            "order": [[3, "desc"]],
            "paging": true,
            "lengthChange": false,
            "autoWidth": false,
            "dom": 't<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
            columnDefs: [
                {
                    targets: 0, // Checkbox column
                    orderable: false
                },
                {
                    targets: 2, // Budget column
                    type: 'num',
                    render: function (data, type, row) {
                        if (type === 'sort') {
                            var range = data.split('-');
                            return parseFloat(range[0]) || 0;
                        }
                        return data;
                    }
                }
            ]
        });
    }

    function fetchJobs() {
        fetch('/api/jobs/freelancer_jobs')
            .then(response => response.json())
            .then(apiResponse => {
                if (apiResponse.status != 'success') {
                    showConnectionStatus(apiResponse.message, false);
                    return;
                }
                const newJobs = apiResponse.data;
                if (newJobs.length == 0) {
                    showConnectionStatus('No new job found', true);
                    return;
                }
                newJobs.forEach(job => {
                    jobsTable.row.add({
                        job_id: job.job_id,
                        job_title: job.title,
                        budget: job.budget,
                        fit: job.job_fit,
                        created_at: job.email_date,
                        status: job.status
                    });
                });

                // Redraw the table
                jobsTable.draw();
                showConnectionStatus(`${newJobs.length} new jobs found`, true);
            })
            .catch(error => {
                console.error('Error fetching jobs:', error);
                showConnectionStatus('Error fetching jobs', false);
            });
    }

    if (fetchJobsBtn) {
        fetchJobsBtn.addEventListener('click', fetchJobs);
    }

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
        selectAll.addEventListener('change', function () {
            jobCheckboxes.forEach(checkbox => checkbox.checked = this.checked);
            updateActionMenu();
        });
    }

    jobCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateActionMenu);
    });

    if (processSelected) {
        processSelected.addEventListener('click', function (e) {
            e.preventDefault();
            const selectedJobs = Array.from(document.querySelectorAll('.job-checkbox:checked'))
                .map(checkbox => checkbox.dataset.jobId);
            for (let jobId of selectedJobs) {
                addTaskToQueue("process_job", { job_id: jobId });
                console.log(jobId);
            }
            console.log('Processing jobs:', selectedJobs);
        });
    }

    if (deleteSelected) {
        deleteSelected.addEventListener('click', function (e) {
            e.preventDefault();
            const selectedJobs = Array.from(document.querySelectorAll('.job-checkbox:checked'))
                .map(checkbox => checkbox.dataset.jobId);
            console.log('Deleting jobs:', selectedJobs);
            // Add your logic to delete the selected jobs
        });
    }

    // Initialize DataTable on document ready
    $(document).ready(function () {
        initializeDataTable();
        var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'))
        var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
            return new bootstrap.Dropdown(dropdownToggleEl)
        })
    });
});
