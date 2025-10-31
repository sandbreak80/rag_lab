#!/bin/bash
# Quick script to push to GitHub after you create the repo

echo "🚀 GitHub Push Script"
echo "===================="
echo ""
echo "First, create the repo on GitHub:"
echo "  1. Go to: https://github.com/new"
echo "  2. Repository name: markdown-rag-mcp"
echo "  3. Visibility: Public"
echo "  4. DO NOT initialize with README"
echo "  5. Click 'Create repository'"
echo ""
read -p "Press Enter when you've created the repo..."
echo ""

# Get GitHub username
read -p "Enter your GitHub username: " GITHUB_USER

# Add remote
echo "📡 Adding GitHub remote..."
git remote add origin "https://github.com/${GITHUB_USER}/markdown-rag-mcp.git"

# Push
echo "⬆️  Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ SUCCESS!"
    echo "===================="
    echo "Your repo is live at:"
    echo "https://github.com/${GITHUB_USER}/markdown-rag-mcp"
    echo ""
    echo "Share it with: git clone https://github.com/${GITHUB_USER}/markdown-rag-mcp.git"
else
    echo ""
    echo "❌ Push failed!"
    echo "You may need to authenticate with GitHub."
    echo "Try: gh auth login"
    echo "Or set up SSH keys: https://docs.github.com/en/authentication"
fi


