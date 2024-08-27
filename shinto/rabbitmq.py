"""RabbitMQ handler module."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from pika import BlockingConnection, ConnectionParameters, PlainCredentials
from pika.exceptions import AMQPError

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Callable

    from pika import BasicProperties
    from pika.amqp_object import Method
    from pika.channel import Channel
    from pika.connection import Connection


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
        queue: str | None = None,
        exchange: str | None = None,
    ) -> None:
        """
        Initialize the RabbitMQ connection.

        Args:
            host (str): RabbitMQ host.
            port (int | str | None): RabbitMQ port. Defaults to 5672.
            username (str): RabbitMQ username.
            password (str): RabbitMQ password.
            queue (str): RabbitMQ queue name.
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
        - `RABBITMQ_EXCHANGE`

        If arguments are provided they will take precedence over the environment variables.

        """
        host = host or os.getenv("RABBITMQ_HOST")
        port = port or os.getenv("RABBITMQ_PORT", "5672")
        username = username or os.getenv("RABBITMQ_USERNAME")
        password = password or os.getenv("RABBITMQ_PASSWORD")
        queue = queue or os.getenv("RABBITMQ_QUEUE")
        exchange = exchange or os.getenv("RABBITMQ_EXCHANGE", "")

        missing_params = [k for k, v in locals().items() if v is None]
        if len(missing_params) > 0:
            msg = f"Missing required parameters: {missing_params}"
            raise TypeError(msg)

        try:
            self._connection = BlockingConnection(
                ConnectionParameters(host, port, "/", PlainCredentials(username, password, True))
            )
        except AMQPError as amqp_error:
            raise QueueError from amqp_error

        self._queue_name = queue
        self._exchange = exchange
        self._channel = self._connection.channel()

    def __del__(self):
        """Close the connection when the object is deleted."""
        if hasattr(self, "_connection"):
            self._connection.close()

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
