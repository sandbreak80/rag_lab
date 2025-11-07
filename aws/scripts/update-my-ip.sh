#!/bin/bash
# Update EC2 Security Group with Your Current IP
# Use this when your laptop changes networks

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Update Security Group with Current IP${NC}"
echo -e "${GREEN}=====================================${NC}"

# ==========================================
# CONFIGURATION
# ==========================================
SG_NAME="rag-lab-security-group"
REGION="us-west-2"
DESCRIPTION="SSH from my current IP"

# ==========================================
# STEP 1: GET CURRENT IP
# ==========================================
echo ""
echo -e "${YELLOW}Getting your current public IP...${NC}"

CURRENT_IP=$(curl -s https://api.ipify.org)

if [ -z "$CURRENT_IP" ]; then
    echo -e "${RED}ERROR: Could not determine your public IP${NC}"
    exit 1
fi

echo -e "Your current IP: ${GREEN}$CURRENT_IP${NC}"

# ==========================================
# STEP 2: GET SECURITY GROUP ID
# ==========================================
echo ""
echo -e "${YELLOW}Finding security group...${NC}"

SG_ID=$(aws ec2 describe-security-groups \
    --region $REGION \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "None")

if [ "$SG_ID" = "None" ]; then
    echo -e "${RED}ERROR: Security group '$SG_NAME' not found${NC}"
    echo "Available security groups:"
    aws ec2 describe-security-groups \
        --region $REGION \
        --query 'SecurityGroups[*].[GroupName,GroupId]' \
        --output table
    exit 1
fi

echo -e "Security Group: ${GREEN}$SG_ID${NC} ($SG_NAME)"

# ==========================================
# STEP 3: REMOVE OLD IP RULES
# ==========================================
echo ""
echo -e "${YELLOW}Removing old SSH rules...${NC}"

# Get existing SSH rules
OLD_RULES=$(aws ec2 describe-security-groups \
    --region $REGION \
    --group-ids $SG_ID \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`22\`]" \
    --output json)

# Remove each old rule
echo "$OLD_RULES" | jq -c '.[]' | while read rule; do
    # Extract CidrIp if present
    CIDR=$(echo "$rule" | jq -r '.IpRanges[0].CidrIp // empty')

    if [ ! -z "$CIDR" ]; then
        echo "  Removing rule for $CIDR"
        aws ec2 revoke-security-group-ingress \
            --region $REGION \
            --group-id $SG_ID \
            --protocol tcp \
            --port 22 \
            --cidr "$CIDR" 2>/dev/null || echo "    (already removed)"
    fi
done

echo -e "${GREEN}✓ Old rules removed${NC}"

# ==========================================
# STEP 4: ADD NEW IP RULE
# ==========================================
echo ""
echo -e "${YELLOW}Adding rule for your current IP...${NC}"

aws ec2 authorize-security-group-ingress \
    --region $REGION \
    --group-id $SG_ID \
    --ip-permissions \
        IpProtocol=tcp,FromPort=22,ToPort=22,IpRanges="[{CidrIp=${CURRENT_IP}/32,Description=\"${DESCRIPTION}\"}]" \
    2>/dev/null || echo "  (rule already exists)"

echo -e "${GREEN}✓ Rule added for ${CURRENT_IP}/32${NC}"

# ==========================================
# STEP 5: VERIFY
# ==========================================
echo ""
echo -e "${YELLOW}Current SSH rules:${NC}"
aws ec2 describe-security-groups \
    --region $REGION \
    --group-ids $SG_ID \
    --query "SecurityGroups[0].IpPermissions[?FromPort==\`22\`].IpRanges[*].[CidrIp,Description]" \
    --output table

# ==========================================
# SUMMARY
# ==========================================
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Update Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "Security Group: $SG_ID"
echo "Your IP: $CURRENT_IP/32"
echo "Port 22 (SSH) is now accessible from your current location."
echo ""
echo -e "${YELLOW}TIP: Run this script whenever you change networks${NC}"
echo ""
echo "Or add to your shell profile:"
echo "  alias update-sg='~/rag_lab/update-my-ip.sh'"
echo ""
echo -e "${GREEN}=====================================${NC}"

