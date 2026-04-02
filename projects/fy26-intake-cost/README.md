# FY26_Intake_Cost Report

## Overview
Interactive cost tracking report for CNTIN-730 initiatives with real-time exchange rate adjustment and multi-language support.

## Schedule
- **Frequency**: Weekdays (Mon-Fri)
- **Times**: 10:00 AM and 15:00 (3:00 PM)
- **Recipient**: chinatechpmo@lululemon.com
- **CC**: rcheng2@lululemon.com, jjang2@lululemon.com

## Data Source

### Jira Configuration
- **Project**: CNTIN
- **Parent**: CNTIN-730 (Goal type, hierarchy level 4)
- **Issue Type**: Initiative
- **JQL Query**: `parent = CNTIN-730 AND issuetype = Initiative ORDER BY key ASC`

### Data Fields Mapping
| Report Column | Jira Field | Custom Field | Notes |
|---------------|------------|--------------|-------|
| Intake | `key` + `summary` | - | Clickable Jira link |
| Create Date | `created` | - | ISO 8601 format |
| Pillar | `labels` | - | Multi-select filter |
| Type | `components` | - | Default: TBD |
| SLA | `created` | Calculated | Days since creation |
| Status | `status.name` | - | Color-coded badges |
| Assignee | `assignee.displayName` | - | Owner |
| Cost (¥/$) | `customfield_16143` | InitiativeChildCount | × exchange rate |
| Approver | `versions` | Affects Versions | - |
| Scope | `description` | ADF format | Expandable full text |
| Follow Up | `issuelinks` | Linked Issues | Related tickets |

### Current Statistics
- **Total Initiatives**: 167 (as of 2026-04-02)
- **Status Categories**:
  - In Progress: 89 (Discovery, Strategy, Execution)
  - Done: 61
  - To Do: 17 (New)
- **Linked Issues**: 116 initiatives have related tickets

## Key Features

### 💱 Dynamic Exchange Rate
- **Default**: 0.135 (CNY → USD)
- **Adjustable**: Real-time slider in report
- **Recalculation**: Instant cost update across all rows
- **Display**: Dual currency (¥CNY / $USD)

### 🌐 Multi-Language Support
- **中文**: Full Chinese interface
- **English**: Complete English translation
- **Toggle**: One-click language switching
- **Persistence**: Saves preference in session

### 📊 Interactive Components

#### Status Distribution Chart (Donut)
- Visual breakdown by status category
- **Clickable**: Filter table by clicking chart segments
- **Percentages**: Show relative distribution
- **Colors**: Status-specific (Done=green, In Progress=blue, etc.)

#### Pillar Distribution Chart (Bar)
- Horizontal bar chart by Pillar (labels)
- **Multi-select**: Filter by multiple pillars
- **Counts**: Shows initiative count per pillar

#### Status Filter Cards
| Card | Jira Statuses | Color |
|------|---------------|-------|
| 未开始 (Not Started) | New | Gray |
| 进行中 (In Progress) | Discovery, Strategy, Execution | Blue |
| 已关闭 (Closed) | Done | Green |
| 已取消 (Cancelled) | Cancelled | Red |

### 🔍 Smart Table Features
- **Expandable Rows**: Click to expand full scope description
- **Search**: Filter by ticket number, summary, or scope
- **Sorting**: Click column headers (where implemented)
- **Responsive**: Adapts to screen width

### 📋 SLA Monitoring
- **Calculation**: Days since creation date
- **Color Coding**:
  - 🟢 ≤ 7 days: Normal
  - 🟡 8-14 days: Warning
  - 🔴 > 14 days: Alert

## Technical Architecture

### Data Flow
```
Jira API (REST v3)
    ↓
fetch_intake_cost.py
    ↓ (Parse ADF, calculate SLA, extract fields)
SQLite (intake_cost.db)
    ↓
generate_html.py
    ↓ (Generate interactive HTML with embedded JS/CSS)
fy26_intake_cost_report_latest.html
    ↓ (run.sh pipeline)
AES-256 Encrypted ZIP
    ↓
Email to recipients
```

### Database Schema
```sql
CREATE TABLE intakes (
    key TEXT PRIMARY KEY,           -- CNTIN-XXX ticket key
    summary TEXT,                   -- Initiative title
    description TEXT,               -- Plain text (parsed from ADF)
    status TEXT,                    -- Current status name
    status_category TEXT,           -- Status category (To Do, In Progress, Done)
    assignee TEXT,                  -- Owner display name
    reporter TEXT,                  -- Creator display name
    created TEXT,                   -- ISO 8601 timestamp
    updated TEXT,                   -- ISO 8601 timestamp
    labels TEXT,                    -- JSON array of labels (Pillars)
    components TEXT,                -- Comma-separated component names (Type)
    affects_versions TEXT,          -- Comma-separated versions (Approver)
    fix_versions TEXT,              -- Comma-separated fix versions
    initiative_child_count INTEGER, -- Cost base value
    linked_issues TEXT,             -- JSON array of linked tickets
    issue_links TEXT,               -- Raw issue links JSON
    intake_type TEXT,               -- Custom field (if used)
    cost_rmb REAL,                  -- Calculated cost in RMB
    approver TEXT,                  -- Approver name
    scope TEXT,                     -- Scope description
    follow_up TEXT                  -- Follow up notes
);

CREATE TABLE fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    count INTEGER,                  -- Number of records fetched
    status TEXT,                    -- success/error
    message TEXT                    -- Details or error message
);
```

### Frontend Stack
- **HTML5**: Semantic structure
- **CSS3**: Grid layout, custom properties, animations
- **Vanilla JavaScript**: No external dependencies
- **SVG**: Custom chart implementation
- **i18n**: JSON-based translation system

## File Structure
```
fy26-intake-cost/
├── scripts/
│   ├── fetch_intake_cost.py      # Jira data fetching
│   ├── generate_html.py          # Interactive HTML generator
│   └── run.sh                    # Full pipeline script
├── reports/                       # Generated reports
│   └── fy26_intake_cost_report_latest.html
├── logs/                          # Execution logs
│   ├── launchd.log               # stdout
│   └── launchd_error.log         # stderr
├── intake_cost.db                # SQLite database
├── com.openclaw.fy26-intake-cost.plist  # Launchd config
└── README.md                     # This file
```

## Dependencies

### System Requirements
- **macOS** 10.15+ (for launchd)
- **Python** 3.9+
- **7z** (p7zip) for ZIP encryption

### Python Packages
```bash
pip install requests urllib3
```

### Environment Variables (REQUIRED)
```bash
# Jira API
export JIRA_API_TOKEN="ATATT3xFfGF0..."
export JIRA_EMAIL="rcheng2@lululemon.com"

# Email
export QQ_MAIL_PASSWORD="ftbabipdlxliceai"
```

## Configuration

### Launchd定时任务
File: `~/Library/LaunchAgents/com.openclaw.fy26-intake-cost.plist`

**Schedule:**
- 10:00 AM - Morning report
- 15:00 (3:00 PM) - Afternoon report
- Weekdays only (Mon-Fri)

**Environment Variables in plist:**
```xml
<key>JIRA_API_TOKEN</key>
<string>your_token_here</string>
<key>QQ_MAIL_PASSWORD</key>
<string>your_password_here</string>
```

**Reload:**
```bash
launchctl unload ~/Library/LaunchAgents/com.openclaw.fy26-intake-cost.plist
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-intake-cost.plist
```

### Exchange Rate Configuration
Default rate set in JavaScript within generated HTML:
```javascript
const EXCHANGE_RATE = 0.135; // CNY to USD
```

Users can adjust this in the report UI, but it doesn't persist between reports.

## Usage

### Manual Execution

#### Full Pipeline
```bash
cd fy26-intake-cost
./run.sh
```

#### Individual Steps
```bash
# 1. Set environment
export JIRA_API_TOKEN="your_token"
export QQ_MAIL_PASSWORD="your_password"

# 2. Fetch data
python3 scripts/fetch_intake_cost.py

# 3. Generate HTML
python3 scripts/generate_html.py

# 4. Send email (via run.sh or send_email.py)
```

### Database Queries

```bash
# Total count
sqlite3 intake_cost.db "SELECT COUNT(*) FROM intakes"

# By status
sqlite3 intake_cost.db "SELECT status, COUNT(*) FROM intakes GROUP BY status"

# Recent fetch logs
sqlite3 intake_cost.db "SELECT * FROM fetch_log ORDER BY fetched_at DESC LIMIT 5"

# Export to CSV
sqlite3 intake_cost.db -csv "SELECT key, summary, status, assignee FROM intakes" > export.csv
```

## Security

### Email Encryption
- **Algorithm**: AES-256
- **Format**: ZIP with password protection
- **Password**: `lulupmo`
- **Tool**: 7z (`7z a -tzip -p<pass> -mem=AES256`)

**Why encrypt?**
Microsoft security systems flag HTML files with JavaScript as potential phishing/malware. Encryption bypasses content scanning.

### Password Handling
- **Email body**: Never contains password
- **Message**: "密码请通过飞书获取"
- **Distribution**: Separate Feishu message to recipients

### API Token Security
- **Storage**: Environment variables only
- **Git**: Never committed to repository
- **Local**: `.jira-config` file (not tracked)
- **plist**: Local machine only

## Troubleshooting

### Issue: 0 records fetched

**Symptoms:**
```
📋 抓取 CNTIN-730 Intakes...
  ✓ 抓到 0 个 Intakes
```

**Diagnosis:**
1. Check environment variable:
   ```bash
   echo $JIRA_API_TOKEN
   ```

2. Test API connection:
   ```bash
   source ~/.openclaw/workspace/.jira-config
   curl -X POST \
     -H "Authorization: Basic $(echo -n "$JIRA_USER_EMAIL:$JIRA_API_TOKEN" | base64)" \
     -H "Content-Type: application/json" \
     https://lululemon.atlassian.net/rest/api/3/search/jql \
     -d '{"jql": "parent = CNTIN-730", "maxResults": 5}'
   ```

3. Check launchd environment:
   ```bash
   cat ~/Library/LaunchAgents/com.openclaw.fy26-intake-cost.plist | grep -A1 JIRA_API_TOKEN
   ```

**Solutions:**
- Ensure `JIRA_API_TOKEN` is set in shell OR in plist EnvironmentVariables
- Regenerate token if expired
- Check for network/proxy issues

### Issue: Email not sending

**Check:**
- `logs/launchd_error.log` for Python tracebacks
- QQ email authorization code not expired
- SMTP connectivity: `telnet smtp.qq.com 465`

### Issue: HTML charts not rendering

**Check:**
- Browser console for JavaScript errors
- Verify all initiatives have required fields
- Check for special characters in descriptions

### Issue: Costs showing as 0

**Check:**
- `initiative_child_count` field populated in Jira
- Custom field ID hasn't changed (`customfield_16143`)
- Verify exchange rate not set to 0

## Performance Notes

### API Pagination
- **Page size**: 100 records per request
- **Pagination**: Uses `nextPageToken` (Jira REST v3)
- **Rate limiting**: Built-in 1-second delay between pages

### Database Optimization
- **Index**: `key` is PRIMARY KEY
- **Vacuum**: SQLite auto-vacuum enabled
- **Cache**: Previous reports retained in `reports/` directory

## Version History

### v1.1 (2026-04-02)
- **Fix**: Added `JIRA_API_TOKEN` to launchd plist
- **Issue**: Script was returning 0 records
- **Fix verified**: Now fetches 167 initiatives correctly

### v1.0 (2026-03-26)
- **Initial release**
- Features:
  - Interactive HTML with expandable rows
  - Real-time exchange rate adjustment
  - Chinese/English language switching
  - Status and Pillar filtering
  - AES-256 encrypted email delivery

## Maintenance

### Daily Checks
- Review `logs/launchd_error.log` for errors
- Confirm report sent at scheduled times

### Weekly Checks
- Verify initiative count matches Jira
- Check for new custom fields in Jira
- Review SLA alerts

### Monthly Tasks
- Rotate Jira API token
- Verify QQ email authorization code
- Archive old reports
- Update documentation if fields change

## Contact

**Issues**: Contact Roberto Cheng (rcheng2@lululemon.com)
**Jira**: https://lululemon.atlassian.net/browse/CNTIN-730
