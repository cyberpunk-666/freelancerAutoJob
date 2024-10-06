
function savePreferences() {
    const formData = new FormData(document.querySelector('form'));
    const preferences = Object.fromEntries(formData);

    fetch('/api/users/preferences', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences),
    })
        .then(response => response.json())
        .then(data => {
            showConnectionStatus('Preferences saved successfully', "success")
        })
        .catch((error) => {
            console.error('Error saving preferences:', error);
            showConnectionStatus(`Error fetching jobs: ${error.message}`, "error")
        });
}


document.addEventListener('DOMContentLoaded', function () {
    const saveBtn = document.getElementById('save-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', savePreferences);
    }
});
