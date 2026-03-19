# FY26_INIT Epic Daily Report System - PRD

## 1. Overview

### 1.1 Product Name
FY26_INIT Epic Daily Report System

### 1.2 Purpose
An automated system to fetch Jira data from 22 projects, generate interactive HTML reports, and send daily emails to stakeholders.

### 1.3 Target Users
- PMO Team (chinatechpmo@lululemon.com)
- Project Managers
- Engineering Leads

---

## 2. System Architecture

### 2.1 Data Flow
```
Jira API → SQLite DB → JSON Report → HTML Report → Email
     ↑                                              ↓
   Daily Cron                                  Recipients
```

### 2.2 Core Components

| Component | File | Purpose |
|-----------|------|---------|
| Data Fetcher | `fetch_fy26_v5.py` | Fetch Epic/Feature/Initiative from Jira |
| Database | `fy26_data.db` | SQLite persistence layer |
| Report Generator | `generate_fy26_report_v5.py` | Generate structured JSON report |
| HTML Generator | `generate_fy26_html_v5.py` | Create interactive HTML dashboard |
| Email Sender | `send_fy26_report_v5.py` | Send reports via QQ Mail |
| Scheduler | `com.openclaw.fy26-daily-report.plist` | macOS LaunchAgent for automation |

---

## 3. Data Model

### 3.1 Hierarchy
```
CNTIN Initiative (FY26_INIT label)
    └── CNTIN Feature (parent = Initiative)
            └── Project Epic (parent = Feature, 22 projects)
```

### 3.2 Database Schema

**Table: epics**
| Field | Type | Description |
|-------|------|-------------|
| key | TEXT | Epic key (e.g., CPR-123) |
| project | TEXT | Project code |
| summary | TEXT | Epic title |
| status | TEXT | Current status |
| assignee | TEXT | Assigned person |
| parent_key | TEXT | Parent Feature key |
| created | TEXT | Creation date |
| labels | TEXT | JSON array of labels |

**Table: features**
| Field | Type | Description |
|-------|------|-------------|
| key | TEXT | Feature key |
| summary | TEXT | Feature title |
| status | TEXT | Current status |
| assignee | TEXT | Assigned person |
| parent_key | TEXT | Parent Initiative key |
| labels | TEXT | JSON array of labels |

**Table: initiatives**
| Field | Type | Description |
|-------|------|-------------|
| key | TEXT | Initiative key |
| summary | TEXT | Initiative title |
| status | TEXT | Current status |
| assignee | TEXT | Assigned person |
| labels | TEXT | JSON array of labels |

---

## 4. Features

### 4.1 Interactive HTML Dashboard

#### Filter Options
1. **Show All** - Display all Initiatives
2. **With Epics** - Only show Initiatives that have Epics
3. **Without Epics** - Show Initiatives with no Epics
4. **No Parent** - Show Epics without parent Feature
5. **Date Range** - Filter by Epic creation date

#### Display Components
- **Summary Bar** - Statistics overview
- **Initiative Cards** - Collapsible sections
- **Feature Sections** - Nested under Initiatives
- **Epic Cards** - Detailed Epic information
- **Pagination** - 10 items per page

### 4.2 Data Visualization
- Color-coded status badges
- Warning indicators for orphan data
- Progress indicators
- Responsive layout

---

## 5. Technical Requirements

### 5.1 Dependencies
```
Python 3.8+
- requests
- sqlite3 (built-in)
- json (built-in)
- pathlib (built-in)
```

### 5.2 Configuration

**Jira Config** (`~/.openclaw/workspace/.jira-config`):
```bash
export JIRA_URL="https://lululemon.atlassian.net"
export JIRA_AUTH="base64_encoded_credentials"
```

**Email Config** (environment variables):
```bash
export QQ_MAIL_PASSWORD="your_qq_mail_password"
```

### 5.3 Cron Schedule
- **Frequency**: Daily at 18:00
- **Timezone**: Asia/Shanghai (GMT+8)

---

## 6. Installation & Setup

### 6.1 Quick Start
```bash
# 1. Extract package
tar -xzf fy26-report-package.tar.gz
cd fy26-report-package

# 2. Run setup
./setup.sh

# 3. Configure Jira credentials
nano config/jira-config

# 4. Test run
./run.sh
```

### 6.2 Directory Structure
```
fy26-report-package/
├── scripts/
│   ├── fetch_fy26_v5.py
│   ├── generate_fy26_report_v5.py
│   ├── generate_fy26_html_v5.py
│   └── send_fy26_report_v5.py
├── config/
│   ├── jira-config.template
│   └── schema.sql
├── data/
│   └── fy26_data.db
├── output/
│   ├── reports/
│   └── logs/
├── setup.sh
├── run.sh
└── README.md
```

---

## 7. API Integration

### 7.1 Jira REST API

**Endpoint**: `GET /rest/api/3/search`

**Query Parameters**:
- `jql`: JQL query string
- `fields`: Required fields
- `maxResults`: Page size (100)

**Sample JQL**:
```
project = CPR AND issuetype = Epic
project = CNTIN AND issuetype = Feature AND labels = FY26_INIT
```

### 7.2 Rate Limiting
- Respect Jira API rate limits
- Implement exponential backoff
- Cache responses to minimize API calls

---

## 8. Security

### 8.1 Credential Management
- Store credentials in environment variables
- Never commit credentials to version control
- Use base64 encoding for Jira auth

### 8.2 Data Protection
- Local SQLite database
- No external data transmission except email
- Email sent via TLS (port 587)

---

## 9. Monitoring & Logging

### 9.1 Log Files
- **Main Log**: `logs/fy26_daily_report.log`
- **Error Log**: `logs/error.log`
- **Fetch Log**: Database table `fetch_log`

### 9.2 Health Checks
```bash
# Check database
sqlite3 data/fy26_data.db "SELECT COUNT(*) FROM epics"

# Check last fetch
sqlite3 data/fy26_data.db "SELECT * FROM fetch_log ORDER BY fetched_at DESC LIMIT 1"

# View logs
tail -f logs/fy26_daily_report.log
```

---

## 10. Troubleshooting

### 10.1 Common Issues

**Issue**: No data fetched
- Check Jira credentials
- Verify network connectivity
- Check JQL syntax

**Issue**: Email not sent
- Verify QQ Mail password
- Check SMTP settings
- Review email logs

**Issue**: Missing Epics
- Check parent_key relationships
- Verify project list
- Review fetch_log for errors

### 10.2 Debug Mode
```bash
# Run with debug output
DEBUG=1 ./run.sh

# Manual fetch
python3 scripts/fetch_fy26_v5.py --verbose
```

---

## 11. Future Enhancements

- [ ] Slack/Teams integration
- [ ] Real-time dashboard
- [ ] Historical trend analysis
- [ ] Custom JQL support
- [ ] Multi-language support

---

## 12. Changelog

### v5.0 (2026-03-12)
- Migrated from JSON to SQLite
- Added interactive HTML dashboard
- Added date range filtering
- Added "No Parent" filter
- Fixed data loss issues

### v4.x (2026-03-11)
- Multiple bug fixes for JSON merging
- Data loss issues (deprecated)

### v3.0 (2026-03-11)
- Correct data structure
- Proper scanning logic

---

**Document Version**: 1.0  
**Last Updated**: 2026-03-12  
**Author**: Tensasky
