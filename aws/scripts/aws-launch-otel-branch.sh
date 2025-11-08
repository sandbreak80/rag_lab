#!/bin/bash
# RAG Lab AWS EC2 Launch Script - OTEL BRANCH
# Launches a fresh instance with the otel branch for Phase 2 testing

set -e

# ==========================================
# CONFIGURATION
# ==========================================
INSTANCE_TYPE="g4dn.2xlarge"
REGION="us-west-2"
AMI_ID="ami-00f46ccd1cbfb363e"  # Ubuntu 24.04 LTS in us-west-2
KEY_NAME="bootcamp"              # Your SSH key pair name
VOLUME_SIZE=200                  # GB - increase for large models
INSTANCE_NAME="rag-lab-otel-testing"
BRANCH="otel"

# ==========================================
# COLORS
# ==========================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}RAG Lab AWS EC2 Launcher - OTEL Branch${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""
echo -e "${YELLOW}This will deploy the ${BOLD}otel${NC}${YELLOW} branch for Phase 2 testing${NC}"
echo ""

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

    # API Gateway (port 8080) - alternate
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=8080,ToPort=8080,IpRanges='[{CidrIp=0.0.0.0/0,Description="RAG Lab API Alternate"}]'

    # Ollama (port 11434)
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=11434,ToPort=11434,IpRanges='[{CidrIp=0.0.0.0/0,Description="Ollama API"}]'

    # Grafana (port 3001)
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=3001,ToPort=3001,IpRanges='[{CidrIp=0.0.0.0/0,Description="Grafana"}]'

    # Prometheus (port 9090)
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=9090,ToPort=9090,IpRanges='[{CidrIp=0.0.0.0/0,Description="Prometheus"}]'

    # OTel Collector gRPC (port 4317) - NEW
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=4317,ToPort=4317,IpRanges='[{CidrIp=0.0.0.0/0,Description="OTel Collector gRPC"}]'

    # OTel Collector HTTP (port 4318) - NEW
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=4318,ToPort=4318,IpRanges='[{CidrIp=0.0.0.0/0,Description="OTel Collector HTTP"}]'

    # OTel Metrics (port 8889) - NEW
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=8889,ToPort=8889,IpRanges='[{CidrIp=0.0.0.0/0,Description="OTel Metrics"}]'

    # GQS Metrics (port 9309) - NEW
    aws ec2 authorize-security-group-ingress \
        --region $REGION \
        --group-id $SG_ID \
        --ip-permissions IpProtocol=tcp,FromPort=9309,ToPort=9309,IpRanges='[{CidrIp=0.0.0.0/0,Description="GQS Metrics"}]'

    # cAdvisor (port 9080)
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

CLOUD_INIT_FILE="$(dirname "$0")/../cloud-init/cloud-init-rag-lab-otel.yaml"
if [ ! -f "$CLOUD_INIT_FILE" ]; then
    echo -e "${RED}ERROR: cloud-init-rag-lab-otel.yaml not found!${NC}"
    echo -e "${YELLOW}Creating it from v10...${NC}"
    cp "$(dirname "$0")/../cloud-init/cloud-init-rag-lab-v10.yaml" "$CLOUD_INIT_FILE"
    sed -i 's/git checkout security/git checkout otel/g' "$CLOUD_INIT_FILE"
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
echo -e "${BLUE}Branch: ${BRANCH}${NC}"
echo ""
echo -e "${YELLOW}⚠️  This will create a NEW instance (separate from existing instances)${NC}"
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
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$INSTANCE_NAME},{Key=Branch,Value=$BRANCH},{Key=Purpose,Value=Phase2-Testing}]" \
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
cat > instance-info-otel.txt <<EOF
====================================
RAG Lab EC2 Instance - OTEL BRANCH
====================================

Instance ID: $INSTANCE_ID
Instance Type: $INSTANCE_TYPE
Region: $REGION
Security Group: $SG_ID ($SG_NAME)
Branch: $BRANCH
Purpose: Phase 2 Verification & Hardening Testing

Network:
  Public IP: $PUBLIC_IP
  Public DNS: $PUBLIC_DNS
  Private IP: $PRIVATE_IP

Access URLs (available in 15-20 minutes):
  Frontend: http://$PUBLIC_IP:3000
  API Gateway: http://$PUBLIC_IP:8080
  Ollama: http://$PUBLIC_IP:11434
  Grafana: http://$PUBLIC_IP:3001
  Prometheus: http://$PUBLIC_IP:9090
  OTel Collector (gRPC): http://$PUBLIC_IP:4317
  OTel Collector (HTTP): http://$PUBLIC_IP:4318
  OTel Metrics: http://$PUBLIC_IP:8889
  GQS Metrics: http://$PUBLIC_IP:9309

SSH Access:
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP

Phase 2 Testing Commands:
  # Check deployment status
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "cd rag_lab && docker compose ps"

  # Check OTel Collector
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "curl http://localhost:8889/metrics"

  # Verify GQS seed
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "wc -l rag_lab/evals/gqs_seed.csv"

  # Run evaluation sample
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "cd rag_lab && make seed"

  # Start GQS metrics
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "cd rag_lab && make metrics &"

  # Check cloud-init progress
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "tail -f /var/log/cloud-init-output.log"

  # Check GPU
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "nvidia-smi"

Instance Management:
  Stop Instance (to save costs):
    aws ec2 stop-instances --region $REGION --instance-ids $INSTANCE_ID

  Start Instance:
    aws ec2 start-instances --region $REGION --instance-ids $INSTANCE_ID

  Terminate Instance:
    aws ec2 terminate-instances --region $REGION --instance-ids $INSTANCE_ID

====================================
Estimated Setup Time: 15-20 minutes
====================================

The cloud-init script is installing:
  1. NVIDIA GPU drivers
  2. Docker + NVIDIA Container Toolkit
  3. Ollama with GPU support
  4. RAG Lab OTEL branch (all services)
  5. OTel Collector
  6. GQS evaluation infrastructure
  7. Required Ollama models (llama3.1:8b, nomic-embed-text)

Monitor progress:
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "tail -f /var/log/cloud-init-output.log"

Check if complete:
  ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP "grep 'Cloud-init.*finished' /var/log/cloud-init-output.log"

Post-Deployment Testing:
  See: docs/AWS_DEPLOYMENT_OTEL_BRANCH.md
  Run: 4-phase testing plan (13 tests)

====================================
EOF

# Also update the main instance-info.txt with latest
cp instance-info-otel.txt ../instance-info.txt

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
echo -e "Branch: ${BLUE}$BRANCH${NC}"
echo ""
echo -e "${YELLOW}⏳ Setup in progress (15-20 minutes)${NC}"
echo ""
echo "Access URLs (available soon):"
echo -e "  Frontend: ${GREEN}http://$PUBLIC_IP:3000${NC}"
echo -e "  API: ${GREEN}http://$PUBLIC_IP:8080${NC}"
echo -e "  Grafana: ${GREEN}http://$PUBLIC_IP:3001${NC}"
echo -e "  Prometheus: ${GREEN}http://$PUBLIC_IP:9090${NC}"
echo -e "  OTel Metrics: ${GREEN}http://$PUBLIC_IP:8889/metrics${NC}"
echo -e "  GQS Metrics: ${GREEN}http://$PUBLIC_IP:9309/metrics${NC}"
echo ""
echo "SSH Access:"
echo -e "  ${GREEN}ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP${NC}"
echo ""
echo "Monitor Setup:"
echo -e "  ${GREEN}ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP 'tail -f /var/log/cloud-init-output.log'${NC}"
echo ""
echo -e "📄 Full details saved to: ${GREEN}instance-info-otel.txt${NC}"
echo ""
echo -e "${BLUE}Phase 2 Testing Guide:${NC}"
echo -e "  ${GREEN}cat docs/AWS_DEPLOYMENT_OTEL_BRANCH.md${NC}"
echo ""
echo -e "${YELLOW}TIP: Setup takes 15-20 minutes. Go get a coffee! ☕${NC}"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Wait for setup to complete (~15-20 mins)"
echo "  2. SSH into instance and check services"
echo "  3. Run Phase 1-4 testing (see deployment guide)"
echo "  4. Document results and any issues"
echo ""
echo -e "${GREEN}=====================================${NC}"

