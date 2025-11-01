#!/bin/bash

# Ollama Local AI - Uninstall/Cleanup Script
# Safely removes all components installed by setup.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}\n"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

confirm() {
    local prompt="$1"
    local default="${2:-n}"
    
    if [[ "$default" == "y" ]]; then
        read -p "$prompt [Y/n] " -n 1 -r
    else
        read -p "$prompt [y/N] " -n 1 -r
    fi
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

print_header "🧹 Ollama Local AI - Cleanup/Uninstall Script"

echo "This script will help you remove components installed by setup.sh"
echo ""
echo "You can choose what to remove:"
echo "  • Docker containers and volumes (AI models)"
echo "  • Obsidian vault and notes"
echo "  • MCP server configuration"
echo "  • Applications (VS Code, Docker, Obsidian, Node.js)"
echo "  • Project files"
echo ""
print_warning "IMPORTANT: Some deletions are permanent!"
echo ""

if ! confirm "Do you want to continue with cleanup?"; then
    echo "Cleanup cancelled."
    exit 0
fi

# ============================================================================
# Step 1: Remove Docker Containers
# ============================================================================

print_header "1️⃣  Removing Docker Containers"

if docker ps -a | grep -q "ollama"; then
    print_info "Found Ollama container"
    
    if confirm "Remove Ollama Docker container?"; then
        print_info "Stopping Ollama container..."
        docker stop ollama 2>/dev/null || true
        
        print_info "Removing Ollama container..."
        docker rm ollama 2>/dev/null || true
        
        print_success "Ollama container removed"
    else
        print_info "Keeping Ollama container"
    fi
else
    print_info "No Ollama container found"
fi

# ============================================================================
# Step 2: Remove Docker Volumes (AI Models)
# ============================================================================

print_header "2️⃣  Removing Docker Volumes (AI Models)"

if docker volume ls | grep -q "ollama"; then
    print_warning "This will DELETE all downloaded AI models (~30GB)"
    print_warning "Models will need to be re-downloaded if you reinstall"
    
    if confirm "Remove Docker volume with AI models?"; then
        print_info "Removing Docker volume..."
        docker volume rm ollama 2>/dev/null || true
        
        print_success "Docker volume removed"
        print_info "Freed ~30GB of disk space"
    else
        print_info "Keeping Docker volume (models preserved)"
    fi
else
    print_info "No Ollama volume found"
fi

# ============================================================================
# Step 3: Remove Obsidian Vault
# ============================================================================

print_header "3️⃣  Removing Obsidian Vault"

VAULT_PATH="$HOME/obsidian_vault"

if [[ -d "$VAULT_PATH" ]]; then
    print_warning "This will DELETE your Obsidian vault and all notes!"
    print_warning "Location: $VAULT_PATH"
    
    # Check if vault has notes
    NOTE_COUNT=$(find "$VAULT_PATH" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')
    if [[ $NOTE_COUNT -gt 0 ]]; then
        print_warning "Found $NOTE_COUNT note(s) in vault"
    fi
    
    if confirm "Do you want to BACKUP the vault first?" "y"; then
        BACKUP_DIR="$HOME/obsidian_vault_backup_$(date +%Y%m%d_%H%M%S)"
        print_info "Creating backup at: $BACKUP_DIR"
        cp -r "$VAULT_PATH" "$BACKUP_DIR"
        print_success "Backup created: $BACKUP_DIR"
    fi
    
    if confirm "Remove Obsidian vault?" ; then
        print_info "Removing vault..."
        rm -rf "$VAULT_PATH"
        print_success "Obsidian vault removed"
    else
        print_info "Keeping Obsidian vault"
    fi
else
    print_info "No Obsidian vault found at $VAULT_PATH"
fi

# ============================================================================
# Step 4: Remove MCP Configuration
# ============================================================================

print_header "4️⃣  Removing MCP Configuration"

MCP_DIR="$HOME/.config/mcp-servers"
CLAUDE_CONFIG="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

if [[ -d "$MCP_DIR" ]]; then
    if confirm "Remove MCP server installation?"; then
        print_info "Removing MCP servers..."
        rm -rf "$MCP_DIR"
        print_success "MCP servers removed"
    else
        print_info "Keeping MCP servers"
    fi
else
    print_info "No MCP server installation found"
fi

if [[ -f "$CLAUDE_CONFIG" ]]; then
    if confirm "Remove Claude Desktop MCP configuration?"; then
        print_info "Removing Claude configuration..."
        rm -f "$CLAUDE_CONFIG"
        print_success "Claude configuration removed"
    else
        print_info "Keeping Claude configuration"
    fi
else
    print_info "No Claude configuration found"
fi

# ============================================================================
# Step 5: Uninstall Applications
# ============================================================================

print_header "5️⃣  Uninstalling Applications"

print_warning "The following applications can be uninstalled:"
echo "  • Visual Studio Code"
echo "  • Docker Desktop"
echo "  • Obsidian"
echo "  • Node.js (via Homebrew)"
echo ""
print_warning "You may want to keep these if you use them for other projects"
echo ""

if confirm "Do you want to uninstall applications?"; then
    
    # VS Code
    if [[ -d "/Applications/Visual Studio Code.app" ]]; then
        if confirm "  Uninstall Visual Studio Code?"; then
            print_info "Removing VS Code..."
            rm -rf "/Applications/Visual Studio Code.app"
            rm -rf "$HOME/Library/Application Support/Code"
            rm -rf "$HOME/.vscode"
            print_success "VS Code removed"
        fi
    fi
    
    # Docker Desktop
    if [[ -d "/Applications/Docker.app" ]]; then
        if confirm "  Uninstall Docker Desktop?"; then
            print_info "Removing Docker Desktop..."
            
            # Quit Docker
            osascript -e 'quit app "Docker"' 2>/dev/null || true
            sleep 2
            
            # Remove Docker app
            rm -rf "/Applications/Docker.app"
            rm -rf "$HOME/Library/Group Containers/group.com.docker"
            rm -rf "$HOME/Library/Containers/com.docker.docker"
            rm -rf "$HOME/.docker"
            
            print_success "Docker Desktop removed"
            print_warning "You may need to restart your Mac to complete removal"
        fi
    fi
    
    # Obsidian
    if [[ -d "/Applications/Obsidian.app" ]]; then
        if confirm "  Uninstall Obsidian?"; then
            print_info "Removing Obsidian..."
            rm -rf "/Applications/Obsidian.app"
            rm -rf "$HOME/Library/Application Support/obsidian"
            print_success "Obsidian removed"
        fi
    fi
    
    # Node.js (if installed via Homebrew)
    if command -v node &> /dev/null && brew list node &> /dev/null; then
        if confirm "  Uninstall Node.js (Homebrew)?"; then
            print_info "Removing Node.js..."
            brew uninstall node
            print_success "Node.js removed"
        fi
    fi
    
else
    print_info "Keeping all applications"
fi

# ============================================================================
# Step 6: Clean Up Python Dependencies
# ============================================================================

print_header "6️⃣  Cleaning Python Dependencies"

if confirm "Remove Python packages installed by this project?"; then
    print_info "Uninstalling Python packages..."
    pip3 uninstall -y requests numpy 2>/dev/null || true
    print_success "Python packages removed"
else
    print_info "Keeping Python packages"
fi

# ============================================================================
# Step 7: Remove Project Files
# ============================================================================

print_header "7️⃣  Removing Project Files"

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

print_info "Project location: $PROJECT_DIR"

if confirm "Remove project files and scripts?"; then
    print_warning "This will remove:"
    echo "  • Setup scripts"
    echo "  • Examples"
    echo "  • Documentation"
    echo ""
    
    if confirm "Are you sure? This cannot be undone."; then
        print_info "Removing project directory..."
        cd "$HOME"
        rm -rf "$PROJECT_DIR"
        print_success "Project files removed"
        
        echo ""
        print_success "Cleanup complete! All project files have been removed."
        exit 0
    else
        print_info "Keeping project files"
    fi
else
    print_info "Keeping project files"
fi

# ============================================================================
# Step 8: Optional - Remove Homebrew
# ============================================================================

print_header "8️⃣  Optional: Remove Homebrew"

if command -v brew &> /dev/null; then
    print_warning "Homebrew is installed"
    print_info "Note: Homebrew may be used by other applications"
    
    if confirm "Do you want to uninstall Homebrew?" ; then
        print_warning "This will remove ALL Homebrew packages!"
        
        if confirm "Are you absolutely sure?"; then
            print_info "Uninstalling Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/uninstall.sh)"
            print_success "Homebrew removed"
        fi
    else
        print_info "Keeping Homebrew"
    fi
fi

# ============================================================================
# Cleanup Summary
# ============================================================================

print_header "🎉 Cleanup Complete!"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Summary of cleanup:"
echo ""

# Check what remains
REMAINING=()

if docker ps -a | grep -q "ollama" 2>/dev/null; then
    REMAINING+=("  • Ollama Docker container")
fi

if docker volume ls | grep -q "ollama" 2>/dev/null; then
    REMAINING+=("  • Docker volumes (AI models)")
fi

if [[ -d "$HOME/obsidian_vault" ]]; then
    REMAINING+=("  • Obsidian vault ($HOME/obsidian_vault)")
fi

if [[ -d "/Applications/Visual Studio Code.app" ]]; then
    REMAINING+=("  • Visual Studio Code")
fi

if [[ -d "/Applications/Docker.app" ]]; then
    REMAINING+=("  • Docker Desktop")
fi

if [[ -d "/Applications/Obsidian.app" ]]; then
    REMAINING+=("  • Obsidian")
fi

if [[ -d "$HOME/.config/mcp-servers" ]]; then
    REMAINING+=("  • MCP servers")
fi

if [[ ${#REMAINING[@]} -gt 0 ]]; then
    echo "Components still installed:"
    printf '%s\n' "${REMAINING[@]}"
    echo ""
    print_info "Run this script again to remove remaining components"
else
    print_success "All components have been removed!"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

print_info "To reinstall, run: ./setup.sh"
echo ""

print_success "Thank you for using Ollama Local AI! 👋"

