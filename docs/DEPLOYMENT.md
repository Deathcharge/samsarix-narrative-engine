# Helix Narrative Engine: Deployment Guide

**Production deployment strategies and best practices**

---

## Table of Contents

1. [Docker Deployment](#docker-deployment)
2. [Kubernetes Deployment](#kubernetes-deployment)
3. [Cloud Platforms](#cloud-platforms)
4. [Environment Configuration](#environment-configuration)
5. [Monitoring and Logging](#monitoring-and-logging)
6. [Security Best Practices](#security-best-practices)
7. [Performance Tuning](#performance-tuning)
8. [Troubleshooting](#troubleshooting)

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Install package
RUN pip install -e .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["python", "-m", "helix_narrative_engine.server"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  narrative-engine:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - LOG_LEVEL=INFO
      - CACHE_ENABLED=true
      - CACHE_TTL=3600
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    networks:
      - helix-network

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    networks:
      - helix-network

networks:
  helix-network:
    driver: bridge
```

### Building and Running

```bash
# Build image
docker build -t helix-narrative-engine:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -e OPENAI_API_KEY=sk-... \
  -e ANTHROPIC_API_KEY=sk-ant-... \
  --name narrative-engine \
  helix-narrative-engine:latest

# View logs
docker logs -f narrative-engine

# Stop container
docker stop narrative-engine
```

---

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: helix-narrative-engine
  labels:
    app: narrative-engine
spec:
  replicas: 3
  selector:
    matchLabels:
      app: narrative-engine
  template:
    metadata:
      labels:
        app: narrative-engine
    spec:
      containers:
      - name: narrative-engine
        image: helix-narrative-engine:latest
        imagePullPolicy: Always
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: openai-key
        - name: ANTHROPIC_API_KEY
          valueFrom:
            secretKeyRef:
              name: llm-secrets
              key: anthropic-key
        - name: LOG_LEVEL
          value: "INFO"
        - name: CACHE_ENABLED
          value: "true"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
```

### Service Manifest

```yaml
apiVersion: v1
kind: Service
metadata:
  name: helix-narrative-engine
spec:
  selector:
    app: narrative-engine
  ports:
  - port: 80
    targetPort: 8000
    protocol: TCP
  type: LoadBalancer
```

### Secrets Configuration

```bash
# Create secrets
kubectl create secret generic llm-secrets \
  --from-literal=openai-key=sk-... \
  --from-literal=anthropic-key=sk-ant-... \
  --from-literal=gemini-key=...

# Apply deployment
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml

# Check status
kubectl get pods
kubectl get services
```

---

## Cloud Platforms

### AWS Lambda

```python
# handler.py
import json
from helix_narrative_engine import NarrativeEngine

engine = NarrativeEngine()

def lambda_handler(event, context):
    """AWS Lambda handler."""
    try:
        body = json.loads(event['body'])
        prompt = body['prompt']
        
        result = asyncio.run(engine.generate(prompt))
        
        return {
            'statusCode': 200,
            'body': json.dumps(result)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Google Cloud Run

```bash
# Deploy to Cloud Run
gcloud run deploy helix-narrative-engine \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars OPENAI_API_KEY=sk-... \
  --memory 2Gi \
  --cpu 2 \
  --timeout 3600
```

### Azure Container Instances

```bash
# Create container group
az container create \
  --resource-group myResourceGroup \
  --name helix-narrative-engine \
  --image helix-narrative-engine:latest \
  --environment-variables \
    OPENAI_API_KEY=sk-... \
    ANTHROPIC_API_KEY=sk-ant-... \
  --cpu 2 \
  --memory 2
```

---

## Environment Configuration

### Production Configuration

```bash
# .env.production
ENVIRONMENT=production
LOG_LEVEL=WARNING
DEBUG=false

# LLM Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...

# Performance
CACHE_ENABLED=true
CACHE_TTL=3600
CACHE_MAX_SIZE=10000
BATCH_SIZE=10

# Monitoring
ENABLE_METRICS=true
METRICS_PORT=9090
ENABLE_TRACING=true

# Timeouts
REQUEST_TIMEOUT=60
GENERATION_TIMEOUT=120

# Quality
QUALITY_THRESHOLD=0.85
MAX_RETRIES=3
```

### Staging Configuration

```bash
# .env.staging
ENVIRONMENT=staging
LOG_LEVEL=INFO
DEBUG=true

# LLM Configuration (test keys)
OPENAI_API_KEY=sk-test-...
ANTHROPIC_API_KEY=sk-ant-test-...

# Performance
CACHE_ENABLED=true
CACHE_TTL=1800

# Monitoring
ENABLE_METRICS=true
ENABLE_TRACING=true
```

---

## Monitoring and Logging

### Logging Configuration

```python
import logging
import logging.handlers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('narrative-engine.log'),
        logging.handlers.RotatingFileHandler(
            'narrative-engine.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
```

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram, Gauge

# Define metrics
generation_counter = Counter(
    'narrative_generations_total',
    'Total narrative generations',
    ['agent', 'llm']
)

generation_duration = Histogram(
    'narrative_generation_duration_seconds',
    'Generation duration in seconds'
)

cache_hits = Gauge(
    'cache_hits_total',
    'Total cache hits'
)

quality_score = Gauge(
    'narrative_quality_score',
    'Average quality score'
)
```

### Health Endpoints

```python
@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/ready")
async def ready():
    """Readiness check endpoint."""
    try:
        # Check LLM providers
        providers = router.get_available_providers()
        return {
            "ready": len(providers) > 0,
            "providers": providers
        }
    except Exception as e:
        return {"ready": False, "error": str(e)}

@app.get("/metrics")
async def metrics():
    """Metrics endpoint."""
    return {
        "cache_stats": cache.get_stats(),
        "monitoring_stats": monitor.get_stats()
    }
```

---

## Security Best Practices

### API Key Management

```python
# Use environment variables
import os

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Never hardcode keys
# Never commit keys to version control
# Rotate keys regularly
```

### Input Validation

```python
from pydantic import BaseModel, Field

class GenerationRequest(BaseModel):
    prompt: str = Field(..., max_length=10000)
    style: str = Field(default="balanced", max_length=50)
    tone: str = Field(default="neutral", max_length=50)
    
    class Config:
        validate_assignment = True
```

### Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@app.post("/generate")
@limiter.limit("10/minute")
async def generate(request: GenerationRequest):
    """Rate-limited generation endpoint."""
    result = await engine.generate(request.prompt)
    return result
```

### HTTPS/TLS

```bash
# Use reverse proxy with TLS
# Example with nginx

server {
    listen 443 ssl http2;
    server_name api.example.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Performance Tuning

### Connection Pooling

```python
import aiohttp

# Create session with connection pool
connector = aiohttp.TCPConnector(
    limit=100,
    limit_per_host=30,
    ttl_dns_cache=300
)
session = aiohttp.ClientSession(connector=connector)
```

### Caching Strategy

```python
# Enable caching for frequently used prompts
engine = NarrativeEngine(
    cache_enabled=True,
    cache_ttl=3600,
    cache_max_size=10000,
    cache_eviction_policy="lru"
)
```

### Batch Processing

```python
# Process multiple prompts efficiently
prompts = [
    "Prompt 1",
    "Prompt 2",
    "Prompt 3"
]

results = await engine.generate_batch(
    prompts,
    batch_size=10
)
```

---

## Troubleshooting

### High Memory Usage

**Problem**: Container memory usage increasing over time

**Solution**:
```python
# Enable cache eviction
engine = NarrativeEngine(
    cache_max_size=5000,  # Reduce cache size
    cache_eviction_policy="lru"  # Use LRU eviction
)

# Monitor memory
import psutil
process = psutil.Process()
print(f"Memory: {process.memory_info().rss / 1024 / 1024:.2f}MB")
```

### Slow Response Times

**Problem**: Generation taking too long

**Solution**:
```python
# Use fast preset
engine.set_preset_mode("fast")

# Reduce max_tokens
engine = NarrativeEngine(max_tokens=1000)

# Enable caching
engine = NarrativeEngine(cache_enabled=True)
```

### API Rate Limiting

**Problem**: Hitting provider rate limits

**Solution**:
```python
# Implement exponential backoff
retry_policy = RetryPolicy(
    max_attempts=5,
    initial_delay=1.0,
    max_delay=60.0
)

result = await retry_policy.execute(
    engine.generate,
    prompt
)
```

### Connection Errors

**Problem**: Intermittent connection failures

**Solution**:
```python
# Use circuit breaker
circuit_breaker = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60.0
)

result = await circuit_breaker.call(
    engine.generate,
    prompt
)
```

---

## Monitoring Checklist

- [ ] Health checks configured
- [ ] Metrics collection enabled
- [ ] Logging configured with rotation
- [ ] Alerts set up for errors
- [ ] Performance baselines established
- [ ] Cost monitoring enabled
- [ ] Security audit completed
- [ ] Load testing performed
- [ ] Disaster recovery plan documented
- [ ] Backup strategy implemented

---

**Last Updated**: April 2026  
**Version**: 1.0.0  
**Author**: Manus AI
