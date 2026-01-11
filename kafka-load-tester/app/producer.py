"""Async Kafka producer with connection pooling."""
import asyncio
import json
import time
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from aiokafka import AIOKafkaProducer
from aiokafka.errors import KafkaError
import logging

from config import settings
from models import LoadTestConfig, LoadTestStatus
import metrics

logger = logging.getLogger(__name__)


class KafkaProducerPool:
    """Pool of async Kafka producers for parallel message sending."""

    def __init__(self):
        self.producers: list[AIOKafkaProducer] = []
        self.is_connected = False
        self.current_test: Optional[LoadTestStatus] = None
        self.stop_requested = False

    async def connect(self):
        """Create and connect producer pool."""
        logger.info(f"Connecting to Kafka at {settings.kafka_bootstrap_servers}")

        try:
            for i in range(settings.producer_pool_size):
                producer = AIOKafkaProducer(
                    bootstrap_servers=settings.kafka_bootstrap_servers,
                    compression_type=settings.kafka_compression_type,
                    acks=int(settings.kafka_acks) if settings.kafka_acks.isdigit() else settings.kafka_acks,
                    linger_ms=settings.kafka_linger_ms,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                await producer.start()
                self.producers.append(producer)
                logger.info(f"Producer {i+1}/{settings.producer_pool_size} connected")

            self.is_connected = True
            logger.info("All producers connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            await self.disconnect()
            raise

    async def disconnect(self):
        """Disconnect all producers."""
        logger.info("Disconnecting producers")
        for producer in self.producers:
            try:
                await producer.stop()
            except Exception as e:
                logger.error(f"Error stopping producer: {e}")
        self.producers.clear()
        self.is_connected = False

    def generate_message(self, sequence: int, payload_size: int, test_id: str, test_name: Optional[str]) -> Dict[str, Any]:
        """Generate a test message with specified payload size."""
        # Generate payload to reach desired size
        base_payload = "x" * max(1, payload_size - 200)  # Reserve space for metadata

        return {
            "id": f"msg-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sequence": sequence,
            "payload": base_payload,
            "metadata": {
                "test_id": test_id,
                "test_name": test_name or "unnamed",
                "producer": "kafka-load-tester"
            }
        }

    async def send_message(self, producer: AIOKafkaProducer, topic: str, message: Dict[str, Any]) -> bool:
        """Send a single message and track metrics."""
        start_time = time.time()
        try:
            await producer.send_and_wait(topic, value=message)
            duration = time.time() - start_time
            metrics.message_send_duration.observe(duration)
            metrics.messages_sent_total.inc()
            return True
        except KafkaError as e:
            logger.error(f"Failed to send message: {e}")
            metrics.messages_failed_total.inc()
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending message: {e}")
            metrics.messages_failed_total.inc()
            return False

    async def run_load_test(self, config: LoadTestConfig) -> Dict[str, Any]:
        """Run a load test with the specified configuration."""
        if not self.is_connected:
            raise RuntimeError("Producers not connected to Kafka")

        if self.current_test and self.current_test.running:
            raise RuntimeError("Another load test is already running")

        test_id = f"test-{uuid.uuid4().hex[:8]}"
        logger.info(f"Starting load test {test_id}: {config.message_count} messages at {config.message_rate}/sec")

        # Initialize test status
        self.current_test = LoadTestStatus(
            running=True,
            test_id=test_id,
            messages_sent=0,
            messages_failed=0,
            current_rate=0.0,
            elapsed_seconds=0.0,
            progress_percent=0.0,
            started_at=datetime.utcnow(),
            config=config
        )
        self.stop_requested = False

        metrics.load_tests_started_total.inc()
        metrics.active_load_test.set(1)

        start_time = time.time()
        messages_sent = 0
        messages_failed = 0

        try:
            # Calculate delay between messages to achieve target rate
            delay_between_messages = 1.0 / config.message_rate if config.message_rate > 0 else 0

            # Send messages
            producer_index = 0
            for i in range(config.message_count):
                if self.stop_requested:
                    logger.info("Stop requested, terminating load test")
                    break

                # Generate message
                message = self.generate_message(
                    sequence=i + 1,
                    payload_size=config.payload_size,
                    test_id=test_id,
                    test_name=config.test_name
                )

                # Send using round-robin producer selection
                producer = self.producers[producer_index]
                producer_index = (producer_index + 1) % len(self.producers)

                success = await self.send_message(producer, config.topic, message)
                if success:
                    messages_sent += 1
                else:
                    messages_failed += 1

                # Update status
                elapsed = time.time() - start_time
                self.current_test.messages_sent = messages_sent
                self.current_test.messages_failed = messages_failed
                self.current_test.elapsed_seconds = elapsed
                self.current_test.progress_percent = (i + 1) / config.message_count * 100
                if elapsed > 0:
                    self.current_test.current_rate = messages_sent / elapsed

                metrics.current_message_rate.set(self.current_test.current_rate)
                metrics.test_progress_percent.set(self.current_test.progress_percent)

                # Rate limiting
                if delay_between_messages > 0:
                    await asyncio.sleep(delay_between_messages)

            # Test completed
            total_duration = time.time() - start_time
            average_rate = messages_sent / total_duration if total_duration > 0 else 0

            logger.info(
                f"Load test {test_id} completed: "
                f"{messages_sent} sent, {messages_failed} failed, "
                f"{total_duration:.2f}s, {average_rate:.2f} msg/s"
            )

            metrics.test_duration.observe(total_duration)
            metrics.load_tests_completed_total.labels(status="success").inc()

            result = {
                "test_id": test_id,
                "success": True,
                "messages_sent": messages_sent,
                "messages_failed": messages_failed,
                "duration_seconds": total_duration,
                "average_rate": average_rate,
                "started_at": self.current_test.started_at.isoformat(),
                "completed_at": datetime.utcnow().isoformat(),
                "config": config.dict()
            }

        except Exception as e:
            logger.error(f"Load test {test_id} failed: {e}")
            metrics.load_tests_completed_total.labels(status="failure").inc()
            result = {
                "test_id": test_id,
                "success": False,
                "error": str(e),
                "messages_sent": messages_sent,
                "messages_failed": messages_failed
            }

        finally:
            # Reset status
            self.current_test.running = False
            metrics.active_load_test.set(0)
            metrics.current_message_rate.set(0)
            metrics.test_progress_percent.set(0)

        return result

    def get_status(self) -> LoadTestStatus:
        """Get current test status."""
        if self.current_test:
            return self.current_test
        return LoadTestStatus(running=False)

    async def stop_test(self):
        """Request to stop the current test."""
        if self.current_test and self.current_test.running:
            logger.info("Requesting load test stop")
            self.stop_requested = True


# Global producer pool instance
producer_pool = KafkaProducerPool()