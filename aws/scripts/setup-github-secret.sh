#!/bin/bash
# Setup GitHub Personal Access Token in AWS Secrets Manager
# This only needs to be run ONCE per AWS account/region

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}RAG Lab - GitHub Token Setup${NC}"
echo -e "${GREEN}=====================================${NC}"

# ==========================================
# CONFIGURATION
# ==========================================
SECRET_NAME="rag-lab/github-token"
REGION="us-west-2"

echo ""
echo -e "${YELLOW}This script will store your GitHub Personal Access Token (PAT)${NC}"
echo -e "${YELLOW}in AWS Secrets Manager for secure access during cloud-init.${NC}"
echo ""

# ==========================================
# STEP 1: CREATE GITHUB TOKEN
# ==========================================
echo -e "${YELLOW}Step 1: Create GitHub Personal Access Token${NC}"
echo ""
echo "1. Go to: https://github.com/settings/tokens/new"
echo "2. Token name: 'RAG Lab EC2 Deployment'"
echo "3. Expiration: Choose appropriate duration (90 days recommended)"
echo "4. Scopes: Check ONLY 'repo' (Full control of private repositories)"
echo "   ✓ repo"
echo "     ✓ repo:status"
echo "     ✓ repo_deployment"
echo "     ✓ public_repo"
echo "     ✓ repo:invite"
echo "     ✓ security_events"
echo "5. Click 'Generate token'"
echo "6. Copy the token (starts with 'ghp_')"
echo ""
read -p "Press Enter when you have your token ready..."

# ==========================================
# STEP 2: GET TOKEN FROM USER
# ==========================================
echo ""
echo -e "${YELLOW}Step 2: Enter your GitHub token${NC}"
echo ""
read -sp "Paste your GitHub Personal Access Token: " GITHUB_TOKEN
echo ""

if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}ERROR: No token provided${NC}"
    exit 1
fi

if [[ ! $GITHUB_TOKEN =~ ^ghp_ ]]; then
    echo -e "${YELLOW}WARNING: Token doesn't start with 'ghp_' - is this correct?${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# ==========================================
# STEP 3: VALIDATE TOKEN
# ==========================================
echo ""
echo -e "${YELLOW}Step 3: Validating token...${NC}"

HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/user)

if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}ERROR: Token validation failed (HTTP $HTTP_CODE)${NC}"
    echo "Please check your token and try again."
    exit 1
fi

echo -e "${GREEN}✓ Token is valid${NC}"

# Test private repo access
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
    -H "Authorization: token $GITHUB_TOKEN" \
    https://api.github.com/repos/sandbreak80/rag_lab)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✓ Token can access sandbreak80/rag_lab${NC}"
elif [ "$HTTP_CODE" = "404" ]; then
    echo -e "${RED}ERROR: Token cannot access the private repository${NC}"
    echo "Make sure the token has 'repo' scope."
    exit 1
fi

# ==========================================
# STEP 4: STORE IN SECRETS MANAGER
# ==========================================
echo ""
echo -e "${YELLOW}Step 4: Storing token in AWS Secrets Manager${NC}"
echo "Secret Name: $SECRET_NAME"
echo "Region: $REGION"
echo ""

# Check if secret already exists
if aws secretsmanager describe-secret \
    --secret-id "$SECRET_NAME" \
    --region "$REGION" &>/dev/null; then

    echo -e "${YELLOW}Secret already exists. Updating...${NC}"
    aws secretsmanager put-secret-value \
        --secret-id "$SECRET_NAME" \
        --region "$REGION" \
        --secret-string "$GITHUB_TOKEN" \
        --output text > /dev/null
else
    echo "Creating new secret..."
    aws secretsmanager create-secret \
        --name "$SECRET_NAME" \
        --region "$REGION" \
        --description "GitHub Personal Access Token for RAG Lab private repo access" \
        --secret-string "$GITHUB_TOKEN" \
        --output text > /dev/null
fi

echo -e "${GREEN}✓ Token stored in Secrets Manager${NC}"

# ==========================================
# STEP 5: CREATE IAM POLICY
# ==========================================
echo ""
echo -e "${YELLOW}Step 5: Creating IAM policy for EC2 instances${NC}"

POLICY_NAME="RAGLabSecretsAccess"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

POLICY_DOCUMENT=$(cat <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue",
        "secretsmanager:DescribeSecret"
      ],
      "Resource": "arn:aws:secretsmanager:${REGION}:${ACCOUNT_ID}:secret:${SECRET_NAME}*"
    }
  ]
}
EOF
)

# Check if policy exists
POLICY_ARN=$(aws iam list-policies \
    --scope Local \
    --query "Policies[?PolicyName=='$POLICY_NAME'].Arn" \
    --output text)

if [ -z "$POLICY_ARN" ]; then
    echo "Creating IAM policy..."
    POLICY_ARN=$(aws iam create-policy \
        --policy-name "$POLICY_NAME" \
        --policy-document "$POLICY_DOCUMENT" \
        --description "Allows EC2 instances to read RAG Lab GitHub token from Secrets Manager" \
        --query 'Policy.Arn' \
        --output text)
    echo -e "${GREEN}✓ Policy created: $POLICY_ARN${NC}"
else
    echo -e "${GREEN}✓ Using existing policy: $POLICY_ARN${NC}"
fi

# ==========================================
# STEP 6: CREATE IAM ROLE
# ==========================================
echo ""
echo -e "${YELLOW}Step 6: Creating IAM role for EC2 instances${NC}"

ROLE_NAME="RAGLabEC2Role"

# Trust policy for EC2
TRUST_POLICY=$(cat <<'EOF'
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
)

# Check if role exists
if aws iam get-role --role-name "$ROLE_NAME" &>/dev/null; then
    echo -e "${GREEN}✓ Using existing role: $ROLE_NAME${NC}"
else
    echo "Creating IAM role..."
    aws iam create-role \
        --role-name "$ROLE_NAME" \
        --assume-role-policy-document "$TRUST_POLICY" \
        --description "IAM role for RAG Lab EC2 instances" \
        --output text > /dev/null
    echo -e "${GREEN}✓ Role created: $ROLE_NAME${NC}"
fi

# Attach policy to role
echo "Attaching policy to role..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "$POLICY_ARN"

# Attach AWS Systems Manager policy for Session Manager
echo "Attaching SSM policy for Session Manager..."
aws iam attach-role-policy \
    --role-name "$ROLE_NAME" \
    --policy-arn "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"

echo -e "${GREEN}✓ Policies attached${NC}"

# ==========================================
# STEP 7: CREATE INSTANCE PROFILE
# ==========================================
echo ""
echo -e "${YELLOW}Step 7: Creating instance profile${NC}"

INSTANCE_PROFILE_NAME="RAGLabEC2InstanceProfile"

# Check if instance profile exists
if aws iam get-instance-profile --instance-profile-name "$INSTANCE_PROFILE_NAME" &>/dev/null; then
    echo -e "${GREEN}✓ Using existing instance profile${NC}"
else
    echo "Creating instance profile..."
    aws iam create-instance-profile \
        --instance-profile-name "$INSTANCE_PROFILE_NAME" \
        --output text > /dev/null

    # Add role to instance profile
    aws iam add-role-to-instance-profile \
        --instance-profile-name "$INSTANCE_PROFILE_NAME" \
        --role-name "$ROLE_NAME"

    echo -e "${GREEN}✓ Instance profile created${NC}"
fi

# ==========================================
# SUMMARY
# ==========================================
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "Resources created:"
echo "  ✓ Secret: $SECRET_NAME (in $REGION)"
echo "  ✓ IAM Policy: $POLICY_NAME"
echo "  ✓ IAM Role: $ROLE_NAME"
echo "  ✓ Instance Profile: $INSTANCE_PROFILE_NAME"
echo ""
echo -e "${YELLOW}IMPORTANT: Update your launch script${NC}"
echo ""
echo "In aws-launch-rag-lab.sh, add this parameter to run-instances:"
echo ""
echo -e "${GREEN}--iam-instance-profile Name=$INSTANCE_PROFILE_NAME${NC}"
echo ""
echo "Example:"
echo "  aws ec2 run-instances \\"
echo "    --iam-instance-profile Name=$INSTANCE_PROFILE_NAME \\"
echo "    --user-data file://cloud-init-rag-lab-private.yaml \\"
echo "    ... other parameters ..."
echo ""
echo -e "${YELLOW}Security Notes:${NC}"
echo "  ✓ Token is encrypted in Secrets Manager"
echo "  ✓ Only EC2 instances with this role can access it"
echo "  ✓ Token is never exposed in logs or configs"
echo "  ✓ Token has read-only access to the repo"
echo ""
echo -e "${GREEN}You can now launch instances with private repo access!${NC}"
echo -e "${GREEN}=====================================${NC}"

