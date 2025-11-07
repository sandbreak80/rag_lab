# AWS Security Best Practices for RAG Lab

**Secure deployment strategies for private GitHub repos and dynamic IP management**

---

## 🔐 Problem 1: Private GitHub Repository Access

### ❌ Insecure Approaches (DO NOT USE)
- Hardcoding token in cloud-init script
- Storing token in EC2 user data
- Committing token to repository
- Using long-lived personal tokens without rotation

### ✅ Secure Solution: AWS Secrets Manager + IAM

**How it works:**
1. Store GitHub Personal Access Token (PAT) in AWS Secrets Manager (encrypted)
2. Create IAM role with permission to read the secret
3. Attach IAM role to EC2 instance
4. Cloud-init retrieves token from Secrets Manager
5. Token is used only during git clone, never logged or stored

**Benefits:**
- ✅ Token encrypted at rest (AWS KMS)
- ✅ Access controlled by IAM
- ✅ Token never exposed in logs
- ✅ Easy token rotation
- ✅ Audit trail via CloudTrail
- ✅ Read-only repo access

---

## 🚀 Setup Instructions

### Step 1: One-Time Setup (Run Once)

```bash
cd rag_lab
chmod +x setup-github-secret.sh
./setup-github-secret.sh
```

**This script will:**
1. Prompt you to create a GitHub Personal Access Token (PAT)
   - Go to: https://github.com/settings/tokens/new
   - Token name: "RAG Lab EC2 Deployment"
   - Expiration: 90 days (recommended)
   - Scopes: Check ONLY **`repo`** (read-only for private repos)
   
2. Validate your token
3. Store token in AWS Secrets Manager (encrypted)
4. Create IAM policy (`RAGLabSecretsAccess`)
5. Create IAM role (`RAGLabEC2Role`)
6. Create instance profile (`RAGLabEC2InstanceProfile`)

**Resources Created:**
```
Secret: rag-lab/github-token (us-west-2)
IAM Policy: RAGLabSecretsAccess
IAM Role: RAGLabEC2Role
Instance Profile: RAGLabEC2InstanceProfile
```

### Step 2: Launch with Private Repo Support

```bash
# Use the private repo cloud-init script
aws ec2 run-instances \
    --iam-instance-profile Name=RAGLabEC2InstanceProfile \
    --user-data file://cloud-init-rag-lab-private.yaml \
    ... other parameters ...
```

**Key Addition:** `--iam-instance-profile Name=RAGLabEC2InstanceProfile`

This grants the EC2 instance permission to retrieve the GitHub token from Secrets Manager.

---

## 🌐 Problem 2: Dynamic IP for SSH Access

### The Issue
Your laptop IP changes when you:
- Switch between home/office/coffee shop WiFi
- Connect/disconnect VPN
- Get reassigned IP by ISP

**Current Problem:** Security group has "My IP" hardcoded, breaks when you move.

---

### ✅ Solution 1: AWS Session Manager (BEST - Recommended)

**No SSH key needed. No open port 22. No IP management.**

#### Setup (One Time)

1. **IAM Role** (already done by `setup-github-secret.sh`):
   ```bash
   # The script already attached this policy:
   # arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
   ```

2. **Install Session Manager Plugin** (on your laptop):
   ```bash
   # macOS
   brew install --cask session-manager-plugin
   
   # Linux
   curl "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
   sudo dpkg -i session-manager-plugin.deb
   
   # Windows
   # Download from: https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html
   ```

#### Usage

```bash
# Connect to instance (NO SSH KEY NEEDED!)
aws ssm start-session --target i-1234567890abcdef0

# Port forwarding (access services locally)
aws ssm start-session \
    --target i-1234567890abcdef0 \
    --document-name AWS-StartPortForwardingSession \
    --parameters '{"portNumber":["3000"],"localPortNumber":["3000"]}'

# Now access http://localhost:3000 in your browser!

# SSH via Session Manager (if you need scp/rsync)
ssh -i your-key.pem ubuntu@i-1234567890abcdef0 \
    -o ProxyCommand="aws ssm start-session --target %h --document-name AWS-StartSSHSession --parameters 'portNumber=%p'"
```

**Benefits:**
- ✅ No open port 22 in security group
- ✅ Works from any IP (home, office, VPN, anywhere)
- ✅ No SSH key management
- ✅ All connections logged in CloudTrail
- ✅ Can revoke access via IAM (not security groups)
- ✅ Support for port forwarding

**Security Group Update:**
```bash
# REMOVE port 22 from security group entirely!
# You don't need it with Session Manager

# Keep only:
# - Port 3000 (Frontend) - optional, use port forwarding instead
# - Port 8000 (API) - optional, use port forwarding instead
```

---

### ✅ Solution 2: Script to Update IP (Alternative)

If you prefer traditional SSH with IP whitelist:

```bash
cd rag_lab
chmod +x update-my-ip.sh
./update-my-ip.sh
```

**What it does:**
1. Gets your current public IP
2. Finds your RAG Lab security group
3. Removes old SSH rules
4. Adds rule for your current IP

**Add to shell profile for easy access:**
```bash
# Add to ~/.bashrc or ~/.zshrc
alias update-sg='~/rag_lab/update-my-ip.sh'

# Now just type:
update-sg
```

**Benefits:**
- ✅ Simple script
- ✅ Works with traditional SSH
- ✅ Can be automated

**Drawbacks:**
- ❌ Must run every time IP changes
- ❌ Port 22 still exposed (albeit to your IP only)
- ❌ Doesn't work if script fails (no internet, AWS down, etc.)

---

### ✅ Solution 3: VPN/Bastion Host (Enterprise)

For production or team environments:

#### Option A: AWS Client VPN
```bash
# Setup AWS Client VPN
# - All team members connect to VPN
# - Security group allows SSH from VPN CIDR only
# - Cost: ~$0.10/connection/hour + data transfer
```

#### Option B: Bastion Host (Jump Server)
```bash
# Launch t4g.nano bastion in public subnet (~$3/month)
# RAG Lab instances in private subnet
# SSH through bastion:
ssh -J ubuntu@bastion-ip ubuntu@private-instance-ip
```

**Benefits:**
- ✅ Centralized access control
- ✅ Works for entire team
- ✅ Auditability

**Drawbacks:**
- ❌ Additional cost
- ❌ More complexity
- ❌ Bastion is a single point of failure

---

## 🏆 Recommended Architecture

### Development/Personal Use
```
✅ AWS Session Manager for access (no SSH)
✅ AWS Secrets Manager for GitHub token
✅ IAM role for EC2 instance
✅ No port 22 in security group
✅ Port forwarding for local access
```

### Team/Production Use
```
✅ AWS Session Manager OR VPN
✅ AWS Secrets Manager for all secrets
✅ IAM roles with least privilege
✅ Private subnets for instances
✅ Application Load Balancer for frontend
✅ CloudTrail for audit logging
✅ GuardDuty for threat detection
```

---

## 🔄 Token Rotation

### Rotate GitHub Token (Every 90 Days)

```bash
# 1. Create new token in GitHub (same process)

# 2. Update secret in Secrets Manager
aws secretsmanager put-secret-value \
    --secret-id rag-lab/github-token \
    --region us-west-2 \
    --secret-string "ghp_new_token_here"

# 3. Existing instances will use new token on next update
# No instance relaunch needed!
```

---

## 📋 Security Checklist

### ✅ Before Launch
- [ ] GitHub PAT created with minimal scope (repo only)
- [ ] PAT stored in Secrets Manager
- [ ] IAM role created with least privilege
- [ ] Instance profile attached to role
- [ ] Session Manager plugin installed (if using)

### ✅ Security Group
- [ ] Remove port 22 if using Session Manager
- [ ] Restrict port 3000 to your IP (or remove, use port forwarding)
- [ ] Restrict port 8000 to your IP (or remove, use port forwarding)
- [ ] Document why each port is open

### ✅ Instance Configuration
- [ ] IAM instance profile attached
- [ ] IMDSv2 required (metadata protection)
- [ ] EBS volumes encrypted
- [ ] CloudWatch logging enabled
- [ ] Automatic security updates enabled

### ✅ Ongoing Maintenance
- [ ] Rotate GitHub token every 90 days
- [ ] Review IAM policies quarterly
- [ ] Monitor CloudTrail for suspicious access
- [ ] Keep cloud-init script version controlled
- [ ] Test token expiration handling

---

## 🚨 Incident Response

### If GitHub Token is Compromised

```bash
# 1. IMMEDIATELY revoke token in GitHub
# Go to: https://github.com/settings/tokens
# Click "Revoke" on the compromised token

# 2. Delete secret in AWS
aws secretsmanager delete-secret \
    --secret-id rag-lab/github-token \
    --region us-west-2 \
    --force-delete-without-recovery

# 3. Create new token and re-run setup
./setup-github-secret.sh

# 4. Review CloudTrail logs
aws cloudtrail lookup-events \
    --lookup-attributes AttributeKey=ResourceName,AttributeValue=rag-lab/github-token \
    --region us-west-2
```

### If EC2 Instance is Compromised

```bash
# 1. Isolate instance
aws ec2 modify-instance-attribute \
    --instance-id i-xxxxx \
    --groups sg-xxxxx  # Security group with no ingress/egress

# 2. Create snapshot for forensics
aws ec2 create-snapshot --volume-id vol-xxxxx

# 3. Terminate instance
aws ec2 terminate-instances --instance-ids i-xxxxx

# 4. Review IAM role usage
aws iam get-role --role-name RAGLabEC2Role

# 5. Rotate all secrets
./setup-github-secret.sh  # Creates new token

# 6. Launch fresh instance
./aws-launch-rag-lab.sh
```

---

## 📊 Cost Comparison

| Solution | Monthly Cost | Setup Time | Maintenance |
|----------|--------------|------------|-------------|
| **Session Manager** | $0 | 5 min | None |
| **update-my-ip.sh** | $0 | 2 min | Run when IP changes |
| **AWS Client VPN** | ~$72 + usage | 30 min | Manage certificates |
| **Bastion Host** | ~$3-5 | 15 min | Patch bastion |

**Winner:** Session Manager (free, zero maintenance, most secure)

---

## 🎓 Best Practices Summary

### DO ✅
- Use AWS Secrets Manager for all secrets
- Use IAM roles (never access keys)
- Use AWS Session Manager for access
- Enable CloudTrail logging
- Rotate tokens regularly (90 days)
- Use read-only GitHub tokens
- Encrypt EBS volumes
- Require IMDSv2
- Test token expiration handling

### DON'T ❌
- Hardcode tokens in scripts
- Commit secrets to git
- Use long-lived tokens without rotation
- Leave port 22 open to 0.0.0.0/0
- Attach policies directly to instances
- Disable CloudTrail
- Use admin/root tokens
- Skip IAM role setup

---

## 📚 Additional Resources

- [AWS Secrets Manager](https://docs.aws.amazon.com/secretsmanager/)
- [AWS Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html)
- [GitHub Personal Access Tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
- [IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [AWS Security Best Practices](https://aws.amazon.com/architecture/security-identity-compliance/)

---

**Questions? See main deployment guide or reach out to the team.**

*Stay secure! 🔒*

