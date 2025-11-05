# Complete Testing & Validation Plan
## Security Services - End-to-End Testing

**Date:** November 5, 2025

---

## 🎯 **Testing Objectives**

1. ✅ Verify all services are running
2. ✅ Test backend security services
3. ✅ Test API Gateway integration
4. ✅ Test end-to-end query flow
5. ✅ Run unit tests
6. ✅ Run integration tests
7. ✅ Run Playwright UI tests
8. ✅ Verify UI changes (if any)

---

## 📋 **Test Plan**

### Phase 1: Service Health Check
```bash
# Check all containers
docker compose ps

# Check security services
curl http://localhost:8013/health
curl http://localhost:8012/health
curl http://localhost:8000/health
```

### Phase 2: Backend Unit Tests
```bash
# Test security services directly
python3 tests/test_security_services.py
```

### Phase 3: API Integration Tests
```bash
# Test through API Gateway
# 1. Normal query
# 2. PII query
# 3. Injection attempt
# 4. Unicode attack
```

### Phase 4: End-to-End Tests
```bash
# Start ALL services
docker compose up -d

# Wait for services to be healthy
sleep 30

# Run Playwright tests
docker compose run --rm playwright-tests
```

### Phase 5: UI Validation
```bash
# Check if frontend is accessible
curl http://localhost:3000

# Verify security UI components (if implemented)
# - Security status display
# - Violation warnings
# - Security toggles
```

---

## ✅ **Success Criteria**

| Test | Expected Result |
|------|----------------|
| Security services health | ✅ Both return 200 |
| PII detection | ✅ Detects and redacts PII |
| Injection detection | ✅ Blocks malicious prompts |
| Unicode sanitization | ✅ Removes zero-width chars |
| API integration | ✅ Security runs on every query |
| End-to-end flow | ✅ Query works through full stack |
| Playwright tests | ✅ All UI tests pass |
| UI displays security | ⚠️ Not implemented yet |

---

## 🚀 **Execution Steps**

Run tests in order:
1. Service health checks
2. Unit tests
3. Integration tests
4. Playwright tests
5. Manual UI verification

