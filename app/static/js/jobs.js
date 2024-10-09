document.addEventListener('DOMContentLoaded', function () {
    const fetchJobsBtn = document.getElementById('fetch-jobs-btn');
    let jobsTable;
    let pollingTimeout = null;
    let emptyResponseCount = 0;
    const MAX_EMPTY_RESPONSES = 20; // Stop after 20 empty responses (adjust as needed)
    const POLLING_INTERVAL = 1000; // 1 second interval

    let currentPage = 0; // Track the current page for job fetching
    let isLoading = false; // Prevent multiple simultaneous requests
    const PAGE_SIZE = 50;  // Adjust based on desired number of jobs per load

    function initializeDataTable() {
        jobsTable = $('#jobsTable').DataTable({
            "processing": true,  // Show processing indicator
            "serverSide": true,   // Enable server-side processing
            "ajax": {
                "url": "/api/jobs/jobs"
            },
            scrollResize: false,
            scrollY: 300,
            scrollCollapse: true,
            paging: true,
            deferRender: false,
            scroller: true,
            ordering: true,
            searching: true,
            // "order": [[3, "desc"]],  // Default sorting by 'created_at' column
            "autoWidth": false,
            "stateSave": true,  // Save table state (sort, filters, etc.)
            "stateDuration": -1,  // Save indefinitely
            "stateSaveCallback": function (settings, data) {
                sessionStorage.setItem('DataTables_' + settings.sInstance, JSON.stringify(data));
            },
            "stateLoadCallback": function (settings) {
                return JSON.parse(sessionStorage.getItem('DataTables_' + settings.sInstance));
            },
            select: {
                style: 'multi',
                selector: 'td:first-child'
            },
            rowId: "job_id",  // Use 'job_id' as the row ID
            "columns": [
                {
                    "searchable": false,
                    "orderable": false,
                    "data": "job_id",
                    "visible": false  // Make this column invisible
                },
                {
                    "searchable": true,
                    "orderable": true,
                    "data": "job_title",  // Job title from the API
                    "title": "Job Title",  // Table header
                    "render": function (data, type, row) {
                        // truncate the job title if it's too long
                        if (data) {
                            data = data.length > 50 ? data.substring(0, 50) + '...' : data;
                        } else {
                            data = '';
                        }
                        if (type === 'display') {
                            // Create a link for the job title
                            return `<a href="/jobs/${row.job_id}" target="_blank">${data}</a>`;
                        }
                        return data;
                    }
                },
                {
                    "searchable": false,
                    "orderable": true,
                    "data": "budget",  // Budget from the API
                    "title": "Budget",  // Table header
                    "render": function (data, type, row) {
                        // Render budget, handle if it's empty
                        return data ? data : 'N/A';
                    }
                },
                {
                    "searchable": false,
                    "orderable": true,
                    "data": "last_updated_at",  // Last updated at date from the API
                    "title": "Last Updated",
                    "render": function (data, type, row) {
                        // Convert to readable date
                        return new Date(data).toLocaleString();
                    }
                },
                {
                    "searchable": false,
                    "orderable": true,
                    "data": "job_fit",  // Job fit from the API
                    "title": "Job Fit",
                    "render": function (data, type, row) {
                        if (type === 'display' || type === 'filter') {
                            if (data === 0 || data === '0') {
                                return '0';
                            } else if (data === null || data === '' || data === undefined) {
                                return 'N/A';
                            }
                            return data;
                        }
                        return data;
                    }
                },
                {
                    "searchable": false,
                    "orderable": true,
                    "data": "status",  // Job status from the API
                    "title": "Status",
                    "render": function (data, type, row) {
                        // Render status, handle if it's empty
                        return data ? data : 'N/A';
                    }
                }
            ]
        });

        return jobsTable
    }



    // Fetch jobs with pagination (for infinite scrolling)
    function fetchJobs(page) {
        if (isLoading) return;
        isLoading = true;
        showLoadingIcon();

        fetch(`/api/jobs/freelancer_jobs?page=${page}&page_size=${PAGE_SIZE}`)
            .then(response => response.json())
            .then(apiResponse => {
                if (apiResponse.status !== 'success') {
                    showConnectionStatus(apiResponse.message, "error");
                    return;
                }
                const newJobs = apiResponse.data;
                if (newJobs.length === 0) {
                    showConnectionStatus('No more jobs to load', "info");
                    stopPolling(); // If needed
                    return;
                }

                // Append jobs to the DataTable
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

                // Redraw the table to show the new jobs
                jobsTable.draw(false);  // 'false' keeps the current paging position
                showConnectionStatus(`${newJobs.length} new jobs loaded`, "success");
                isLoading = false;
            })
            .catch(error => {
                console.error('Error fetching jobs:', error);
                showConnectionStatus('Error fetching jobs', "error");
                isLoading = false;
            })
            .finally(() => {
                hideLoadingIcon();
            });
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
    let isPolling = false
    const pollButton = document.getElementById('start-polling');
    $('#start-polling').on('click', function () {
        if (isPolling) {
            // Stop polling
            stopPolling();
            pollButton.textContent = 'Start Polling';
            pollButton.classList.remove('btn-danger');
            pollButton.classList.add('btn-success');
            isPolling = false;
        } else {
            // Start polling
            startPolling();
            pollButton.textContent = 'Stop Polling';
            pollButton.classList.remove('btn-success');
            pollButton.classList.add('btn-danger');
            isPolling = true;
        }
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
        if (!pollingTimeout) {
            emptyResponseCount = 0;
            showConnectionStatus("Polling...", "loading", 0);
            pollEndpoints(); // Start polling immediately
        }
    }
    function stopPolling() {
        if (pollingTimeout) {
            clearInterval(pollingTimeout);
            hideConnectionStatus()
            pollingTimeout = null;
            emptyResponseCount = 0;
            stickyStatus = null
        }
    }
    initializeDataTable()
    // Update any UI elements that depend on selection
    updateSelectionDependentUI();

    // Restore table state when page is loaded
    var savedState = localStorage.getItem('DataTables_jobsTable');
    if (savedState) {
        jobsTable.state.load();
    }



});
