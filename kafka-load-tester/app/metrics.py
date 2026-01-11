"""Prometheus metrics for monitoring."""
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST


# Counters
messages_sent_total = Counter(
    'kafka_load_tester_messages_sent_total',
    'Total number of messages sent to Kafka'
)

messages_failed_total = Counter(
    'kafka_load_tester_messages_failed_total',
    'Total number of messages that failed to send'
)

load_tests_started_total = Counter(
    'kafka_load_tester_tests_started_total',
    'Total number of load tests started'
)

load_tests_completed_total = Counter(
    'kafka_load_tester_tests_completed_total',
    'Total number of load tests completed',
    ['status']  # success or failure
)

# Gauges
active_load_test = Gauge(
    'kafka_load_tester_active_test',
    'Whether a load test is currently running (1=yes, 0=no)'
)

current_message_rate = Gauge(
    'kafka_load_tester_current_rate',
    'Current message sending rate (messages/second)'
)

test_progress_percent = Gauge(
    'kafka_load_tester_progress_percent',
    'Progress percentage of current test (0-100)'
)

# Histograms
message_send_duration = Histogram(
    'kafka_load_tester_message_send_duration_seconds',
    'Time to send a message to Kafka',
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

test_duration = Histogram(
    'kafka_load_tester_test_duration_seconds',
    'Total duration of load tests',
    buckets=(1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600)
)


def get_metrics():
    """Generate Prometheus metrics in text format."""
    return generate_latest()


def get_content_type():
    """Get the content type for Prometheus metrics."""
    return CONTENT_TYPE_LATEST