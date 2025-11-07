#!/bin/bash
# RAG Lab AWS EC2 Launch Script - g5.2xlarge with vLLM Support
# NVIDIA A10G GPU (Ampere architecture) - Supports vLLM

set -e

# ==========================================
# CONFIGURATION
# ==========================================
INSTANCE_TYPE="g5.2xlarge"
REGION="us-west-2"
AMI_ID="ami-00f46ccd1cbfb363e"  # Ubuntu 24.04 LTS
KEY_NAME="bootcamp"              # Your SSH key pair name
VOLUME_SIZE=300                  # GB - larger for models
INSTANCE_NAME="rag-lab-g5-vllm"

# ==========================================
# COLORS
# ==========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}RAG Lab - g5.2xlarge with vLLM${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "${BLUE}Instance Type:${NC} g5.2xlarge"
echo -e "${BLUE}GPU:${NC} NVIDIA A10G Tensor Core (24GB VRAM)"
echo -e "${BLUE}Architecture:${NC} Ampere (vLLM supported ✅)"
echo -e "${BLUE}Cost:${NC} ~\$1.21/hour (~\$29/day)"
echo ""

# ==========================================
# GPU COMPARISON
# ==========================================
echo -e "${YELLOW}GPU Comparison:${NC}"
echo "┌─────────────────┬─────────────┬─────────────┐"
echo "│                 │   g4dn      │     g5      │"
echo "├─────────────────┼─────────────┼─────────────┤"
echo "│ GPU             │ T4 (Turing) │ A10G (Amp.) │"
echo "│ VRAM            │ 16GB        │ 24GB        │"
echo "│ vLLM Support    │ ❌ NO       │ ✅ YES      │"
echo "│ Cost/hour       │ \$0.752     │ \$1.212     │"
echo "│ Cost/day        │ \$18        │ \$29        │"
echo "│ Performance     │ Base        │ +50% faster │"
echo "└─────────────────┴─────────────┴─────────────┘"
echo ""

# ==========================================
# PREREQUISITES CHECK
# ==========================================
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    echo -e "${RED}ERROR: AWS CLI not found${NC}"
    echo "Install: https://aws.amazon.com/cli/"
    exit 1
fi

# Check cloud-init script
CLOUD_INIT_SCRIPT="../cloud-init/cloud-init-vllm-g5.yaml"
if [ ! -f "$CLOUD_INIT_SCRIPT" ]; then
    echo -e "${RED}ERROR: $CLOUD_INIT_SCRIPT not found${NC}"
    exit 1
fi

# Check GitHub secret
SECRET_CHECK=$(aws secretsmanager describe-secret \
    --secret-id rag-lab/github-token \
    --region $REGION 2>&1 || echo "NOT_FOUND")

if [[ $SECRET_CHECK == *"NOT_FOUND"* ]] || [[ $SECRET_CHECK == *"ResourceNotFoundException"* ]]; then
    echo -e "${RED}ERROR: GitHub token not found in Secrets Manager${NC}"
    echo "Please run: ./setup-github-secret.sh"
    exit 1
fi

echo -e "${GREEN}✓ All prerequisites met${NC}"

# ==========================================
# SECURITY GROUP
# ==========================================
echo ""
echo -e "${YELLOW}Setting up Security Group...${NC}"

SG_NAME="rag-lab-security-group"
SG_ID=$(aws ec2 describe-security-groups \
    --region $REGION \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "None")

if [ "$SG_ID" = "None" ]; then
    echo "Creating new security group..."
    SG_ID=$(aws ec2 create-security-group \
        --region $REGION \
        --group-name $SG_NAME \
        --description "Security group for RAG Lab with GPU" \
        --query 'GroupId' \
        --output text)
    
    # Add rules
    aws ec2 authorize-security-group-ingress --region $REGION --group-id $SG_ID \
        --ip-permissions \
        IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges='[{CidrIp=0.0.0.0/0,Description="SSH"}]' \
        IpProtocol=tcp,FromPort=3000,ToPort=3000,IpRanges='[{CidrIp=0.0.0.0/0,Description="Frontend"}]' \
        IpProtocol=tcp,FromPort=8000,ToPort=8000,IpRanges='[{CidrIp=0.0.0.0/0,Description="API Gateway"}]' \
        IpProtocol=tcp,FromPort=11434,ToPort=11434,IpRanges='[{CidrIp=0.0.0.0/0,Description="Ollama"}]' \
        IpProtocol=tcp,FromPort=8001,ToPort=8001,IpRanges='[{CidrIp=0.0.0.0/0,Description="vLLM API"}]'
    
    echo -e "${GREEN}✓ Security group created: $SG_ID${NC}"
else
    echo -e "${GREEN}✓ Using existing security group: $SG_ID${NC}"
fi

# ==========================================
# LAUNCH CONFIRMATION
# ==========================================
echo ""
echo -e "${YELLOW}Ready to launch:${NC}"
echo "  Instance: $INSTANCE_TYPE"
echo "  GPU: NVIDIA A10G (24GB)"
echo "  Storage: ${VOLUME_SIZE}GB"
echo "  Cost: ~\$1.21/hour (~\$29/day)"
echo "  Features: vLLM + Ollama + RAG Lab"
echo ""
read -p "Continue with launch? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Launch cancelled."
    exit 1
fi

# ==========================================
# LAUNCH INSTANCE
# ==========================================
echo ""
echo -e "${YELLOW}Launching instance...${NC}"

INSTANCE_ID=$(aws ec2 run-instances \
    --region $REGION \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --iam-instance-profile Name=RAGLabEC2InstanceProfile \
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=$VOLUME_SIZE,VolumeType=gp3,DeleteOnTermination=true,Encrypted=true}" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --user-data file://$CLOUD_INIT_SCRIPT \
    --metadata-options "HttpTokens=required,HttpPutResponseHopLimit=2" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo -e "${GREEN}✓ Instance launched: $INSTANCE_ID${NC}"

# ==========================================
# WAIT FOR INSTANCE
# ==========================================
echo ""
echo -e "${YELLOW}Waiting for instance to start...${NC}"
aws ec2 wait instance-running --region $REGION --instance-ids $INSTANCE_ID
echo -e "${GREEN}✓ Instance is running${NC}"

# ==========================================
# GET INSTANCE DETAILS
# ==========================================
INSTANCE_INFO=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].[PublicIpAddress,PublicDnsName]' \
    --output text)

PUBLIC_IP=$(echo $INSTANCE_INFO | awk '{print $1}')
PUBLIC_DNS=$(echo $INSTANCE_INFO | awk '{print $2}')

# ==========================================
# SAVE INSTANCE INFO
# ==========================================
cat > instance-g5-info.txt <<EOF
====================================
RAG Lab - g5.2xlarge with vLLM
====================================

Instance Details:
  Instance ID: $INSTANCE_ID
  Instance Type: $INSTANCE_TYPE
  Region: $REGION
  Public IP: $PUBLIC_IP
  Public DNS: $PUBLIC_DNS

GPU Specifications:
  GPU: NVIDIA A10G Tensor Core
  VRAM: 24GB
  Architecture: Ampere (vLLM supported ✅)
  CUDA Cores: 9,216
  Tensor Cores: 320 (3rd gen)
  Ray Tracing Cores: 80

Access URLs (available in 15-20 minutes):
  Frontend: http://$PUBLIC_IP:3000
  API Gateway: http://$PUBLIC_IP:8000
  Ollama API: http://$PUBLIC_IP:11434
  vLLM API: http://$PUBLIC_IP:8001

SSH/Session Manager:
  # Session Manager (recommended)
  aws ssm start-session --target $INSTANCE_ID
  
  # Traditional SSH
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP
  
  # Port forwarding
  aws ssm start-session --target $INSTANCE_ID \\
      --document-name AWS-StartPortForwardingSession \\
      --parameters '{"portNumber":["3000"],"localPortNumber":["3000"]}'

Monitor Setup Progress:
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "tail -f /var/log/cloud-init-output.log"

Check Installation:
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "cat /home/ubuntu/deployment-info.txt"

vLLM Commands (after SSH):
  # Start vLLM server
  sudo systemctl start vllm
  
  # Check vLLM status
  sudo systemctl status vllm
  
  # Test vLLM API
  /home/ubuntu/test-vllm.sh
  
  # Custom model
  /home/ubuntu/start-vllm.sh /home/ubuntu/models/MODEL_NAME 8001

Cost Management:
  # Stop instance (save 98% - only EBS charges)
  aws ec2 stop-instances --region $REGION --instance-ids $INSTANCE_ID
  
  # Start instance
  aws ec2 start-instances --region $REGION --instance-ids $INSTANCE_ID
  
  # Terminate (delete everything)
  aws ec2 terminate-instances --region $REGION --instance-ids $INSTANCE_ID

Cost Breakdown:
  Running: ~\$1.21/hour (~\$29/day, ~\$870/month)
  Stopped: ~\$0.65/day (EBS storage only)
  Savings when stopped: 98%

Performance Comparison (vs g4dn.2xlarge):
  ✅ 50% more VRAM (24GB vs 16GB)
  ✅ vLLM support (Ampere vs Turing)
  ✅ ~50% faster inference
  ✅ Better for large models
  ⚠️  60% more expensive

Recommended Usage:
  - Use g5 for: vLLM, large models (13B+), production inference
  - Use g4dn for: Ollama only, smaller models, cost-sensitive dev

Setup Time: 15-20 minutes (includes vLLM installation)

====================================
EOF

# ==========================================
# SUMMARY
# ==========================================
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Launch Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "Instance ID: ${GREEN}$INSTANCE_ID${NC}"
echo -e "Instance Type: ${BLUE}$INSTANCE_TYPE${NC}"
echo -e "GPU: ${BLUE}NVIDIA A10G (24GB, Ampere)${NC}"
echo -e "Public IP: ${GREEN}$PUBLIC_IP${NC}"
echo ""
echo -e "${YELLOW}⏳ Setup in progress (15-20 minutes)${NC}"
echo ""
echo "What's being installed:"
echo "  1. NVIDIA A10G drivers"
echo "  2. Docker + NVIDIA Container Toolkit"
echo "  3. vLLM (native Python installation)"
echo "  4. Ollama with GPU support"
echo "  5. RAG Lab (all 15 microservices)"
echo ""
echo "Access URLs (will be ready soon):"
echo -e "  Frontend: ${GREEN}http://$PUBLIC_IP:3000${NC}"
echo -e "  API: ${GREEN}http://$PUBLIC_IP:8000${NC}"
echo -e "  vLLM: ${GREEN}http://$PUBLIC_IP:8001${NC}"
echo ""
echo "Monitor setup:"
echo -e "  ${GREEN}ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP 'tail -f /var/log/cloud-init-output.log'${NC}"
echo ""
echo -e "📄 Full details: ${GREEN}instance-g5-info.txt${NC}"
echo ""
echo -e "${YELLOW}Cost: ~\$1.21/hour - Stop when not using to save 98%!${NC}"
echo ""
echo -e "${GREEN}=====================================${NC}"

