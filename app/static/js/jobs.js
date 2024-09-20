async function addFetchEmailsTask(userId) {
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
                user_id: userId,
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
