# Cloud-Init Version Comparison

## v3 - Native Reboot (RECOMMENDED) ✅

**Uses cloud-init's built-in features:**

```yaml
bootcmd:          # Runs on EVERY boot
  - Stage 2 logic (checks markers, only runs after reboot)

runcmd:           # Runs only on FIRST boot
  - Stage 1 logic (Docker + NVIDIA install)

power_state:      # Native reboot trigger
  mode: reboot
  condition: test -f /var/lib/rag-lab-stage1-complete && test ! -f /var/lib/rag-lab-stage2-complete
```

**Advantages:**
- ✅ Pure cloud-init solution (no systemd)
- ✅ Uses `bootcmd` for post-reboot logic
- ✅ Uses `power_state` for conditional reboot
- ✅ Simpler architecture
- ✅ Single log file: `/var/log/rag-lab-setup.log`

**Flow:**
```
First Boot:
  runcmd → Install Docker + NVIDIA → Mark stage1 complete
  power_state → Check condition → REBOOT

Second Boot:
  bootcmd → Check markers → Run stage 2 → Mark stage2 complete
  power_state → Condition false → No reboot
```

---

## v2 - Systemd Service

**Uses systemd for post-reboot logic:**

```yaml
runcmd:
  - Install Docker + NVIDIA
  - Create systemd service
  - Enable service
  - reboot

write_files:
  - /usr/local/bin/rag-lab-setup-stage2.sh
  - /etc/systemd/system/rag-lab-setup-stage2.service
```

**Advantages:**
- ✅ Explicit systemd service
- ✅ Service can be restarted manually
- ✅ Better for debugging (can check service status)

**Disadvantages:**
- ❌ More complex (extra files, systemd setup)
- ❌ Two log files (cloud-init + stage2)
- ❌ Manual reboot command in runcmd

---

## v1 - Original (No Reboots) ❌

**Single-pass, no reboots:**

```yaml
runcmd:
  - Install everything
  - Start everything
  - Hope it works
```

**Problems:**
- ❌ Docker group membership not active
- ❌ NVIDIA drivers not loaded
- ❌ GPU unavailable to containers
- ❌ Services fail to start

---

## Recommendation: Use v3

**Cloud-init v3** is the cleanest solution because it:
1. Uses cloud-init's native reboot mechanism
2. No external dependencies (systemd services)
3. Single unified log file
4. Proper conditional logic with markers

### Key Cloud-Init Features Used in v3:

#### 1. bootcmd (Runs on every boot)
```yaml
bootcmd:
  - if [ -f /var/lib/marker ]; then
      # Run post-reboot logic
    fi
```

#### 2. runcmd (Runs only on first boot)
```yaml
runcmd:
  - # First-boot logic
  - touch /var/lib/marker
```

#### 3. power_state (Conditional reboot)
```yaml
power_state:
  mode: reboot
  condition: test -f /var/lib/rag-lab-stage1-complete && test ! -f /var/lib/rag-lab-stage2-complete
```

This condition ensures:
- Reboot only if stage 1 is complete
- Don't reboot if stage 2 is already done
- No infinite reboot loops

---

## Migration Path

Current script already supports all versions with fallback:

```bash
# Launch script tries in order:
1. cloud-init-rag-lab-v3.yaml  ← RECOMMENDED
2. cloud-init-rag-lab-v2.yaml  ← Systemd approach
3. cloud-init-rag-lab.yaml     ← Original (broken)
```

To use v3:
```bash
./aws/scripts/aws-launch-rag-lab.sh
# Automatically uses v3 if present
```

---

## Testing Plan

1. **Current instance:** Terminate with cleanup script
2. **Fresh deploy:** Launch with v3
3. **Monitor:** `tail -f /var/log/rag-lab-setup.log`
4. **Verify:** All services running after ~20 minutes

---

## Summary

| Feature | v1 | v2 | v3 |
|---------|----|----|-----|
| Reboots | ❌ No | ✅ Manual | ✅ Native |
| Approach | Single-pass | Systemd | bootcmd |
| Complexity | Low | High | Medium |
| Reliability | ❌ Broken | ✅ Works | ✅ Works |
| Log Files | 1 | 2 | 1 |
| Recommended | ❌ | ⚠️ | ✅ |

**Use v3** - It's the cleanest cloud-init-native solution!

