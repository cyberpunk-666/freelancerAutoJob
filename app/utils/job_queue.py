import boto3
import logging
import json
from botocore.exceptions import ClientError

class JobQueue:
    def __init__(self, queue_url):
        # Initialize the boto3 client for SQS
        self.sqs_client = boto3.client('sqs', region_name='your-region')
        self.queue_url = queue_url

    def add_job(self, job_id, user_id):
        """Add a job to the SQS queue."""
        try:
            # Prepare job data as JSON
            message_body = json.dumps({
                'job_id': job_id,
                'user_id': user_id
            })
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body
            )
            logging.info(f"Job {job_id} added to SQS queue. Message ID: {response['MessageId']}")
        except ClientError as e:
            logging.error(f"Failed to add job {job_id} to SQS: {str(e)}")

    def get_job(self):
        """Retrieve a job from the SQS queue."""
        try:
            # Poll SQS for a message
            response = self.sqs_client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=1,
                WaitTimeSeconds=10
            )

            if 'Messages' in response:
                message = response['Messages'][0]
                receipt_handle = message['ReceiptHandle']
                # Safely parse the message body as JSON
                job_data = json.loads(message['Body'])

                logging.info(f"Job {job_data['job_id']} received from SQS queue.")
                return job_data, receipt_handle
            else:
                return None, None  # No jobs available
        except ClientError as e:
            logging.error(f"Failed to receive message from SQS: {str(e)}")
            return None, None

    def delete_job(self, receipt_handle):
        """Delete a job from the SQS queue."""
        try:
            self.sqs_client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle
            )
            logging.info("Job successfully deleted from SQS queue.")
        except ClientError as e:
            logging.error(f"Failed to delete message from SQS: {str(e)}")
