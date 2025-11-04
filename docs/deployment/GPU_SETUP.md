# 🚀 NVIDIA GPU Setup & Verification

**Guide for enabling GPU acceleration with Ollama on Ubuntu Server**

---

## ✅ Prerequisites

Your Ubuntu server should have:
- ✅ NVIDIA GPU (any CUDA-capable GPU)
- ✅ NVIDIA drivers installed
- ✅ nvidia-docker2 or nvidia-container-toolkit installed
- ✅ Docker Compose v1.28+ (for `deploy.resources` support)

---

## 🔍 Step 1: Verify NVIDIA Drivers

```bash
# Check NVIDIA driver is installed
nvidia-smi
```

**Expected output:**
```
+-----------------------------------------------------------------------------+
| NVIDIA-SMI 525.xx.xx    Driver Version: 525.xx.xx    CUDA Version: 12.x   |
|-------------------------------+----------------------+----------------------+
| GPU  Name        Persistence-M| Bus-Id        Disp.A | Volatile Uncorr. ECC |
| Fan  Temp  Perf  Pwr:Usage/Cap|         Memory-Usage | GPU-Util  Compute M. |
|===============================+======================+======================|
|   0  Tesla T4            Off  | 00000000:00:1E.0 Off |                    0 |
| N/A   45C    P0    27W /  70W |      0MiB / 15360MiB |      0%      Default |
+-------------------------------+----------------------+----------------------+
```

If this fails, install NVIDIA drivers:
```bash
# Ubuntu 20.04/22.04
sudo apt update
sudo apt install nvidia-driver-525
sudo reboot
```

---

## 🐳 Step 2: Verify Docker GPU Support

```bash
# Check nvidia-container-toolkit is installed
dpkg -l | grep nvidia-container-toolkit
```

If not installed:
```bash
# Add NVIDIA Docker repository
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list

# Install nvidia-container-toolkit
sudo apt update
sudo apt install -y nvidia-container-toolkit

# Restart Docker
sudo systemctl restart docker
```

---

## 🧪 Step 3: Test Docker GPU Access

```bash
# Run a test container
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

**Expected:** Should show the same `nvidia-smi` output as before.

If this fails:
```bash
# Check Docker daemon configuration
cat /etc/docker/daemon.json

# Should contain:
{
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}

# If missing, add it and restart Docker
sudo systemctl restart docker
```

---

## 🚀 Step 4: Deploy RAG Lab with GPU

```bash
cd ~/rag_lab

# Pull latest code (GPU support enabled)
git pull origin main

# Restart Ollama with GPU
docker compose down
docker compose up -d ollama

# Watch Ollama start
docker compose logs -f ollama
```

**Look for GPU initialization messages:**
```
time=2024-11-04T05:30:00.000Z level=INFO source=gpu.go:123 msg="Initializing GPU"
time=2024-11-04T05:30:00.100Z level=INFO source=gpu.go:145 msg="CUDA driver version: 12.0"
time=2024-11-04T05:30:00.200Z level=INFO source=gpu.go:167 msg="GPU 0: Tesla T4 (15360 MiB)"
```

---

## ✅ Step 5: Verify GPU Usage

### Check GPU is Accessible

```bash
# From inside Ollama container
docker compose exec ollama nvidia-smi
```

Should show GPU info.

### Check Ollama Logs for GPU Detection

```bash
docker compose logs ollama | grep -i gpu
```

**Expected output:**
```
msg="Initializing GPU"
msg="CUDA driver version: 12.0"
msg="GPU 0: Tesla T4"
```

### Monitor GPU Usage During Inference

```bash
# Terminal 1: Watch GPU usage
watch -n 1 nvidia-smi

# Terminal 2: Run inference
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Explain quantum computing in simple terms",
  "stream": false
}'
```

**During inference, you should see:**
- GPU Utilization: 80-100%
- GPU Memory Usage: Increasing
- Power Usage: Near max

---

## 📊 Performance Comparison

### CPU vs GPU Inference Speed

**Test prompt:**
```bash
# Test script
time curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Write a haiku about AI",
  "stream": false
}'
```

**Expected results:**

| Hardware | Speed | Tokens/sec |
|----------|-------|------------|
| **CPU (16 cores)** | ~30-60s | 5-10 tok/s |
| **GPU (Tesla T4)** | ~2-5s | 50-100 tok/s |
| **GPU (A100)** | ~1-2s | 200-500 tok/s |

**GPU is 10-100x faster!** 🚀

---

## 🐛 Troubleshooting

### Issue: "could not select device driver with capabilities: [[gpu]]"

**Solution:**
```bash
# Verify nvidia-container-toolkit is installed
sudo apt install nvidia-container-toolkit
sudo systemctl restart docker

# Verify Docker can see GPUs
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Issue: Ollama not using GPU (still slow)

**Check:**
```bash
# 1. Verify GPU is detected
docker compose exec ollama nvidia-smi

# 2. Check Ollama logs
docker compose logs ollama | grep -i "gpu\|cuda"

# 3. Verify model is loaded on GPU
docker compose exec ollama ollama ps
```

**If model shows "CPU" instead of "GPU":**
```bash
# Restart Ollama
docker compose restart ollama

# Re-pull model (forces GPU detection)
docker compose exec ollama ollama pull llama3.2:3b
```

### Issue: Out of GPU Memory

**Symptoms:**
```
CUDA out of memory
```

**Solutions:**

1. **Use smaller model:**
```bash
# 1B model (uses ~2GB GPU RAM)
docker compose exec ollama ollama pull llama3.2:1b
```

2. **Reduce context window:**
```bash
# In frontend Settings, reduce Context Window to 2048 or 4096
```

3. **Check GPU memory:**
```bash
nvidia-smi --query-gpu=memory.total,memory.used,memory.free --format=csv
```

### Issue: Multiple GPUs, want to use specific one

**Edit docker-compose.yml:**
```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            device_ids: ['0']  # Use GPU 0 only
            capabilities: [gpu]
```

Or use all GPUs:
```yaml
            count: all  # Use all available GPUs
```

---

## 📈 Monitoring GPU Usage

### Real-time Monitoring

```bash
# Watch GPU usage (updates every second)
watch -n 1 nvidia-smi

# Or use gpustat (more compact)
pip install gpustat
watch -n 1 gpustat
```

### Log GPU Metrics

```bash
# Log GPU usage to file
nvidia-smi --query-gpu=timestamp,name,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv -l 1 > gpu_usage.log
```

### Grafana Dashboard (Advanced)

For production monitoring, integrate with Prometheus + Grafana:

1. Install NVIDIA DCGM Exporter
2. Configure Prometheus to scrape metrics
3. Import NVIDIA GPU dashboard to Grafana

See: https://github.com/NVIDIA/dcgm-exporter

---

## 🎯 Optimization Tips

### 1. Keep Models in GPU Memory

Models stay in GPU memory for 5 minutes by default. To keep them loaded:

```bash
# Set keep_alive to -1 (forever)
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "test",
  "keep_alive": -1
}'
```

### 2. Warm Up GPU

After starting Ollama, run a test query to warm up the GPU:

```bash
curl http://localhost:11434/api/generate -d '{
  "model": "llama3.2:3b",
  "prompt": "Hello",
  "stream": false
}'
```

First query is slower (loads model), subsequent queries are fast.

### 3. Use Appropriate Model Size

| GPU Memory | Recommended Model | Max Context |
|------------|-------------------|-------------|
| 4GB | llama3.2:1b | 8K |
| 8GB | llama3.2:3b | 8K |
| 16GB | llama3.1:8b | 32K |
| 24GB | llama3.1:13b | 64K |
| 40GB+ | llama3.1:70b | 128K |

### 4. Enable Flash Attention (if supported)

Flash Attention reduces memory usage and increases speed:

```bash
# Ollama automatically uses Flash Attention if GPU supports it
# Requires: Compute Capability 8.0+ (A100, RTX 30xx, RTX 40xx)
```

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] `nvidia-smi` shows GPU info
- [ ] `docker compose exec ollama nvidia-smi` works
- [ ] Ollama logs show "Initializing GPU"
- [ ] Inference completes in < 5 seconds for 3B model
- [ ] GPU utilization reaches 80-100% during inference
- [ ] GPU memory usage increases when model loads
- [ ] Frontend loads models successfully
- [ ] Chat responses are fast (< 5s for short queries)

---

## 📚 Additional Resources

- **NVIDIA Container Toolkit:** https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/
- **Ollama GPU Support:** https://github.com/ollama/ollama/blob/main/docs/gpu.md
- **Docker Compose GPU:** https://docs.docker.com/compose/gpu-support/
- **CUDA Compatibility:** https://docs.nvidia.com/deploy/cuda-compatibility/

---

## 🎉 Success!

If all checks pass, your RAG Lab is now running with **GPU acceleration**! 

Enjoy **10-100x faster** LLM inference! 🚀

---

**Questions?** Check the main deployment guide: `docs/deployment/UBUNTU_DEPLOYMENT.md`

