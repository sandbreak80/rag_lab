# 🔒 Security Hardening for Internet-Facing Deployment

**Date:** November 5, 2025
**Status:** 📋 TODO - Complete after Research Agent
**Priority:** 🔴 CRITICAL before public deployment

---

## 🎯 Current Status

**Environment:** Development (localhost only)
**Target:** Production-ready, internet-facing
**Security Level:** ⚠️ Development (NOT internet-ready)

---

## 🚨 CRITICAL: Must-Have Before Internet Deployment

### 1. SSL/TLS (HTTPS) ✅ Priority: CRITICAL

**Current State:** ❌ HTTP only
**Required:** ✅ HTTPS with valid SSL certificate

**Actions:**
- [ ] Obtain SSL certificate (Let's Encrypt free, auto-renewing)
- [ ] Configure Nginx for HTTPS (ports 80→443 redirect)
- [ ] Update docker-compose to expose port 443
- [ ] Force HTTPS redirect for all traffic
- [ ] Enable HSTS (HTTP Strict Transport Security)
- [ ] Configure SSL/TLS 1.3 minimum

**Implementation:**
```nginx
# nginx/nginx.conf
server {
    listen 443 ssl http2;
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.3 TLSv1.2;
    ssl_ciphers HIGH:!aNULL:!MD5;

    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
}

server {
    listen 80;
    return 301 https://$server_name$request_uri;
}
```

**Tools:**
- Certbot for Let's Encrypt
- Or use Cloudflare (free tier includes SSL)

---

### 2. Authentication & Authorization ✅ Priority: CRITICAL

**Current State:** ⚠️ Partial (auth-service exists but not enforced everywhere)
**Required:** ✅ All endpoints protected, JWT validation

**Actions:**
- [ ] Enforce authentication on ALL sensitive endpoints
- [ ] Require login for:
  - [ ] Chat queries (or rate limit anonymous users severely)
  - [ ] Document uploads
  - [ ] Settings changes
  - [ ] Research agent triggers
  - [ ] Admin endpoints
- [ ] Implement API key system for programmatic access
- [ ] Add OAuth2/OIDC (Google, GitHub login)
- [ ] Session management (timeout after 1 hour idle)
- [ ] Password requirements (12+ chars, complexity)
- [ ] Account lockout after failed attempts
- [ ] Email verification on signup
- [ ] 2FA/MFA for admin accounts

**API Protection:**
```python
# All routes should have:
@jwt_required()
def protected_endpoint():
    user_id = get_jwt_identity()
    # Check permissions
```

---

### 3. Rate Limiting & DDoS Protection ✅ Priority: CRITICAL

**Current State:** ⚠️ Partial (Redis rate limiter exists)
**Required:** ✅ Multi-layer rate limiting

**Actions:**
- [ ] Nginx rate limiting (requests per IP)
- [ ] Application rate limiting (per user/API key)
- [ ] Cloudflare or similar CDN (DDoS protection)
- [ ] Rate limits for:
  - [ ] Login attempts: 5/15 min per IP
  - [ ] API queries: 100/hour for free, 1000/hour for paid
  - [ ] Document uploads: 10/hour per user
  - [ ] Research agent triggers: Admin only
- [ ] Implement CAPTCHA on public forms
- [ ] IP blocklist for known bad actors

**Nginx Config:**
```nginx
limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

location /api/ {
    limit_req zone=api burst=20 nodelay;
}

location /api/auth/login {
    limit_req zone=login burst=3 nodelay;
}
```

---

### 4. Input Validation & Sanitization ✅ Priority: CRITICAL

**Current State:** ⚠️ Partial (security-guardrails exists)
**Required:** ✅ Comprehensive validation on all inputs

**Actions:**
- [ ] Validate ALL user inputs (length, type, format)
- [ ] Sanitize HTML/JavaScript in user content
- [ ] SQL injection prevention (use parameterized queries)
- [ ] Path traversal prevention (file uploads)
- [ ] Command injection prevention
- [ ] LDAP injection prevention
- [ ] XML/XXE attack prevention
- [ ] File upload restrictions:
  - [ ] Max size: 10MB
  - [ ] Allowed types: PDF, MD, TXT only
  - [ ] Scan uploads with ClamAV
  - [ ] Store in isolated directory (not web-accessible)
- [ ] Prompt injection (already implemented ✅)

**Example:**
```python
from werkzeug.utils import secure_filename
import os

ALLOWED_EXTENSIONS = {'pdf', 'md', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400

    file = request.files['file']
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type'}), 400

    # Check size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    if size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large'}), 400

    # Secure filename
    filename = secure_filename(file.filename)
    # Save to isolated directory
```

---

### 5. Database Security ✅ Priority: HIGH

**Current State:** ⚠️ SQLite files in Docker volumes
**Required:** ✅ Encrypted, backed up, access controlled

**Actions:**
- [ ] Database encryption at rest
- [ ] Encrypt SQLite databases (SQLCipher)
- [ ] Strong password for any external DB (PostgreSQL if scaling)
- [ ] No DB credentials in code (use environment variables)
- [ ] Automated backups (daily)
- [ ] Backup encryption
- [ ] Test restore procedures
- [ ] Limit DB user permissions (principle of least privilege)
- [ ] No root/admin DB access from app

**Environment Variables:**
```bash
# NEVER commit these!
DB_ENCRYPTION_KEY=<strong-random-key>
JWT_SECRET_KEY=<strong-random-key>
API_MASTER_KEY=<strong-random-key>
```

---

### 6. Secrets Management ✅ Priority: HIGH

**Current State:** ❌ Secrets in config.env (NOT for production!)
**Required:** ✅ Proper secrets vault

**Actions:**
- [ ] Remove all secrets from code/config files
- [ ] Use secrets management:
  - [ ] Option 1: HashiCorp Vault
  - [ ] Option 2: AWS Secrets Manager
  - [ ] Option 3: Docker Secrets
  - [ ] Option 4: Kubernetes Secrets (if using K8s)
- [ ] Rotate secrets regularly (90 days)
- [ ] Audit secret access
- [ ] Never log secrets
- [ ] Git: Add config.env to .gitignore (already done ✅)

---

### 7. Docker Security ✅ Priority: HIGH

**Current State:** ⚠️ Running as root in containers
**Required:** ✅ Non-root users, minimal images

**Actions:**
- [ ] Run containers as non-root user
- [ ] Use minimal base images (alpine, distroless)
- [ ] Scan images for vulnerabilities (Trivy, Snyk)
- [ ] Remove unnecessary packages
- [ ] Set read-only filesystems where possible
- [ ] Limit container resources (CPU, memory)
- [ ] Use Docker secrets instead of env vars
- [ ] Enable Docker Content Trust
- [ ] Regular image updates

**Dockerfile Example:**
```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER appuser
WORKDIR /home/appuser/app

# Copy app files
COPY --chown=appuser:appuser . .

CMD ["python", "service.py"]
```

---

### 8. Logging & Monitoring ✅ Priority: HIGH

**Current State:** ⚠️ Basic console logging
**Required:** ✅ Centralized logging, alerting, monitoring

**Actions:**
- [ ] Centralized logging (ELK stack, Loki, CloudWatch)
- [ ] Log all:
  - [ ] Authentication attempts (success/failure)
  - [ ] API calls (who, what, when, from where)
  - [ ] Errors and exceptions
  - [ ] Security events (injection attempts, rate limits hit)
  - [ ] Admin actions
- [ ] DO NOT log:
  - [ ] Passwords
  - [ ] JWT tokens
  - [ ] PII (mask/redact)
  - [ ] API keys
- [ ] Set up alerts for:
  - [ ] Multiple failed login attempts
  - [ ] Unusual API usage patterns
  - [ ] Service downtime
  - [ ] High error rates
  - [ ] Security violations
- [ ] Monitoring dashboard (Grafana)
- [ ] Uptime monitoring (UptimeRobot, Pingdom)

---

### 9. Network Security ✅ Priority: HIGH

**Current State:** ⚠️ All ports exposed
**Required:** ✅ Firewall, VPC, minimal exposure

**Actions:**
- [ ] Firewall configuration:
  - [ ] Allow: 80 (HTTP), 443 (HTTPS)
  - [ ] Block: ALL other ports from internet
  - [ ] Internal services (ports 8000-8015) behind firewall
- [ ] Use VPC/private network for internal services
- [ ] Nginx as reverse proxy (only public-facing service)
- [ ] No direct access to:
  - [ ] Vector DB
  - [ ] Redis
  - [ ] Ollama
  - [ ] Internal microservices
- [ ] Implement WAF (Web Application Firewall)
  - [ ] Cloudflare WAF (free tier)
  - [ ] ModSecurity
- [ ] DDoS protection (Cloudflare)
- [ ] IP whitelisting for admin endpoints

**Docker Compose (Production):**
```yaml
services:
  nginx:
    ports:
      - "80:80"
      - "443:443"  # Only Nginx exposed!

  api-gateway:
    ports: []  # NOT exposed directly

  # All other services: NO port exposure
```

---

### 10. CORS & Security Headers ✅ Priority: MEDIUM

**Current State:** ⚠️ CORS allows all origins
**Required:** ✅ Strict CORS, security headers

**Actions:**
- [ ] Restrict CORS to your domain only
- [ ] Security headers (already partial ✅):
  - [x] Content-Security-Policy
  - [x] X-Frame-Options
  - [x] X-Content-Type-Options
  - [ ] Permissions-Policy (enhance)
  - [ ] Referrer-Policy
  - [x] Strict-Transport-Security

**Nginx Config:**
```nginx
add_header Content-Security-Policy "default-src 'self'; script-src 'self'; object-src 'none';" always;
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
```

**Flask CORS:**
```python
CORS(app, origins=['https://yourdomain.com'])  # NOT '*'
```

---

### 11. Dependency Security ✅ Priority: MEDIUM

**Current State:** ⚠️ Dependencies not regularly scanned
**Required:** ✅ Automated vulnerability scanning

**Actions:**
- [ ] Scan Python dependencies (Snyk, Safety)
- [ ] Scan npm dependencies (npm audit)
- [ ] Automated security updates (Dependabot)
- [ ] Pin dependency versions (already done ✅)
- [ ] Regular updates (monthly)
- [ ] CVE monitoring for used libraries

**Commands:**
```bash
# Python
pip install safety
safety check

# npm
npm audit
npm audit fix

# Docker images
trivy image your-image:tag
```

---

### 12. Backup & Disaster Recovery ✅ Priority: MEDIUM

**Current State:** ❌ No automated backups
**Required:** ✅ Daily backups, tested restore

**Actions:**
- [ ] Automated daily backups:
  - [ ] Vector database
  - [ ] Auth database
  - [ ] Research agent database
  - [ ] Uploaded documents
  - [ ] Configuration
- [ ] Off-site backup storage (S3, Backblaze)
- [ ] Encrypted backups
- [ ] Retention policy (30 days)
- [ ] Test restore monthly
- [ ] Document recovery procedures
- [ ] RTO/RPO defined (Recovery Time/Point Objectives)

---

### 13. Privacy & Compliance ✅ Priority: MEDIUM (depends on use case)

**Current State:** ⚠️ Basic PII detection
**Required:** ✅ GDPR/CCPA compliance (if applicable)

**Actions:**
- [ ] Privacy policy
- [ ] Terms of service
- [ ] Cookie consent banner
- [ ] Data retention policy
- [ ] User data export (GDPR right to access)
- [ ] User data deletion (GDPR right to erasure)
- [ ] Data processing agreement
- [ ] Audit logs (who accessed what data)
- [ ] Data anonymization/pseudonymization
- [ ] PII detection & handling (already implemented ✅)

---

### 14. API Documentation & Versioning ✅ Priority: LOW

**Current State:** ⚠️ No public API docs
**Required:** ✅ OpenAPI/Swagger docs

**Actions:**
- [ ] OpenAPI/Swagger documentation
- [ ] API versioning (/api/v1/, /api/v2/)
- [ ] Deprecation notices
- [ ] Rate limit documentation
- [ ] Authentication documentation
- [ ] Error response documentation

---

### 15. Testing & Security Audits ✅ Priority: HIGH

**Current State:** ⚠️ Basic unit tests
**Required:** ✅ Comprehensive security testing

**Actions:**
- [ ] Penetration testing
- [ ] Security audit by third party
- [ ] OWASP Top 10 testing
- [ ] Load testing
- [ ] Chaos engineering (resilience testing)
- [ ] Bug bounty program (after public launch)

**Tools:**
- OWASP ZAP (free, automated security testing)
- Burp Suite (professional pentesting)
- Nmap (network scanning)

---

## 🚀 Deployment Checklist

### Pre-Launch
- [ ] SSL certificate installed and auto-renewing
- [ ] All secrets in vault (NOT in config files)
- [ ] Firewall configured (only 80/443 open)
- [ ] Authentication enforced on all endpoints
- [ ] Rate limiting active
- [ ] Monitoring & alerting configured
- [ ] Backups automated and tested
- [ ] Error pages configured (don't expose stack traces)
- [ ] Security headers configured
- [ ] CORS restricted to your domain
- [ ] Dependencies scanned for vulnerabilities
- [ ] Docker images scanned
- [ ] Privacy policy & ToS live
- [ ] Incident response plan documented

### Day 1 (Launch)
- [ ] Monitor logs for anomalies
- [ ] Check rate limits are working
- [ ] Verify backups running
- [ ] Test authentication flow
- [ ] Monitor resource usage
- [ ] Check for DDoS attacks

### Ongoing
- [ ] Weekly: Review logs and alerts
- [ ] Monthly: Update dependencies
- [ ] Quarterly: Security audit
- [ ] Quarterly: Restore test
- [ ] Annually: Penetration test

---

## 🛠️ Quick Wins (Do These First)

1. **Add HTTPS** (2 hours)
   - Get Let's Encrypt cert
   - Configure Nginx

2. **Enforce Authentication** (4 hours)
   - Protect all sensitive endpoints
   - Add login requirement to frontend

3. **Restrict CORS** (15 minutes)
   - Change `origins='*'` to your domain

4. **Add Security Headers** (30 minutes)
   - Already mostly done! ✅

5. **Set Up Monitoring** (2 hours)
   - Basic Grafana dashboard
   - Uptime monitoring

**Total: ~9 hours for critical security baseline**

---

## 📚 Resources

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- Docker Security: https://cheatsheetseries.owasp.org/cheatsheets/Docker_Security_Cheat_Sheet.html
- Flask Security: https://flask.palletsprojects.com/en/2.3.x/security/
- Let's Encrypt: https://letsencrypt.org/
- Cloudflare (free tier): https://www.cloudflare.com/

---

## 💰 Estimated Costs (Monthly)

**Minimal Setup:**
- SSL: $0 (Let's Encrypt free)
- Cloudflare Free Tier: $0
- Hosting: $10-50 (Digital Ocean, AWS)
- **Total: $10-50/month**

**Professional Setup:**
- SSL: $0 (Let's Encrypt)
- Cloudflare Pro: $20/month
- Monitoring (Datadog): $15/month
- Secrets Manager (AWS): $0.40/month
- Backups (S3): $5/month
- **Total: ~$50-100/month**

---

## 🎯 Priority Order

1. 🔴 **CRITICAL** (Do before ANY internet exposure):
   - SSL/TLS
   - Authentication enforcement
   - Rate limiting
   - Firewall configuration

2. 🟠 **HIGH** (Do within first week):
   - Secrets management
   - Database security
   - Logging & monitoring
   - Docker hardening

3. 🟡 **MEDIUM** (Do within first month):
   - CORS restriction
   - Dependency scanning
   - Backups
   - Privacy compliance

4. 🟢 **LOW** (Nice to have):
   - API documentation
   - Performance optimization
   - Advanced features

---

**Status:** 📋 This is your roadmap! Complete after Research Agent is done.

**Next Steps:** Finish Research Agent → Then tackle security hardening! 🚀

