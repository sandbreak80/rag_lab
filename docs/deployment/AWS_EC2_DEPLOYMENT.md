# AWS EC2 Deployment Guide for RAG Lab

**Complete guide for deploying RAG Lab on AWS EC2 with GPU support**

---

## 🎯 Overview

This guide covers automated deployment of RAG Lab on AWS EC2 using:
- **Instance Type:** g4dn.2xlarge (NVIDIA T4 GPU, 8 vCPUs, 32GB RAM)
- **OS:** Ubuntu 24.04 LTS
- **Automation:** Cloud-init for zero-touch deployment
- **Tools:** AWS CLI v2

**Deployment Method:** Cloud-init script (recommended)
- ✅ **Cost Effective:** No AMI storage costs
- ✅ **Always Up-to-Date:** Fresh install from latest code
- ✅ **Version Controlled:** Infrastructure as Code
- ✅ **Automated:** One command deployment

---

## 📋 Prerequisites

### 1. AWS Account & Credentials
```bash
# Install AWS CLI v2
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Configure credentials
aws configure
# AWS Access Key ID: [your-key]
# AWS Secret Access Key: [your-secret]
# Default region name: us-west-2
# Default output format: json
```

### 2. SSH Key Pair
```bash
# Create new key pair in AWS
aws ec2 create-key-pair \
    --region us-west-2 \
    --key-name rag-lab-key \
    --query 'KeyMaterial' \
    --output text > rag-lab-key.pem

chmod 400 rag-lab-key.pem

# OR use existing key (update KEY_NAME in launch script)
```

### 3. Clone RAG Lab Repository
```bash
git clone https://github.com/sandbreak80/rag_lab.git
cd rag_lab
```

---

## 🚀 Quick Launch (One Command)

### Launch with Automated Script
```bash
cd rag_lab
chmod +x aws-launch-rag-lab.sh
./aws-launch-rag-lab.sh
```

**What it does:**
1. Creates security group with required ports (22, 3000, 8000, 11434)
2. Validates cloud-init script
3. Launches g4dn.2xlarge instance
4. Waits for instance to start
5. Displays access information
6. Saves details to `instance-info.txt`

**Total Time:** 10-15 minutes until RAG Lab is fully operational

---

## 📝 Manual Launch (AWS CLI)

If you prefer manual control:

```bash
# 1. Create security group
SG_ID=$(aws ec2 create-security-group \
    --region us-west-2 \
    --group-name rag-lab-sg \
    --description "RAG Lab security group" \
    --query 'GroupId' \
    --output text)

# 2. Add firewall rules
aws ec2 authorize-security-group-ingress \
    --region us-west-2 \
    --group-id $SG_ID \
    --ip-permissions \
        IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges='[{CidrIp=0.0.0.0/0,Description="SSH"}]' \
        IpProtocol=tcp,FromPort=3000,ToPort=3000,IpRanges='[{CidrIp=0.0.0.0/0,Description="Frontend"}]' \
        IpProtocol=tcp,FromPort=8000,ToPort=8000,IpRanges='[{CidrIp=0.0.0.0/0,Description="API"}]' \
        IpProtocol=tcp,FromPort=11434,ToPort=11434,IpRanges='[{CidrIp=0.0.0.0/0,Description="Ollama"}]'

# 3. Launch instance
INSTANCE_ID=$(aws ec2 run-instances \
    --region us-west-2 \
    --image-id ami-00f46ccd1cbfb363e \
    --instance-type g4dn.2xlarge \
    --key-name rag-lab-key \
    --security-group-ids $SG_ID \
    --block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=200,VolumeType=gp3,DeleteOnTermination=true}' \
    --user-data file://cloud-init-rag-lab.yaml \
    --tag-specifications 'ResourceType=instance,Tags=[{Key=Name,Value=rag-lab-gpu}]' \
    --query 'Instances[0].InstanceId' \
    --output text)

echo "Instance ID: $INSTANCE_ID"

# 4. Wait for instance
aws ec2 wait instance-running --region us-west-2 --instance-ids $INSTANCE_ID

# 5. Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --region us-west-2 \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo "Public IP: $PUBLIC_IP"
echo "Frontend: http://$PUBLIC_IP:3000"
echo "SSH: ssh -i rag-lab-key.pem ubuntu@$PUBLIC_IP"
```

---

## 🔧 Cloud-Init Script Details

The `cloud-init-rag-lab.yaml` script automates:

### 1. System Setup
- Update all packages
- Install ubuntu-drivers-common, curl, git, docker prerequisites

### 2. NVIDIA GPU Drivers
- Install NVIDIA drivers via ubuntu-drivers
- Configure GPU for compute workloads

### 3. Docker Installation
- Install Docker CE from official repository
- Add ubuntu user to docker group
- Enable and start Docker service

### 4. NVIDIA Container Toolkit
- Install NVIDIA Container Toolkit
- Configure Docker to use NVIDIA runtime
- Restart Docker with GPU support

### 5. Ollama Deployment
- Pull Ollama Docker image
- Start Ollama with GPU access
- Pull required models: llama3.1:8b, nomic-embed-text

### 6. RAG Lab Deployment
- Clone repository from GitHub
- Build all Docker images
- Start all 15 microservices
- Wait for health checks

### 7. Helper Files
- Create `/home/ubuntu/deployment-info.txt` with usage instructions
- Create `/home/ubuntu/update-rag-lab.sh` for easy updates

---

## 🛠️ Post-Launch

### Monitor Setup Progress
```bash
# SSH into instance
ssh -i rag-lab-key.pem ubuntu@PUBLIC_IP

# Watch cloud-init progress (live)
tail -f /var/log/cloud-init-output.log

# Check if cloud-init finished
cat /var/log/cloud-init-output.log | grep "Cloud-init.*finished"

# Check GPU
nvidia-smi

# Check Docker services
cd rag_lab
docker compose ps

# View deployment info
cat /home/ubuntu/deployment-info.txt
```

### Access the Application
```bash
# Frontend (React UI)
http://PUBLIC_IP:3000

# API Gateway
http://PUBLIC_IP:8000

# Ollama API
http://PUBLIC_IP:11434

# Health check
curl http://PUBLIC_IP:8000/health
```

### Create First User
```bash
# Register via API
curl -X POST http://PUBLIC_IP:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "YourSecurePassword123!",
    "email": "admin@example.com"
  }'

# OR create via frontend at http://PUBLIC_IP:3000
```

---

## 💰 Cost Management

### Estimated Costs (us-west-2)
- **g4dn.2xlarge:** ~$0.752/hour (~$18/day)
- **EBS gp3 200GB:** ~$16/month
- **Data Transfer:** Variable (first 100GB/month free)

**Total:** ~$554/month if running 24/7

### Cost Savings Tips

#### 1. Stop Instance When Not in Use
```bash
# Stop instance (keeps EBS volume)
aws ec2 stop-instances --region us-west-2 --instance-ids $INSTANCE_ID

# Cost while stopped: Only EBS (~$16/month)
# Savings: ~$538/month (~97% reduction)

# Start instance when needed
aws ec2 start-instances --region us-west-2 --instance-ids $INSTANCE_ID
```

#### 2. Use Spot Instances (70% discount)
```bash
# Launch as spot instance
aws ec2 run-instances \
    --instance-market-options '{"MarketType":"spot","SpotOptions":{"SpotInstanceType":"one-time","InstanceInterruptionBehavior":"stop"}}' \
    # ... rest of parameters ...

# Cost: ~$0.226/hour (vs $0.752 on-demand)
# Note: Can be interrupted if capacity needed
```

#### 3. Scheduled Start/Stop with Lambda
```bash
# Create Lambda function to stop at night, start in morning
# Example: 8am-6pm = 10 hours/day = $225/month (59% savings)
```

#### 4. Use Smaller Instance for Development
```bash
# g4dn.xlarge: $0.526/hour (1 GPU, 4 vCPU, 16GB RAM)
# Savings: 30% reduction, still has GPU
```

### Why Cloud-Init vs AMI?

| Approach | Pros | Cons | Cost |
|----------|------|------|------|
| **Cloud-Init** ✅ | Always latest code, no AMI storage, version controlled | 10-15 min setup | Free |
| **AMI** | Faster launch (2-3 min) | Outdated code, storage costs, manual updates | ~$5-10/month per AMI |

**Recommendation:** Use cloud-init. The 10-minute setup is worth the cost savings and guaranteed fresh deployment.

---

## 🔒 Security Best Practices

### 1. Restrict Security Group
```bash
# Instead of 0.0.0.0/0, use your IP
MY_IP=$(curl -s ifconfig.me)

aws ec2 authorize-security-group-ingress \
    --region us-west-2 \
    --group-id $SG_ID \
    --protocol tcp \
    --port 22 \
    --cidr $MY_IP/32 \
    --group-rule-description "SSH from my IP only"
```

### 2. Use Session Manager (No SSH Key Needed)
```bash
# Install Session Manager plugin
# https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

# Connect without SSH key
aws ssm start-session --target $INSTANCE_ID
```

### 3. Enable Encryption
```bash
# Use encrypted EBS volumes
--block-device-mappings 'DeviceName=/dev/sda1,Ebs={VolumeSize=200,VolumeType=gp3,Encrypted=true,DeleteOnTermination=true}'
```

### 4. Use IAM Roles (Not Access Keys)
```bash
# Attach IAM role to instance for AWS service access
# Avoid embedding AWS credentials in code
```

---

## 🔄 Update & Maintenance

### Update to Latest RAG Lab Version
```bash
# SSH into instance
ssh -i rag-lab-key.pem ubuntu@$PUBLIC_IP

# Run update script (created by cloud-init)
/home/ubuntu/update-rag-lab.sh

# OR manually:
cd /home/ubuntu/rag_lab
git pull origin security
docker compose down
docker compose build
docker compose up -d
```

### Pull Additional Ollama Models
```bash
# List available models
docker exec ollama ollama list

# Pull models
docker exec ollama ollama pull llama3.2:3b      # Smaller, faster
docker exec ollama ollama pull llama3.1:70b     # Larger, better quality
docker exec ollama ollama pull mistral:7b       # Alternative model
docker exec ollama ollama pull codellama:13b    # Code-focused
```

### Backup Data
```bash
# Create EBS snapshot
aws ec2 create-snapshot \
    --region us-west-2 \
    --volume-id vol-xxxxx \
    --description "RAG Lab backup $(date +%Y-%m-%d)"

# OR backup to S3
ssh -i rag-lab-key.pem ubuntu@$PUBLIC_IP \
    "cd /home/ubuntu/rag_lab && tar -czf - data/" | \
    aws s3 cp - s3://my-bucket/rag-lab-backup-$(date +%Y%m%d).tar.gz
```

---

## 🐛 Troubleshooting

### Check Cloud-Init Status
```bash
# View full log
cat /var/log/cloud-init-output.log

# Check for errors
grep -i error /var/log/cloud-init-output.log

# Cloud-init status
cloud-init status --long
```

### GPU Not Available
```bash
# Check NVIDIA driver
nvidia-smi

# If not working, may need reboot after driver install
sudo reboot

# Check Docker GPU access
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi
```

### Services Not Starting
```bash
cd /home/ubuntu/rag_lab

# Check service status
docker compose ps

# View logs
docker compose logs -f

# Restart services
docker compose restart

# Rebuild if needed
docker compose down
docker compose build --no-cache
docker compose up -d
```

### Frontend Returns 502/504
```bash
# Services still starting, wait 5-10 minutes
docker compose ps

# Check API Gateway is healthy
curl http://localhost:8000/health

# Check frontend logs
docker compose logs frontend
```

---

## 📊 Monitoring

### CloudWatch (Optional)
```bash
# Install CloudWatch agent
wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb
sudo dpkg -i amazon-cloudwatch-agent.deb

# Configure agent to send:
# - Docker metrics
# - GPU metrics (nvidia-smi)
# - Application logs
```

### Grafana Dashboard (Optional)
```bash
# Add Grafana to docker-compose.yml
# Monitor RAG Lab metrics in real-time
```

---

## 🚀 Advanced Configurations

### Auto-Scaling Group
```bash
# Create launch template from cloud-init
# Use ALB for load balancing
# Scale based on GPU utilization
```

### Multi-Region Deployment
```bash
# Launch in multiple regions
# Use Route53 for geographic routing
# Replicate vector database
```

### Production Deployment
```bash
# Use RDS for auth database
# Use S3 for document storage
# Use ElastiCache for Redis
# Use ECS/EKS for orchestration
```

---

## 📝 Instance Management Commands

```bash
# Describe instance
aws ec2 describe-instances --instance-ids $INSTANCE_ID

# Stop instance (save costs)
aws ec2 stop-instances --instance-ids $INSTANCE_ID

# Start instance
aws ec2 start-instances --instance-ids $INSTANCE_ID

# Reboot instance
aws ec2 reboot-instances --instance-ids $INSTANCE_ID

# Terminate instance (delete)
aws ec2 terminate-instances --instance-ids $INSTANCE_ID

# Create AMI from instance (optional)
aws ec2 create-image \
    --instance-id $INSTANCE_ID \
    --name "RAG-Lab-$(date +%Y%m%d)" \
    --description "RAG Lab with all services"
```

---

## 📚 Additional Resources

- [AWS EC2 Documentation](https://docs.aws.amazon.com/ec2/)
- [g4dn Instance Details](https://aws.amazon.com/ec2/instance-types/g4/)
- [Cloud-Init Documentation](https://cloudinit.readthedocs.io/)
- [NVIDIA Docker Guide](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

## ✅ Success Checklist

- [ ] AWS CLI v2 installed and configured
- [ ] SSH key pair created
- [ ] Cloud-init script validated
- [ ] Security group created with required ports
- [ ] Instance launched successfully
- [ ] Cloud-init completed (check logs)
- [ ] GPU available (nvidia-smi works)
- [ ] Docker services running (15 services)
- [ ] Frontend accessible (http://PUBLIC_IP:3000)
- [ ] API accessible (http://PUBLIC_IP:8000)
- [ ] User account created
- [ ] Test query successful

---

**Deployment Time:** 10-15 minutes automated  
**Cost:** ~$18/day running, ~$0.50/day stopped  
**Maintenance:** Auto-updates via cloud-init or update script

---

*Happy deploying! 🚀*

