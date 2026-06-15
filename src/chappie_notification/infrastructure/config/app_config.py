"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables with the CHAPPIE_ prefix.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppConfig(BaseSettings):
    """Centralized application configuration.

    All values have defaults suitable for local development.
    Override via environment variables with CHAPPIE_ prefix.
    """

    # RabbitMQ
    rabbitmq_url: str = "amqp://guest:guest@localhost:5672/"

    # chappie-daemon
    daemon_base_url: str = "http://localhost:8765"

    # n8n
    n8n_base_url: str = "http://localhost:5678"
    n8n_webhook_secret: str = ""

    # TTS
    tts_voice: str = "es-AR-ElenaNeural"
    tts_output_path: str = "/tmp/chappie_tts.mp3"
    tts_text_path: str = "/tmp/chappie_tts_text.txt"

    # Whitelist
    whitelist_path: str = "./config/commands-whitelist.yaml"

    # Timeouts
    agent_timeout: int = 120
    command_timeout: int = 30
    http_timeout: int = 10

    model_config = SettingsConfigDict(
        env_prefix="CHAPPIE_",
        env_file=".env",
        env_file_encoding="utf-8",
    )
