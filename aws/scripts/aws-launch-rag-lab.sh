#!/bin/bash
# RAG Lab AWS EC2 Launch Script
# Uses AWS CLI v2 to launch g4dn.2xlarge instance with cloud-init

set -e

# ==========================================
# CONFIGURATION
# ==========================================
INSTANCE_TYPE="g4dn.2xlarge"
REGION="us-west-2"
AMI_ID="ami-00f46ccd1cbfb363e"  # Ubuntu 24.04 LTS in us-west-2
KEY_NAME="bootcamp"              # Your SSH key pair name
VOLUME_SIZE=200                  # GB - increase for large models
INSTANCE_NAME="rag-lab-gpu"

# ==========================================
# COLORS
# ==========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}RAG Lab AWS EC2 Launcher${NC}"
echo -e "${GREEN}=====================================${NC}"

# ==========================================
# STEP 1: CREATE SECURITY GROUP
# ==========================================
echo -e "\n${YELLOW}Step 1: Setting up Security Group${NC}"

SG_NAME="rag-lab-security-group"
SG_DESCRIPTION="Security group for RAG Lab with GPU"

# Check if security group exists
SG_ID=$(aws ec2 describe-security-groups \
    --region $REGION \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "None")

if [ "$SG_ID" = "None" ]; then
    echo "Creating new security group: $SG_NAME"
    SG_ID=$(aws ec2 create-security-group \
        --region $REGION \
        --group-name $SG_NAME \
        --description "$SG_DESCRIPTION" \
        --query 'GroupId' \
        --output text)

    echo "Security Group ID: $SG_ID"

    # Add ingress rules
    echo "Adding ingress rules..."

    # SSH (port 22)
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges='[{CidrIp=0.0.0.0/0,Description="SSH access"}]'

    # Frontend (port 3000)
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=3000,ToPort=3000,IpRanges='[{CidrIp=0.0.0.0/0,Description="RAG Lab Frontend"}]'

    # API Gateway (port 8000)
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=8000,ToPort=8000,IpRanges='[{CidrIp=0.0.0.0/0,Description="RAG Lab API Gateway"}]'

    # Ollama (port 11434) - optional, for external access
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=11434,ToPort=11434,IpRanges='[{CidrIp=0.0.0.0/0,Description="Ollama API"}]'

    # Grafana (port 3001) - for monitoring dashboard
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=3001,ToPort=3001,IpRanges='[{CidrIp=0.0.0.0/0,Description="Grafana"}]'

    # Prometheus (port 9090) - for metrics collection
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=9090,ToPort=9090,IpRanges='[{CidrIp=0.0.0.0/0,Description="Prometheus"}]'

    # cAdvisor (port 9080) - for container metrics
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=9080,ToPort=9080,IpRanges='[{CidrIp=0.0.0.0/0,Description="cAdvisor"}]'

    echo -e "${GREEN}✓ Security group created and configured${NC}"
else
    echo -e "${GREEN}✓ Using existing security group: $SG_ID${NC}"
fi

# ==========================================
# STEP 2: VALIDATE CLOUD-INIT SCRIPT
# ==========================================
echo -e "\n${YELLOW}Step 2: Validating cloud-init script${NC}"

CLOUD_INIT_FILE="$(dirname "$0")/../cloud-init/cloud-init-rag-lab-v10.yaml"
if [ ! -f "$CLOUD_INIT_FILE" ]; then
    echo -e "${YELLOW}v10 not found, trying v9...${NC}"
    CLOUD_INIT_FILE="$(dirname "$0")/../cloud-init/cloud-init-rag-lab-v9.yaml"
    if [ ! -f "$CLOUD_INIT_FILE" ]; then
        echo -e "${YELLOW}v9 not found, trying v3...${NC}"
        CLOUD_INIT_FILE="$(dirname "$0")/../cloud-init/cloud-init-rag-lab-v3.yaml"
    fi
fi
if [ ! -f "$CLOUD_INIT_FILE" ]; then
    echo -e "${YELLOW}cloud-init-rag-lab-v3.yaml not found, trying v2...${NC}"
    CLOUD_INIT_FILE="$(dirname "$0")/../cloud-init/cloud-init-rag-lab-v2.yaml"
    if [ ! -f "$CLOUD_INIT_FILE" ]; then
        echo -e "${YELLOW}v2 not found, trying v1...${NC}"
        CLOUD_INIT_FILE="$(dirname "$0")/../cloud-init/cloud-init-rag-lab.yaml"
        if [ ! -f "$CLOUD_INIT_FILE" ]; then
            echo -e "${RED}ERROR: No cloud-init file found!${NC}"
            exit 1
        fi
    fi
fi

echo "Using cloud-init: $(basename $CLOUD_INIT_FILE)"

echo -e "${GREEN}✓ Cloud-init script found${NC}"

# ==========================================
# STEP 3: LAUNCH EC2 INSTANCE
# ==========================================
echo -e "\n${YELLOW}Step 3: Launching EC2 Instance${NC}"
echo "Instance Type: $INSTANCE_TYPE"
echo "Region: $REGION"
echo "AMI: $AMI_ID (Ubuntu 24.04 LTS)"
echo "Volume Size: ${VOLUME_SIZE}GB"
echo ""
read -p "Continue with launch? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Launch cancelled."
    exit 1
fi

echo "Launching instance..."

INSTANCE_ID=$(aws ec2 run-instances \
    --region $REGION \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-group-ids $SG_ID \
    --block-device-mappings "DeviceName=/dev/sda1,Ebs={VolumeSize=$VOLUME_SIZE,VolumeType=gp3,DeleteOnTermination=true}" \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME}]" \
    --user-data file://$CLOUD_INIT_FILE \
    --metadata-options "HttpTokens=required,HttpPutResponseHopLimit=2" \
    --query 'Instances[0].InstanceId' \
    --output text)

echo -e "${GREEN}✓ Instance launched: $INSTANCE_ID${NC}"

# ==========================================
# STEP 4: WAIT FOR INSTANCE TO START
# ==========================================
echo -e "\n${YELLOW}Step 4: Waiting for instance to start${NC}"
echo "This may take 2-3 minutes..."

aws ec2 wait instance-running \
    --region $REGION \
    --instance-ids $INSTANCE_ID

echo -e "${GREEN}✓ Instance is running${NC}"

# ==========================================
# STEP 5: GET INSTANCE DETAILS
# ==========================================
echo -e "\n${YELLOW}Step 5: Getting instance details${NC}"

INSTANCE_INFO=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].[PublicIpAddress,PublicDnsName,PrivateIpAddress]' \
    --output text)

PUBLIC_IP=$(echo $INSTANCE_INFO | awk '{print $1}')
PUBLIC_DNS=$(echo $INSTANCE_INFO | awk '{print $2}')
PRIVATE_IP=$(echo $INSTANCE_INFO | awk '{print $3}')

# ==========================================
# STEP 6: SAVE INSTANCE INFO
# ==========================================
cat > instance-info.txt <<EOF
====================================
RAG Lab EC2 Instance Information
====================================

Instance ID: $INSTANCE_ID
Instance Type: $INSTANCE_TYPE
Region: $REGION
Security Group: $SG_ID ($SG_NAME)

Network:
  Public IP: $PUBLIC_IP
  Public DNS: $PUBLIC_DNS
  Private IP: $PRIVATE_IP

Access URLs (available in 10-15 minutes):
  Frontend: http://$PUBLIC_IP:3000
  API Gateway: http://$PUBLIC_IP:8000
  Ollama: http://$PUBLIC_IP:11434

SSH Access:
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP

Useful Commands:
  # Check cloud-init progress
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "tail -f /var/log/cloud-init-output.log"

  # Check deployment status
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "cat /home/ubuntu/deployment-info.txt"

  # Check Docker services
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "cd rag_lab && docker compose ps"

  # Check GPU
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "nvidia-smi"

Update to Latest Version:
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "/home/ubuntu/update-rag-lab.sh"

Stop Instance (to save costs):
  aws ec2 stop-instances --region $REGION --instance-ids $INSTANCE_ID

Start Instance:
  aws ec2 start-instances --region $REGION --instance-ids $INSTANCE_ID

Terminate Instance:
  aws ec2 terminate-instances --region $REGION --instance-ids $INSTANCE_ID

====================================
Estimated Setup Time: 10-15 minutes
====================================

The cloud-init script is installing:
  1. NVIDIA GPU drivers
  2. Docker + NVIDIA Container Toolkit
  3. Ollama with GPU support
  4. RAG Lab (all 15 microservices)
  5. Required Ollama models (llama3.1:8b, nomic-embed-text)

Monitor progress:
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "tail -f /var/log/cloud-init-output.log"

Check if complete:
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "cat /var/log/cloud-init-output.log | grep 'Cloud-init.*finished'"

====================================
EOF

# ==========================================
# SUMMARY
# ==========================================
echo -e "\n${GREEN}=====================================${NC}"
echo -e "${GREEN}Launch Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "Instance ID: ${GREEN}$INSTANCE_ID${NC}"
echo -e "Public IP: ${GREEN}$PUBLIC_IP${NC}"
echo -e "Public DNS: ${GREEN}$PUBLIC_DNS${NC}"
echo ""
echo -e "${YELLOW}⏳ Setup in progress (10-15 minutes)${NC}"
echo ""
echo "Access URLs (available soon):"
echo -e "  Frontend: ${GREEN}http://$PUBLIC_IP:3000${NC}"
echo -e "  API: ${GREEN}http://$PUBLIC_IP:8000${NC}"
echo ""
echo "SSH Access:"
echo -e "  ${GREEN}ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP${NC}"
echo ""
echo "Monitor Setup:"
echo -e "  ${GREEN}ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP 'tail -f /var/log/cloud-init-output.log'${NC}"
echo ""
echo -e "📄 Full details saved to: ${GREEN}instance-info.txt${NC}"
echo ""
echo -e "${YELLOW}TIP: Setup takes 10-15 minutes. Go get a coffee! ☕${NC}"
echo -e "${GREEN}=====================================${NC}"

