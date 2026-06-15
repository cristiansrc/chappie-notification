"""Dependency injection container for chappie-notification.

Wires all ports to adapters and injects dependencies into use cases and consumers.
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable

from chappie_notification.application.use_cases.execute_agent import ExecuteAgentUseCase
from chappie_notification.application.use_cases.execute_command import ExecuteCommandUseCase
from chappie_notification.application.use_cases.generate_tts import GenerateTTSUseCase
from chappie_notification.application.use_cases.handle_error import HandleErrorUseCase
from chappie_notification.application.use_cases.process_response import ProcessResponseUseCase
from chappie_notification.application.use_cases.show_notification import ShowNotificationUseCase
from chappie_notification.infrastructure.adapters.async_file_writer_adapter import (
    AsyncFileWriterAdapter,
)
from chappie_notification.infrastructure.adapters.edge_tts_adapter import (
    EdgeTTSSynthesizerAdapter,
)
from chappie_notification.infrastructure.adapters.httpx_client_adapter import (
    HTTPXClientAdapter,
)
from chappie_notification.infrastructure.adapters.opencode_agent_adapter import (
    OpenCodeAgentExecutorAdapter,
)
from chappie_notification.infrastructure.adapters.rabbitmq_publisher_adapter import (
    RabbitMQPublisherAdapter,
)
from chappie_notification.infrastructure.adapters.subprocess_command_adapter import (
    SubprocessCommandExecutorAdapter,
)
from chappie_notification.infrastructure.adapters.swaync_notification_adapter import (
    SwayNCNotificationSenderAdapter,
)
from chappie_notification.infrastructure.adapters.whitelist_validator_adapter import (
    WhitelistCommandValidatorAdapter,
)
from chappie_notification.infrastructure.config.app_config import AppConfig
from chappie_notification.infrastructure.consumers.error_consumer import ErrorConsumer
from chappie_notification.infrastructure.consumers.execution_consumer import ExecutionConsumer
from chappie_notification.infrastructure.consumers.notification_consumer import (
    NotificationConsumer,
)
from chappie_notification.infrastructure.consumers.tts_consumer import TTSConsumer

logger = logging.getLogger(__name__)


class Container:
    """Holds all wired dependencies for the application."""

    def __init__(self) -> None:
        # Config
        self.config = AppConfig()

        # Driven adapters (output ports)
        self.rabbitmq_publisher: RabbitMQPublisherAdapter | None = None
        self.tts_synthesizer: EdgeTTSSynthesizerAdapter | None = None
        self.agent_executor: OpenCodeAgentExecutorAdapter | None = None
        self.command_executor: SubprocessCommandExecutorAdapter | None = None
        self.command_validator: WhitelistCommandValidatorAdapter | None = None
        self.notification_sender: SwayNCNotificationSenderAdapter | None = None
        self.http_client: HTTPXClientAdapter | None = None
        self.file_writer: AsyncFileWriterAdapter | None = None

        # Use cases
        self.process_response_uc: ProcessResponseUseCase | None = None
        self.handle_error_uc: HandleErrorUseCase | None = None
        self.generate_tts_uc: GenerateTTSUseCase | None = None
        self.show_notification_uc: ShowNotificationUseCase | None = None
        self.execute_agent_uc: ExecuteAgentUseCase | None = None
        self.execute_command_uc: ExecuteCommandUseCase | None = None

        # Consumers
        self.execution_consumer: ExecutionConsumer | None = None
        self.error_consumer: ErrorConsumer | None = None
        self.tts_consumer: TTSConsumer | None = None
        self.notification_consumer: NotificationConsumer | None = None


async def create_container() -> Container:
    """Create and wire the DI container.

    Returns:
        A fully wired Container instance.
    """
    container = Container()
    config = container.config

    # Initialize driven adapters
    container.rabbitmq_publisher = RabbitMQPublisherAdapter(
        connection_url=config.rabbitmq_url,
    )
    container.tts_synthesizer = EdgeTTSSynthesizerAdapter(
        voice=config.tts_voice,
    )
    container.agent_executor = OpenCodeAgentExecutorAdapter(
        timeout=config.agent_timeout,
    )
    container.command_executor = SubprocessCommandExecutorAdapter(
        timeout=config.command_timeout,
    )
    container.command_validator = WhitelistCommandValidatorAdapter(
        whitelist_path=config.whitelist_path,
    )
    container.notification_sender = SwayNCNotificationSenderAdapter()
    container.http_client = HTTPXClientAdapter()
    container.file_writer = AsyncFileWriterAdapter()

    # Initialize use cases
    container.execute_agent_uc = ExecuteAgentUseCase(
        agent_executor=container.agent_executor,
        rabbitmq_publisher=container.rabbitmq_publisher,
        config=config,
    )
    container.execute_command_uc = ExecuteCommandUseCase(
        command_executor=container.command_executor,
        command_validator=container.command_validator,
        rabbitmq_publisher=container.rabbitmq_publisher,
        config=config,
    )

    container.process_response_uc = ProcessResponseUseCase(
        rabbitmq_publisher=container.rabbitmq_publisher,
        execute_agent_uc=container.execute_agent_uc,
        execute_command_uc=container.execute_command_uc,
    )

    container.handle_error_uc = HandleErrorUseCase(
        http_client=container.http_client,
        config=config,
    )

    container.generate_tts_uc = GenerateTTSUseCase(
        tts_synthesizer=container.tts_synthesizer,
        file_writer=container.file_writer,
        http_client=container.http_client,
        config=config,
    )

    container.show_notification_uc = ShowNotificationUseCase(
        notification_sender=container.notification_sender,
        rabbitmq_publisher=container.rabbitmq_publisher,
    )

    # Initialize consumers (connection is opened by each consumer)
    container.execution_consumer = ExecutionConsumer(
        rabbitmq_url=config.rabbitmq_url,
        use_case=container.process_response_uc,
        config=config,
    )
    container.error_consumer = ErrorConsumer(
        rabbitmq_url=config.rabbitmq_url,
        use_case=container.handle_error_uc,
        config=config,
    )
    container.tts_consumer = TTSConsumer(
        rabbitmq_url=config.rabbitmq_url,
        use_case=container.generate_tts_uc,
        publisher=container.rabbitmq_publisher,
        config=config,
    )
    container.notification_consumer = NotificationConsumer(
        rabbitmq_url=config.rabbitmq_url,
        use_case=container.show_notification_uc,
        publisher=container.rabbitmq_publisher,
        config=config,
    )

    logger.info("DI container created successfully")
    return container
