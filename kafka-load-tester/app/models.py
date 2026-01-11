"""Pydantic models for request/response validation."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LoadTestConfig(BaseModel):
    """Configuration for a load test."""

    message_count: int = Field(
        default=1000,
        ge=1,
        le=10000000,
        description="Number of messages to send"
    )
    message_rate: int = Field(
        default=100,
        ge=1,
        le=100000,
        description="Messages per second"
    )
    topic: str = Field(
        default="load-test",
        min_length=1,
        max_length=255,
        description="Target Kafka topic"
    )
    payload_size: int = Field(
        default=100,
        ge=1,
        le=1048576,
        description="Message payload size in bytes"
    )
    test_name: Optional[str] = Field(
        default=None,
        description="Optional test run name"
    )


class LoadTestStatus(BaseModel):
    """Current status of a load test."""

    running: bool
    test_id: Optional[str] = None
    messages_sent: int = 0
    messages_failed: int = 0
    current_rate: float = 0.0
    elapsed_seconds: float = 0.0
    progress_percent: float = 0.0
    started_at: Optional[datetime] = None
    config: Optional[LoadTestConfig] = None


class LoadTestResult(BaseModel):
    """Result of a completed load test."""

    test_id: str
    success: bool
    messages_sent: int
    messages_failed: int
    duration_seconds: float
    average_rate: float
    started_at: datetime
    completed_at: datetime
    config: LoadTestConfig


class HealthCheck(BaseModel):
    """Health check response."""

    status: str
    kafka_connected: bool
    app_name: str
    version: str