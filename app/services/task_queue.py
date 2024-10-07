import boto3
import logging
import json
from botocore.exceptions import ClientError
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.models.api_response import APIResponse


class TaskQueue:
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskQueue, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            TaskQueue._initialized = True
            self.is_processing = False
            self.callbacks = {}
            region_name = os.getenv('AWS_SQS_REGION')
            self.sqs_client = boto3.client('sqs', region_name=region_name)
            self.base_queue_url = os.getenv('AWS_SQS_QUEUE_URL')
            num_workers = os.getenv('TASK_QUEUE_NUM_WORKERS')
            self.num_workers = int(num_workers) if num_workers else 1
            self.executor = ThreadPoolExecutor(max_workers=self.num_workers)

    def register_callback(self, task_type, callback):
        """Register a callback function for a specific task type."""
        self.callbacks[task_type] = callback

    def get_user_queue_url(self, user_id, is_fifo=True) -> str:
        """Retrieve the queue URL for a user, creating the queue only if it doesn't exist."""
        # Sanitize the user_id to comply with SQS FIFO naming rules
        sanitized_user_id = ''.join(e for e in str(user_id) if e.isalnum() or e in ['-', '_'])

        # Construct the queue name
        queue_name = f"user_{sanitized_user_id}_queue"
        if is_fifo:
            queue_name += ".fifo"

        try:
            # Check if the queue already exists by trying to get its URL
            response = self.sqs_client.get_queue_url(QueueName=queue_name)
            queue_url = response['QueueUrl']
            logging.info(f"Queue already exists for user {user_id}: {queue_url}")

        except self.sqs_client.exceptions.QueueDoesNotExist:
            # If the queue doesn't exist, create it
            logging.info(f"Queue does not exist for user {user_id}. Creating new queue...")
            attributes = (
                {'FifoQueue': 'true', 'ContentBasedDeduplication': 'true'} if is_fifo else {'ContentBasedDeduplication': 'true'}
            )
            create_response = self.sqs_client.create_queue(QueueName=queue_name, Attributes=attributes)
            queue_url = create_response['QueueUrl']
            logging.info(f"Created new queue for user {user_id}: {queue_url}")

        except ClientError as e:
            logging.error(f"Error retrieving or creating queue for user {user_id}: {str(e)}")
            raise

        return queue_url

    def add_task(self, user_id, type, task_data) -> APIResponse:
        """Add a single task to the user's SQS queue."""
        if not type:
            return APIResponse(status="failure", message="Task type is required")
        if not user_id:
            return APIResponse(status="failure", message="User ID is required")

        task = {'user_id': user_id, 'type': type, 'task_data': task_data}
        return self.add_tasks(user_id, [task])

    def get_task(self, user_id) -> APIResponse:
        """Retrieve a task from the user's SQS queue."""
        try:
            queue_url = self.get_user_queue_url(user_id)
            response = self.sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=10)

            if 'Messages' in response:
                message = response['Messages'][0]
                receipt_handle = message['ReceiptHandle']
                message_body = json.loads(message['Body'])

                logging.info(f"Task received from SQS queue for user {user_id}.")
                return APIResponse(
                    status="success",
                    message="Task retrieved successfully",
                    data={"task": message_body, "receipt_handle": receipt_handle},
                )
            else:
                return APIResponse(status="success", message="No tasks available for user", data=None)
        except ClientError as e:
            logging.error(f"Failed to receive message from SQS for user {user_id}: {str(e)}")
            return APIResponse(status="failure", message="Failed to retrieve task from queue")

    def delete_task(self, user_id, receipt_handle) -> APIResponse:
        """Delete a task from the user's SQS queue."""
        try:
            queue_url = self.get_user_queue_url(user_id)
            self.sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
            logging.info(f"Task successfully deleted from SQS queue for user {user_id}.")
            return APIResponse(status="success", message="Task deleted successfully")
        except ClientError as e:
            logging.error(f"Failed to delete message from SQS for user {user_id}: {str(e)}")
            return APIResponse(status="failure", message="Failed to delete task from queue")

    def get_callback_names(self) -> list:
        """Get a list of registered callback names."""
        return list(self.callbacks.keys())

    def process_message(self, user_id, message) -> APIResponse:
        """Process a message from the user's specific queue."""
        try:
            task_data = json.loads(message['Body'])
            task_type = task_data.get('type')

            if task_type in self.callbacks:
                callback_result = self.callbacks[task_type](task_data)
                queue_url = self.get_user_queue_url(user_id)
                self.sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])
                return APIResponse(status="success", message="Message processed and deleted", data=callback_result)
            else:
                logging.warning(f"No callback registered for task type: {task_type}")
                return APIResponse(status="failure", message=f"No callback registered for task type: {task_type}")
        except json.JSONDecodeError:
            logging.error("Failed to parse message body as JSON")
            return APIResponse(status="failure", message="Failed to parse message body")
        except ClientError as e:
            logging.error(f"Error processing message for user {user_id}: {str(e)}")
            return APIResponse(status="failure", message="Error processing message")

    def start_processing(self) -> APIResponse:
        try:
            self.is_processing = True
            self.executor.submit(self._processing_loop)
            return APIResponse(status="success", message="Task processing started")
        except Exception as e:
            logging.error(f"Failed to start processing: {str(e)}")
            return APIResponse(status="failure", message="Failed to start task processing")

    def stop_processing(self) -> APIResponse:
        try:
            self.is_processing = False
            self.executor.shutdown(wait=True)
            return APIResponse(status="success", message="Task processing stopped")
        except Exception as e:
            logging.error(f"Failed to stop processing: {str(e)}")
            return APIResponse(status="failure", message="Failed to stop task processing")

    def has_task_for_user(self, user_id) -> APIResponse:
        """Check if there are any messages in the user's queue directly."""
        try:
            queue_url = self.get_user_queue_url(user_id)
            response = self.sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])

            visible_count = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
            if visible_count > 0:
                logging.info(f"Queue for user {user_id} has {visible_count} messages.")
                return APIResponse(
                    status="success", message="Tasks are available for user", data={"visible_count": visible_count}
                )
            else:
                logging.info(f"No tasks found in the queue for user {user_id}.")
                return APIResponse(status="success", message="No tasks found for user")

        except ClientError as e:
            logging.error(f"Error checking for tasks for user {user_id}: {str(e)}")
            return APIResponse(status="failure", message="Error checking for tasks")

    def get_task_count_for_user(self, user_id) -> APIResponse:
        """Get the number of messages in the user's queue directly."""
        try:
            queue_url = self.get_user_queue_url(user_id)
            response = self.sqs_client.get_queue_attributes(
                QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages', 'ApproximateNumberOfMessagesNotVisible']
            )

            visible_count = int(response['Attributes'].get('ApproximateNumberOfMessages', 0))
            in_flight_count = int(response['Attributes'].get('ApproximateNumberOfMessagesNotVisible', 0))

            logging.info(
                f"Queue for user {user_id} has {visible_count} visible messages and {in_flight_count} in-flight messages."
            )
            return APIResponse(
                status="success",
                message="Task count retrieved successfully",
                data={"visible_count": visible_count, "in_flight_count": in_flight_count},
            )
        except ClientError as e:
            logging.error(f"Error getting task count for user {user_id}: {str(e)}")
            return APIResponse(status="failure", message="Error getting task count")

    def process_message(self, user_id, message) -> APIResponse:
        """Process a message from the user's specific queue."""
        try:
            task_data = json.loads(message['Body'])
            task_type = task_data.get('type')

            if task_type in self.callbacks:
                callback_result = self.callbacks[task_type](task_data)
                queue_url = self.get_user_queue_url(user_id)
                self.sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=message['ReceiptHandle'])
                return APIResponse(status="success", message="Message processed and deleted", data=callback_result)
            else:
                logging.warning(f"No callback registered for task type: {task_type}")
                return APIResponse(status="failure", message=f"No callback registered for task type: {task_type}")
        except json.JSONDecodeError:
            logging.error("Failed to parse message body as JSON")
            return APIResponse(status="failure", message="Failed to parse message body")
        except ClientError as e:
            logging.error(f"Error processing message for user {user_id}: {str(e)}")
            return APIResponse(status="failure", message="Error processing message")

    def get_tasks(self, user_id) -> APIResponse:
        """Retrieve tasks for a specific user from the user's queue."""
        try:
            queue_url = self.get_user_queue_url(user_id)
            response = self.sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=10)

            tasks = []
            if 'Messages' in response:
                for message in response['Messages']:
                    try:
                        message_body = json.loads(message['Body'])
                        if message_body.get('user_id') == user_id:
                            tasks.append({'task': message_body, 'receipt_handle': message['ReceiptHandle']})
                    except json.JSONDecodeError:
                        logging.warning(f"Failed to parse message body as JSON for message {message['MessageId']}")
                        continue

            if tasks:
                return APIResponse(status="success", message="Tasks retrieved successfully", data=tasks)
            else:
                return APIResponse(status="success", message="No tasks found for the user", data=[])
        except ClientError as e:
            logging.error(f"Failed to receive messages for user {user_id}: {str(e)}")
            return APIResponse(status="failure", message="Failed to retrieve tasks")

    def has_task_for_user(self, user_id) -> APIResponse:
        """Check if there are any tasks for the given user in the queue."""
        try:
            queue_url = self.get_user_queue_url(user_id)
            response = self.sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=0)

            if 'Messages' in response:
                for message in response['Messages']:
                    try:
                        message_body = json.loads(message['Body'])
                        if message_body.get('user_id') == user_id:
                            logging.info(f"Task found for user {user_id}. Message ID: {message['MessageId']}")
                            return APIResponse(
                                status="success", message="Task exists for user", data={"message_id": message['MessageId']}
                            )
                    except json.JSONDecodeError:
                        logging.warning(f"Failed to parse message body as JSON for message {message['MessageId']}")
                        continue

            logging.info(f"No tasks found for user {user_id}.")
            return APIResponse(status="success", message="No tasks found for user")

        except ClientError as e:
            logging.error(f"Error checking for tasks for user {user_id}: {str(e)}")
            return APIResponse(status="failure", message="Error checking for tasks")

    def get_all_queues(self) -> APIResponse:
        """Retrieve all queues and return a list of (user_id, queue_url) tuples."""
        try:
            response = self.sqs_client.list_queues()
            queue_urls = response.get('QueueUrls', [])
            user_queue_tuples = []

            # Extract user_id from queue names
            for queue_url in queue_urls:
                # Assuming the queue name is in the form 'user_<user_id>_queue'
                queue_name = queue_url.split('/')[-1]  # Get the last part of the URL (the queue name)
                if queue_name.startswith('user_'):
                    try:
                        # Extract the user_id (assuming the format is 'user_<user_id>_queue' or 'user_<user_id>_queue.fifo')
                        user_id_part = queue_name.split('_')[1]
                        user_id = int(user_id_part)  # Assuming user_id is an integer
                        user_queue_tuples.append((user_id, queue_url))
                    except (IndexError, ValueError):
                        logging.warning(f"Unable to parse user_id from queue name: {queue_name}")

            return APIResponse(status="success", message="All user queues retrieved successfully", data=user_queue_tuples)

        except ClientError as e:
            logging.error(f"Error retrieving all queues: {str(e)}")
            return APIResponse(status="failure", message="Error retrieving all queues")

    def _processing_loop(self):
        """Continuously process tasks from all users' queues."""
        futures = []
        while self.is_processing:
            try:
                user_queues = self.get_all_queues().data
                for user_id, queue_url in user_queues:
                    response = self.sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=10, WaitTimeSeconds=10)
                    messages = response.get('Messages', [])

                    for message in messages:
                        future = self.executor.submit(self.process_message, user_id, message)
                        futures.append(future)

                # Process completed futures
                for future in as_completed(futures):
                    try:
                        result = future.result()
                        if result.status == "success":
                            logging.info(f"Task processed successfully: {result.message}")
                        else:
                            logging.error(f"Task processing failed: {result.message}")
                    except Exception as e:
                        logging.error(f"Error processing task: {str(e)}")

                # Clear the futures list to prevent accumulation
                futures.clear()

            except ClientError as e:
                logging.error(f"Error receiving messages: {e}")

    def add_tasks(self, user_id, tasks) -> APIResponse:
        """Add multiple tasks to the user's SQS queue."""
        if not user_id:
            return APIResponse(status="failure", message="User ID is required")
        if not tasks or not isinstance(tasks, list):
            return APIResponse(status="failure", message="Tasks must be provided as a list")

        queue_url = self.get_user_queue_url(user_id)
        return self._batch_and_send_tasks(queue_url, tasks)

    def _batch_and_send_tasks(self, queue_url, tasks):
        BATCH_SIZE = 10
        MAX_RETRIES = 5
        INITIAL_BACKOFF = 0.5
        MAX_BACKOFF = 16

        results = []
        for i in range(0, len(tasks), BATCH_SIZE):
            batch = tasks[i : i + BATCH_SIZE]
            batch_result = self._send_task_batch(queue_url, batch, MAX_RETRIES, INITIAL_BACKOFF, MAX_BACKOFF)
            results.extend(batch_result)
            time.sleep(0.5)  # Delay between batches to avoid throttling

        successful = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failure']

        if failed:
            return APIResponse(
                status="partial_success" if successful else "failure",
                message=f"Added {len(successful)} tasks, failed to add {len(failed)} tasks",
                data={"successful": successful, "failed": failed},
            )
        return APIResponse(
            status="success", message=f"Successfully added {len(successful)} tasks", data={"successful": successful}
        )

    def _send_task_batch(self, queue_url, batch, max_retries, initial_backoff, max_backoff):
        for attempt in range(max_retries):
            try:
                entries = [
                    {
                        'Id': str(i),
                        'MessageBody': json.dumps(
                            {'task_data': task['task_data'], 'user_id': task['user_id'], 'type': task['type']}
                        ),
                        'MessageGroupId': 'default',
                        'MessageDeduplicationId': str(uuid.uuid4()),
                    }
                    for i, task in enumerate(batch)
                ]

                response = self.sqs_client.send_message_batch(QueueUrl=queue_url, Entries=entries)

                results = []
                if 'Successful' in response:
                    for success in response['Successful']:
                        results.append(
                            {
                                'status': 'success',
                                'message': 'Task added to queue successfully',
                                'data': {'message_id': success['MessageId']},
                            }
                        )

                if 'Failed' in response:
                    for failure in response['Failed']:
                        results.append(
                            {
                                'status': 'failure',
                                'message': f"Failed to add task: {failure['Message']}",
                                'data': {'id': failure['Id']},
                            }
                        )

                return results

            except self.sqs_client.exceptions.ThrottlingException:
                wait_time = min(initial_backoff * (2**attempt), max_backoff)
                logging.warning(f"Throttling detected. Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
            except Exception as e:
                logging.error(f"Error occurred while sending batch: {str(e)}")
                return [{'status': 'failure', 'message': f"Error sending batch: {str(e)}"} for _ in batch]

        return [{'status': 'failure', 'message': "Max retries reached"} for _ in batch]
