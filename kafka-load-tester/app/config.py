"""Configuration management using Pydantic Settings."""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    # Kafka Configuration
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "load-test"
    kafka_compression_type: str = "gzip"
    kafka_acks: str = "1"
    kafka_linger_ms: int = 10
    kafka_batch_size: int = 16384
    kafka_max_request_size: int = 1048576

    # Application Configuration
    app_name: str = "Kafka Load Tester"
    app_version: str = "1.0.0"
    producer_pool_size: int = 5
    max_message_size: int = 1048576  # 1MB

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()