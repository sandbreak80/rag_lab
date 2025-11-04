# 🚀 Ubuntu Server Deployment Guide

**Clean deployment guide for running the RAG Lab on Ubuntu Server 20.04+**

---

## ✅ Prerequisites

### What You Need

- Ubuntu 20.04 or later
- Docker installed
- Internet connection
- At least 8GB RAM (16GB recommended)
- 20GB free disk space

### What You DON'T Need

- ❌ Node.js / npm (frontend builds inside Docker)
- ❌ Python / pip (services run in containers)
- ❌ Virtual environments
- ❌ System package installations

**Everything runs in Docker!**

---

## 🔧 Step 1: Install Docker

If Docker is not already installed:

```bash
# Update package list
sudo apt update

# Install Docker
sudo apt install -y docker.io

# Start and enable Docker
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to docker group (optional, avoids sudo)
sudo usermod -aG docker $USER
newgrp docker

# Verify Docker is running
docker --version
docker compose version
```

**Expected output:**
```
Docker version 24.0.0 or higher
Docker Compose version v2.x.x
```

---

## 📥 Step 2: Clone the Repository

```bash
# Clone from GitHub
git clone https://github.com/sandbreak80/rag_lab.git

# Navigate to the project
cd rag_lab
```

---

## 🚀 Step 3: Deploy (One Command!)

```bash
# Run the all-in-one build script
cd scripts
./build-and-start.sh
```

### What This Does

The script will automatically:

1. ✅ **Check Docker** - Verify Docker and Docker Compose are available
2. ✅ **Stop Existing** - Clean up any running containers
3. ✅ **Build Images** - Build all 14 microservices + React frontend
4. ✅ **Start Ollama** - Launch the LLM inference engine
5. ✅ **Pull Models** - Download llama3.2:3b and nomic-embed-text
6. ✅ **Start Services** - Launch all services with health checks
7. ✅ **Display URLs** - Show you where to access the application

### Expected Output

```
╔════════════════════════════════════════════════════════════╗
║  Enterprise Agentic AI Platform with Advanced RAG         ║
║  Build and Start Script                                    ║
╚════════════════════════════════════════════════════════════╝

▶ Checking Docker...
✓ Docker is running

▶ Checking Docker Compose...
✓ Docker Compose is available

▶ Stopping any running containers...
✓ Containers stopped

▶ Building Docker images...
[+] Building 127.3s (85/85) FINISHED
✓ Docker images built

▶ Starting Ollama service...
✓ Ollama started

▶ Waiting for Ollama to be ready...
✓ Ollama is responding

▶ Pulling Ollama models...
Pulling llama3.2:3b...
✓ Model llama3.2:3b pulled successfully

Pulling nomic-embed-text...
✓ Model nomic-embed-text pulled successfully

▶ Starting all services...
✓ All services started

▶ Waiting for services to be healthy...
Waiting for vector-db...      ✓
Waiting for embedding-service... ✓
Waiting for frontend...       ✓

╔════════════════════════════════════════════════════════════╗
║  🚀 RAG Lab is Running!                                   ║
╚════════════════════════════════════════════════════════════╝

📱 Frontend:           http://localhost:3000
🔌 API Gateway:        http://localhost:8000
🤖 Ollama:             http://localhost:11434
🔍 SearXNG:            http://localhost:8080

✅ All services are healthy and ready!
```

### Deployment Time

- **First run (with model downloads):** ~5-10 minutes
- **Subsequent runs (models cached):** ~2-3 minutes

---

## 🌐 Step 4: Access the Application

### From the Server (localhost)

```bash
# Test API Gateway
curl http://localhost:8000/health

# Test Ollama
curl http://localhost:11434/api/tags
```

### From Your Computer (Remote Access)

If deploying on a remote Ubuntu server (like AWS EC2):

**Option 1: SSH Tunnel (Recommended)**

```bash
# From your local machine
ssh -L 3000:localhost:3000 ubuntu@your-server-ip

# Now access http://localhost:3000 in your browser
```

**Option 2: Configure Security Group / Firewall**

```bash
# On the server, allow port 3000
sudo ufw allow 3000/tcp
sudo ufw reload

# Add inbound rule in AWS/Cloud provider console
# Allow TCP port 3000 from your IP

# Access http://your-server-ip:3000
```

---

## 🛑 Stopping the Application

```bash
cd scripts
./stop.sh
```

This stops all containers but **keeps your data** (uploaded documents, vector database, etc.).

### Clean Stop (Remove All Data)

```bash
cd scripts
./stop.sh --clean
```

This removes all Docker volumes (uploaded docs, embeddings, etc.). Use for a completely fresh start.

---

## 🔄 Updating the Application

```bash
# Pull latest code
cd ~/rag_lab
git pull origin main

# Rebuild and restart
cd scripts
./stop.sh
./build-and-start.sh
```

---

## 🐛 Troubleshooting

### Port Already in Use

```bash
# Find what's using port 3000
sudo lsof -i :3000

# Kill the process (replace PID)
sudo kill -9 <PID>

# Or change port in docker-compose.yml
# frontend: ports: - "8080:80"  # Change 3000 to 8080
```

### Docker Permission Denied

```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Or use sudo
sudo ./build-and-start.sh
```

### Ollama Won't Start

```bash
# Check if Ollama container is running
docker compose ps ollama

# Check Ollama logs
docker compose logs ollama

# Restart Ollama
docker compose restart ollama
```

### Models Won't Download

```bash
# Manually pull models
docker compose exec ollama ollama pull llama3.2:3b
docker compose exec ollama ollama pull nomic-embed-text

# Check disk space
df -h

# Check Ollama is accessible
curl http://localhost:11434/api/tags
```

### Frontend Won't Build

```bash
# Check frontend logs
docker compose logs frontend

# Rebuild frontend only
docker compose build frontend
docker compose up -d frontend
```

### Services Won't Start

```bash
# Check which services are failing
docker compose ps

# Check logs for a specific service
docker compose logs vector-db
docker compose logs api-gateway

# Restart a specific service
docker compose restart vector-db
```

### Out of Memory

```bash
# Check memory usage
free -h
docker stats --no-stream

# Restart with memory limits
docker compose down
docker compose up -d
```

### Complete Reset (Nuclear Option)

If everything is broken:

```bash
# Stop everything and remove all data
cd scripts
./stop.sh --clean

# Remove all Docker images
docker system prune -a --volumes -f

# Rebuild from scratch
./build-and-start.sh --clean
```

---

## 📊 Monitoring

### Check Service Status

```bash
# View all services
docker compose ps

# Expected output: All services "Up" and "healthy"
NAME                    STATUS
rag-api-gateway         Up (healthy)
rag-chat-service        Up (healthy)
rag-frontend            Up (healthy)
rag-ollama              Up (healthy)
...
```

### View Logs

```bash
# All services (live tail)
docker compose logs -f

# Specific service
docker compose logs -f frontend
docker compose logs -f api-gateway

# Last 100 lines
docker compose logs --tail=100 frontend
```

### Check Resource Usage

```bash
# Real-time stats
docker stats

# Disk usage
docker system df
```

---

## 🔐 Security Notes

### This is an Educational Lab

**NOT production-ready** without additional security:

- ⚠️ No authentication
- ⚠️ No rate limiting
- ⚠️ No SSL/TLS
- ⚠️ Services exposed to localhost only

### For Production

See `docs/SECURITY_ENHANCEMENT_PLAN.md` for:
- Authentication & authorization
- API key management
- Rate limiting
- SSL/TLS certificates
- Prompt injection prevention
- Content filtering

---

## 📈 Performance Tips

### GPU Support

If you have an NVIDIA GPU:

1. Install NVIDIA Docker runtime:
```bash
sudo apt install nvidia-docker2
sudo systemctl restart docker
```

2. Uncomment GPU section in `docker-compose.yml`:
```yaml
ollama:
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: all
            capabilities: [gpu]
```

3. Restart services:
```bash
docker compose down
docker compose up -d
```

### Reduce Memory Usage

Use smaller models:

```bash
# Pull a smaller model
docker compose exec ollama ollama pull llama3.2:1b

# Update config.env
CHAT_MODEL=llama3.2:1b
```

### Improve Performance

1. Use SSD storage (not HDD)
2. Allocate more RAM to Docker
3. Use GPU for inference
4. Pre-pull models before startup

---

## 📚 Next Steps

Once deployed:

1. **Upload Documents** - Go to Documents tab, upload PDFs/Markdown
2. **Ask Questions** - Go to Chat tab, ask about your documents
3. **Try Labs** - Explore educational exercises in Lab tab
4. **Tune Settings** - Experiment with RAG configurations
5. **Monitor Metrics** - View performance in Metrics tab

### Educational Labs

See `docs/lab/` for hands-on exercises:
- `QUICK_START.md` - Getting started guide
- `EXERCISE_MODEL_VS_CONTEXT.md` - Model comparison
- RAG configuration tuning
- Knowledge graph experiments
- Security testing

---

## 🆘 Getting Help

### Logs to Check

When reporting issues, include:

```bash
# Service status
docker compose ps > status.txt

# Service logs
docker compose logs > logs.txt

# System info
docker --version > sysinfo.txt
docker compose version >> sysinfo.txt
uname -a >> sysinfo.txt
free -h >> sysinfo.txt
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Port in use | Change port in docker-compose.yml |
| Permission denied | Add user to docker group |
| Out of memory | Use smaller model or add RAM |
| Models won't download | Check internet, disk space |
| Frontend 404 | Wait for build, check logs |

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] All services show "Up (healthy)" in `docker compose ps`
- [ ] Frontend accessible at http://localhost:3000
- [ ] API Gateway returns JSON at http://localhost:8000/health
- [ ] Ollama lists models at http://localhost:11434/api/tags
- [ ] Can upload a document in Documents tab
- [ ] Can ask a question in Chat tab
- [ ] Metrics show in Metrics tab

---

**🎉 You're ready to use the RAG Lab!**

For more documentation, see:
- `docs/PROJECT_COMPLETE.md` - Full project overview
- `docs/ARCHITECTURE.md` - System architecture
- `docs/lab/` - Educational exercises
- `scripts/README.md` - Script documentation

