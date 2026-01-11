# Context: Kafka Load Tester Application

## Overview

This document provides context for building a Kafka load testing application that will be deployed to an existing AWS EKS infrastructure managed via GitOps (ArgoCD).

## Existing Infrastructure (devops_demo repository)

### Current Setup

**AWS Infrastructure:**
- **Region**: ca-west-1 (Calgary)
- **EKS Cluster**: Kubernetes v1.34
- **Node Groups**: 2x t3.large nodes (2 vCPU, 8Gi RAM each)
- **VPC**: 10.0.0.0/16 with public/private subnets across 3 AZs
- **GitOps**: ArgoCD managing all applications via App-of-Apps pattern

**Deployed Services:**

| Service | Description | Access |
|---------|-------------|--------|
| ArgoCD | GitOps continuous delivery | LoadBalancer (HTTP) |
| Prometheus | Metrics collection | Internal (9090) |
| Grafana | Metrics visualization | Port-forward 3000 |
| Kafka (Strimzi) | Event streaming (KRaft mode, no Zookeeper) | Internal bootstrap: kafka-kafka-bootstrap.kafka.svc:9092 |
| Kafka UI | Web management interface | LoadBalancer (HTTP) |

**Kafka Configuration:**
- **Version**: 4.0.0
- **Mode**: KRaft (no Zookeeper required)
- **Brokers**: 1 replica (combined controller+broker)
- **Storage**: Ephemeral (no persistent volumes)
- **Replication Factor**: 1
- **Auto-create Topics**: Enabled
- **Listeners**:
  - Plain text: port 9092 (internal)
  - TLS: port 9093 (internal)
- **Operator**: Strimzi 0.49.1 (CNCF project)
- **Bootstrap Server**: `kafka-kafka-bootstrap.kafka.svc.cluster.local:9092`
  - Short form within kafka namespace: `kafka-kafka-bootstrap:9092`

### ArgoCD Deployment Pattern

Applications are deployed using the **App-of-Apps pattern**:

```
Root Application (watches helm/apps/)
    │
    ├── kafka-operator (Strimzi operator)
    ├── kafka-cluster (Kafka CRD)
    ├── kafka-ui (Web interface)
    ├── monitoring (Prometheus + Grafana)
    └── [your-app-here] (future)
```

**How ArgoCD works:**
1. ArgoCD watches `helm/apps/` directory in the devops_demo repository
2. New Application manifests in `helm/apps/` are automatically detected
3. ArgoCD syncs applications from their specified source repositories
4. Auto-sync and self-heal are enabled

**Example ArgoCD Application Manifest:**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: kafka-load-tester
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/[username]/kafka-load-tester.git
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

## Application Requirements (kafka-load-tester repository)

### Purpose

Build a **Kafka Load Testing Application** that:
- Generates configurable load on the Kafka cluster
- Allows testing Kafka scaling and performance
- Runs in multiple environments (local Docker, Kubernetes)
- Demonstrates real-world application deployment patterns

### Functional Requirements

**Core Features:**
1. **Web UI** - Simple interface to configure and trigger load tests
2. **Producer** - Send messages to Kafka at configurable rates
3. **Consumer** (optional) - Consume and verify messages
4. **Metrics** - Expose metrics for Prometheus scraping
5. **Configuration** - Environment-based config (dev/prod)

**UI Controls:**
- Number of messages to send (e.g., 1000, 10000, 1000000)
- Message rate (messages/second)
- Target topic name
- Message payload size
- Start/Stop controls
- Real-time progress display

**Message Format Example:**
```json
{
  "id": "msg-12345",
  "timestamp": "2026-01-11T12:34:56Z",
  "sequence": 12345,
  "payload": "test data...",
  "metadata": {
    "producer": "load-tester-pod-xyz",
    "test_run": "run-abc123"
  }
}
```

### Technical Requirements

**Technology Stack:**
- **Language**: Python 3.11+
- **Web Framework**: FastAPI (modern, async, auto-docs)
- **Kafka Client**: confluent-kafka-python or aiokafka
- **Frontend**: Simple HTML/CSS/JavaScript (or React if preferred)
- **Container**: Docker with multi-stage build
- **Orchestration**: Kubernetes manifests with Kustomize

**Container Requirements:**
- Base image: `python:3.11-slim`
- Multi-stage build for smaller image size
- Non-root user for security
- Health check endpoints
- Graceful shutdown handling

**Kubernetes Requirements:**
- Deployment with configurable replicas
- Service (ClusterIP or LoadBalancer)
- ConfigMap for environment-specific settings
- Liveness and readiness probes
- Resource requests/limits
- Labels for Prometheus scraping

### Multi-Environment Architecture

**Directory Structure:**
```
kafka-load-tester/
├── app/
│   ├── main.py              # FastAPI application
│   ├── kafka_producer.py    # Kafka producer logic
│   ├── kafka_consumer.py    # Kafka consumer logic (optional)
│   ├── config.py            # Configuration management
│   ├── static/              # HTML/CSS/JS frontend
│   └── requirements.txt     # Python dependencies
├── k8s/
│   ├── base/                # Base Kubernetes manifests
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   └── overlays/            # Environment-specific configs
│       ├── dev/
│       │   └── kustomization.yaml
│       └── prod/
│           └── kustomization.yaml
├── Dockerfile
├── docker-compose.yml       # Local development
├── .env.example
├── README.md
└── .gitignore
```

**Environment Configurations:**

| Setting | Local (Docker) | Dev (K8s) | Prod (K8s) |
|---------|---------------|-----------|------------|
| Kafka Bootstrap | localhost:9092 | kafka-kafka-bootstrap.kafka.svc:9092 | kafka-kafka-bootstrap.kafka.svc:9092 |
| Replicas | 1 | 1 | 2-3 |
| Message Rate | 10/sec | 100/sec | 1000/sec |
| Resource Requests | N/A | 100m CPU, 128Mi RAM | 200m CPU, 256Mi RAM |

### Local Development with Docker Compose

**Purpose**: Allow developers to test the application locally without Kubernetes.

**docker-compose.yml Features:**
- Local Kafka container (Confluent or Strimzi image)
- Application container
- Shared network
- Volume mounts for hot-reload development
- Environment variables for configuration

### Deployment Flow

```
Developer Workflow:
1. Clone kafka-load-tester repository
2. Make code changes
3. Test locally with docker-compose up
4. Commit and push to GitHub
5. (Optional) GitHub Actions builds and pushes Docker image
6. ArgoCD detects changes in k8s/overlays/prod
7. ArgoCD syncs to EKS cluster
8. Application deploys to kafka namespace
9. Monitor via Grafana/Prometheus
```

### Integration with Existing Infrastructure

**Namespace**: `kafka` (same namespace as Kafka cluster)

**Service Discovery**:
- Application connects to: `kafka-kafka-bootstrap:9092` (short DNS name within namespace)
- Or: `kafka-kafka-bootstrap.kafka.svc.cluster.local:9092` (full FQDN)

**Monitoring Integration**:
- Expose Prometheus metrics on `/metrics` endpoint
- Use standard labels for ServiceMonitor discovery
- Metrics to track:
  - Messages sent/received
  - Message rate
  - Latency (p50, p95, p99)
  - Errors/retries

**ArgoCD Integration**:
- Create `kafka-load-tester-app.yaml` in devops_demo's `helm/apps/` directory
- Points to kafka-load-tester repository
- Uses Kustomize for environment overlays
- Auto-sync enabled

### Success Criteria

**Application must:**
1. ✅ Run locally with Docker Compose
2. ✅ Deploy to Kubernetes via ArgoCD
3. ✅ Successfully send messages to Kafka
4. ✅ Expose metrics for Prometheus
5. ✅ Provide web UI for load testing
6. ✅ Handle graceful shutdown
7. ✅ Support environment-specific configurations

**Testing scenarios:**
- Send 1,000 messages at 100/sec
- Send 10,000 messages at 1,000/sec
- Send 1,000,000 messages at 10,000/sec (scale test)
- Verify messages in Kafka UI
- Monitor metrics in Grafana

### Cost Considerations

**Network Traffic:**
- Application → Kafka: Internal cluster traffic (FREE)
- User → Application UI: Through LoadBalancer (small cost)
- No NAT Gateway usage for Kafka communication

**Resource Usage:**
- CPU: 100-200m per replica
- Memory: 128-256Mi per replica
- Fits comfortably on existing t3.large nodes

### Security Notes

- No authentication/authorization required (dev environment)
- Plain text Kafka connection (not TLS)
- LoadBalancer exposes UI publicly (acceptable for demo)
- Future enhancement: Add basic auth or integrate with AWS IAM

### References

**Kafka Connection Details:**
- Bootstrap servers: `kafka-kafka-bootstrap.kafka.svc.cluster.local:9092`
- Protocol: PLAINTEXT (no TLS)
- Auto-create topics: Enabled
- Default partitions: 1
- Default replication: 1

**Existing Monitoring:**
- Prometheus: `prometheus-kube-prometheus-prometheus.monitoring.svc:9090`
- Grafana: `prometheus-grafana.monitoring.svc:80`

**Container Registry:**
- Use Docker Hub or GitHub Container Registry
- Image naming: `[username]/kafka-load-tester:latest`

## Next Steps

1. Create kafka-load-tester repository
2. Implement FastAPI application with Kafka producer
3. Create Dockerfile and docker-compose.yml
4. Create Kubernetes manifests with Kustomize overlays
5. Test locally with Docker Compose
6. Create ArgoCD Application manifest in devops_demo
7. Deploy to EKS and verify
8. Test load generation and monitor in Kafka UI
9. Document in README.md

## Questions for Implementation

- Should the consumer be included in the same app or separate?
- Preferred frontend: Simple HTML or React?
- Container registry preference: Docker Hub or GHCR?
- Should we add GitHub Actions for CI/CD?
- Message payload: JSON or binary?
- Support for batch sending or individual messages?
