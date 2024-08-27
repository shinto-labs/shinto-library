"""Unit tests for the rabbitmq module."""

import unittest
from unittest import mock
from unittest.mock import MagicMock, patch

from pika.exceptions import AMQPError

from shinto.rabbitmq import QueueError, QueueHandler


class TestRabbitMQ(unittest.TestCase):
    """Test the rabbitmq module."""

    @patch("shinto.rabbitmq.PlainCredentials")
    @patch("shinto.rabbitmq.ConnectionParameters")
    @patch("shinto.rabbitmq.BlockingConnection")
    def test_creation(
        self,
        mock_blocking_connection: MagicMock,
        mock_connection_parameters: MagicMock,
        mock_plain_credentials: MagicMock,
    ):
        """Test creation of the QueueHandler."""
        handler = QueueHandler("localhost", 5672, "user", "password", "queue", "exchange")
        mock_blocking_connection.assert_called_once()
        mock_connection_parameters.assert_called_once()
        mock_plain_credentials.assert_called_once()
        self.assertIsNotNone(handler)

    def test_creation_missing_arguments(self):
        """Test creation of the QueueHandler with missing arguments."""
        with self.assertRaises(TypeError):
            QueueHandler()

    @mock.patch.dict(
        "os.environ",
        {
            "RABBITMQ_HOST": "localhost",
            "RABBITMQ_PORT": "5672",
            "RABBITMQ_USERNAME": "user",
            "RABBITMQ_PASSWORD": "password",
            "RABBITMQ_QUEUE": "queue",
            "RABBITMQ_EXCHANGE": "exchange",
        },
    )
    @patch("shinto.rabbitmq.PlainCredentials")
    @patch("shinto.rabbitmq.ConnectionParameters")
    @patch("shinto.rabbitmq.BlockingConnection")
    def test_creation_from_env_params(
        self,
        mock_blocking_connection: MagicMock,
        mock_connection_parameters: MagicMock,
        mock_plain_credentials: MagicMock,
    ):
        """Test creation of the QueueHandler from environment variables."""
        handler = QueueHandler()
        mock_blocking_connection.assert_called_once()
        mock_connection_parameters.assert_called_once()
        mock_plain_credentials.assert_called_once()
        self.assertIsNotNone(handler)

    @patch("shinto.rabbitmq.PlainCredentials")
    @patch("shinto.rabbitmq.ConnectionParameters")
    @patch("shinto.rabbitmq.BlockingConnection")
    def test_creation_exception(
        self,
        mock_blocking_connection: MagicMock,
        _mock_connection_parameters: MagicMock,
        _mock_plain_credentials: MagicMock,
    ):
        """Test creation of the QueueHandler."""
        mock_blocking_connection.side_effect = AMQPError
        with self.assertRaises(QueueError):
            QueueHandler("localhost", 5672, "user", "password", "queue", "exchange")


if __name__ == "__main__":
    unittest.main()
