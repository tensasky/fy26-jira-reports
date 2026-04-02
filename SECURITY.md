# Security Audit - 2026-04-02

## ⚠️ CRITICAL: Sensitive Data in Git History

### Issue
The following files contain sensitive tokens and are tracked in Git history:

- `config/com.openclaw.cntin730-report.plist`
- `fy26_pmo/com.openclaw.fy26-pmo-report.plist`
- `projects/cntin730-report/config/com.openclaw.cntin730-report.plist`
- `projects/fy26-intake-cost/com.openclaw.fy26-intake-cost.plist`

These files contain:
- `JIRA_API_TOKEN` (Atlassian API Token)
- `QQ_MAIL_PASSWORD` (QQ Email Authorization Code)

### Immediate Actions Taken
1. ✅ Removed plist files from git tracking
2. ✅ Added *.plist to .gitignore
3. ✅ Created template plist files (without sensitive data)
4. ✅ Updated README with security warnings

### ⚠️ WARNING: Git History Still Contains Sensitive Data

Even after removing files from current commit, the sensitive data remains in Git history.

**Anyone with access to this repo can see historical tokens by:**
```bash
git log --all --full-history --source --name-only -- '*.plist'
git show <commit-hash>:path/to/file.plist
```

### Recommended Actions

#### Option 1: Rotate Tokens (RECOMMENDED - Easiest)
1. Revoke current JIRA_API_TOKEN at https://id.atlassian.com/manage-profile/security/api-tokens
2. Generate new token
3. Update local `.jira-config` and plist files
4. Old tokens in history will be invalid

#### Option 2: Clean Git History (Advanced)
Use BFG Repo-Cleaner or git-filter-repo to remove sensitive data from entire history:

```bash
# Using BFG Repo-Cleaner
bfg --replace-text passwords.txt repo.git
git reflog expire --expire=now --all
git gc --prune=now --aggressive

# Force push (WARNING: affects all collaborators)
git push --force
```

**⚠️ Force push will require all collaborators to reclone the repo!**

#### Option 3: Make Repo Private
If tokens cannot be rotated immediately, make the GitHub repository private until tokens are rotated.

### Prevention

1. **Never commit files containing:**
   - API tokens
   - Passwords
   - Authorization codes
   - Private keys

2. **Use .gitignore:**
   ```
   *.plist
   .jira-config
   .env
   *token*
   *password*
   ```

3. **Use template files:**
   - Commit `config.template.plist`
   - Add setup instructions
   - Copy to `config.plist` locally (not tracked)

4. **Pre-commit hooks:**
   ```bash
   # .git/hooks/pre-commit
   if git diff --cached --name-only | grep -E "\.plist$|\.config$"; then
       echo "ERROR: Attempting to commit plist/config files!"
       exit 1
   fi
   ```

### Current Token Status
- JIRA_API_TOKEN: ⚠️ Exposed in git history
- QQ_MAIL_PASSWORD: ⚠️ Exposed in git history

**ACTION REQUIRED:** Rotate both tokens immediately!

---
Last Updated: 2026-04-02
