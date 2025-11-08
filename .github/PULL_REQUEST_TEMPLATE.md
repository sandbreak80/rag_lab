## Pull Request Template for OTEL Sprint

### PR Type
<!-- Check one -->
- [ ] Day 1: Provenance Fix
- [ ] Day 2: Waterfall & UX
- [ ] Day 3: OTEL Foundation
- [ ] Day 4: OpenLLMetry
- [ ] Day 5: Conversation Persistence

---

### Description
<!-- Brief description of what this PR does -->

**Related TODO IDs:**
- [ ] <!-- TODO ID from todo list -->

**Related Documentation:**
- `docs/deployment/OTEL_DEPLOYMENT_PLAN.md`
- `docs/deployment/OTEL_WEEK_1_EXECUTION_SUMMARY.md`

---

### Changes Made
<!-- Detailed list of changes -->

#### New Files:
-

#### Modified Files:
-

#### Deleted Files:
-

---

### Testing Performed

#### Unit Tests
```bash
# Commands run
pytest tests/test_*.py -v

# Results
✅ All tests passing
```

#### Integration Tests
```bash
# Commands run
pytest tests/integration/test_*.py -v

# Results
✅ All tests passing
```

#### Manual Testing
- [ ] Service health checks passing
- [ ] Frontend builds successfully
- [ ] No console errors
- [ ] Feature works as expected
- [ ] No regression in existing features

---

### Acceptance Criteria
<!-- From deployment plan -->

- [ ] <!-- Criterion 1 -->
- [ ] <!-- Criterion 2 -->
- [ ] <!-- Criterion 3 -->

---

### Screenshots/Demo
<!-- If applicable, add screenshots or demo links -->

---

### Deployment Notes

#### Database Migrations
<!-- Any schema changes -->
- [ ] No migrations needed
- [ ] Migrations included: <!-- list files -->

#### Configuration Changes
<!-- Any new environment variables or config -->
- [ ] No config changes
- [ ] New config: <!-- list changes -->

#### Breaking Changes
<!-- Any breaking changes to API or behavior -->
- [ ] No breaking changes
- [ ] Breaking changes: <!-- describe -->

---

### Rollback Plan
<!-- How to rollback if this PR causes issues -->

1. Revert commit: `git revert <commit-sha>`
2. Or checkout previous version: `git checkout v1.3.0`
3. Rebuild and restart: `docker compose down && docker compose up -d`

---

### Checklist

#### Before Review
- [ ] Code follows project style guide
- [ ] All tests passing
- [ ] Linter clean (no errors)
- [ ] TypeScript type checking passes (frontend)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] No console errors in browser
- [ ] Commit messages are clear

#### Before Merge
- [ ] Reviewed by at least one person
- [ ] All acceptance criteria met
- [ ] CI/CD passes (if applicable)
- [ ] No merge conflicts
- [ ] Branch up to date with main

---

### Related Issues
<!-- Link to any issues this PR addresses -->

Closes #
Fixes #
Addresses #

---

### Additional Notes
<!-- Any other context for reviewers -->

---

**Review Priority:** <!-- Low / Medium / High / Critical -->
**Estimated Review Time:** <!-- hours -->
**Risk Level:** <!-- Low / Medium / High -->

