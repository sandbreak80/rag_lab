#!/bin/bash
# Add Grafana port 3001 to existing security group

REGION="us-west-2"
SG_NAME="rag-lab-security-group"

# Get security group ID
SG_ID=$(aws ec2 describe-security-groups \
    --region $REGION \
    --filters "Name=group-name,Values=$SG_NAME" \
    --query 'SecurityGroups[0].GroupId' \
    --output text)

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
    echo "Error: Security group '$SG_NAME' not found"
    exit 1
fi

echo "Adding port 3001 to security group: $SG_ID"

# Add Grafana port 3001
aws ec2 authorize-security-group-ingress \
    --region $REGION \
    --group-id $SG_ID \
    --ip-permissions IpProtocol=tcp,FromPort=3001,ToPort=3001,IpRanges='[{CidrIp=0.0.0.0/0,Description="Grafana"}]' 2>&1

echo "Done! Port 3001 should now be accessible."
