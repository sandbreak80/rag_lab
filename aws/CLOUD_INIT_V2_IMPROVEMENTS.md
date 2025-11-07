# Cloud-Init v2 Improvements

## Changes Made for Next Test

### 🔄 **Proper Reboot Handling**
The original cloud-init script had issues because it didn't account for necessary reboots:
- **After Docker installation:** Group membership changes require reboot
- **After NVIDIA driver installation:** Kernel modules require reboot

**Solution:** Split into 2 stages:
1. **Stage 1 (cloud-init):** Install Docker + NVIDIA drivers → Reboot
2. **Stage 2 (systemd service):** Runs automatically after reboot to complete setup

### 📦 **Ollama Model Pulling**
Now includes optional models from `pull-ollama-models.sh`:

**Required Models:**
- `llama3.1:8b` - Primary chat model
- `nomic-embed-text` - Embedding model

**Optional Models (for labs):**
- `llama3.2:3b` - Small, fast model
- `gemma2:2b` - Tiny efficient model
- `mistral:7b` - Alternative 7B model

These allow testing different model sizes and performance characteristics.

### 🔧 **Home Directory Permissions**
Fixed the permission issue that prevented RAG Lab from being cloned:
```bash
chown -R ubuntu:ubuntu /home/ubuntu
```

### 📊 **Better Logging**
- Stage 1: `/var/log/cloud-init-output.log`
- Stage 2: `/var/log/rag-lab-setup-stage2.log`

Monitor progress:
```bash
# After reboot, watch stage 2
tail -f /var/log/rag-lab-setup-stage2.log
```

### ✅ **Completion Markers**
Uses marker files to track progress:
- `/var/lib/rag-lab-stage1-complete`
- `/var/lib/rag-lab-setup-complete`

The systemd service only runs once and disables itself after successful completion.

### 🎯 **Systemd Service Conditions**
```ini
ConditionPathExists=!/var/lib/rag-lab-setup-complete
```
Ensures stage 2 only runs once, even across multiple reboots.

## Testing the Teardown Script

After this deployment, we'll test `terminate-cleanup.sh` to ensure it:
1. ✅ Terminates the EC2 instance
2. ✅ Deletes the security group (`rag-lab-security-group`)
3. ✅ Releases any Elastic IPs
4. ✅ Optionally cleans up snapshots

## Deployment Timeline

### With v2 Cloud-Init:
- **0-5 min:** Package installation, Docker install, NVIDIA driver install
- **5-6 min:** Automatic reboot
- **6-8 min:** System comes back online, Stage 2 starts
- **8-13 min:** Ollama models pull (3-5 models, ~6GB total)
- **13-18 min:** RAG Lab build and startup
- **18-20 min:** Services fully healthy

**Total: ~20 minutes** (vs 10-15 min advertised, but more reliable)

## Key Files

### Launch
- `aws/scripts/aws-launch-rag-lab.sh` - Launch script (uses v2)
- `aws/cloud-init/cloud-init-rag-lab-v2.yaml` - New cloud-init with reboots

### Teardown
- `aws/scripts/terminate-cleanup.sh` - Complete cleanup script

### Monitoring
```bash
# SSH into instance
ssh -i bootcamp.pem ubuntu@PUBLIC_IP

# Monitor stage 2 progress
tail -f /var/log/rag-lab-setup-stage2.log

# Check if complete
[ -f /var/lib/rag-lab-setup-complete ] && echo "Setup complete!" || echo "Still running..."

# Check GPU
nvidia-smi

# Check services
cd /home/ubuntu/rag_lab && docker compose ps
```

## Next Test Plan

1. **Current instance:** Let it finish, test manually
2. **Teardown test:** Run terminate-cleanup.sh on current instance
3. **Fresh deployment:** Launch with v2 cloud-init
4. **Validate:** Confirm everything works end-to-end

## Cost Optimization Notes

The terminate script is crucial for cost management:
- **Running instance:** $18/day (~$554/month)
- **After termination:** $0/day
- **Important:** Must delete security group too (no cost, but cleanup)

With stop/start capability:
- **Stopped instance:** $0.50/day (EBS only, ~$16/month)
- **Savings:** 97% vs running 24/7

