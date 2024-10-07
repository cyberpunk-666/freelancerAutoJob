document.addEventListener('DOMContentLoaded', function () {
    const fetchJobsBtn = document.getElementById('fetch-jobs-btn');
    let jobsTable;
    let pollingInterval = null;
    let emptyResponseCount = 0;
    const MAX_EMPTY_RESPONSES = 20; // Stop after 20 empty responses (adjust as needed)
    const POLLING_INTERVAL = 1000; // 1 second interval


    function initializeDataTable() {
        jobsTable = $('#jobsTable').DataTable({
            "order": [[3, "desc"]],
            "paging": true,
            "lengthChange": true, // Allow users to change page length
            "pageLength": 50, // Set default page size to 10
            "lengthMenu": [10, 50, 100, 500], // Options for page size
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
            select: true,
            select: {
                style: 'multi',
                selector: 'td:first-child'
            },
            columnDefs: [
                {
                    orderable: false,
                    className: 'select-checkbox',
                    targets: 0
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
                },
                {
                    targets: 4, // Fit column
                    render: function (data, type, row) {
                        if (type === 'display') {
                            return data != null && data != "None" ? data.toString() : '';
                        }
                        return data;
                    }
                }
            ]
        });

        jobsTable.on('select deselect', function (e, dt, type, cell, originalEvent) {
            const selectedRows = jobsTable.rows({ selected: true }).data().length;
            // Update any UI elements that depend on selection
            updateSelectionDependentUI();
        });
        return jobsTable
    }

    // Function to update jobs in DataTable
    function updateJobsInDataTable(jobs) {
        for (let job of jobs) {
            // Find the row with matching job_id in the DataTable
            const rowIndex = jobsTable.row(`#${job.job_id}`).index();

            if (rowIndex !== undefined) {
                // Get the current row data
                let rowData = jobsTable.row(rowIndex).data();

                // Update specific columns
                rowData.status = job.status;
                rowData.job_fit = job.job_fit;

                // Update the row with the modified data
                jobsTable.row(rowIndex).data(rowData);
            }
        }

        // Redraw the table to reflect the changes
        jobsTable.draw();
    }


    function fetchJobs() {
        showLoadingIcon()
        try {
            fetch('/api/jobs/freelancer_jobs')
                .then(response => response.json())
                .then(apiResponse => {
                    if (apiResponse.status != 'success') {
                        showConnectionStatus(apiResponse.message, "error");
                        return;
                    }
                    const newJobs = apiResponse.data;
                    if (newJobs.length == 0) {
                        showConnectionStatus('No new job found', "success");
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
                    showConnectionStatus(`${newJobs.length} new jobs found`, "success");
                })
                .catch(error => {
                    console.error('Error fetching jobs:', error);
                    showConnectionStatus('Error fetching jobs', "error");
                });
        } catch (error) {
            console.error('Error fetching jobs:', error);
            showConnectionStatus('Error fetching jobs', "error");
        } finally {
            hideLoadingIcon();
        }
    }

    if (fetchJobsBtn) {
        fetchJobsBtn.addEventListener('click', fetchJobs);
    }
    $('#select-all-unprocessed').on('click', function () {
        // Deselect all rows first
        jobsTable.rows().deselect();

        jobsTable.rows(function (idx, data, node) {
            return !data[6] || Object.keys(data[6]).length === 0;
        }).every(function (rowIdx, tableLoop, rowLoop) {
            $(this.node()).find('input[type="checkbox"]').prop('checked', true);
            $(this.node()).addClass('selected');
        });
        jobsTable.draw();


        // Update the DataTable to reflect the changes
        //jobsTable.draw();

        // Update any UI elements that depend on selection
        updateSelectionDependentUI();
    });

    function getSelectedRows() {
        return jobsTable.rows({ selected: true }).data();
    }

    function updateSelectionDependentUI() {
        const selectedRows = jobsTable.rows({ selected: true }).count();

        // Enable/disable action buttons based on selection
        $('#process-selected, #delete-selected').toggleClass('disabled', selectedRows === 0);

        // Update the "Select All" checkbox state
        $('#select-all').prop('checked', selectedRows > 0 && selectedRows === jobsTable.rows().count());

        // Update the "Select All Unprocessed" checkbox state
        $('#select-all-unprocessed').prop('checked', selectedRows > 0 && selectedRows === jobsTable.rows().count());

    }

    // Handle "Select All" checkbox
    $('#select-all').on('change', function () {
        var isChecked = this.checked;
        jobsTable.rows().nodes().to$().find('input[type="checkbox"]').prop('checked', isChecked);
        jobsTable.rows().select(isChecked);
        // Update any UI elements that depend on selection
        updateSelectionDependentUI();
    });

    $('#process-selected').on('click', async function (e) {
        e.preventDefault();
        if ($(this).hasClass('disabled')) return;

        try {
            showLoadingIcon();
            const selectedRowsCount = jobsTable.rows({ selected: true }).count();
            jobsTable.rows({ selected: true }).every(async function (rowIdx, tableLoop, rowLoop) {
                var cellData = this.data();
                var checkboxHtml = cellData[0]; // Get the HTML string for the first cell
                var jobId = $(checkboxHtml).data('job-id'); // Extract the job ID from the data-job-id attribute
                await addTaskToQueue("process_job", { job_id: jobId });
            });
            showConnectionStatus(`${selectedRowsCount} jobs added to queue`, true);
            startPolling()
        } catch (error) {
            showConnectionStatus(`Error adding jobs to queue:`, false);
            console.error('Error adding jobs to queue:', error);
        } finally {
            hideLoadingIcon();
        }
    });

    // Delete selected jobs
    $('#delete-selected').on('click', function () {
        var selectedJobIds = [];
        jobsTable.rows({ selected: true }).every(function (rowIdx, tableLoop, rowLoop) {
            var jobId = this.data()['job_id'];
            selectedJobIds.push(jobId);
        });
        console.log('Deleting jobs:', selectedJobIds);
        // Add your deletion logic here
    });

    // start-polling
    $('#start-polling').on('click', function () {
        startPolling();
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
                console.log('Error adding task to queue:', error);
            });
    }

    let lastSyncDate = new Date().toISOString(); // Start polling from current time
    let pollingTimeout;

    async function pollEndpoints() {
        try {
            clearTimeout(pollingTimeout); // Clear any existing timeout

            const [queueResponse, jobUpdatesResponse] = await Promise.all([
                fetch('/api/task_queue/task_count'),
                fetch(`/api/jobs/poll-updates?last_sync=${lastSyncDate}`)
            ]);

            const queueResult = await queueResponse.json();
            const jobUpdatesResult = await jobUpdatesResponse.json();

            let totalTasks = 0;
            let statusMessage = "";

            if (queueResult.status === "success") {
                const messageCount = queueResult.data.visible_count;
                totalTasks += messageCount;
                updateTaskCount(messageCount);
            } else {
                console.error("Error fetching queue message count:", queueResult.message);
                statusMessage += "Queue error. ";
            }

            if (jobUpdatesResult.status === "success") {
                const updatedJobs = jobUpdatesResult.data;
                totalTasks += updatedJobs.length;
                if (updatedJobs.length > 0) {
                    updateJobsInDataTable(updatedJobs);
                    lastSyncDate = new Date().toISOString();
                    statusMessage += `${updatedJobs.length} jobs updated.`;
                }
            } else {
                console.error("Error fetching job updates:", jobUpdatesResult.message);
                statusMessage += "Job update error.";
            }

            // Reset empty response count if we received any updates
            if (totalTasks > 0) {
                emptyResponseCount = 0;
                if (statusMessage)
                    showConnectionStatus(statusMessage, "success", 0, 3000);
            } else {
                emptyResponseCount++;
                if (emptyResponseCount >= MAX_EMPTY_RESPONSES) {
                    stopPolling();
                    showConnectionStatus("Polling stopped: No recent updates", "info", 0, 3000);
                    return; // Exit the function to prevent scheduling next poll
                }
            }

            // Schedule the next poll only after processing is complete
            pollingTimeout = setTimeout(pollEndpoints, POLLING_INTERVAL);
        } catch (error) {
            console.error("Polling error:", error);
            showConnectionStatus("Connection error", "error", 0, 3000);
            stopPolling();
        }
    }

    function startPolling() {
        if (!pollingInterval) {
            emptyResponseCount = 0;
            showConnectionStatus("Polling...", "loading", 0);
            pollEndpoints(); // Start polling immediately
        }
    }
    function stopPolling() {
        if (pollingInterval) {
            clearInterval(pollingInterval);
            hideConnectionStatus()
            pollingInterval = null;
            emptyResponseCount = 0;
            stickyStatus = null
        }
    }




    // Initialize DataTable on document ready
    $(document).ready(function () {
        initializeDataTable();
        // Update any UI elements that depend on selection
        updateSelectionDependentUI();
        // Disable/enable action buttons based on selected rows
        const processSelected = document.getElementById('process-selected');
        const deleteSelected = document.getElementById('delete-selected');

        // Restore table state when page is loaded
        var savedState = localStorage.getItem('DataTables_jobsTable');
        if (savedState) {
            jobsTable.state.load();
        }
    });
});
