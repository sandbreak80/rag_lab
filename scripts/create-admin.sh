#!/bin/bash
#
# Create Admin Account Script
# Creates a default admin user for testing and development
#
# Usage: ./scripts/create-admin.sh [username] [email] [password]
#

set -e

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default credentials (can be overridden)
DEFAULT_USERNAME="admin"
DEFAULT_EMAIL="admin@localhost"
DEFAULT_PASSWORD="admin123"

# Use provided arguments or defaults
USERNAME="${1:-$DEFAULT_USERNAME}"
EMAIL="${2:-$DEFAULT_EMAIL}"
PASSWORD="${3:-$DEFAULT_PASSWORD}"

echo -e "${YELLOW}🔐 Creating Admin Account${NC}"
echo "================================"
echo ""
echo "Username: $USERNAME"
echo "Email:    $EMAIL"
echo "Password: ****** (${#PASSWORD} characters)"
echo ""

# Check if auth service is running
echo "Checking if auth service is running..."
if ! docker ps | grep -q rag-auth-service; then
    echo -e "${RED}❌ Error: Auth service is not running${NC}"
    echo "Please start the services first: docker compose up -d"
    exit 1
fi

AUTH_URL="http://localhost:8014"

# Check if auth service is healthy
echo "Checking auth service health..."
HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" "$AUTH_URL/health" || echo "000")

if [ "$HEALTH_CHECK" != "200" ]; then
    echo -e "${RED}❌ Error: Auth service is not healthy (HTTP $HEALTH_CHECK)${NC}"
    echo "Wait a few seconds and try again, or check logs: docker logs rag-auth-service"
    exit 1
fi

echo -e "${GREEN}✅ Auth service is healthy${NC}"
echo ""

# Attempt to register the user
echo "Attempting to create admin account..."

RESPONSE=$(curl -s -X POST "$AUTH_URL/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$USERNAME\",
    \"email\": \"$EMAIL\",
    \"password\": \"$PASSWORD\"
  }")

# Check if registration was successful
if echo "$RESPONSE" | grep -q '"success".*true'; then
    echo -e "${GREEN}✅ Admin account created successfully!${NC}"
    echo ""

    # Extract user info from response
    IS_ADMIN=$(echo "$RESPONSE" | grep -o '"is_admin":[^,}]*' | cut -d':' -f2 | tr -d ' ')

    if [ "$IS_ADMIN" = "true" ]; then
        echo -e "${GREEN}🎉 User has admin privileges!${NC}"
    else
        echo -e "${YELLOW}⚠️  User was created but is NOT admin (another user was registered first)${NC}"
    fi

    echo ""
    echo "=== Login Credentials ==="
    echo "Username: $USERNAME"
    echo "Password: $PASSWORD"
    echo ""
    echo "=== Quick Test ==="
    echo "Login via API:"
    echo "curl -X POST $AUTH_URL/login \\"
    echo "  -H 'Content-Type: application/json' \\"
    echo "  -d '{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}'"
    echo ""
    echo "Or open the UI: http://localhost:3000/login"
    echo ""

elif echo "$RESPONSE" | grep -q -E '"error":|"message":'; then
    ERROR_MSG=$(echo "$RESPONSE" | grep -o '"error":\s*"[^"]*"' | cut -d'"' -f4)
    if [ -z "$ERROR_MSG" ]; then
        ERROR_MSG=$(echo "$RESPONSE" | grep -o '"message":\s*"[^"]*"' | cut -d'"' -f4)
    fi

    echo -e "${RED}❌ Failed to create admin account${NC}"
    echo "Error: $ERROR_MSG"
    echo ""

    if echo "$ERROR_MSG" | grep -qi "already exists"; then
        echo "This username or email is already registered."
        echo ""
        echo "=== Options ==="
        echo "1. Use a different username/email:"
        echo "   ./scripts/create-admin.sh myusername my@email.com mypassword"
        echo ""
        echo "2. Reset the auth database:"
        echo "   docker compose down"
        echo "   docker volume rm rag_lab_auth-data"
        echo "   docker compose up -d"
        echo "   ./scripts/create-admin.sh"
        echo ""
    fi

    exit 1
else
    echo -e "${RED}❌ Unexpected response from auth service${NC}"
    echo "Response: $RESPONSE"
    exit 1
fi

exit 0

