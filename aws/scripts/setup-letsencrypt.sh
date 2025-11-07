#!/bin/bash
# Setup Let's Encrypt HTTPS for RAG Lab
# Requires: Domain name pointing to this server

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ==========================================
# VALIDATE INPUT
# ==========================================
if [ -z "$1" ]; then
    echo -e "${RED}ERROR: Domain name required${NC}"
    echo "Usage: $0 yourdomain.com"
    echo ""
    echo "Example: $0 rag-lab.example.com"
    exit 1
fi

DOMAIN=$1
EMAIL=${2:-"admin@$DOMAIN"}

echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}Let's Encrypt HTTPS Setup${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo ""

# ==========================================
# PREREQUISITE CHECKS
# ==========================================
echo -e "${YELLOW}Checking prerequisites...${NC}"

# Check if domain resolves to this server
PUBLIC_IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
DOMAIN_IP=$(dig +short $DOMAIN | tail -1)

if [ "$DOMAIN_IP" != "$PUBLIC_IP" ]; then
    echo -e "${RED}WARNING: Domain $DOMAIN does not resolve to this server!${NC}"
    echo "Domain resolves to: $DOMAIN_IP"
    echo "Server IP: $PUBLIC_IP"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if port 80 is accessible
if ! nc -z -w5 localhost 80; then
    echo -e "${RED}ERROR: Port 80 is not accessible. NGINX may not be running.${NC}"
    echo "Run: sudo systemctl start nginx"
    exit 1
fi

# ==========================================
# INSTALL CERTBOT
# ==========================================
echo ""
echo -e "${YELLOW}Installing Certbot...${NC}"
sudo apt-get update
sudo apt-get install -y certbot python3-certbot-nginx

# ==========================================
# OBTAIN CERTIFICATE
# ==========================================
echo ""
echo -e "${YELLOW}Obtaining SSL certificate from Let's Encrypt...${NC}"
echo "This will:"
echo "1. Verify domain ownership"
echo "2. Obtain SSL certificate"
echo "3. Automatically configure NGINX"
echo "4. Set up auto-renewal"
echo ""

sudo certbot --nginx \
    -d $DOMAIN \
    --non-interactive \
    --agree-tos \
    --email $EMAIL \
    --redirect

# ==========================================
# VERIFY CERTIFICATE
# ==========================================
echo ""
echo -e "${YELLOW}Verifying certificate...${NC}"
sudo certbot certificates

# ==========================================
# TEST AUTO-RENEWAL
# ==========================================
echo ""
echo -e "${YELLOW}Testing auto-renewal...${NC}"
sudo certbot renew --dry-run

# ==========================================
# UPDATE NGINX CONFIGURATION
# ==========================================
echo ""
echo -e "${YELLOW}Updating NGINX configuration for production...${NC}"

# Add additional security headers for HTTPS
sudo tee -a /etc/nginx/sites-available/rag-lab > /dev/null <<'NGINX_EOF'

# Additional security for HTTPS
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
add_header Content-Security-Policy "upgrade-insecure-requests" always;
NGINX_EOF

sudo nginx -t && sudo systemctl reload nginx

# ==========================================
# SUMMARY
# ==========================================
echo ""
echo -e "${GREEN}=====================================${NC}"
echo -e "${GREEN}HTTPS Setup Complete!${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""
echo -e "Your site is now accessible at:"
echo -e "  ${GREEN}https://$DOMAIN${NC}"
echo ""
echo "Certificate Details:"
echo "  Domain: $DOMAIN"
echo "  Valid for: 90 days"
echo "  Auto-renewal: Enabled (cron job created)"
echo ""
echo "HTTP (port 80) automatically redirects to HTTPS (port 443)"
echo ""
echo "Certificate will auto-renew before expiration."
echo "Check renewal status: sudo certbot renew --dry-run"
echo ""
echo -e "${GREEN}=====================================${NC}"

