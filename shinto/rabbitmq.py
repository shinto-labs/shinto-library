"""RabbitMQ handler module."""

import os
from collections.abc import Callable

from pika import BasicProperties, BlockingConnection, ConnectionParameters, PlainCredentials
from pika.amqp_object import Method
from pika.channel import Channel
from pika.connection import Connection
from pika.exceptions import AMQPError

from shinto.config import load_config_file


class QueueError(Exception):
    """Exception while queueing the message."""


class QueueHandler:
    """RabbitMQ handler. Will wait for messages or publish messages."""

    _connection: Connection
    _channel: Channel
    _exchange: str
    _queue_name: str

    def __init__(
        self,
        host: str | None = None,
        port: int | str | None = None,
        username: str | None = None,
        password: str | None = None,
        queue_name: str | None = None,
        exchange: str = "",
    ) -> None:
        """
        Initialize the RabbitMQ connection.

        Args:
            host (str): RabbitMQ host.
            port (int | str | None): RabbitMQ port. Defaults to 5672.
            username (str): RabbitMQ username.
            password (str): RabbitMQ password.
            queue_name (str): RabbitMQ queue name.
            exchange (str): RabbitMQ exchange name. Defaults to "".

        Raises:
            TypeError: If any of the required parameters are missing.

        Arguments can also be provided as environment variables:
        -------------------------------------------------------
        - `RABBITMQ_HOST`
        - `RABBITMQ_PORT`
        - `RABBITMQ_USERNAME`
        - `RABBITMQ_PASSWORD`
        - `RABBITMQ_QUEUE`

        If arguments are provided they will take precedence over the environment variables.

        """
        host = host or os.getenv("RABBITMQ_HOST")
        port = port or os.getenv("RABBITMQ_PORT", "5672")
        username = username or os.getenv("RABBITMQ_USERNAME")
        password = password or os.getenv("RABBITMQ_PASSWORD")
        queue_name = queue_name or os.getenv("RABBITMQ_QUEUE")

        missing_params = [k for k, v in locals().items() if v is None]
        if len(missing_params) > 0:
            msg = f"Missing required parameters: {missing_params}"
            raise TypeError(msg)

        self._connection = BlockingConnection(
            ConnectionParameters(host, port, "/", PlainCredentials(username, password, True))
        )
        self._queue_name = queue_name
        self._exchange = exchange
        self._channel = self._connection.channel()

    def __del__(self):
        """Close the connection when the object is deleted."""
        self._connection.close()

    @classmethod
    def from_config_file(
        cls, file_path: str, start_element: list[str] | None = None
    ) -> "QueueHandler":
        """
        Initialize the RabbitMQ connection from a configuration file.

        Args:
            file_path (str): Path to the configuration file.
            start_element (list):
                Path to the RabbitMQ connection parameters in the configuration file.
                Should be used when the parameters are nested in the configuration file.

        RabbitMQ connection parameters are prioritised in the following order:
        ----------------------------------------------------------------------
        1. Environment variables
        2. Configuration file
        3. Default values

        Parameters can be provided as environment variables:
        ---------------------------------------------------
        - `RABBITMQ_HOST`
        - `RABBITMQ_PORT`
        - `RABBITMQ_USERNAME`
        - `RABBITMQ_PASSWORD`
        - `RABBITMQ_QUEUE`

        Parameters can be provided in the configuration file:
        ----------------------------------------------------
        - `host`
        - `port`: default 5672
        - `username`
        - `password`
        - `queue`

        """
        # Load the RabbitMQ connection parameters from the configuration file
        config = load_config_file(file_path=file_path, start_element=start_element)

        # 1. Get the RabbitMQ connection parameters from environment variables
        # 2. Otherwise use the parameters from the configuration file
        # 3. Otherwise use the default parameters
        host = os.getenv("RABBITMQ_HOST", config.get("host"))
        port = os.getenv("RABBITMQ_PORT", config.get("port", 5672))
        user = os.getenv("RABBITMQ_USERNAME", config.get("username"))
        password = os.getenv("RABBITMQ_PASSWORD", config.get("password"))
        queue = os.getenv("RABBITMQ_QUEUE", config.get("queue"))

        # Create the RabbitMQ connection
        return cls(
            host=host,
            port=port,
            username=user,
            password=password,
            queue_name=queue,
        )

    def check_for_queue(self):
        """Check if queue exists and if not: Declare it."""
        self._channel.queue_declare(
            queue=self._queue_name, durable=True, arguments={"x-max-priority": 10}
        )

    def consume(
        self,
        callback: Callable[[Channel, Method, BasicProperties, bytes], None],
    ):
        """
        Consume messages from the queue.

        Wait for messages in the RabbitMQ Queue and use callback when one is received
        The callback function:
            def callback(channel, method, properties, body):

        !Callback function MUST ACK or NACK the message after processing
            use: 'channel.basic_ack(delivery_tag=method.delivery_tag)' to ACK message
        """
        try:
            self._channel.basic_consume(
                queue=self._queue_name, on_message_callback=callback, auto_ack=False
            )
            self._channel.start_consuming()
        except AMQPError as amqp_error:
            raise QueueError from amqp_error

    def publish(self, message: str):
        """Publish message."""
        try:
            self._channel.basic_publish(
                exchange=self._exchange, routing_key=self._queue_name, body=message
            )
        except AMQPError as amqp_error:
            raise QueueError from amqp_error
