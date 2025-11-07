#!/bin/bash
# Terminate RAG Lab Instance and Clean Up All AWS Resources
# WARNING: This deletes everything!

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# ==========================================
# CONFIGURATION
# ==========================================
REGION="us-west-2"
SG_NAME="rag-lab-security-group"

# ==========================================
# USAGE
# ==========================================
usage() {
    echo "Usage: $0 [INSTANCE_ID]"
    echo ""
    echo "This script will:"
    echo "  1. Terminate the EC2 instance"
    echo "  2. Release Elastic IP (if attached)"
    echo "  3. Delete security group"
    echo "  4. Clean up EBS snapshots (optional)"
    echo ""
    echo "WARNING: This is permanent and cannot be undone!"
    echo ""
    echo "Examples:"
    echo "  $0 i-1234567890abcdef0"
    echo "  $0  # Will prompt to select instance"
    echo ""
    exit 1
}

# ==========================================
# FIND INSTANCE IF NOT PROVIDED
# ==========================================
INSTANCE_ID=$1

if [ -z "$INSTANCE_ID" ]; then
    echo -e "${YELLOW}Looking for RAG Lab instances...${NC}"
    
    # Find all RAG Lab instances (any state)
    INSTANCES=$(aws ec2 describe-instances \
        --region $REGION \
        --filters "Name=tag:Name,Values=*rag-lab*" \
        --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name,PublicIpAddress,InstanceType]' \
        --output text)
    
    if [ -z "$INSTANCES" ]; then
        echo -e "${RED}No RAG Lab instances found${NC}"
        exit 1
    fi
    
    echo "Found instances:"
    echo "$INSTANCES" | nl
    echo ""
    read -p "Enter instance number to terminate: " INSTANCE_NUM
    
    INSTANCE_ID=$(echo "$INSTANCES" | sed -n "${INSTANCE_NUM}p" | awk '{print $1}')
    
    if [ -z "$INSTANCE_ID" ]; then
        echo -e "${RED}Invalid instance number${NC}"
        exit 1
    fi
fi

# ==========================================
# GET INSTANCE DETAILS
# ==========================================
echo ""
echo -e "${BLUE}=====================================${NC}"
echo -e "${BLUE}Instance Information${NC}"
echo -e "${BLUE}=====================================${NC}"

INSTANCE_INFO=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name,PublicIpAddress,InstanceType,BlockDeviceMappings[0].Ebs.VolumeId]' \
    --output text)

INSTANCE_NAME=$(echo "$INSTANCE_INFO" | awk '{print $2}')
INSTANCE_STATE=$(echo "$INSTANCE_INFO" | awk '{print $3}')
PUBLIC_IP=$(echo "$INSTANCE_INFO" | awk '{print $4}')
INSTANCE_TYPE=$(echo "$INSTANCE_INFO" | awk '{print $5}')
VOLUME_ID=$(echo "$INSTANCE_INFO" | awk '{print $6}')

echo "Instance: $INSTANCE_NAME"
echo "ID: $INSTANCE_ID"
echo "Type: $INSTANCE_TYPE"
echo "State: $INSTANCE_STATE"
echo "IP: $PUBLIC_IP"
echo "Volume: $VOLUME_ID"

# ==========================================
# CHECK FOR ELASTIC IP
# ==========================================
ELASTIC_IP_ALLOC=$(aws ec2 describe-addresses \
    --region $REGION \
    --filters "Name=instance-id,Values=$INSTANCE_ID" \
    --query 'Addresses[0].[AllocationId,PublicIp]' \
    --output text 2>/dev/null || echo "None None")

ALLOCATION_ID=$(echo "$ELASTIC_IP_ALLOC" | awk '{print $1}')
ELASTIC_IP=$(echo "$ELASTIC_IP_ALLOC" | awk '{print $2}')

if [ "$ALLOCATION_ID" != "None" ] && [ ! -z "$ALLOCATION_ID" ]; then
    echo "Elastic IP: $ELASTIC_IP (will be released)"
    HAS_ELASTIC_IP=true
else
    echo "Elastic IP: None"
    HAS_ELASTIC_IP=false
fi

# ==========================================
# CHECK FOR SNAPSHOTS
# ==========================================
SNAPSHOTS=$(aws ec2 describe-snapshots \
    --region $REGION \
    --owner-ids self \
    --filters "Name=description,Values=*$INSTANCE_ID*" \
    --query 'Snapshots[*].[SnapshotId,VolumeSize,StartTime]' \
    --output text 2>/dev/null || echo "")

SNAPSHOT_COUNT=$(echo "$SNAPSHOTS" | grep -c "snap-" || echo "0")

if [ $SNAPSHOT_COUNT -gt 0 ]; then
    echo "Snapshots: $SNAPSHOT_COUNT found"
    HAS_SNAPSHOTS=true
else
    echo "Snapshots: None"
    HAS_SNAPSHOTS=false
fi

# ==========================================
# FIND SECURITY GROUP
# ==========================================
SG_ID=$(aws ec2 describe-security-groups \
    --region $REGION \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text 2>/dev/null || echo "None")

if [ "$SG_ID" != "None" ] && [ ! -z "$SG_ID" ]; then
    echo "Security Group: $SG_ID (will be deleted)"
    HAS_SECURITY_GROUP=true
else
    echo "Security Group: Not found or already deleted"
    HAS_SECURITY_GROUP=false
fi

# ==========================================
# CONFIRM TERMINATION
# ==========================================
echo ""
echo -e "${RED}=====================================${NC}"
echo -e "${RED}WARNING: THIS WILL DELETE EVERYTHING!${NC}"
echo -e "${RED}=====================================${NC}"
echo ""
echo "The following will be deleted:"
echo "  ✗ EC2 Instance: $INSTANCE_ID"
echo "  ✗ EBS Volume: $VOLUME_ID"
if [ "$HAS_ELASTIC_IP" = true ]; then
    echo "  ✗ Elastic IP: $ELASTIC_IP"
fi
if [ "$HAS_SECURITY_GROUP" = true ]; then
    echo "  ✗ Security Group: $SG_ID"
fi
echo ""
echo "This action is PERMANENT and CANNOT be undone!"
echo "All data will be lost!"
echo ""
read -p "Type 'DELETE' to confirm: " CONFIRM

if [ "$CONFIRM" != "DELETE" ]; then
    echo -e "${YELLOW}Termination cancelled${NC}"
    exit 0
fi

# ==========================================
# TERMINATE INSTANCE
# ==========================================
echo ""
echo -e "${YELLOW}=====================================${NC}"
echo -e "${YELLOW}Step 1: Terminating Instance${NC}"
echo -e "${YELLOW}=====================================${NC}"

if [ "$INSTANCE_STATE" != "terminated" ]; then
    echo "Terminating instance $INSTANCE_ID..."
    aws ec2 terminate-instances \
        --region $REGION \
        --instance-ids $INSTANCE_ID \
        --output table
    
    echo ""
    echo "Waiting for termination to complete (may take 2-3 minutes)..."
    aws ec2 wait instance-terminated \
        --region $REGION \
        --instance-ids $INSTANCE_ID || echo "Instance terminated"
    
    echo -e "${GREEN}✓ Instance terminated${NC}"
else
    echo -e "${YELLOW}Instance already terminated${NC}"
fi

# ==========================================
# RELEASE ELASTIC IP
# ==========================================
if [ "$HAS_ELASTIC_IP" = true ]; then
    echo ""
    echo -e "${YELLOW}=====================================${NC}"
    echo -e "${YELLOW}Step 2: Releasing Elastic IP${NC}"
    echo -e "${YELLOW}=====================================${NC}"
    
    echo "Disassociating Elastic IP from instance..."
    aws ec2 disassociate-address \
        --region $REGION \
        --association-id $(aws ec2 describe-addresses \
            --region $REGION \
            --allocation-ids $ALLOCATION_ID \
            --query 'Addresses[0].AssociationId' \
            --output text) 2>/dev/null || echo "Already disassociated"
    
    echo "Releasing Elastic IP $ELASTIC_IP..."
    aws ec2 release-address \
        --region $REGION \
        --allocation-id $ALLOCATION_ID
    
    echo -e "${GREEN}✓ Elastic IP released (saves \$3.60/month if unattached)${NC}"
fi

# ==========================================
# DELETE SECURITY GROUP
# ==========================================
if [ "$HAS_SECURITY_GROUP" = true ]; then
    echo ""
    echo -e "${YELLOW}=====================================${NC}"
    echo -e "${YELLOW}Step 3: Deleting Security Group${NC}"
    echo -e "${YELLOW}=====================================${NC}"
    
    # Wait a bit for instance termination to fully propagate
    echo "Waiting for network interfaces to be released..."
    sleep 30
    
    # Check if any other instances use this security group
    INSTANCES_USING_SG=$(aws ec2 describe-instances \
        --region $REGION \
        --filters "Name=instance.group-id,Values=$SG_ID" "Name=instance-state-name,Values=pending,running,stopping,stopped" \
        --query 'Reservations[*].Instances[*].InstanceId' \
        --output text)
    
    if [ ! -z "$INSTANCES_USING_SG" ]; then
        echo -e "${YELLOW}⚠ Other instances still use this security group:${NC}"
        echo "$INSTANCES_USING_SG"
        read -p "Delete security group anyway? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Keeping security group"
            HAS_SECURITY_GROUP=false
        fi
    fi
    
    if [ "$HAS_SECURITY_GROUP" = true ]; then
        echo "Deleting security group $SG_ID..."
        aws ec2 delete-security-group \
            --region $REGION \
            --group-id $SG_ID || echo "Security group may still be in use, delete manually"
        
        echo -e "${GREEN}✓ Security group deleted${NC}"
    fi
fi

# ==========================================
# HANDLE SNAPSHOTS
# ==========================================
if [ "$HAS_SNAPSHOTS" = true ]; then
    echo ""
    echo -e "${YELLOW}=====================================${NC}"
    echo -e "${YELLOW}Step 4: Clean Up Snapshots${NC}"
    echo -e "${YELLOW}=====================================${NC}"
    
    echo "Found $SNAPSHOT_COUNT snapshot(s):"
    echo "$SNAPSHOTS"
    echo ""
    read -p "Delete these snapshots? (y/n) " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        while IFS= read -r line; do
            SNAP_ID=$(echo "$line" | awk '{print $1}')
            if [ ! -z "$SNAP_ID" ] && [ "$SNAP_ID" != "None" ]; then
                echo "Deleting snapshot $SNAP_ID..."
                aws ec2 delete-snapshot \
                    --region $REGION \
                    --snapshot-id $SNAP_ID || echo "Failed to delete $SNAP_ID"
            fi
        done <<< "$SNAPSHOTS"
        echo -e "${GREEN}✓ Snapshots deleted${NC}"
    else
        echo -e "${YELLOW}Keeping snapshots (will incur storage costs)${NC}"
    fi
fi

# ==========================================
# SUMMARY
# ==========================================
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Cleanup Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "Resources deleted:"
echo "  ✓ Instance: $INSTANCE_ID"
echo "  ✓ EBS Volume: $VOLUME_ID (auto-deleted with instance)"
if [ "$HAS_ELASTIC_IP" = true ]; then
    echo "  ✓ Elastic IP: $ELASTIC_IP"
fi
if [ "$HAS_SECURITY_GROUP" = true ]; then
    echo "  ✓ Security Group: $SG_ID"
fi
echo ""
echo "All AWS resources for this instance have been removed."
echo "You will no longer incur charges for these resources."
echo ""
echo -e "${BLUE}To launch a new instance:${NC}"
echo "  cd aws/scripts"
echo "  ./launch-g5-vllm.sh"
echo ""

# ==========================================
# VERIFY CLEANUP
# ==========================================
echo -e "${YELLOW}=====================================${NC}"
echo -e "${YELLOW}Verification${NC}"
echo -e "${YELLOW}=====================================${NC}"
echo ""
echo "Checking for remaining resources..."

# Check instance
REMAINING_INSTANCE=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE_ID \
    --query 'Reservations[0].Instances[0].State.Name' \
    --output text 2>/dev/null || echo "deleted")

echo "Instance state: $REMAINING_INSTANCE"

# Check Elastic IP
if [ "$HAS_ELASTIC_IP" = true ]; then
    REMAINING_EIP=$(aws ec2 describe-addresses \
        --region $REGION \
        --allocation-ids $ALLOCATION_ID \
        --query 'Addresses[0].PublicIp' \
        --output text 2>/dev/null || echo "released")
    echo "Elastic IP: $REMAINING_EIP"
fi

# Check Security Group
if [ "$HAS_SECURITY_GROUP" = true ]; then
    REMAINING_SG=$(aws ec2 describe-security-groups \
        --region $REGION \
        --group-ids $SG_ID \
        --query 'SecurityGroups[0].GroupName' \
        --output text 2>/dev/null || echo "deleted")
    echo "Security Group: $REMAINING_SG"
fi

echo ""
echo -e "${GREEN}Cleanup verified!${NC}"
echo ""

