# 🧹 Cleanup & Uninstall Guide

Complete guide to safely removing Ollama Local AI components from your system.

---

## 🎯 Quick Uninstall

To remove all components:

```bash
./cleanup.sh
```

The script will guide you through removing:
- Docker containers and volumes
- Obsidian vault
- MCP configuration
- Applications (optional)
- Project files

---

## 📋 What Can Be Removed

### 1. **Docker Components**
- Ollama container
- Docker volumes (AI models ~30GB)

### 2. **Obsidian**
- Vault at `~/obsidian_vault`
- Application (optional)
- Plugin configuration

### 3. **MCP Server**
- MCP server installation
- Claude Desktop configuration

### 4. **Applications** (Optional)
- Visual Studio Code
- Docker Desktop
- Obsidian
- Node.js

### 5. **Python Dependencies**
- requests
- numpy

### 6. **Project Files**
- Scripts
- Examples
- Documentation

---

## 🛡️ Safety Features

### Confirmations
- Script asks before deleting each component
- Separate confirmations for destructive actions
- Option to cancel at any time

### Backups
- Automatic backup offer for Obsidian vault
- Backup created with timestamp
- Keeps originals until you confirm

### Selective Removal
- Choose what to remove
- Keep applications you use elsewhere
- Preserve data you want to keep

---

## 📝 Cleanup Process

### Step-by-Step

**1. Run the cleanup script:**
```bash
cd ~/code_projects/ollama_local
./cleanup.sh
```

**2. Answer prompts:**
- Read each prompt carefully
- 'y' = Yes, remove this
- 'n' = No, keep this
- Can cancel anytime with Ctrl+C

**3. Review summary:**
- Script shows what was removed
- Lists components still installed
- Provides reinstall instructions

---

## 🔄 Partial Cleanup

### Remove Only Docker Components

```bash
# Stop and remove container
docker stop ollama
docker rm ollama

# Remove volumes (deletes models!)
docker volume rm ollama
```

### Remove Only Obsidian Vault

```bash
# Backup first (recommended)
cp -r ~/obsidian_vault ~/obsidian_vault_backup

# Remove vault
rm -rf ~/obsidian_vault
```

### Remove Only MCP Configuration

```bash
# Remove MCP servers
rm -rf ~/.config/mcp-servers

# Remove Claude config
rm -f ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Remove Only Project Files

```bash
# From project directory
cd ~/code_projects/ollama_local
cd ..
rm -rf ollama_local
```

---

## ⚠️ Important Notes

### Before Removing

1. **Backup Important Data**
   - Export Obsidian notes if needed
   - Save any custom scripts
   - Note your model configurations

2. **Check Dependencies**
   - VS Code: May be used for other projects
   - Docker: May run other containers
   - Node.js: May be needed by other apps
   - Obsidian: May have other vaults

3. **Understand What's Being Deleted**
   - AI models (~30GB) must be re-downloaded
   - Obsidian notes are permanent unless backed up
   - Application data is removed

### After Removing

1. **Verify Removal**
   ```bash
   # Check Docker
   docker ps -a | grep ollama
   docker volume ls | grep ollama
   
   # Check applications
   ls -la /Applications/ | grep -E "Docker|Obsidian|Visual Studio Code"
   
   # Check vault
   ls -la ~/obsidian_vault
   
   # Check MCP
   ls -la ~/.config/mcp-servers
   ```

2. **Free Up Space**
   ```bash
   # Check disk space freed
   df -h
   ```

3. **Clean Docker**
   ```bash
   # Remove unused Docker resources
   docker system prune -a
   ```

---

## 🔁 Reinstallation

### Full Reinstall

```bash
# If you kept project files
./setup.sh

# If you removed project files
git clone <REPO_URL>
cd ollama-local-ai
./setup.sh
```

### Selective Reinstall

**Just Docker + Ollama:**
```bash
# Install Docker Desktop
brew install --cask docker

# Run Ollama
docker run -d \
  --name ollama \
  -p 11434:11434 \
  -v ollama:/root/.ollama \
  ollama/ollama

# Download models
./pull_models.sh
```

**Just Obsidian:**
```bash
# Install Obsidian
brew install --cask obsidian

# Create new vault
mkdir ~/obsidian_vault
open ~/obsidian_vault
```

---

## 📊 Disk Space Recovery

### Expected Space Freed

| Component | Space Freed |
|-----------|-------------|
| AI Models | ~30GB |
| Docker Images | ~5GB |
| Applications | ~2GB |
| Obsidian Vault | Varies |
| **Total** | **~37GB+** |

### Verify Space Freed

```bash
# Before cleanup
df -h | grep /System/Volumes/Data

# After cleanup
df -h | grep /System/Volumes/Data

# Docker-specific
docker system df
```

---

## 🔍 Troubleshooting

### Script Won't Run

```bash
# Make executable
chmod +x cleanup.sh

# Run directly
bash cleanup.sh
```

### Can't Remove Docker Container

```bash
# Force stop
docker stop -t 0 ollama

# Force remove
docker rm -f ollama

# Check for other containers
docker ps -a
```

### Can't Remove Volume

```bash
# Check what's using it
docker volume inspect ollama

# Force remove (destructive!)
docker volume rm -f ollama
```

### Can't Remove Application

```bash
# Force remove (macOS)
sudo rm -rf "/Applications/App Name.app"

# Clean preferences
rm -rf ~/Library/Preferences/com.app.*
rm -rf ~/Library/Application\ Support/AppName
```

### Permission Denied

```bash
# Use sudo for system files
sudo rm -rf /path/to/file

# Fix permissions
sudo chown -R $(whoami) ~/obsidian_vault
```

---

## 📦 What Cleanup Preserves

The cleanup script does NOT remove:

### System Components
- ✅ Homebrew (optional removal)
- ✅ Python system installation
- ✅ macOS system files

### Personal Data
- ✅ Other Docker containers
- ✅ Other Obsidian vaults
- ✅ VS Code settings (if you keep VS Code)
- ✅ Other projects

### Application Data
- ✅ Docker data for other projects
- ✅ Node.js packages for other projects
- ✅ VS Code extensions (if you keep VS Code)

---

## 🆘 Support

### Before Cleanup

- **Backup everything important**
- **Read through this guide**
- **Understand what will be removed**

### During Cleanup

- **Read each prompt carefully**
- **Use backup option for vault**
- **Cancel if unsure** (Ctrl+C)

### After Cleanup

- **Verify removal was successful**
- **Check disk space**
- **Report issues** on GitHub

---

## 📞 Quick Reference

### Commands

```bash
# Full cleanup (interactive)
./cleanup.sh

# Just Docker
docker stop ollama && docker rm ollama
docker volume rm ollama

# Just vault (with backup)
cp -r ~/obsidian_vault ~/obsidian_vault_backup
rm -rf ~/obsidian_vault

# Just MCP
rm -rf ~/.config/mcp-servers

# Just project
cd .. && rm -rf ollama_local

# Reinstall
./setup.sh
```

### Files & Locations

- **Project**: `~/code_projects/ollama_local`
- **Vault**: `~/obsidian_vault`
- **MCP**: `~/.config/mcp-servers`
- **Claude Config**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Docker Volume**: `/var/lib/docker/volumes/ollama`

---

## ✅ Cleanup Checklist

Before running cleanup:

- [ ] Backed up important Obsidian notes
- [ ] Saved custom scripts/configurations
- [ ] Checked if applications are used elsewhere
- [ ] Read this guide completely
- [ ] Ready to confirm deletions

After cleanup:

- [ ] Verified components removed
- [ ] Checked disk space freed
- [ ] Removed project directory (if desired)
- [ ] Cleaned Docker system (if desired)
- [ ] Restarted Mac (if removed Docker)

---

**Need to reinstall?** Run `./setup.sh` to start fresh! 🚀

