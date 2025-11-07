# AWS g4dn.2xlarge Deployment Session Summary

**Date:** November 7, 2025
**Branch:** security
**Instance Type:** g4dn.2xlarge (NVIDIA Tesla T4, 8 vCPUs, 32GB RAM)

---

## ✅ Completed Tasks

### 1. **Infrastructure Setup**
- ✅ Launched g4dn.2xlarge EC2 instance (Instance ID: `i-0bccdf802ac04099a`)
- ✅ Created security group with ports: 22 (SSH), 3000 (Frontend), 8000 (API), 11434 (Ollama)
- ✅ Instance is running and accessible at **16.144.40.150**

### 2. **GPU Configuration**
- ✅ NVIDIA Tesla T4 GPU detected and verified
- ✅ NVIDIA driver 580.95.05 installed successfully
- ✅ CUDA Version 13.0 available
- ✅ GPU shows 15360 MiB total memory

### 3. **Docker Installation**
- ✅ Docker CE installed
- ✅ Docker Compose plugin installed
- ✅ NVIDIA Container Toolkit installed
- ✅ Docker configured for GPU access

### 4. **RAG Lab Deployment**
- ✅ RAG Lab codebase uploaded to `/home/ubuntu/`
- ✅ Security branch code in place
- ✅ All files and directories present

### 5. **Documentation & Scripts**
- ✅ Updated cloud-init script (v2) with proper reboot handling
- ✅ Added Ollama optional models pulling
- ✅ Fixed home directory permission issues
- ✅ Updated launch script to use cloud-init-v2
- ✅ Verified terminate-cleanup script exists

---

## 📋 Identified Issues (Fixed in v2)

### Issue 1: Missing Reboots
**Problem:** Cloud-init didn't reboot after Docker or NVIDIA driver installation
**Impact:** GPU drivers not loaded, containers couldn't access GPU
**Solution:** Split into 2 stages with automatic reboot between them

### Issue 2: Home Directory Permissions
**Problem:** `/home/ubuntu` had root ownership
**Impact:** Git clone failed with permission denied
**Solution:** Added `chown -R ubuntu:ubuntu /home/ubuntu` in stage 2

### Issue 3: Repository Authentication
**Problem:** Repository appears to be private, requires authentication
**Impact:** Git clone fails
**Solution:** Upload tarball directly during deployment

### Issue 4: Missing Optional Models
**Problem:** Only required models were pulled
**Impact:** Can't test different model sizes in labs
**Solution:** Added optional model pulling (llama3.2:3b, gemma2:2b, mistral:7b)

---

## 🎯 Cloud-Init v2 Improvements

### Architecture
```
Stage 1 (cloud-init):
  ├── Install Docker
  ├── Install NVIDIA drivers
  ├── Install NVIDIA Container Toolkit
  ├── Create systemd service for Stage 2
  └── REBOOT

Stage 2 (systemd service - runs after reboot):
  ├── Verify GPU available
  ├── Fix permissions
  ├── Deploy RAG Lab code
  ├── Start Ollama with GPU
  ├── Pull required models (llama3.1:8b, nomic-embed-text)
  ├── Pull optional models (llama3.2:3b, gemma2:2b, mistral:7b)
  ├── Build RAG Lab services
  ├── Start all containers
  └── Create default user
```

### Key Features
- **Automatic reboot handling** via systemd
- **Progress markers** to prevent re-running completed stages
- **Better logging** (separate logs for each stage)
- **Self-disabling** (service disables after successful completion)
- **Failure recovery** (systemd will retry on failure)

### Files Modified/Created
1. `aws/cloud-init/cloud-init-rag-lab-v2.yaml` - New cloud-init with reboots
2. `aws/scripts/aws-launch-rag-lab.sh` - Updated to use v2 (with fallback to v1)
3. `aws/CLOUD_INIT_V2_IMPROVEMENTS.md` - Documentation of changes
4. `aws/SESSION_SUMMARY_AWS_DEPLOYMENT.md` - This file

---

## 🧪 Next Steps for Testing

### Option A: Complete Current Instance (Manual)
```bash
# SSH into instance
ssh -i bootcamp.pem ubuntu@16.144.40.150

# Start Ollama
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 \
  --name ollama --restart unless-stopped ollama/ollama

# Pull models
docker exec ollama ollama pull llama3.1:8b
docker exec ollama ollama pull nomic-embed-text

# Build RAG Lab
cd /home/ubuntu
docker compose build
docker compose up -d

# Wait and verify
docker compose ps
```

### Option B: Test Teardown & Fresh Deploy (Recommended)
```bash
# 1. Test teardown script
cd /Users/bmstoner/code_projects/rag_lab/aws
./scripts/terminate-cleanup.sh i-0bccdf802ac04099a

# 2. Fresh deployment with v2
./scripts/aws-launch-rag-lab.sh

# 3. Monitor stage 2 after reboot
ssh -i bootcamp.pem ubuntu@NEW_IP \
  "tail -f /var/log/rag-lab-setup-stage2.log"
```

---

## 💰 Cost Information

### Current Instance
- **Type:** g4dn.2xlarge
- **Cost:** $0.752/hour (~$18/day, ~$554/month if 24/7)
- **Region:** us-west-2
- **Volume:** 200GB gp3 (~$16/month)

### Cost Optimization
```bash
# Stop (pay only for EBS ~$16/month)
aws ec2 stop-instances --region us-west-2 --instance-ids i-0bccdf802ac04099a

# Start when needed
aws ec2 start-instances --region us-west-2 --instance-ids i-0bccdf802ac04099a

# Terminate (pay $0)
./aws/scripts/terminate-cleanup.sh i-0bccdf802ac04099a
```

**Savings with stop/start:** ~$538/month (97% reduction)

---

## 📊 Testing Checklist

Once deployment completes, verify:

- [ ] GPU accessible (`nvidia-smi` shows Tesla T4)
- [ ] Ollama running and has GPU access
- [ ] Required models pulled (llama3.1:8b, nomic-embed-text)
- [ ] Optional models pulled (llama3.2:3b, gemma2:2b, mistral:7b)
- [ ] All 15 RAG Lab services running (`docker compose ps`)
- [ ] Frontend accessible (http://16.144.40.150:3000)
- [ ] API healthy (http://16.144.40.150:8000/health)
- [ ] Can create user account
- [ ] Can run test query
- [ ] Teardown script works correctly

---

## 🔧 Useful Commands

### Instance Access
```bash
# SSH
ssh -i /Users/bmstoner/SynologyDrive/vcode_projects/bootcamp.pem ubuntu@16.144.40.150

# Check GPU
nvidia-smi

# Check containers
docker ps

# Check RAG Lab services
cd /home/ubuntu && docker compose ps
```

### Monitoring
```bash
# Cloud-init progress (Stage 1)
tail -f /var/log/cloud-init-output.log

# Stage 2 progress (after reboot)
tail -f /var/log/rag-lab-setup-stage2.log

# Check if setup complete
[ -f /var/lib/rag-lab-setup-complete ] && echo "Done!" || echo "Still running..."
```

### Management
```bash
# Restart all services
cd /home/ubuntu && docker compose restart

# View logs
docker compose logs -f

# Stop all services
docker compose down

# Start all services
docker compose up -d
```

---

## 📁 Instance Details

### Current Instance
```
Instance ID:    i-0bccdf802ac04099a
Instance Type:  g4dn.2xlarge
Public IP:      16.144.40.150
Public DNS:     ec2-16-144-40-150.us-west-2.compute.amazonaws.com
Private IP:     172.31.1.228
Security Group: sg-0e1a1844c745017b0 (rag-lab-security-group)
Region:         us-west-2
AMI:            ami-00f46ccd1cbfb363e (Ubuntu 24.04 LTS)
Volume:         200GB gp3
```

### Access URLs
```
Frontend:  http://16.144.40.150:3000
API:       http://16.144.40.150:8000
Ollama:    http://16.144.40.150:11434
```

### Saved Files
```
Local:  aws/instance-info.txt
Remote: /home/ubuntu/deployment-info.txt
```

---

## 🎓 Lessons Learned

1. **Reboots are critical** - Both Docker and NVIDIA drivers need reboots to function properly
2. **Cloud-init runs once** - Need systemd services or scripts for post-reboot tasks
3. **Permissions matter** - Home directory ownership can break deployments
4. **Progress markers** - Use marker files to track multi-stage deployments
5. **Always test teardown** - Ensure cleanup scripts work to avoid unexpected AWS costs

---

## 🚀 Success Criteria

The deployment will be considered successful when:
1. ✅ Instance launches automatically
2. ✅ System reboots and continues setup without intervention
3. ✅ GPU is available and working
4. ✅ Ollama starts with GPU support
5. ✅ All models pull successfully
6. ✅ RAG Lab builds and starts all 15 services
7. ✅ Frontend is accessible and functional
8. ✅ API responds to health checks
9. ✅ Can create users and run queries
10. ✅ Teardown script cleanly removes all resources

---

## 📞 Support Information

**Repository:** https://github.com/sandbreak80/rag_lab
**Branch:** security
**AWS Region:** us-west-2
**Instance Type:** g4dn.2xlarge
**SSH Key:** bootcamp.pem

**Created:** November 7, 2025
**Last Updated:** November 7, 2025

