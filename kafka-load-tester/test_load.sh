#!/bin/bash
set -e

echo "=== Testing Kafka Load Tester ==="
echo
echo "1. Checking if services are healthy..."
docker compose ps

echo
echo "2. Testing health endpoint..."
curl -s http://localhost:8085/health | python3 -m json.tool

echo
echo "3. Starting a small load test (100 messages @ 10/sec)..."
curl -s -X POST http://localhost:8085/api/start \
  -H "Content-Type: application/json" \
  -d '{
    "message_count": 100,
    "message_rate": 10,
    "topic": "test-topic",
    "payload_size": 100,
    "test_name": "quick-test"
  }' | python3 -m json.tool

echo
echo "4. Waiting for test to complete (12 seconds)..."
sleep 12

echo
echo "5. Checking status..."
curl -s http://localhost:8085/api/status | python3 -m json.tool

echo
echo "6. Checking metrics..."
curl -s http://localhost:8085/metrics | grep kafka_load_tester_messages_sent_total

echo
echo "=== Test Complete ==="
echo "Load Tester UI: http://localhost:8085"
echo "Kafka UI: http://localhost:8080"