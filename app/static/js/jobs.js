function fetchJobs() {
    fetch('/jobs/fetch_jobs', { method: 'POST' })
        .then(response => response.json())
        .then(jobs => {
            const tbody = document.querySelector('#jobsTable tbody');
            tbody.innerHTML = '';
            jobs.forEach(job => {
                const row = `<tr>
                    <td><input type="checkbox" class="job-checkbox" value="${job.id}"></td>
                    <td>${job.title}</td>
                    <td>${job.description}</td>
                    <td><button onclick="processJob(${job.id})">Process</button></td>
                </tr>`;
                tbody.innerHTML += row;
            });
        });
}

function processJob(jobId) {
    fetch(`/jobs/process_job/${jobId}`, { method: 'POST' })
        .then(response => response.json())
        .then(result => alert(`Job ${jobId} processed: ${JSON.stringify(result)}`));
}

function queueSelectedJobs() {
    const selectedJobs = Array.from(document.querySelectorAll('.job-checkbox:checked')).map(cb => cb.value);
    fetch('/jobs/queue_jobs', { method: 'POST', body: JSON.stringify({ job_ids: selectedJobs }), headers: { 'Content-Type': 'application/json' } })
        .then(response => response.json())
        .then(result => alert(result.message));
}