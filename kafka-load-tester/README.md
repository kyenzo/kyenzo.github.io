# Kafka Load Tester

A modern web-based load testing application for Apache Kafka, built with FastAPI and designed for cloud-native deployments.

## Features

- **Web UI**: Clean, real-time interface for configuring and monitoring load tests
- **Async Architecture**: Built with Python asyncio and aiokafka for high-throughput message generation
- **Real-time Monitoring**: WebSocket-based live updates of test progress
- **Prometheus Metrics**: Built-in metrics for monitoring and alerting
- **Multi-Environment**: Support for local Docker, dev, and production Kubernetes deployments
- **Configurable Load**: Adjustable message count, rate, topic, and payload size
- **Quick Presets**: Pre-configured test scenarios for common use cases

## Architecture

```
┌─────────────────┐
│   Web UI        │ (HTML/JS + WebSockets)
│   (Browser)     │
└────────┬────────┘
         │ HTTP/WS
┌────────▼────────┐
│   FastAPI       │
│   - REST API    │
│   - WebSocket   │
│   - /metrics    │
└────────┬────────┘
         │
┌────────▼────────┐
│  aiokafka       │
│  Producer Pool  │
└────────┬────────┘
         │
┌────────▼────────┐
│  Kafka Cluster  │
└─────────────────┘
```

## Quick Start with Docker Compose

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+

### Run Locally

1. Clone the repository:
```bash
git clone <repository-url>
cd kafka-load-tester
```

2. Start the application stack:
```bash
docker-compose up -d
```

This will start:
- **Kafka broker** (KRaft mode, no Zookeeper) on `localhost:9092`
- **Kafka UI** on `http://localhost:8080`
- **Load Tester** on `http://localhost:8085`

3. Access the application:
- Load Tester UI: http://localhost:8085
- Kafka UI: http://localhost:8080

4. Run your first load test:
- Open http://localhost:8085
- Use default settings or select a preset
- Click "Start Load Test"
- Watch real-time progress

5. Verify messages in Kafka:
- Open http://localhost:8080
- Navigate to Topics → load-test
- View messages

### Stop the Stack

```bash
docker-compose down
```

To remove volumes as well:
```bash
docker-compose down -v
```

## Configuration

### Connecting to Remote Kafka Cluster

To connect to a remote Kafka cluster (e.g., via VPC peering or VPN):

1. **Update docker-compose.yml** to remove the local Kafka container and update environment variables:

```yaml
services:
  load-tester:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: kafka-load-tester
    ports:
      - "8085:8000"
    environment:
      KAFKA_BOOTSTRAP_SERVERS: <remote-kafka-host>:9092  # Your remote Kafka
      KAFKA_TOPIC: load-test
      KAFKA_COMPRESSION_TYPE: gzip
      KAFKA_ACKS: '1'
      PRODUCER_POOL_SIZE: 5
```

2. **For AWS EKS cluster**, use the Kubernetes bootstrap server:
   - `kafka-kafka-bootstrap.kafka.svc.cluster.local:9092`

3. **For VPN/VPC peering**, use the private IP or hostname:
   - `10.0.x.x:9092` (private IP)
   - `kafka.internal.example.com:9092` (private DNS)

### Environment Variables

Create a `.env` file (see `.env.example`):

```env
# Kafka Configuration
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_TOPIC=load-test
KAFKA_COMPRESSION_TYPE=gzip
KAFKA_ACKS=1
PRODUCER_POOL_SIZE=5

# Server Configuration
HOST=0.0.0.0
PORT=8000
```

**Note:** Port 8080 is typically reserved for ArgoCD. The docker-compose file maps the application to port 8085 externally.

### Load Test Parameters

| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| Message Count | Total messages to send | 1 - 10,000,000 | 1,000 |
| Message Rate | Messages per second | 1 - 100,000 | 100 |
| Topic | Kafka topic name | - | load-test |
| Payload Size | Message size in bytes | 1 - 1,048,576 | 100 |
| Test Name | Optional identifier | - | - |

## Quick Test Presets

- **Small**: 1,000 messages @ 100/s (10 seconds)
- **Medium**: 10,000 messages @ 1,000/s (10 seconds)
- **Large**: 100,000 messages @ 5,000/s (20 seconds)
- **Stress**: 1,000,000 messages @ 10,000/s (100 seconds)

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

- `GET /health` - Health check
- `GET /api/status` - Current test status
- `POST /api/start` - Start load test
- `POST /api/stop` - Stop current test
- `WS /ws/status` - WebSocket for real-time updates
- `GET /metrics` - Prometheus metrics

## Kubernetes Deployment

### Prerequisites

- Kubernetes cluster with existing Kafka installation
- `kubectl` configured
- Kustomize 4.0+

### Deploy to Kubernetes

1. **Build and push Docker image**:
```bash
docker build -t <your-registry>/kafka-load-tester:latest .
docker push <your-registry>/kafka-load-tester:latest
```

2. **Update image in deployment**:
Edit `k8s/base/deployment.yaml` and update the image field.

3. **Deploy using Kustomize**:

For dev environment:
```bash
kubectl apply -k k8s/overlays/dev
```

For production:
```bash
kubectl apply -k k8s/overlays/prod
```

### Verify Deployment

```bash
# Check pods
kubectl get pods -n kafka -l app=kafka-load-tester

# Check service
kubectl get svc -n kafka -l app=kafka-load-tester

# View logs
kubectl logs -n kafka -l app=kafka-load-tester -f

# Port forward for testing
kubectl port-forward -n kafka svc/prod-kafka-load-tester 8000:80
```

### Access in Kubernetes

**Development** (ClusterIP):
```bash
kubectl port-forward -n kafka svc/dev-kafka-load-tester 8000:8000
```

**Production** (LoadBalancer):
Get the external IP:
```bash
kubectl get svc -n kafka prod-kafka-load-tester
```

## Monitoring with Prometheus

The application exposes Prometheus metrics on `/metrics`:

### Available Metrics

**Counters:**
- `kafka_load_tester_messages_sent_total` - Total messages sent
- `kafka_load_tester_messages_failed_total` - Total failed messages
- `kafka_load_tester_tests_started_total` - Total tests started
- `kafka_load_tester_tests_completed_total` - Total tests completed

**Gauges:**
- `kafka_load_tester_active_test` - Whether a test is running (1/0)
- `kafka_load_tester_current_rate` - Current message rate (msg/s)
- `kafka_load_tester_progress_percent` - Test progress (0-100)

**Histograms:**
- `kafka_load_tester_message_send_duration_seconds` - Message send latency
- `kafka_load_tester_test_duration_seconds` - Test duration

### Prometheus ServiceMonitor

The deployment includes annotations for Prometheus auto-discovery:
```yaml
annotations:
  prometheus.io/scrape: "true"
  prometheus.io/port: "8000"
  prometheus.io/path: "/metrics"
```

## Development

### Local Development without Docker

1. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
```

2. **Install dependencies**:
```bash
cd app
pip install -r requirements.txt
```

3. **Start Kafka locally** (using Docker):
```bash
docker-compose up -d kafka kafka-ui
```

4. **Run the application**:
```bash
python main.py
```

5. **Access**:
- Application: http://localhost:8000
- Kafka UI: http://localhost:8080

### Project Structure

```
kafka-load-tester/
├── app/
│   ├── main.py              # FastAPI application
│   ├── producer.py          # Kafka producer with connection pool
│   ├── config.py            # Configuration management
│   ├── models.py            # Pydantic models
│   ├── metrics.py           # Prometheus metrics
│   ├── static/
│   │   ├── index.html       # Web UI
│   │   ├── app.js           # Frontend JavaScript
│   │   └── style.css        # Styles
│   └── requirements.txt     # Python dependencies
├── k8s/
│   ├── base/                # Base Kubernetes manifests
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   ├── configmap.yaml
│   │   └── kustomization.yaml
│   └── overlays/            # Environment-specific configs
│       ├── dev/
│       └── prod/
├── Dockerfile               # Multi-stage Docker build
├── docker-compose.yml       # Local development stack
├── .env.example             # Environment variables template
└── README.md
```

## Troubleshooting

### Application won't connect to Kafka

1. Check Kafka is running:
```bash
docker-compose ps kafka
```

2. Verify Kafka bootstrap servers:
```bash
# For Docker Compose
KAFKA_BOOTSTRAP_SERVERS=kafka:29092

# For local development
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# For Kubernetes
KAFKA_BOOTSTRAP_SERVERS=kafka-kafka-bootstrap.kafka.svc:9092
```

3. Check application logs:
```bash
# Docker
docker-compose logs load-tester

# Kubernetes
kubectl logs -n kafka -l app=kafka-load-tester
```

### Messages not appearing in Kafka

1. Verify topic exists:
- Open Kafka UI (http://localhost:8080)
- Check Topics section

2. Check auto-create is enabled:
```bash
# Should be enabled in docker-compose.yml
KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'true'
```

3. Check for errors in load tester logs

### High memory usage

Reduce `PRODUCER_POOL_SIZE` in environment configuration:
```env
PRODUCER_POOL_SIZE=3
```

### Slow message sending

1. Increase producer pool size:
```env
PRODUCER_POOL_SIZE=10
```

2. Adjust batch settings:
```env
KAFKA_LINGER_MS=5
KAFKA_BATCH_SIZE=32768
```

## ArgoCD Integration

To deploy via ArgoCD, create an Application manifest in your devops repository:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: kafka-load-tester
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/<username>/kafka-load-tester.git
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

1. **High throughput** (>10K msg/s):
   - Increase `PRODUCER_POOL_SIZE` to 10-20
   - Use compression: `KAFKA_COMPRESSION_TYPE=snappy`
   - Increase `KAFKA_BATCH_SIZE` to 32768 or higher
   - Set `KAFKA_ACKS=1` (not `all`)

2. **Low latency**:
   - Decrease `KAFKA_LINGER_MS` to 0-1
   - Reduce `PRODUCER_POOL_SIZE` to 1-3
   - Set `KAFKA_ACKS=1`

3. **Reliability**:
   - Set `KAFKA_ACKS=all`
   - Increase `KAFKA_LINGER_MS` to 10-50
   - Use `KAFKA_COMPRESSION_TYPE=gzip` or `lz4`

## License

MIT

## Contributing

Contributions welcome! Please open an issue or submit a pull request.

## Support

For issues and questions:
- GitHub Issues: <repository-url>/issues
- Documentation: This README

## Roadmap

- [ ] Consumer implementation for message verification
- [ ] Support for multiple topics simultaneously
- [ ] Message schema validation
- [ ] Historical test results storage
- [ ] Advanced metrics and dashboards
- [ ] Load test scheduling
- [ ] SASL/SSL authentication support
