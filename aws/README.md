# AWS Deployment for RAG Lab ☁️

**Production-ready AWS EC2 deployment with GPU support, vLLM, and enterprise security**

---

## 🎯 Quick Start

### For vLLM Support (Recommended - Production)
```bash
# One-time setup
cd rag_lab/aws/scripts
./setup-github-secret.sh

# Launch g5.2xlarge with A10G GPU + vLLM
./launch-g5-vllm.sh
```

### For Ollama Only (Cost-Effective - Development)
```bash
# One-time setup
cd rag_lab/aws/scripts
./setup-github-secret.sh

# Launch g4dn.2xlarge with T4 GPU + Ollama
./aws-launch-rag-lab.sh
```

---

## 📁 Directory Structure

```
aws/
├── README.md                           # This file
├── GPU_COMPATIBILITY_GUIDE.md          # GPU comparison & selection guide
├── scripts/
│   ├── launch-g5-vllm.sh              # Launch g5 with vLLM (A10G GPU)
│   ├── aws-launch-rag-lab.sh          # Launch g4dn with Ollama (T4 GPU)
│   ├── setup-github-secret.sh         # One-time security setup
│   └── update-my-ip.sh                # Update security group IP
├── cloud-init/
│   ├── cloud-init-vllm-g5.yaml        # g5 setup with vLLM
│   ├── cloud-init-rag-lab-private.yaml # Private repo with Ollama
│   └── cloud-init-rag-lab.yaml        # Public repo with Ollama
└── docs/
    ├── AWS_QUICK_START.md              # Quick reference
    └── AWS_DEPLOYMENT_COMPLETE.md      # Implementation details
```

Additional documentation in `docs/deployment/`:
- `AWS_EC2_DEPLOYMENT.md` - Complete deployment guide
- `AWS_SECURITY_BEST_PRACTICES.md` - Security deep-dive

---

## 🎮 GPU Options

### g5.2xlarge - NVIDIA A10G (Recommended for Production)
- **GPU:** A10G Tensor Core (Ampere architecture)
- **VRAM:** 24GB
- **vLLM Support:** ✅ YES
- **Cost:** ~$1.21/hour (~$29/day)
- **Best for:** Production, vLLM, larger models (13B+)
- **Launch:** `./launch-g5-vllm.sh`

### g4dn.2xlarge - NVIDIA T4 (Cost-Effective Development)
- **GPU:** T4 (Turing architecture)
- **VRAM:** 16GB
- **vLLM Support:** ❌ NO (Ollama only)
- **Cost:** ~$0.752/hour (~$18/day)
- **Best for:** Development, Ollama, smaller models (7B)
- **Launch:** `./aws-launch-rag-lab.sh`

📘 **[Read GPU Compatibility Guide](GPU_COMPATIBILITY_GUIDE.md)** for detailed comparison

---

## 🔐 Security Features

### Private GitHub Repository Access
- ✅ GitHub token stored in AWS Secrets Manager (encrypted)
- ✅ IAM roles (no hardcoded credentials)
- ✅ Token never exposed in logs
- ✅ 90-day rotation support
- ✅ CloudTrail audit trail

### Dynamic IP Management
- ✅ AWS Session Manager (no SSH needed, works from any IP)
- ✅ Auto-update script for security groups
- ✅ Port forwarding support
- ✅ No open port 22 required

### Infrastructure Security
- ✅ Encrypted EBS volumes
- ✅ IMDSv2 required
- ✅ Security group best practices
- ✅ Read-only GitHub tokens

---

## 💰 Cost Management

### Estimated Costs

| Instance | Running | Stopped | Savings |
|----------|---------|---------|---------|
| g5.2xlarge | $29/day | $0.65/day | 98% |
| g4dn.2xlarge | $18/day | $0.50/day | 97% |

### Stop When Not Using (Biggest Savings!)
```bash
# Stop instance (keeps data, only pay EBS storage)
aws ec2 stop-instances --instance-ids INSTANCE_ID

# Start when needed
aws ec2 start-instances --instance-ids INSTANCE_ID
```

**Typical monthly costs:**
- **Development (stop overnight):** $150-200/month
- **Production (24/7):** $540-870/month
- **Demo/Testing (4hrs/week):** $20-30/month

---

## 🚀 Features

### What Gets Installed

**g5.2xlarge (vLLM + Ollama):**
- ✅ NVIDIA A10G drivers
- ✅ Docker + NVIDIA Container Toolkit
- ✅ vLLM (native Python, OpenAI-compatible API)
- ✅ Ollama (Docker, for compatibility)
- ✅ RAG Lab (all 15 microservices)
- ✅ Helper scripts (start-vllm.sh, test-vllm.sh)

**g4dn.2xlarge (Ollama):**
- ✅ NVIDIA T4 drivers
- ✅ Docker + NVIDIA Container Toolkit
- ✅ Ollama (Docker)
- ✅ RAG Lab (all 15 microservices)
- ✅ Models pre-loaded (llama3.1:8b, nomic-embed-text)

### Setup Time
- g5.2xlarge: 15-20 minutes (vLLM installation)
- g4dn.2xlarge: 10-15 minutes

---

## 📖 Usage Examples

### Example 1: Launch for Production vLLM
```bash
# One-time setup
./setup-github-secret.sh

# Launch g5 instance
./launch-g5-vllm.sh

# Wait 15-20 minutes, then access
# Session Manager (recommended)
aws ssm start-session --target INSTANCE_ID

# Port forward to access locally
aws ssm start-session --target INSTANCE_ID \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["3000"],"localPortNumber":["3000"]}'

# Access: http://localhost:3000
```

### Example 2: Launch for Development with Ollama
```bash
# One-time setup
./setup-github-secret.sh

# Launch g4dn instance
./aws-launch-rag-lab.sh

# Wait 10-15 minutes, then access
http://PUBLIC_IP:3000
```

### Example 3: Quick Demo (Launch & Stop)
```bash
# Launch instance
./launch-g5-vllm.sh

# Do your demo (2-3 hours)
# Access services, show features

# Stop when done (save $$)
aws ec2 stop-instances --instance-ids INSTANCE_ID

# Total cost: ~$3-5 for a demo
```

---

## 🛠️ Troubleshooting

### Monitor Setup Progress
```bash
# SSH into instance
ssh -i your-key.pem ubuntu@PUBLIC_IP

# Watch cloud-init logs
tail -f /var/log/cloud-init-output.log

# Check if complete
cat /var/log/cloud-init-output.log | grep "Cloud-init.*finished"
```

### Check GPU
```bash
# Verify GPU is detected
nvidia-smi

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Check Services
```bash
# Check Docker services
cd /home/ubuntu/rag_lab
docker compose ps

# View logs
docker compose logs -f

# Restart if needed
docker compose restart
```

### Check vLLM (g5 only)
```bash
# Check vLLM service
sudo systemctl status vllm

# Test vLLM API
/home/ubuntu/test-vllm.sh

# Start vLLM manually
/home/ubuntu/start-vllm.sh
```

---

## 📚 Documentation

### Quick References
- **[GPU Compatibility Guide](GPU_COMPATIBILITY_GUIDE.md)** - Choose the right GPU
- **[Quick Start](docs/AWS_QUICK_START.md)** - Essential commands
- **[Deployment Complete](docs/AWS_DEPLOYMENT_COMPLETE.md)** - Implementation details

### Comprehensive Guides
- **[AWS EC2 Deployment](../docs/deployment/AWS_EC2_DEPLOYMENT.md)** - Full deployment guide
- **[Security Best Practices](../docs/deployment/AWS_SECURITY_BEST_PRACTICES.md)** - Security deep-dive

---

## 🎯 Decision Tree

**Choose your path:**

```
Do you need vLLM support?
├─ YES → Do you need large models (13B+)?
│        ├─ YES → Use g5.2xlarge ($29/day)
│        └─ NO  → Use g5.xlarge ($24/day)
│
└─ NO  → Is this for production?
         ├─ YES → Use g5.2xlarge anyway (future-proof)
         └─ NO  → Use g4dn.2xlarge ($18/day) or g4dn.xlarge ($13/day)
```

**Cost-conscious?**
- Development: g4dn.xlarge ($13/day, stop overnight → $150/month)
- Production: g5.2xlarge ($29/day, business hours → $360/month)
- Testing: Any instance, stop after use (< $50/month)

---

## ✅ Checklist

### Before First Launch
- [ ] AWS CLI v2 installed and configured
- [ ] SSH key pair created in AWS
- [ ] Run `./setup-github-secret.sh` (one time)
- [ ] AWS Session Manager plugin installed (optional)
- [ ] Understand cost (~$18-29/day running)

### After Launch
- [ ] Wait 10-20 minutes for setup
- [ ] Check cloud-init logs for completion
- [ ] Verify GPU with `nvidia-smi`
- [ ] Access frontend (http://PUBLIC_IP:3000)
- [ ] Create user account
- [ ] Test query functionality
- [ ] **Stop instance when done** ← Important!

---

## 🆘 Support

### Common Issues

**Issue:** Cloud-init fails to clone repo
```bash
# Check secret exists
aws secretsmanager describe-secret --secret-id rag-lab/github-token

# Check IAM role attached
aws ec2 describe-instances --instance-ids INSTANCE_ID \
    --query 'Reservations[0].Instances[0].IamInstanceProfile'
```

**Issue:** vLLM not working
```bash
# Check if g5 instance (A10G required)
nvidia-smi  # Should show A10G

# Check vLLM installation
source /home/ubuntu/vllm-env/bin/activate
python -c "import vllm; print(vllm.__version__)"
```

**Issue:** Services not starting
```bash
# Check Docker
docker compose ps

# Check logs
docker compose logs -f

# Restart
docker compose restart
```

---

## 🚀 Next Steps

1. **Read:** [GPU Compatibility Guide](GPU_COMPATIBILITY_GUIDE.md)
2. **Setup:** Run `./setup-github-secret.sh`
3. **Launch:** Run appropriate launch script
4. **Learn:** [AWS Security Best Practices](../docs/deployment/AWS_SECURITY_BEST_PRACTICES.md)
5. **Optimize:** Implement stop/start schedule

---

## 📊 Comparison Matrix

| Feature | g4dn.2xlarge | g5.2xlarge |
|---------|--------------|------------|
| **GPU** | T4 (Turing) | A10G (Ampere) |
| **VRAM** | 16GB | 24GB |
| **vLLM** | ❌ No | ✅ Yes |
| **Cost** | $18/day | $29/day |
| **Max Model** | 7B | 13B+ |
| **Inference Speed** | Base | 1.5-2x faster |
| **Best For** | Dev, small models | Prod, large models |

---

**Ready to deploy? Start with the [GPU Compatibility Guide](GPU_COMPATIBILITY_GUIDE.md)!**

*Last updated: November 6, 2025*

