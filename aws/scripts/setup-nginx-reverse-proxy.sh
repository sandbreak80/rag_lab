#!/bin/bash
# Setup NGINX Reverse Proxy for RAG Lab on AWS
# Exposes frontend on port 80 (HTTP) and optionally 443 (HTTPS)

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}NGINX Reverse Proxy Setup${NC}"
echo -e "${GREEN}=====================================${NC}"

# ==========================================
# INSTALL NGINX (if not already installed)
# ==========================================
echo ""
echo -e "${YELLOW}Installing NGINX...${NC}"
sudo apt-get update
sudo apt-get install -y nginx

# ==========================================
# CREATE NGINX CONFIGURATION
# ==========================================
echo -e "${YELLOW}Creating NGINX configuration...${NC}"

PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "Public IP: $PUBLIC_IP"

# Create NGINX config
sudo tee /etc/nginx/sites-available/rag-lab <<'EOF'
server {
    listen 80;
    listen [::]:80;
    server_name _;  # Accept all hostnames

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    server_tokens off;

    # Logging
    access_log /var/log/nginx/rag-lab-access.log;
    error_log /var/log/nginx/rag-lab-error.log;

    # Frontend (proxied to Docker container on port 3000)
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
        proxy_send_timeout 300s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:3000/health;
        access_log off;
    }
}
EOF

# ==========================================
# ENABLE SITE
# ==========================================
echo -e "${YELLOW}Enabling site...${NC}"

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Enable RAG Lab site
sudo ln -sf /etc/nginx/sites-available/rag-lab /etc/nginx/sites-enabled/

# Test configuration
echo -e "${YELLOW}Testing NGINX configuration...${NC}"
sudo nginx -t

# ==========================================
# START NGINX
# ==========================================
echo -e "${YELLOW}Starting NGINX...${NC}"
sudo systemctl enable nginx
sudo systemctl restart nginx

# ==========================================
# SUMMARY
# ==========================================
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}NGINX Setup Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "Access RAG Lab at:"
echo -e "  ${GREEN}http://$PUBLIC_IP${NC}"
echo ""
echo "NGINX Status:"
sudo systemctl status nginx --no-pager | head -5
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "1. Open port 80 in your security group:"
echo "   aws ec2 authorize-security-group-ingress \\"
echo "     --group-id YOUR_SG_ID \\"
echo "     --protocol tcp --port 80 --cidr 0.0.0.0/0"
echo ""
echo "2. (Optional) Setup HTTPS with Let's Encrypt:"
echo "   ./setup-letsencrypt.sh yourdomain.com"
echo ""
echo -e "${GREEN}=====================================${NC}"

