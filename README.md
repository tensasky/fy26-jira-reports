# FY26 Jira Reports

> ⚠️ **SECURITY NOTICE**: This repository has been audited for sensitive data. See [SECURITY.md](SECURITY.md) for details.

This repository contains three automated reporting systems for FY26 project management.

## 📊 Reports Overview

| Report | Schedule | Description | Jira Query |
|--------|----------|-------------|------------|
| **FY26_PMO** | Daily 18:00 | Daily Epic Status Report | Multi-project Epics linked to CNTIN Features |
| **CNTIN-730** | Weekdays 12:00 | Weekly FY26 Initiatives Report | Initiatives under CNTIN-730 Goal |
| **FY26_Intake_Cost** | Weekdays 10:00 & 15:00 | Intake Cost Tracking Report | Initiatives under CNTIN-730 with cost fields |

## 🔒 Security Setup (IMPORTANT!)

### ⚠️ Never Commit Sensitive Files

The following files are **gitignored** and should never be committed:
- `.jira-config` - Contains API tokens
- `*.plist` - Launchd configs with tokens  
- Any file with `token`, `password`, or `secret` in the name

See [SECURITY.md](SECURITY.md) for full security audit details.

### Initial Setup

```bash
# 1. Clone the repository
git clone https://github.com/tensasky/fy26-jira-reports.git
cd fy26-jira-reports

# 2. Create your local config from template
cp .jira-config.template .jira-config
# Edit .jira-config with your actual tokens

# 3. Copy template plist files (edit these locally)
cp fy26_pmo/com.openclaw.fy26-pmo-report.template.plist \
   ~/Library/LaunchAgents/com.openclaw.fy26-pmo-report.plist

cp projects/cntin730-report/config/com.openclaw.cntin730-report.template.plist \
   ~/Library/LaunchAgents/com.openclaw.cntin730-report.plist

cp projects/fy26-intake-cost/com.openclaw.fy26-intake-cost.template.plist \
   ~/Library/LaunchAgents/com.openclaw.fy26-intake-cost.plist

# 4. Edit plist files to add your tokens (see instructions below)
#    ⚠️ DO NOT commit these plist files!

# 5. Set secure permissions
chmod 600 .jira-config

# 6. Verify nothing sensitive is tracked
git status
```

### Configure Launchd Plist Files

Edit each plist file in `~/Library/LaunchAgents/` to add your credentials:

```xml
<key>EnvironmentVariables</key>
<dict>
    <key>PATH</key>
    <string>/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin</string>
    <key>HOME</key>
    <string>/Users/admin</string>
    <!-- Add these lines (replace with your actual values) -->
    <key>JIRA_API_TOKEN</key>
    <string>YOUR_ACTUAL_JIRA_TOKEN_HERE</string>
    <key>QQ_MAIL_PASSWORD</key>
    <string>YOUR_ACTUAL_QQ_AUTH_CODE_HERE</string>
</dict>
```

### Load Launchd Jobs

```bash
# Load all定时任务
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-pmo-report.plist
launchctl load ~/Library/LaunchAgents/com.openclaw.cntin730-report.plist
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-intake-cost.plist

# Verify they're loaded
launchctl list | grep openclaw
```

## 📁 Repository Structure

```
├── fy26_pmo/                   # FY26_PMO Daily Report
│   ├── scripts/
│   │   ├── fetch_data.py       # Data fetching from Jira
│   │   ├── generate_html_v5.py # HTML report generation
│   │   └── send_email.py       # Email delivery
│   ├── reports/                # Generated reports
│   └── README.md
│
├── cntin730-report/            # CNTIN-730 Weekly Report
│   ├── scripts/
│   │   ├── cntin730_report.py  # Combined fetch + generate
│   │   └── send_report.py      # Email delivery
│   ├── reports/                # Generated reports
│   └── README.md
│
├── fy26-intake-cost/           # FY26_Intake_Cost Report
│   ├── scripts/
│   │   ├── fetch_intake_cost.py # Data fetching from Jira
│   │   ├── generate_html.py    # Interactive HTML generator
│   │   └── run.sh              # Full pipeline script
│   ├── reports/                # Generated reports
│   └── README.md
│
├── docs/                       # Documentation
├── SECURITY.md                 # Security audit and guidelines
├── MEMORY.md                   # Long-term memory & decisions
└── README.md                   # This file
```

## 🔧 Dependencies

### System Requirements
- **macOS** with launchd support
- **Python 3.9+**
- **7z** (for AES-256 ZIP encryption) - `brew install p7zip`

### Python Packages
```bash
pip install requests urllib3
```

### Environment Variables

All scripts require these environment variables:

```bash
# Jira API Configuration (REQUIRED)
export JIRA_API_TOKEN="YOUR_JIRA_API_TOKEN"  # Your Jira API Token
export JIRA_EMAIL="rcheng2@lululemon.com"     # Jira account email

# Email Configuration (REQUIRED)
export QQ_MAIL_PASSWORD="YOUR_QQ_AUTH_CODE"   # QQ email authorization code
```

### Jira API Token Setup
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a label (e.g., "FY26 Reports")
4. Copy the token and set as `JIRA_API_TOKEN`

### QQ Email Authorization Code
1. Log into QQ Mail (mail.qq.com)
2. Go to Settings → Accounts → POP3/IMAP/SMTP
3. Generate an "Authorization Code" (授权码)
4. Use this code as `QQ_MAIL_PASSWORD`

## 📧 Email Delivery

All reports are sent to: **chinatechpmo@lululemon.com**
CC: rcheng2@lululemon.com, jjang2@lululemon.com

**Security:**
- Reports sent as **AES-256 encrypted ZIP** files
- Password: `lulupmo`
- HTML files contain no sensitive data in comments

## 🔄 Data Flow

### FY26_PMO Report
```
Jira API → fetch_data.py → SQLite (jira_report.db) → generate_html_v5.py → HTML → send_email.py → Encrypted ZIP
```

**Data Logic:**
1. Fetch Epics from 22 projects (CNTEC, CNTOM, CNTDM, etc.)
2. Fetch CNTIN Initiatives with `FY26_INIT` label
3. Fetch Features (linked to Initiatives via parent)
4. Generate hierarchy: Initiative → Feature → Epic
5. Track status trends via `customfield_14024`

### CNTIN-730 Report
```
Jira API → cntin730_report.py → HTML → send_report.py → Encrypted ZIP
```

**Data Logic:**
1. Query: `parent = CNTIN-730 AND issuetype = Initiative`
2. CNTIN-730 is a **Goal** type (hierarchy level 4)
3. Fetches all child Initiatives (167 total)
4. Generates interactive HTML with filters

### FY26_Intake_Cost Report
```
Jira API → fetch_intake_cost.py → SQLite (intake_cost.db) → generate_html.py → HTML → run.sh → Encrypted ZIP
```

**Data Logic:**
1. Query: `parent = CNTIN-730 AND issuetype = Initiative`
2. Extract custom fields for cost tracking
3. Calculate SLA from creation date
4. Interactive HTML with real-time exchange rate

## 🐛 Troubleshooting

### Issue: "请设置 JIRA_API_TOKEN 环境变量"
**Cause:** Environment variable not set
**Fix:** 
```bash
export JIRA_API_TOKEN="your_token"
# Or add to ~/.zshrc for persistence
```

### Issue: 0 records returned from Jira
**Cause:** API token permissions or query syntax
**Fix:**
- Verify token at https://id.atlassian.com/manage-profile/security/api-tokens
- Test query manually:
```bash
source ~/.openclaw/workspace/.jira-config
curl -X POST -H "Authorization: Basic $(echo -n "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" | base64)" \
  -H "Content-Type: application/json" \
  "https://lululemon.atlassian.net/rest/api/3/search/jql" \
  -d '{"jql": "parent = CNTIN-730", "maxResults": 10}'
```

### Issue: Email not sending
**Cause:** QQ email authorization code expired
**Fix:** Regenerate authorization code at QQ Mail settings

## 📝 Version Control

This repository tracks all changes. Key files:
- `MEMORY.md` - Long-term decisions and configurations
- `CHANGELOG.md` - Detailed change history per report
- Git commits with descriptive messages

## 🔒 Security Best Practices

1. **Never commit sensitive files**: `.jira-config`, `*.plist`, any file with tokens
2. **Rotate tokens regularly**: Every 90 days
3. **Use template files**: Copy from `.template` files, edit locally
4. **Set file permissions**: `chmod 600 .jira-config`
5. **Verify before committing**: Run `git status` and review changes

See [SECURITY.md](SECURITY.md) for full security guidelines and audit details.

## 📄 License

Internal Use Only - Lululemon China Tech Team
