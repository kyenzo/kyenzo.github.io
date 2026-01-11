# Kafka Load Tester - Quick Start Guide

## What Was Built

A complete, production-ready Kafka load testing application with:

✅ **FastAPI Backend** - Async Python web framework with WebSocket support
✅ **Modern Web UI** - Real-time progress monitoring with clean dark theme
✅ **Async Kafka Producer** - High-throughput message generation with aiokafka
✅ **Prometheus Metrics** - Built-in observability for monitoring
✅ **Multi-Environment** - Docker Compose for local, Kubernetes for production
✅ **Docker Optimized** - Multi-stage builds, non-root user, health checks

## Technology Stack

- **Backend**: Python 3.11 + FastAPI + aiokafka
- **Frontend**: Vanilla JavaScript + WebSockets
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Kubernetes + Kustomize
- **Monitoring**: Prometheus metrics
- **Compression**: Gzip (built-in, no external deps)

## Quick Start (5 minutes)

### 1. Start the Application

```bash
cd kafka-load-tester
docker compose up -d
```

This starts:
- Kafka broker (KRaft mode, port 9092)
- Kafka UI (port 8080)
- Load Tester (port 8085)

### 2. Access the Web UI

Open in your browser: **http://localhost:8085**

### 3. Run Your First Test

**Option A: Use Presets**
- Click "Medium: 10K @ 1K/s" button
- Click "Start Load Test"
- Watch real-time progress

**Option B: Custom Configuration**
- Messages: 1000
- Rate: 100 msg/s
- Topic: load-test
- Payload: 100 bytes
- Click "Start Load Test"

### 4. View Results

**In the UI:**
- Watch messages sent counter
- Monitor current rate (msg/s)
- See progress bar fill up

**In Kafka UI:**
- Open http://localhost:8080
- Go to Topics → load-test
- View message contents

**Metrics:**
- Visit http://localhost:8085/metrics
- Check `kafka_load_tester_messages_sent_total`

## Available Services

| Service | URL | Purpose |
|---------|-----|---------|
| Load Tester UI | http://localhost:8085 | Main application interface |
| Kafka UI | http://localhost:8080 | Manage Kafka topics and view messages |
| Health Check | http://localhost:8085/health | Application health status |
| Metrics | http://localhost:8085/metrics | Prometheus metrics |
| API Docs | http://localhost:8085/docs | Interactive API documentation |

## Test Presets

| Preset | Messages | Rate | Duration | Use Case |
|--------|----------|------|----------|----------|
| Small | 1,000 | 100/s | ~10s | Quick validation |
| Medium | 10,000 | 1,000/s | ~10s | Standard testing |
| Large | 100,000 | 5,000/s | ~20s | Performance testing |
| Stress | 1,000,000 | 10,000/s | ~100s | Stress testing |

## Configuration Options

### Message Parameters
- **Count**: 1 to 10,000,000 messages
- **Rate**: 1 to 100,000 messages/second
- **Topic**: Any valid Kafka topic name
- **Payload Size**: 1 byte to 1MB
- **Test Name**: Optional identifier

### Producer Settings (Environment Variables)
```bash
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
KAFKA_COMPRESSION_TYPE=gzip
KAFKA_ACKS=1
PRODUCER_POOL_SIZE=5
```

## Connecting to Remote Kafka

### For Remote Cluster (VPC Peering/VPN)

Edit `docker-compose.yml`:

```yaml
services:
  load-tester:
    # Remove kafka and kafka-ui services
    environment:
      KAFKA_BOOTSTRAP_SERVERS: 10.0.x.x:9092  # Your remote Kafka IP
```

### For AWS EKS (Strimzi Operator)

```yaml
KAFKA_BOOTSTRAP_SERVERS: kafka-kafka-bootstrap.kafka.svc.cluster.local:9092
```

Then:
```bash
docker compose down
docker compose up -d
```

## Common Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f load-tester

# Check status
docker compose ps

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v

# Rebuild after code changes
docker compose up -d --build
```

## API Usage

### Start a Load Test

```bash
curl -X POST http://localhost:8085/api/start \
  -H "Content-Type: application/json" \
  -d '{
    "message_count": 1000,
    "message_rate": 100,
    "topic": "my-topic",
    "payload_size": 100,
    "test_name": "api-test"
  }'
```

### Check Status

```bash
curl http://localhost:8085/api/status | jq
```

### Stop Test

```bash
curl -X POST http://localhost:8085/api/stop
```

## Message Format

Messages sent to Kafka have this structure:

```json
{
  "id": "msg-a1b2c3d4",
  "timestamp": "2026-01-11T20:00:00Z",
  "sequence": 12345,
  "payload": "xxxxxxxxx...",
  "metadata": {
    "test_id": "test-abc123",
    "test_name": "my-test",
    "producer": "kafka-load-tester"
  }
}
```

## Monitoring with Prometheus

Key metrics available at `/metrics`:

```
kafka_load_tester_messages_sent_total
kafka_load_tester_messages_failed_total
kafka_load_tester_tests_started_total
kafka_load_tester_tests_completed_total
kafka_load_tester_active_test
kafka_load_tester_current_rate
kafka_load_tester_message_send_duration_seconds
```

## Troubleshooting

### Application won't connect to Kafka

```bash
# Check if Kafka is healthy
docker compose ps kafka

# View Kafka logs
docker compose logs kafka

# Check bootstrap servers in config
docker compose exec load-tester env | grep KAFKA
```

### Port already in use

If port 8085 is taken:

1. Edit `docker-compose.yml`:
   ```yaml
   ports:
     - "8090:8000"  # Change 8085 to 8090
   ```

2. Restart:
   ```bash
   docker compose down && docker compose up -d
   ```

### Check application logs

```bash
docker compose logs -f load-tester
```

## Next Steps

### Deploy to Kubernetes

See [README.md](README.md) for full Kubernetes deployment instructions using Kustomize.

```bash
# Build and push image
docker build -t your-registry/kafka-load-tester:latest .
docker push your-registry/kafka-load-tester:latest

# Deploy to dev
kubectl apply -k k8s/overlays/dev

# Deploy to prod
kubectl apply -k k8s/overlays/prod
```

### ArgoCD Integration

Add to your GitOps repository:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: kafka-load-tester
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/kafka-load-tester.git
    targetRevision: main
    path: k8s/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: kafka
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Performance Tips

### High Throughput (>10K msg/s)
- Increase `PRODUCER_POOL_SIZE` to 10-20
- Use `KAFKA_COMPRESSION_TYPE=gzip` or `lz4`
- Set `KAFKA_ACKS=1` (not `all`)

### Low Latency
- Set `PRODUCER_POOL_SIZE` to 1-3
- Use `KAFKA_COMPRESSION_TYPE=none`
- Reduce payload size

## Support

- Documentation: [README.md](README.md)
- API Docs: http://localhost:8085/docs
- Test Script: `./test_load.sh`

---

**Built with:** Python 3.11, FastAPI, aiokafka, and modern web technologies