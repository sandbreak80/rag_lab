# Security Notes for AWS Deployment

## GitHub Token Usage

The cloud-init scripts contain a GitHub Personal Access Token for cloning the private repository.

### ⚠️ IMPORTANT SECURITY CONSIDERATIONS

1. **Token is embedded in cloud-init script**
   - Visible in EC2 user-data
   - Stored in `/var/log/cloud-init-output.log`
   - DO NOT commit cloud-init files with tokens to public repos

2. **Token Permissions**
   - Should have minimal required permissions
   - Recommend: `repo` (read-only) access only
   - Set expiration date

3. **Rotation**
   - Rotate token periodically
   - Update cloud-init scripts after rotation
   - Revoke old tokens

4. **Alternative Approaches** (More Secure)

   **Option A: Use AWS Secrets Manager**
   ```yaml
   runcmd:
     - TOKEN=$(aws secretsmanager get-secret-value --secret-id github-token --query SecretString --output text)
     - git clone https://$TOKEN@github.com/sandbreak80/rag_lab.git
   ```

   **Option B: Use AWS CodeCommit**
   - Mirror repo to AWS CodeCommit
   - Use IAM roles (no tokens needed)

   **Option C: Deploy Keys**
   - Generate SSH deploy key
   - Add to GitHub repo
   - Use SSH clone instead of HTTPS

   **Option D: Public Repository**
   - Make repo public (if acceptable)
   - No authentication needed

### Current Token

```
Token: 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
Permissions: Unknown (should verify)
Expiration: Unknown (should set)
```

### Cleanup After Testing

After testing is complete:
1. Revoke this token in GitHub settings
2. Create new token with minimal permissions
3. Consider implementing one of the more secure alternatives

### Best Practices

- ✅ Use AWS Secrets Manager for production
- ✅ Set token expiration dates
- ✅ Use minimal required permissions
- ✅ Rotate tokens regularly
- ❌ Don't commit tokens to git
- ❌ Don't expose tokens in logs (where possible)
- ❌ Don't use personal tokens in production

### GitHub Token Management

**To create a new token:**
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo` (for private repositories)
4. Set expiration: 30-90 days
5. Copy token immediately (only shown once)

**To revoke token:**
1. Go to GitHub → Settings → Developer settings → Personal access tokens
2. Find the token
3. Click "Delete" or "Revoke"

### For Production Deployments

Use AWS Secrets Manager:

```bash
# Store token in Secrets Manager
aws secretsmanager create-secret \
  --name rag-lab/github-token \
  --secret-string "ghp_..."

# Grant EC2 instance IAM role access
# Then in cloud-init:
TOKEN=$(aws secretsmanager get-secret-value \
  --secret-id rag-lab/github-token \
  --query SecretString \
  --output text)
```

This way the token:
- Is encrypted at rest
- Is not in user-data
- Can be rotated without updating cloud-init
- Has proper IAM access control

