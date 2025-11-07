# AWS Quick Start - RAG Lab 🚀

**Launch RAG Lab on AWS EC2 with GPU in one command**

---

## ⚡ Quick Launch

```bash
cd rag_lab
./aws-launch-rag-lab.sh
```

**That's it!** ✅

- Automated setup (10-15 minutes)
- g4dn.2xlarge with NVIDIA T4 GPU
- All 15 microservices
- Ollama with models pre-loaded

---

## 📋 Before You Start

1. **Install AWS CLI v2**
   ```bash
   curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
   unzip awscliv2.zip && sudo ./aws/install
   ```

2. **Configure AWS credentials**
   ```bash
   aws configure
   # Enter your AWS Access Key, Secret Key, region (us-west-2)
   ```

3. **Update the launch script with your key name**
   ```bash
   # Edit aws-launch-rag-lab.sh
   KEY_NAME="bootcamp"  # Change to your SSH key pair name
   ```

---

## 🌐 Access Your Instance

After launch completes (10-15 min):

```bash
# Frontend
http://PUBLIC_IP:3000

# API
http://PUBLIC_IP:8000

# SSH
ssh -i your-key.pem ubuntu@PUBLIC_IP
```

📄 **Details saved to:** `instance-info.txt`

---

## 💰 Cost Savings

### Stop When Not Using
```bash
# Stop (only pay for EBS ~$16/month)
aws ec2 stop-instances --instance-ids INSTANCE_ID

# Start when needed
aws ec2 start-instances --instance-ids INSTANCE_ID
```

**Savings:** ~$538/month (97% reduction)

### Costs
- **Running:** ~$18/day (~$554/month)
- **Stopped:** ~$0.50/day (~$16/month)
- **Terminated:** $0

---

## 🛠️ Monitor Setup

```bash
# Watch cloud-init progress
ssh -i your-key.pem ubuntu@PUBLIC_IP "tail -f /var/log/cloud-init-output.log"

# Check services
ssh -i your-key.pem ubuntu@PUBLIC_IP "cd rag_lab && docker compose ps"

# Check GPU
ssh -i your-key.pem ubuntu@PUBLIC_IP "nvidia-smi"
```

---

## 🔄 Update RAG Lab

```bash
ssh -i your-key.pem ubuntu@PUBLIC_IP "/home/ubuntu/update-rag-lab.sh"
```

---

## 🐛 Troubleshooting

### Services not ready?
**Wait 10-15 minutes** - Cloud-init is still running

### Check progress:
```bash
ssh -i your-key.pem ubuntu@PUBLIC_IP \
  "cat /var/log/cloud-init-output.log | grep 'Cloud-init.*finished'"
```

### Frontend shows 502?
Services still starting. Check:
```bash
ssh -i your-key.pem ubuntu@PUBLIC_IP "cd rag_lab && docker compose ps"
```

---

## 📚 Full Documentation

See [AWS_EC2_DEPLOYMENT.md](docs/deployment/AWS_EC2_DEPLOYMENT.md) for:
- Manual launch steps
- Security best practices
- Advanced configurations
- Monitoring setup
- Spot instances
- Auto-scaling

---

## ✅ What Cloud-Init Installs

Automatically configured:
- ✅ NVIDIA GPU drivers
- ✅ Docker + NVIDIA Container Toolkit
- ✅ Ollama with GPU support
- ✅ Models: llama3.1:8b, nomic-embed-text
- ✅ RAG Lab (all 15 microservices)
- ✅ Helper scripts

---

## 🎯 Why Cloud-Init vs AMI?

| Cloud-Init ✅ | AMI |
|--------------|-----|
| Always latest code | Can be outdated |
| No storage costs | ~$5-10/month |
| Version controlled | Manual updates |
| 10-15 min setup | 2-3 min launch |

**Verdict:** Cloud-init saves money and ensures fresh deployments!

---

## 🔐 Security Note

The default security group allows:
- Port 22 (SSH) from anywhere
- Port 3000 (Frontend) from anywhere
- Port 8000 (API) from anywhere

**For production:** Restrict to your IP only!

```bash
# Get your IP
MY_IP=$(curl -s ifconfig.me)

# Restrict SSH
aws ec2 authorize-security-group-ingress \
    --group-id SG_ID \
    --protocol tcp --port 22 \
    --cidr $MY_IP/32
```

---

**Questions?** See full docs or check `/home/ubuntu/deployment-info.txt` on your instance.

**Happy deploying! 🚀**

