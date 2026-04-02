# CNTIN-730 FY26 Initiatives Weekly Report

## Overview
Weekly automated report for CNTIN-730 FY26 Initiatives tracking.

## Schedule
- **Frequency**: Weekdays (Mon-Fri)
- **Time**: 12:00 (Noon)
- **Recipient**: chinatechpmo@lululemon.com
- **CC**: rcheng2@lululemon.com, jjang2@lululemon.com

## Data Source

### Jira Configuration
- **Project**: CNTIN
- **Parent**: CNTIN-730 (Goal type, hierarchy level 4)
- **Issue Type**: Initiative
- **JQL Query**: `parent = CNTIN-730 AND issuetype = Initiative`

### Data Fields
| Field | Jira Source | Usage |
|-------|-------------|-------|
| Key | `key` | Ticket identifier with link |
| Summary | `fields.summary` | Initiative title |
| Status | `fields.status.name` | Current workflow status |
| Assignee | `fields.assignee.displayName` | Owner |
| Priority | `fields.priority.name` | Importance level |
| Created | `fields.created` | Creation timestamp |
| Updated | `fields.updated` | Last update timestamp |
| Due Date | `fields.duedate` | Target completion date |
| Description | `fields.description` | Full description (ADF format) |
| Labels | `fields.labels` | Categorization tags |

### Current Statistics
- **Total Initiatives**: 167 (as of 2026-04-02)
- **Status Distribution**:
  - New: 8
  - Discovery: 86
  - Strategy: 9
  - Execution: 3
  - Done: 59
  - Cancelled: 2
- **Missing SLA**: 31 (status ≠ Done, updated > 2 weeks ago)

## Report Features

### Interactive Components
- **Statistics Cards**: Total, Done, Discovery, Missing SLA counts
- **Search**: Filter by key, summary, or description
- **Status Filter**: Click to filter by status
- **Assignee Filter**: Quick filter by owner
- **Label Filter**: Filter by initiative labels
- **Row Expansion**: Click any row to expand full description

### SLA Monitoring
- **Missing SLA Alert**: ⚠️ icon appears when:
  - Status ≠ Done
  - Last update > 2 weeks ago
- Highlighted in orange for visibility

### Export
- **Excel Export**: Click floating button to download CSV
- Filtered results only (respects current filters)

## File Structure
```
cntin730-report/
├── scripts/
│   ├── cntin730_report.py    # Main script (fetch + generate)
│   └── send_report.py        # Email delivery with AES-256 encryption
├── reports/                   # Generated HTML reports
├── logs/                      # Execution logs
│   ├── cron.log              # stdout from launchd
│   └── cron_error.log        # stderr from launchd
├── com.openclaw.cntin730-report.plist  # Launchd定时任务配置
└── README.md                  # This file
```

## Dependencies

### Python Packages
```bash
pip install requests urllib3
```

### Environment Variables (REQUIRED)
```bash
export JIRA_API_TOKEN="your_jira_api_token"
export JIRA_EMAIL="rcheng2@lululemon.com"
export QQ_MAIL_PASSWORD="your_qq_auth_code"
```

### System Dependencies
- **7z**: For AES-256 ZIP encryption
  ```bash
  brew install p7zip
  ```

## Configuration

### Launchd定时任务
File: `~/Library/LaunchAgents/com.openclaw.cntin730-report.plist`

**Key Settings:**
- Run time: Weekdays at 12:00
- Working directory: `~/projects/cntin730-report`
- Environment variables: JIRA_API_TOKEN, QQ_MAIL_PASSWORD

**Install/Reload:**
```bash
launchctl unload ~/Library/LaunchAgents/com.openclaw.cntin730-report.plist
launchctl load ~/Library/LaunchAgents/com.openclaw.cntin730-report.plist
```

### Jira API Token Setup
1. Visit: https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Label: "CNTIN-730 Report"
4. Copy token and set as `JIRA_API_TOKEN`

## Data Logic

### Fetch Logic (cntin730_report.py)
```python
# 1. Query Jira for all child initiatives
jql = "parent = CNTIN-730 AND issuetype = Initiative"

# 2. Paginate through results (100 per page)
# API uses nextPageToken for pagination

# 3. Process each issue:
#    - Extract basic fields (key, summary, status, etc.)
#    - Parse ADF description to plain text
#    - Calculate SLA (updated > 2 weeks and status != Done)
#    - Generate AI summary (What/Why from description)

# 4. Generate interactive HTML with filtering

# 5. Save to reports directory
```

### AI Summary Generation
Extracts from description:
- **What**: Project goal / objective (aims to, goal is, build, create, etc.)
- **Why**: Business value / reason (because, to enable, benefit, etc.)

Uses keyword matching on first 5 sentences.

## Usage

### Manual Execution
```bash
cd ~/projects/cntin730-report

# Full pipeline
./scripts/cntin730_report.py

# Or step by step
export JIRA_API_TOKEN="your_token"
python3 scripts/cntin730_report.py
python3 scripts/send_report.py
```

### Testing
```bash
# Test Jira connectivity
curl -X POST \
  -H "Authorization: Basic $(echo -n 'rcheng2@lululemon.com:$JIRA_API_TOKEN' | base64)" \
  -H "Content-Type: application/json" \
  "https://lululemon.atlassian.net/rest/api/3/search/jql" \
  -d '{"jql": "parent = CNTIN-730", "maxResults": 5}'
```

## Security

### Email Encryption
- **Format**: AES-256 encrypted ZIP
- **Password**: `lulupmo`
- **Command**: `7z a -tzip -p<password> -mem=AES256 <output> <input>`
- **Rationale**: Bypasses Microsoft security scanning that blocks HTML with JS

### Password Distribution
- **Email**: Contains only "密码请通过飞书获取"
- **Feishu**: Password sent separately to recipients
- **Never**: Include password in email body or subject

## Troubleshooting

### Issue: 0 records returned
**Diagnosis:**
```bash
# Check if JIRA_API_TOKEN is set
echo $JIRA_API_TOKEN

# Test API directly
python3 -c "
import requests, base64, os
token = os.getenv('JIRA_API_TOKEN')
auth = base64.b64encode(f'rcheng2@lululemon.com:{token}'.encode()).decode()
resp = requests.post(...)
print(resp.json())
"
```

**Solutions:**
1. Ensure `JIRA_API_TOKEN` is exported in shell or plist
2. Regenerate token if expired
3. Check network connectivity to lululemon.atlassian.net

### Issue: Email not sent
**Check:**
- `QQ_MAIL_PASSWORD` is valid (not expired)
- logs/cron_error.log for error messages
- Network access to smtp.qq.com:465

### Issue: Report shows stale data
**Check:**
- launchd job is loaded: `launchctl list | grep cntin730`
- Last run time in logs/cron.log
- Manually run to refresh: `python3 scripts/cntin730_report.py`

## Version History

### v5.3 (2026-04-02)
- **Fix**: Added `JIRA_API_TOKEN` to launchd plist environment
- **Issue**: Script was returning 0 records due to missing env var
- **Impact**: Now correctly fetches all 167 initiatives

### v5.3 (2026-03-31)
- **Change**: 统一数据范围，移除 status != Cancelled 过滤
- **Reason**: 与 FY26_Intake_Cost 报表数据范围保持一致
- **Impact**: Report now includes Cancelled initiatives

### v5.2 (2026-03-19)
- **Fix**: 修复点击展开功能，完整显示 Description 和 AI Summary
- **Fix**: 优化列宽设置

### v1.0 (2026-03-26)
- **Initial**: First release with encrypted email delivery
- **Features**: 155+ initiatives, SLA monitoring, interactive filters

## Maintenance Notes

### Monthly Checks
- [ ] Verify Jira API token not expired
- [ ] Check QQ email authorization code valid
- [ ] Review logs for errors
- [ ] Confirm initiative count matches Jira

### Quarterly Reviews
- [ ] Update documentation if JQL changes
- [ ] Review and optimize performance
- [ ] Check for new Jira API deprecations
