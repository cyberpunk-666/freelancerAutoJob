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

function showConnectionStatus(message, is_success) {
    const connectionStatus = document.getElementById('connection-status');
    connectionStatus.textContent = message;
    connectionStatus.style.display = 'block';
    if (is_success) {
        connectionStatus.className = 'alert alert-success';
    } else {
        connectionStatus.className = 'alert alert-danger';
    }

    // Hide the message after 3 seconds (3000 milliseconds)
    setTimeout(() => {
        connectionStatus.style.display = 'none';
    }, 3000);
}

function showLoadingIcon() {
    document.getElementById('loading-icon').style.display = 'flex';
}

function hideLoadingIcon() {
    document.getElementById('loading-icon').style.display = 'none';
}
