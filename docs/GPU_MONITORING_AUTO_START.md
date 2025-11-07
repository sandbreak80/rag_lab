# GPU Monitoring - Auto-Start Configuration

## ✅ GPU Monitoring Now Starts Automatically

As of commit `96ef872`, GPU monitoring via NVIDIA DCGM Exporter starts automatically on all GPU-enabled AWS instances.

---

## 📊 What Gets Monitored

The `dcgm-exporter` service collects comprehensive GPU metrics:

- **GPU Utilization** - Percentage of GPU compute in use
- **GPU Temperature** - Current thermal state (°C)
- **GPU Memory Usage** - VRAM consumption
- **GPU Memory Bandwidth** - Memory copy utilization
- **Power Consumption** - Current power draw
- **Clock Speeds** - SM and memory clock frequencies
- **ECC Errors** - Error correction statistics
- **NVLink Stats** - Multi-GPU interconnect metrics

---

## 🔧 How It Works

### Cloud-Init Scripts (v9 & v10)

Both cloud-init scripts now include the `--profile gpu` flag:

```bash
# Before
docker compose up -d

# After  
docker compose --profile gpu up -d
```

This automatically starts:
- All standard services (Ollama, API Gateway, Frontend, etc.)
- GPU monitoring (`dcgm-exporter`) on port 9400

### Deployment Script

The `deploy-to-aws.sh` script uses `--profile gpu` when deploying all services:

```bash
if [ "$SERVICE" = "all" ]; then
    docker compose --profile gpu up -d
fi
```

---

## 🎯 Configuration Details

### docker-compose.yml

The `dcgm-exporter` service retains the optional profile for portability:

```yaml
dcgm-exporter:
  image: nvcr.io/nvidia/k8s/dcgm-exporter:3.1.8-3.1.5-ubuntu20.04
  profiles: ["gpu"]  # Optional on non-GPU systems
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

**Why keep the profile?**
- ✅ Non-GPU systems can use docker-compose.yml without errors
- ✅ GPU systems automatically enable it via deployment scripts
- ✅ Developers can opt-in locally with `--profile gpu`

### Metrics Endpoint

DCGM Exporter exposes metrics at:
- **Internal:** `http://dcgm-exporter:9400/metrics`
- **External:** `http://<instance-ip>:9400/metrics` (if port 9400 is open)

Prometheus scrapes these metrics every 10 seconds.

---

## 📈 Grafana Dashboard Integration

GPU metrics appear in the "RAG Lab - System Overview" dashboard at:

**http://54.190.74.93:3000/monitoring**

Panels displaying GPU data:
1. **GPU Utilization %** - Real-time compute usage
2. **GPU Memory Usage %** - VRAM consumption over time
3. **GPU Temperature (°C)** - Thermal monitoring with thresholds

---

## 🚀 Deployment Scenarios

### New Instance Launch

When launching a new GPU instance with `aws-launch-rag-lab.sh`:

```bash
./aws/scripts/aws-launch-rag-lab.sh
```

GPU monitoring starts automatically via cloud-init.

### Existing Instance Update

To enable GPU monitoring on a running instance:

```bash
# Option 1: Use deployment script
./scripts/deploy-to-aws.sh

# Option 2: Manual SSH
ssh ubuntu@<instance-ip>
cd /home/ubuntu/rag_lab
docker compose --profile gpu up -d dcgm-exporter
```

### Local Development

For local testing with GPU:

```bash
docker compose --profile gpu up -d
```

Without GPU (default):

```bash
docker compose up -d
```

---

## 🔍 Verification

Check if GPU monitoring is running:

```bash
# Check container status
docker ps | grep dcgm

# View GPU metrics
curl http://localhost:9400/metrics | grep DCGM_FI_DEV_GPU_UTIL

# Check Prometheus target
curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.labels.job=="dcgm-exporter")'

# View NVIDIA SMI
nvidia-smi
```

---

## 🐛 Troubleshooting

### GPU Not Detected

```bash
# Check NVIDIA driver
nvidia-smi

# Check NVIDIA container runtime
docker run --rm --gpus all nvidia/cuda:11.0-base nvidia-smi
```

### DCGM Exporter Not Starting

```bash
# View logs
docker logs rag-dcgm-exporter

# Restart with GPU profile
docker compose --profile gpu up -d dcgm-exporter
```

### No Metrics in Grafana

1. **Wait 30 seconds** - Prometheus needs time to scrape first metrics
2. **Check Prometheus** - Visit http://localhost:9090
3. **Query manually** - Run query: `DCGM_FI_DEV_GPU_UTIL`
4. **Verify target** - Check Prometheus targets page

---

## 📝 Files Modified

- `aws/cloud-init/cloud-init-rag-lab-v9.yaml`
- `aws/cloud-init/cloud-init-rag-lab-v10.yaml`
- `scripts/deploy-to-aws.sh`

---

## 🔗 Related Documentation

- [NVIDIA DCGM Documentation](https://docs.nvidia.com/datacenter/dcgm/latest/)
- [DCGM Exporter GitHub](https://github.com/NVIDIA/dcgm-exporter)
- [Prometheus Configuration](../monitoring/prometheus/prometheus.yml)
- [Grafana Dashboard](../monitoring/grafana/dashboards/rag-lab-overview.json)

---

## ✅ Summary

GPU monitoring is now:
- ✅ **Automatic** on GPU instances
- ✅ **Integrated** with Prometheus + Grafana
- ✅ **Visible** in monitoring dashboard
- ✅ **Optional** on non-GPU systems
- ✅ **Documented** for manual control

No manual intervention required! 🎉

