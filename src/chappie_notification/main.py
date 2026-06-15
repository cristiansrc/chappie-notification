"""Main entrypoint for chappie-notification daemon.

Initializes the DI container, starts all consumers, and runs forever.
Handles graceful shutdown on SIGTERM and SIGINT.
"""

from __future__ import annotations

import asyncio
import logging
import signal
import sys

from chappie_notification.infrastructure.config.container import Container, create_container

logger = logging.getLogger(__name__)


class ChappieNotificationDaemon:
    """Main daemon class that manages the lifecycle of all consumers."""

    def __init__(self, container: Container) -> None:
        """Initialize the daemon.

        Args:
            container: The DI container with all wired dependencies.
        """
        self._container = container
        self._shutdown_event = asyncio.Event()

    async def start(self) -> None:
        """Start all consumers and run until shutdown."""
        consumers = [
            self._container.execution_consumer,
            self._container.error_consumer,
            self._container.tts_consumer,
            self._container.notification_consumer,
        ]

        # Filter out None consumers
        valid_consumers = [c for c in consumers if c is not None]

        # Start all consumers concurrently
        start_tasks = [consumer.start() for consumer in valid_consumers]
        await asyncio.gather(*start_tasks, return_exceptions=True)

        logger.info(
            "All consumers started. chappie-notification daemon is running."
        )

        # Wait for shutdown signal
        await self._shutdown_event.wait()

    async def shutdown(self) -> None:
        """Gracefully shutdown all consumers."""
        logger.info("Shutting down chappie-notification daemon...")

        consumers = [
            self._container.execution_consumer,
            self._container.error_consumer,
            self._container.tts_consumer,
            self._container.notification_consumer,
        ]

        for consumer in consumers:
            if consumer is not None:
                try:
                    await consumer.stop()
                except Exception as e:
                    logger.error(
                        "Error stopping consumer",
                        extra={"consumer": type(consumer).__name__, "error": str(e)},
                    )

        # Close HTTP client
        if self._container.http_client is not None:
            try:
                await self._container.http_client.close()
            except Exception as e:
                logger.error("Error closing HTTP client", extra={"error": str(e)})

        # Close RabbitMQ publisher
        if self._container.rabbitmq_publisher is not None:
            try:
                await self._container.rabbitmq_publisher.close()
            except Exception as e:
                logger.error(
                    "Error closing RabbitMQ publisher",
                    extra={"error": str(e)},
                )

        logger.info("chappie-notification daemon shutdown complete")
        self._shutdown_event.set()


def setup_logging() -> None:
    """Configure structured JSON logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='{"timestamp":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s",'
        '"message":"%(message)s"}',
        datefmt="%Y-%m-%dT%H:%M:%S",
        stream=sys.stdout,
    )


async def main() -> None:
    """Main entrypoint."""
    setup_logging()

    logger.info("Starting chappie-notification daemon...")

    # Create DI container
    container = await create_container()

    # Create and start daemon
    daemon = ChappieNotificationDaemon(container)

    # Handle shutdown signals
    loop = asyncio.get_event_loop()

    def _signal_handler() -> None:
        """Handle shutdown signals."""
        asyncio.ensure_future(daemon.shutdown())

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, _signal_handler)

    try:
        await daemon.start()
    except Exception as e:
        logger.error(
            "Daemon crashed",
            extra={"error": str(e)},
        )
        raise
    finally:
        await daemon.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
