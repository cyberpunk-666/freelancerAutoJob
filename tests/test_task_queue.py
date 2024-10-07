import unittest
from unittest.mock import MagicMock, patch

from app.models.api_response import APIResponse
from app.services.task_queue import TaskQueue
import boto3


class TestTaskQueue(unittest.TestCase):

    def setUp(self):
        # Create an instance of TaskQueue
        self.task_queue = TaskQueue()

        # Mock the SQS client using patch
        self.sqs_patcher = patch('boto3.client')
        self.mock_boto_client = self.sqs_patcher.start()

        # Create a mock SQS client instance
        self.mock_sqs_client = MagicMock()
        self.mock_boto_client.return_value = self.mock_sqs_client

        # Mock the list_queues method
        self.mock_sqs_client.list_queues.return_value = {'QueueUrls': []}

    def tearDown(self):
        self.sqs_patcher.stop()

    def test_get_all_queues_success(self):
        """Test get_all_queues method for successful retrieval of queues."""
        # Mock the response from SQS
        mock_response = {
            'QueueUrls': [
                'https://sqs.us-east-1.amazonaws.com/058264153804/user_1_queue.fifo',
                'https://sqs.us-east-1.amazonaws.com/058264153804/user_2_queue.fifo',
            ]
        }
        self.task_queue.sqs_client.list_queues.return_value = mock_response

        response = self.task_queue.get_all_queues()

        self.assertEqual(response.status, "success")
        self.assertEqual(response.message, "All user queues retrieved successfully")
        self.assertEqual(response.data, [(1, mock_response['QueueUrls'][0]), (2, mock_response['QueueUrls'][1])])

    def get_all_queues(self) -> APIResponse:
        """Retrieve all queues."""
        try:
            response = self.sqs_client.list_queues()
            queues = response.get('QueueUrls', [])
            return APIResponse(status="success", message="All queues retrieved successfully", data=queues)
        except Exception as e:  # Catch all exceptions, or you can specify ClientError
            return APIResponse(status="failure", message="Error retrieving all queues")

    def test_get_all_queues_failure(self):
        """Test get_all_queues method for failure when retrieving queues."""
        # Simulate an error in the list_queues method
        self.mock_sqs_client.list_queues.side_effect = Exception("Error retrieving queues")

        response = self.task_queue.get_all_queues()

        # Validate that the response indicates failure
        self.assertEqual(response.status, "failure")
        self.assertEqual(response.message, "Error retrieving all queues")

    def test_processing_loop(self, mock_as_completed):
        """Test the _processing_loop method for processing tasks."""
        # Mock the queue retrieval and message reception
        mock_response = {
            'QueueUrls': [
                'https://sqs.us-east-1.amazonaws.com/058264153804/user_1_queue.fifo',
            ]
        }
        self.task_queue.get_all_queues = MagicMock(return_value=APIResponse("success", "", mock_response['QueueUrls']))

        self.task_queue.sqs_client.receive_message.return_value = {'Messages': [{'Body': 'test message'}]}

        # Mock the process_message method
        self.task_queue.process_message = MagicMock(return_value=APIResponse("success", "Task processed"))

        # Set up the futures to complete successfully
        mock_future = MagicMock()
        mock_future.result.return_value = APIResponse("success", "Task processed")
        mock_as_completed.return_value = [mock_future]

        self.task_queue._processing_loop()

        # Ensure the receive_message method was called correctly
        self.task_queue.sqs_client.receive_message.assert_called_once()
        # Ensure process_message was called
        self.task_queue.process_message.assert_called_once_with(1, {'Body': 'test message'})


if __name__ == "__main__":
    unittest.main()
