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
            self.queue_url = os.getenv('AWS_SQS_QUEUE_URL')
            num_workers = os.getenv('TASK_QUEUE_NUM_WORKERS')
            self.num_workers = int(num_workers) if num_workers else 1
            self.executor = ThreadPoolExecutor(max_workers=self.num_workers)

    def add_task(self, user_id, type, task_data) -> APIResponse:
        """Add a task to the SQS queue."""
        try:
            if not type:
                return APIResponse(status="failure", message="Task type is required")
            if not user_id:
                return APIResponse(status="failure", message="User ID is required")
            
            message_body = json.dumps({
                'task_data': task_data,
                'user_id': user_id,
                'type': type
            })
                        
            deduplication_id = str(uuid.uuid4())
            
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body,
                MessageGroupId='default',
                MessageDeduplicationId=deduplication_id
            )
            logging.info(f"Task added to SQS queue. Message ID: {response['MessageId']}")
            return APIResponse(status="success", message="Task added to queue successfully", data={"message_id": response['MessageId']})
        except ClientError as e:
            logging.error(f"Failed to add task to SQS: {str(e)}")
            return APIResponse(status="failure", message="Failed to add task to queue")

    def get_task(self) -> APIResponse:
        """Retrieve a task from the SQS queue."""
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )

            if 'Messages' in response:
                message = response['Messages'][0]
                receipt_handle = message['ReceiptHandle']
                message_body = json.loads(message['Body'])
                
                logging.info(f"Task received from SQS queue.")
                return APIResponse(status="success", message="Task retrieved successfully", data={"task": message_body, "receipt_handle": receipt_handle})
            else:
                return APIResponse(status="success", message="No tasks available", data=None)
        except ClientError as e:
            logging.error(f"Failed to receive message from SQS: {str(e)}")
            return APIResponse(status="failure", message="Failed to retrieve task from queue")

    def delete_task(self, receipt_handle) -> APIResponse:
        """Delete a task from the SQS queue."""
        try:
            self.sqs_client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            logging.info("Task successfully deleted from SQS queue.")
            return APIResponse(status="success", message="Task deleted successfully")
        except ClientError as e:
            logging.error(f"Failed to delete message from SQS: {str(e)}")
            return APIResponse(status="failure", message="Failed to delete task from queue")

    def process_task(self, task_data) -> APIResponse:
        """Process a single task."""
        try:
            print(f"Processing task: {task_data}")
            # Simulate some work
            time.sleep(2)
            print(f"Finished processing task: {task_data}")
            return APIResponse(status="success", message="Task processed successfully")
        except Exception as e:
            logging.error(f"Error processing task: {str(e)}")
            return APIResponse(status="failure", message="Failed to process task")

    def register_callback(self, task_type, callback) -> APIResponse:
        """Register a callback function for a specific task type."""
        try:
            self.callbacks[task_type] = callback
            return APIResponse(status="success", message=f"Callback registered for task type: {task_type}")
        except Exception as e:
            logging.error(f"Failed to register callback: {str(e)}")
            return APIResponse(status="failure", message="Failed to register callback")

    def get_callback_names(self) -> list:
        """Get a list of registered callback names."""
        return list(self.callbacks.keys())

    def process_message(self, message) -> APIResponse:
        try:
            task_data = json.loads(message['Body'])
            task_type = task_data.get('type')

            if task_type in self.callbacks:
                callback_result = self.callbacks[task_type](task_data)
                self.sqs_client.delete_message(
                    QueueUrl=self.queue_url,
                    ReceiptHandle=message['ReceiptHandle']
                )
                return APIResponse(status="success", message="Message processed and deleted", data=callback_result)
            else:
                logging.warning(f"No callback registered for task type: {task_type}")
                return APIResponse(status="failure", message=f"No callback registered for task type: {task_type}")
        except json.JSONDecodeError:
            logging.error("Failed to parse message body as JSON")
            return APIResponse(status="failure", message="Failed to parse message body")
        except ClientError as e:
            logging.error(f"Error processing message: {e}")
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
        
    def get_tasks(self, user_id) -> APIResponse:
        """Retrieve tasks for a specific user from the SQS queue."""
        try:
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=10,
                WaitTimeSeconds=10,
                MessageAttributeNames=['All'],
                MessageAttributeValues={
                    'DataType': 'String',
                    'StringValue': user_id
                }
            )

            tasks = []
            if 'Messages' in response:
                for message in response['Messages']:
                    message_body = json.loads(message['Body'])
                    tasks.append(message_body)

            return APIResponse(status="success", message="Tasks retrieved successfully", data=tasks)
        except ClientError as e:
            logging.error(f"Failed to receive messages for user {user_id}: {str(e)}")
            return APIResponse(status="failure", message="Failed to retrieve tasks")

    def _processing_loop(self):
        futures = []
        while self.is_processing:
            try:
                response = self.sqs_client.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20
                )

                messages = response.get('Messages', [])

                for message in messages:
                    future = self.executor.submit(self.process_message, message)
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
