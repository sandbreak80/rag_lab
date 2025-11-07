# RAG Lab Monitoring Stack

Professional monitoring using **Prometheus + Grafana** for real-time metrics, historical data, and beautiful dashboards.

## 🎯 What's Monitored

### 1. **Container Metrics** (via cAdvisor)
- CPU usage per container
- Memory usage per container
- Network I/O (RX/TX)
- Disk I/O
- Container restarts
- Container uptime

### 2. **GPU Metrics** (via NVIDIA DCGM Exporter)
- GPU utilization %
- GPU memory usage
- GPU temperature
- Power consumption
- SM/Memory clock speeds

### 3. **Service Metrics** (via Prometheus exporters)
- Request count
- Response latency (histograms)
- Error rates
- Active connections
- Custom metrics (tokens, cache hits, etc.)

## 🚀 Quick Start

### Start Monitoring Stack

```bash
# Start all services including monitoring (without GPU)
docker compose up -d

# OR: Start with GPU monitoring (requires NVIDIA GPU)
docker compose --profile gpu up -d

# Check monitoring services are running
docker compose ps prometheus grafana cadvisor

# If using GPU profile, also check:
docker compose ps dcgm-exporter
```

### Access Dashboards

- **Grafana**: http://localhost:3001
  - Username: `admin`
  - Password: `admin`
  - Pre-loaded dashboards in "RAG Lab" folder

- **Prometheus**: http://localhost:9090
  - Query interface for advanced users
  - View targets: http://localhost:9090/targets

- **cAdvisor**: http://localhost:9080
  - Raw container metrics

## 📊 Grafana Dashboards

### RAG Lab - System Overview
- Service health status
- Container CPU/Memory usage
- Network I/O
- GPU utilization, memory, temperature

### Import Community Dashboards (Optional)

1. Go to Grafana → Dashboards → Import
2. Enter dashboard ID:
   - **193** - Docker Container & Host Metrics
   - **12239** - NVIDIA DCGM Exporter Dashboard
   - **1860** - Node Exporter Full

## 🔧 Adding Metrics to Your Service

### Step 1: Install prometheus_client

Add to your service's requirements or Dockerfile:

```bash
pip install prometheus-client
```

### Step 2: Use ServiceMetrics (Auto Prometheus Support)

```python
from services.common.metrics import ServiceMetrics

# Initialize metrics
metrics = ServiceMetrics("my-service", enable_prometheus=True)

# Use metrics in your code
metrics.increment('requests_total')
metrics.record_time('api_latency_ms', 150.5)
metrics.set_gauge('active_connections', 42)
```

### Step 3: Add /metrics Endpoint

```python
from flask import Flask, Response

app = Flask(__name__)
metrics = ServiceMetrics("my-service")

@app.route('/metrics')
def prometheus_metrics():
    """Prometheus metrics endpoint"""
    metrics_data, content_type = metrics.get_prometheus_metrics()
    return Response(metrics_data, mimetype=content_type)
```

### Step 4: Update Prometheus Config

Add your service to `monitoring/prometheus/prometheus.yml`:

```yaml
  - job_name: 'my-service'
    scrape_interval: 15s
    static_configs:
      - targets: ['my-service:8000']
        labels:
          service: 'my-service'
          type: 'application'
    metrics_path: '/metrics'
```

### Step 5: Reload Prometheus

```bash
# Send reload signal (if web.enable-lifecycle is set)
curl -X POST http://localhost:9090/-/reload

# OR restart Prometheus
docker compose restart prometheus
```

## 📈 Querying Metrics

### Prometheus Query Examples

```promql
# Service uptime
up{job="api-gateway"}

# Container CPU usage
rate(container_cpu_usage_seconds_total{name="rag-chat-service"}[5m])

# GPU utilization
DCGM_FI_DEV_GPU_UTIL

# Request rate
rate(my_service_requests_total[5m])

# 95th percentile latency
histogram_quantile(0.95, rate(my_service_api_latency_ms_seconds_bucket[5m]))
```

## 🔔 Alerting (Optional)

Alerts are defined in `monitoring/prometheus/alerts.yml`.

### Example Alert

```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High error rate on {{ $labels.service }}"
```

### Configure Alertmanager (Optional)

1. Add alertmanager service to docker-compose.yml
2. Configure notification channels (email, Slack, PagerDuty)
3. Update prometheus.yml to use alertmanager

## 🛠️ Troubleshooting

### Prometheus Not Scraping Targets

1. Check target status: http://localhost:9090/targets
2. Verify service is exposing /metrics endpoint:
   ```bash
   curl http://localhost:8000/metrics
   ```
3. Check Prometheus logs:
   ```bash
   docker compose logs prometheus
   ```

### Grafana Dashboard Not Showing Data

1. Verify Prometheus datasource is connected:
   - Grafana → Configuration → Data Sources
   - Test connection should be green
2. Check time range (default: last 15 minutes)
3. Verify metrics exist in Prometheus:
   - Go to Prometheus → Graph
   - Query: `up`

### GPU Metrics Not Available

1. Ensure NVIDIA drivers are installed
2. Verify nvidia-docker runtime is configured
3. Check DCGM exporter logs:
   ```bash
   docker compose logs dcgm-exporter
   ```

### Metrics Not Persisting

- Prometheus stores data in `prometheus-data` volume
- Retention period: 30 days (configurable in prometheus.yml)
- Check disk space:
  ```bash
  docker volume inspect rag_lab_prometheus-data
  ```

## 📊 Data Retention

- **Prometheus**: 30 days (configurable)
- **Grafana**: Dashboards persist in `grafana-data` volume

### Change Retention Period

Edit `docker-compose.yml`:

```yaml
prometheus:
  command:
    - '--storage.tsdb.retention.time=60d'  # Change to 60 days
```

## 🔒 Security

### Production Recommendations

1. **Disable anonymous access**:
   ```yaml
   grafana:
     environment:
       - GF_AUTH_ANONYMOUS_ENABLED=false
   ```

2. **Change default password**:
   ```yaml
   - GF_SECURITY_ADMIN_PASSWORD=<strong-password>
   ```

3. **Enable HTTPS**:
   - Configure Nginx reverse proxy
   - Add SSL certificates

4. **Restrict access**:
   - Use firewall rules to limit access to monitoring ports
   - Use Docker network isolation

## 📚 Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [PromQL Cheat Sheet](https://promlabs.com/promql-cheat-sheet/)

## 🎓 Next Steps

1. ✅ Explore pre-built dashboards in Grafana
2. ✅ Add custom metrics to your services
3. ✅ Create custom dashboards for your use case
4. ✅ Set up alerting for critical conditions
5. ✅ Export dashboards for backup/sharing

