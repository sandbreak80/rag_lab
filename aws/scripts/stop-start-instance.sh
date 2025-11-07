#!/bin/bash
# Stop or Start RAG Lab EC2 Instance
# Handles Elastic IP for consistent access

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

# ==========================================
# USAGE
# ==========================================
usage() {
    echo "Usage: $0 {stop|start|status} [INSTANCE_ID]"
    echo ""
    echo "Commands:"
    echo "  stop    - Stop the instance (saves 97% cost!)"
    echo "  start   - Start the instance"
    echo "  status  - Check instance status"
    echo ""
    echo "Examples:"
    echo "  $0 stop i-1234567890abcdef0"
    echo "  $0 start i-1234567890abcdef0"
    echo ""
    exit 1
}

if [ $# -lt 1 ]; then
    usage
fi

COMMAND=$1
INSTANCE_ID=$2

# ==========================================
# FIND INSTANCE IF NOT PROVIDED
# ==========================================
if [ -z "$INSTANCE_ID" ]; then
    echo -e "${YELLOW}Looking for RAG Lab instances...${NC}"

    # Find instances with "rag-lab" in name
    INSTANCES=$(aws ec2 describe-instances \
        --region $REGION \
        --filters "Name=tag:Name,Values=*rag-lab*" "Name=instance-state-name,Values=running,stopped" \
        --query 'Reservations[*].Instances[*].[InstanceId,Tags[?Key==`Name`].Value|[0],State.Name,PublicIpAddress]' \
        --output text)

    if [ -z "$INSTANCES" ]; then
        echo -e "${RED}No RAG Lab instances found${NC}"
        exit 1
    fi

    echo "Found instances:"
    echo "$INSTANCES" | nl
    echo ""
    read -p "Enter instance number: " INSTANCE_NUM

    INSTANCE_ID=$(echo "$INSTANCES" | sed -n "${INSTANCE_NUM}p" | awk '{print $1}')

    if [ -z "$INSTANCE_ID" ]; then
        echo -e "${RED}Invalid instance number${NC}"
        exit 1
    fi
fi

echo -e "${BLUE}Instance ID: $INSTANCE_ID${NC}"

# ==========================================
# GET INSTANCE INFO
# ==========================================
get_instance_info() {
    aws ec2 describe-instances \
        --region $REGION \
        --instance-ids $INSTANCE_ID \
        --query 'Reservations[0].Instances[0].[State.Name,PublicIpAddress,InstanceType,Tags[?Key==`Name`].Value|[0]]' \
        --output text
}

INFO=$(get_instance_info)
CURRENT_STATE=$(echo "$INFO" | awk '{print $1}')
PUBLIC_IP=$(echo "$INFO" | awk '{print $2}')
INSTANCE_TYPE=$(echo "$INFO" | awk '{print $3}')
INSTANCE_NAME=$(echo "$INFO" | awk '{print $4}')

echo "Instance: $INSTANCE_NAME"
echo "Type: $INSTANCE_TYPE"
echo "State: $CURRENT_STATE"
echo "IP: $PUBLIC_IP"

# ==========================================
# CHECK FOR ELASTIC IP
# ==========================================
check_elastic_ip() {
    ELASTIC_IP=$(aws ec2 describe-addresses \
        --region $REGION \
        --filters "Name=instance-id,Values=$INSTANCE_ID" \
        --query 'Addresses[0].PublicIp' \
        --output text 2>/dev/null || echo "None")

    if [ "$ELASTIC_IP" != "None" ] && [ ! -z "$ELASTIC_IP" ]; then
        echo -e "${GREEN}✓ Elastic IP attached: $ELASTIC_IP${NC}"
        echo "  Your URL will remain: http://$ELASTIC_IP"
        return 0
    else
        echo -e "${YELLOW}⚠ No Elastic IP - Public IP will change on restart${NC}"
        echo "  Consider allocating an Elastic IP for consistent access"
        return 1
    fi
}

# ==========================================
# STOP COMMAND
# ==========================================
if [ "$COMMAND" = "stop" ]; then
    echo ""
    echo -e "${YELLOW}=====================================${NC}"
    echo -e "${YELLOW}Stopping Instance${NC}"
    echo -e "${YELLOW}=====================================${NC}"

    if [ "$CURRENT_STATE" = "stopped" ]; then
        echo -e "${GREEN}Instance is already stopped${NC}"
        exit 0
    fi

    if [ "$CURRENT_STATE" != "running" ]; then
        echo -e "${RED}Instance is in state: $CURRENT_STATE${NC}"
        echo "Can only stop running instances"
        exit 1
    fi

    # Show cost savings
    echo ""
    echo -e "${BLUE}Cost Savings:${NC}"
    case $INSTANCE_TYPE in
        g5.2xlarge)
            echo "  Running: ~\$29/day (~\$870/month)"
            echo "  Stopped: ~\$0.65/day (~\$20/month)"
            echo "  Savings: ~\$850/month (98%!)"
            ;;
        g4dn.2xlarge)
            echo "  Running: ~\$18/day (~\$540/month)"
            echo "  Stopped: ~\$0.50/day (~\$15/month)"
            echo "  Savings: ~\$525/month (97%!)"
            ;;
        *)
            echo "  Only pay for EBS storage when stopped"
            ;;
    esac

    echo ""
    check_elastic_ip || true

    echo ""
    read -p "Stop instance $INSTANCE_ID? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi

    echo -e "${YELLOW}Stopping instance...${NC}"
    aws ec2 stop-instances --region $REGION --instance-ids $INSTANCE_ID

    echo "Waiting for instance to stop..."
    aws ec2 wait instance-stopped --region $REGION --instance-ids $INSTANCE_ID

    echo ""
    echo -e "${GREEN}=====================================${NC}"
    echo -e "${GREEN}Instance Stopped Successfully!${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo ""
    echo "EBS volumes are preserved (data safe)"
    echo "Now only paying for storage (~\$0.50-0.65/day)"
    echo ""
    echo "To start again:"
    echo "  $0 start $INSTANCE_ID"
    echo ""

# ==========================================
# START COMMAND
# ==========================================
elif [ "$COMMAND" = "start" ]; then
    echo ""
    echo -e "${YELLOW}=====================================${NC}"
    echo -e "${YELLOW}Starting Instance${NC}"
    echo -e "${YELLOW}=====================================${NC}"

    if [ "$CURRENT_STATE" = "running" ]; then
        echo -e "${GREEN}Instance is already running${NC}"
        echo "Access at: http://$PUBLIC_IP"
        exit 0
    fi

    if [ "$CURRENT_STATE" != "stopped" ]; then
        echo -e "${RED}Instance is in state: $CURRENT_STATE${NC}"
        echo "Can only start stopped instances"
        exit 1
    fi

    # Check for Elastic IP
    HAS_ELASTIC_IP=false
    check_elastic_ip && HAS_ELASTIC_IP=true

    if [ "$HAS_ELASTIC_IP" = false ]; then
        echo ""
        echo -e "${YELLOW}WARNING: No Elastic IP!${NC}"
        echo "The public IP will change when instance starts."
        echo ""
        read -p "Allocate Elastic IP now? (recommended) (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Allocating Elastic IP..."
            ALLOCATION_ID=$(aws ec2 allocate-address \
                --region $REGION \
                --domain vpc \
                --query 'AllocationId' \
                --output text)

            NEW_ELASTIC_IP=$(aws ec2 describe-addresses \
                --region $REGION \
                --allocation-ids $ALLOCATION_ID \
                --query 'Addresses[0].PublicIp' \
                --output text)

            echo -e "${GREEN}✓ Allocated Elastic IP: $NEW_ELASTIC_IP${NC}"
            echo "  Allocation ID: $ALLOCATION_ID"
            echo ""
            echo "Will associate after instance starts..."
            ASSOCIATE_EIP=true
        fi
    fi

    echo ""
    read -p "Start instance $INSTANCE_ID? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Cancelled"
        exit 0
    fi

    echo -e "${YELLOW}Starting instance...${NC}"
    aws ec2 start-instances --region $REGION --instance-ids $INSTANCE_ID

    echo "Waiting for instance to start (may take 2-3 minutes)..."
    aws ec2 wait instance-running --region $REGION --instance-ids $INSTANCE_ID

    # Associate Elastic IP if allocated
    if [ "$ASSOCIATE_EIP" = true ]; then
        echo ""
        echo "Associating Elastic IP..."
        aws ec2 associate-address \
            --region $REGION \
            --instance-id $INSTANCE_ID \
            --allocation-id $ALLOCATION_ID

        FINAL_IP=$NEW_ELASTIC_IP
    else
        # Get new public IP
        sleep 5  # Wait for network interface
        NEW_INFO=$(get_instance_info)
        FINAL_IP=$(echo "$NEW_INFO" | awk '{print $2}')
    fi

    echo ""
    echo -e "${GREEN}=====================================${NC}"
    echo -e "${GREEN}Instance Started Successfully!${NC}"
    echo -e "${GREEN}=====================================${NC}"
    echo ""
    echo "Instance ID: $INSTANCE_ID"
    echo "Public IP: $FINAL_IP"
    echo ""
    echo "Access RAG Lab at:"
    echo -e "  ${GREEN}http://$FINAL_IP${NC}"
    echo ""
    echo "Services will be ready in ~2-3 minutes"
    echo ""

    if [ "$ASSOCIATE_EIP" = true ]; then
        echo -e "${BLUE}✓ Elastic IP allocated and associated${NC}"
        echo "  Your URL will stay the same on future restarts!"
        echo "  Cost: \$0.00/month (free while attached)"
        echo ""
    fi

    if [ "$HAS_ELASTIC_IP" = false ] && [ "$ASSOCIATE_EIP" != true ]; then
        echo -e "${YELLOW}⚠ Public IP changed from $PUBLIC_IP to $FINAL_IP${NC}"
        echo ""
        echo "To avoid IP changes in the future:"
        echo "  aws ec2 allocate-address --region $REGION --domain vpc"
        echo "  aws ec2 associate-address --instance-id $INSTANCE_ID --allocation-id ALLOCATION_ID"
        echo ""
    fi

    echo "To stop again (save 97% costs):"
    echo "  $0 stop $INSTANCE_ID"
    echo ""

# ==========================================
# STATUS COMMAND
# ==========================================
elif [ "$COMMAND" = "status" ]; then
    echo ""
    echo -e "${BLUE}=====================================${NC}"
    echo -e "${BLUE}Instance Status${NC}"
    echo -e "${BLUE}=====================================${NC}"
    echo ""
    echo "Instance: $INSTANCE_NAME"
    echo "ID: $INSTANCE_ID"
    echo "Type: $INSTANCE_TYPE"
    echo "State: $CURRENT_STATE"
    echo "IP: $PUBLIC_IP"
    echo ""

    check_elastic_ip || echo ""

    if [ "$CURRENT_STATE" = "running" ]; then
        echo "Access at: http://$PUBLIC_IP"
        echo ""
        echo "To stop (save costs):"
        echo "  $0 stop $INSTANCE_ID"
    elif [ "$CURRENT_STATE" = "stopped" ]; then
        echo "Instance is stopped (saving 97% costs!)"
        echo ""
        echo "To start:"
        echo "  $0 start $INSTANCE_ID"
    fi
    echo ""

else
    echo -e "${RED}Unknown command: $COMMAND${NC}"
    usage
fi

