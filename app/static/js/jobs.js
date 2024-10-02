document.addEventListener('DOMContentLoaded', function () {
    const fetchJobsBtn = document.getElementById('fetch-jobs-btn');
    let jobsTable;

    function initializeDataTable() {
        jobsTable = $('#jobsTable').DataTable({
            "order": [[3, "desc"]],
            "paging": true,
            "lengthChange": false,
            "autoWidth": false,
            "dom": 't<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>',
            "stateSave": true,
            "stateDuration": -1,  // -1 means the state will be saved indefinitely
            "stateSaveCallback": function (settings, data) {
                sessionStorage.setItem('DataTables_' + settings.sInstance, JSON.stringify(data));
            },
            "stateLoadCallback": function (settings) {
                return JSON.parse(sessionStorage.getItem('DataTables_' + settings.sInstance));
            },
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
        showLoadingIcon()
        try {
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
        } catch (error) {
            console.error('Error fetching jobs:', error);
            showConnectionStatus('Error fetching jobs', false);
        } finally {
            hideLoadingIcon();
        }
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

    function addTaskToQueue(taskType, taskData) {
        const payload = {
            type: taskType,
            task_data: taskData
        };

        return fetch('/api/task_queue/add_task', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(payload)
        })
            .then(response => {
                return response.json();
            })
            .then(data => {
                return data;
            })
            .catch(error => {
                showConnectionStatus(`Error adding task to queue:`, false);
                console.log('Error adding task to queue:', error);
            });
    }

    // Update the processSelected event listener
    if (processSelected) {
        processSelected.addEventListener('click', async function (e) {
            e.preventDefault();
            const selectedJobs = Array.from(document.querySelectorAll('.job-checkbox:checked'))
                .map(checkbox => checkbox.dataset.jobId);
            showLoadingIcon()

            try {
                for (let job of selectedJobs) {
                    await addTaskToQueue("process_job", { job_id: job })
                }
                showConnectionStatus(`${selectedJobs.length} jobs added to queue`, true);
            } catch (error) {
                showConnectionStatus(`Error adding jobs to queue:`, false);
                console.error('Error adding jobs to queue:', error);
            } finally {
                hideLoadingIcon();
            }

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
        jobsTable = initializeDataTable();

        // Restore table state when page is loaded
        var savedState = localStorage.getItem('DataTables_jobsTable');
        if (savedState) {
            jobsTable.state.load();
        }

        var dropdownElementList = [].slice.call(document.querySelectorAll('.dropdown-toggle'))
        var dropdownList = dropdownElementList.map(function (dropdownToggleEl) {
            return new bootstrap.Dropdown(dropdownToggleEl)
        })
    });
});
