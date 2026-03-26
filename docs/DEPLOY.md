# FY26 Jira Reports - Deployment Guide

## 1. Prerequisites

### 1.1 System Requirements
- **OS**: macOS 12.0+ (Monterey or later)
- **Python**: 3.9 or higher
- **Memory**: 4GB RAM minimum
- **Disk**: 1GB free space
- **Network**: Access to Jira (lululemon.atlassian.net) and SMTP (smtp.qq.com)

### 1.2 Required Tools
```bash
# Check Python version
python3 --version  # Should be 3.9+

# Install 7z for encryption
brew install p7zip

# Verify installation
7z --version
```

### 1.3 Required Access
- Jira API token with read access to projects: CNTIN, CNTEC, CNTOM, etc.
- QQ Email account (3823810468@qq.com) with SMTP enabled
- macOS administrator access for launchd configuration

## 2. Environment Setup

### 2.1 Clone Repository
```bash
cd ~/
git clone https://github.com/tensasky/fy26-jira-reports.git
ln -s ~/fy26-jira-reports ~/.openclaw/workspace
```

### 2.2 Configure Environment Variables
```bash
# Create config file
mkdir -p ~/.openclaw/workspace
cat > ~/.openclaw/workspace/.jira-config << 'EOF'
export JIRA_URL="https://lululemon.atlassian.net"
export JIRA_EMAIL="rcheng2@lululemon.com"
export JIRA_API_TOKEN="YOUR_JIRA_API_TOKEN_HERE"
export QQ_EMAIL_SENDER="3823810468@qq.com"
export QQ_EMAIL_PASSWORD="YOUR_QQ_EMAIL_PASSWORD_HERE"
EOF

# Secure the file
chmod 600 ~/.openclaw/workspace/.jira-config
```

### 2.3 Install Python Dependencies
```bash
cd ~/fy26-jira-reports

# Install required packages
pip3 install requests urllib3

# Or use requirements.txt if available
pip3 install -r requirements.txt
```

## 3. Report-Specific Deployment

### 3.1 CNTIN-730 Weekly Report

#### 3.1.1 Directory Structure
```
projects/cntin730-report/
├── scripts/
│   ├── cntin730_report.py      # Main script
│   └── send_report.py          # Email sender
├── reports/                     # Output directory
├── logs/                        # Log files
└── config/
    └── com.openclaw.cntin730-report.plist
```

#### 3.1.2 Configuration
```bash
# Create log directory
mkdir -p ~/fy26-jira-reports/projects/cntin730-report/logs

# Copy launchd plist
cp ~/fy26-jira-reports/projects/cntin730-report/config/com.openclaw.cntin730-report.plist \
   ~/Library/LaunchAgents/

# Load the job
launchctl load ~/Library/LaunchAgents/com.openclaw.cntin730-report.plist

# Verify
launchctl list | grep cntin730
```

#### 3.1.3 Schedule
- **When**: Weekdays (Mon-Fri) at 12:00
- **What**: Sends CNTIN-730 FY26 Initiatives Report
- **Recipient**: chinatechpmo@lululemon.com

### 3.2 FY26_PMO Daily Report

#### 3.2.1 Database Setup
```bash
cd ~/fy26-jira-reports/fy26_pmo

# Initialize SQLite database
python3 -c "
import sqlite3
conn = sqlite3.connect('jira_report.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS epics (
        key TEXT PRIMARY KEY,
        summary TEXT,
        status TEXT,
        project TEXT,
        parent_key TEXT,
        created TEXT
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS initiatives (
        key TEXT PRIMARY KEY,
        summary TEXT,
        status TEXT,
        labels TEXT
    )
''')

conn.commit()
conn.close()
"
```

#### 3.2.2 Configuration
```bash
# Copy launchd plist
cp ~/fy26-jira-reports/fy26_pmo/com.openclaw.fy26-pmo-report.plist \
   ~/Library/LaunchAgents/

# Load the job
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-pmo-report.plist

# Verify
launchctl list | grep fy26-pmo
```

#### 3.2.3 Schedule
- **When**: Daily at 18:00
- **What**: Sends FY26_PMO Epic Status Report
- **Recipient**: chinatechpmo@lululemon.com

### 3.3 FY26_Intake_Cost Report

#### 3.3.1 Database Setup
```bash
cd ~/fy26-jira-reports/projects/fy26-intake-cost

# Database will be created automatically on first run
# Verify permissions
mkdir -p logs reports
```

#### 3.3.2 Configuration
```bash
# Copy launchd plist
cp ~/fy26-jira-reports/projects/fy26-intake-cost/com.openclaw.fy26-intake-cost.plist \
   ~/Library/LaunchAgents/

# Load the job
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-intake-cost.plist

# Verify
launchctl list | grep fy26-intake-cost
```

#### 3.3.3 Schedule
- **When**: Weekdays at 10:00 and 15:00
- **What**: Sends FY26_Intake_Cost Report
- **Recipient**: chinatechpmo@lululemon.com

## 4. Verification

### 4.1 Test Manual Execution
```bash
# Test CNTIN-730
cd ~/fy26-jira-reports/projects/cntin730-report
source ~/.openclaw/workspace/.jira-config
python3 scripts/cntin730_report.py

# Test FY26_PMO
cd ~/fy26-jira-reports/fy26_pmo
source ~/.openclaw/workspace/.jira-config
python3 fetch_data.py
python3 generate_html_v5.py

# Test FY26_Intake_Cost
cd ~/fy26-jira-reports/projects/fy26-intake-cost
source ~/.openclaw/workspace/.jira-config
python3 scripts/fetch_intake_cost.py
python3 scripts/generate_html.py
```

### 4.2 Test Email Delivery
```bash
# Send test email (dry run)
export QQ_MAIL_PASSWORD="your_password"
python3 scripts/send_report.py --test

# Check inbox at chinatechpmo@lululemon.com
# ZIP password: lulupmo
```

### 4.3 Verify Scheduled Jobs
```bash
# List all OpenClaw jobs
launchctl list | grep openclaw

# Expected output:
# - 0 com.openclaw.cntin730-report
# - 0 com.openclaw.fy26-intake-cost
# - 1 com.openclaw.fy26-pmo-report

# Check job details
launchctl print gui/$(id - u)/com.openclaw.fy26-pmo-report
```

## 5. Troubleshooting

### 5.1 Job Not Running
**Symptom**: No reports received, logs empty

**Solution**:
```bash
# Check if job is loaded
launchctl list | grep openclaw

# If not found, reload
launchctl unload ~/Library/LaunchAgents/com.openclaw.*.plist 2>/dev/null
launchctl load ~/Library/LaunchAgents/com.openclaw.*.plist

# Check for errors
cat ~/fy26-jira-reports/projects/*/logs/launchd_error.log
```

### 5.2 Jira API Errors
**Symptom**: "Authentication failed" or "403 Forbidden"

**Solution**:
```bash
# Verify token
source ~/.openclaw/workspace/.jira-config
curl -H "Authorization: Bearer $JIRA_API_TOKEN" \
     "https://lululemon.atlassian.net/rest/api/3/myself"

# If failed, regenerate token at:
# https://id.atlassian.com/manage-profile/security/api-tokens
```

### 5.3 Email Delivery Failures
**Symptom**: Reports generated but not received

**Solution**:
```bash
# Test SMTP connection
python3 -c "
import smtplib
server = smtplib.SMTP('smtp.qq.com', 587)
server.starttls()
server.login('3823810468@qq.com', 'your_password')
print('Login successful')
server.quit()
"

# Check QQ email settings
# 1. Enable SMTP in QQ Mail settings
# 2. Use authorization code (not email password)
# 3. Ensure 2FA is properly configured
```

### 5.4 Permission Errors
**Symptom**: "Permission denied" in logs

**Solution**:
```bash
# Fix file permissions
chmod -R u+rw ~/fy26-jira-reports
chmod 600 ~/.openclaw/workspace/.jira-config
chmod 644 ~/Library/LaunchAgents/com.openclaw.*.plist

# Fix script permissions
chmod +x ~/fy26-jira-reports/*/scripts/*.py
chmod +x ~/fy26-jira-reports/*/run.sh
```

## 6. Maintenance

### 6.1 Daily Checks
```bash
# Check yesterday's logs
find ~/fy26-jira-reports -name "*.log" -mtime -1 -exec ls -lh {} \;

# Verify database integrity
sqlite3 ~/fy26-jira-reports/fy26_pmo/jira_report.db "PRAGMA integrity_check;"
sqlite3 ~/fy26-jira-reports/projects/fy26-intake-cost/intake_cost.db "PRAGMA integrity_check;"
```

### 6.2 Weekly Maintenance
```bash
# Rotate logs
find ~/fy26-jira-reports -name "*.log" -mtime +7 -delete

# Clean old reports (keep last 30 days)
find ~/fy26-jira-reports -name "*.html" -mtime +30 -delete
find ~/fy26-jira-reports -name "*.zip" -mtime +30 -delete

# Update repository
cd ~/fy26-jira-reports
git pull origin main
```

### 6.3 Monthly Review
- Review error logs for patterns
- Check report delivery success rate
- Verify data accuracy against Jira
- Update documentation if needed

## 7. Rollback Procedure

### 7.1 Stop All Jobs
```bash
launchctl unload ~/Library/LaunchAgents/com.openclaw.*.plist
```

### 7.2 Backup Data
```bash
mkdir -p ~/backup/$(date +%Y%m%d)
cp ~/fy26-jira-reports/*/jira_report.db ~/backup/$(date +%Y%m%d)/
cp ~/fy26-jira-reports/*/*/*.db ~/backup/$(date +%Y%m%d)/
```

### 7.3 Restore Previous Version
```bash
cd ~/fy26-jira-reports
git log --oneline  # Find previous commit
git checkout <commit_hash>
```

## 8. Security Checklist

- [ ] API tokens stored in `.jira-config` with 600 permissions
- [ ] Email password not hardcoded in scripts
- [ ] Database files have 600 permissions
- [ ] Log files don't contain sensitive data
- [ ] ZIP encryption enabled for all email attachments
- [ ] Repository is private (if on GitHub)
- [ ] No credentials committed to version control

## 9. Support Contacts

| Issue Type | Contact | Notes |
|------------|---------|-------|
| Jira Access | IT Helpdesk | API token issues |
| Email Delivery | QQ Mail Support | SMTP configuration |
| System Issues | DevOps Team | launchd, macOS |
| Report Content | PMO Team | Data accuracy questions |

## 10. Quick Reference

### 10.1 Useful Commands
```bash
# Force run a report immediately
launchctl start com.openclaw.fy26-pmo-report

# Check next scheduled run
launchctl print gui/$(id - u)/com.openclaw.fy26-pmo-report | grep "next scheduled"

# View real-time logs
tail -f ~/fy26-jira-reports/projects/*/logs/*.log

# Test single component
python3 -c "import scripts.fetch_data; print('OK')"
```

### 10.2 File Locations
| Component | Path |
|-----------|------|
| Main directory | `~/fy26-jira-reports` |
| Config | `~/.openclaw/workspace/.jira-config` |
| Launchd plists | `~/Library/LaunchAgents/com.openclaw.*.plist` |
| Logs | `~/fy26-jira-reports/projects/*/logs/` |
| Reports | `~/fy26-jira-reports/projects/*/reports/` |
| Databases | `~/fy26-jira-reports/*/*.db` |
