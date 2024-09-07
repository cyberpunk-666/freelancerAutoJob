import unittest
from unittest.mock import patch
import boto3
from moto import mock_aws
from utils.job_queue import JobQueue
import json


class TestJobQueue(unittest.TestCase):

    @mock_aws
    def setUp(self):
        """Setup an SQS queue using moto before each test."""
        self.sqs = boto3.client('sqs', region_name='us-east-1')
        self.queue_url = self.sqs.create_queue(QueueName='test_queue')['QueueUrl']
        self.job_queue = JobQueue(self.queue_url)

    @mock_aws
    def test_add_job(self):
        """Test that add_job correctly sends a message to the SQS queue."""
        job_id = '123'
        user_id = '456'
        self.job_queue.add_job(job_id, user_id)

        # Retrieve messages from the queue to validate
        response = self.sqs.receive_message(QueueUrl=self.queue_url, MaxNumberOfMessages=1)
        message = response['Messages'][0]
        body = json.loads(message['Body'])

        self.assertEqual(body['job_id'], job_id)
        self.assertEqual(body['user_id'], user_id)

    @mock_aws
    def test_get_job(self):
        """Test that get_job correctly retrieves a message from the SQS queue."""
        # Add a message to the queue manually
        message_body = json.dumps({'job_id': '123', 'user_id': '456'})
        self.sqs.send_message(QueueUrl=self.queue_url, MessageBody=message_body)

        job_data, receipt_handle = self.job_queue.get_job()

        self.assertIsNotNone(job_data)
        self.assertEqual(job_data['job_id'], '123')
        self.assertEqual(job_data['user_id'], '456')

    @mock_aws
    def test_get_job_empty_queue(self):
        """Test that get_job returns None when no jobs are in the queue."""
        job_data, receipt_handle = self.job_queue.get_job()
        self.assertIsNone(job_data)
        self.assertIsNone(receipt_handle)

    @mock_aws
    def test_delete_job(self):
        """Test that delete_job removes a message from the SQS queue."""
        # Add a message to the queue manually
        message_body = json.dumps({'job_id': '123', 'user_id': '456'})
        response = self.sqs.send_message(QueueUrl=self.queue_url, MessageBody=message_body)

        # Get the job and delete it
        job_data, receipt_handle = self.job_queue.get_job()
        self.job_queue.delete_job(receipt_handle)

        # Ensure the message is no longer in the queue
        response = self.sqs.receive_message(QueueUrl=self.queue_url, MaxNumberOfMessages=1)
        self.assertNotIn('Messages', response)


if __name__ == '__main__':
    unittest.main()
