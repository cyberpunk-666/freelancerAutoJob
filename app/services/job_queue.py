import boto3
import logging
import json
from botocore.exceptions import ClientError
import os
import uuid
class JobQueue:
    def __init__(self, queue_url):
        # Initialize the boto3 client for SQS
        region_name = os.getenv('AWS_SQS_REGION')
        self.sqs_client = boto3.client('sqs', region_name=region_name)
        self.queue_url = queue_url


    def add_job(self, user_id, job_data):
        """Add a job to the SQS queue."""
        try:
            # Prepare job data as JSON
            message_body = json.dumps({
                'job_data': job_data,
                'user_id': user_id
            })
            
            # Generate a unique MessageDeduplicationId
            deduplication_id = str(uuid.uuid4())
            
            response = self.sqs_client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=message_body,
                MessageGroupId='default',
                MessageDeduplicationId=deduplication_id  # Add this line
            )
            logging.info(f"Job added to SQS queue. Message ID: {response['MessageId']}")
        except ClientError as e:
            logging.error(f"Failed to add job to SQS: {str(e)}")

    def get_job(self, delete_after = True):
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
                message_body = json.loads(message['Body'])
                
                if delete_after:
                    self.delete_job(receipt_handle)

                logging.info(f"Job received from SQS queue.")
                return message_body
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

    def process_jobs(self):
        """Process jobs from the SQS queue."""
        while True:
            job_data = self.get_job()
            if job_data:
                # Process the job
                self.process_job(job_data)
                
    def process_job(self, job_data):
        """Process a single job."""
        # Implement your job processing logic here
        print(f"Processing job: {job_data}")
