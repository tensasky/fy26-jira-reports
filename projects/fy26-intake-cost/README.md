# FY26_Intake_Cost Report

## Overview
Interactive cost tracking report for CNTIN-730 initiatives with real-time exchange rate adjustment and multi-language support.

## Schedule
- **Frequency**: Weekdays (Mon-Fri)
- **Times**: 10:00 AM and 15:00 (3:00 PM)
- **Recipient**: chinatechpmo@lululemon.com

## Key Features

### 💱 Dynamic Exchange Rate
- Adjustable CNY → USD exchange rate (default: 0.135)
- Real-time cost recalculation
- Dual currency display (¥CNY / $USD)

### 🌐 Multi-Language Support
- Chinese (中文)
- English
- One-click language switching

### 📊 Interactive Components
- **Status Cards**: Click to filter by status
- **Charts**: Status donut chart + Pillar bar chart (clickable)
- **Search**: Filter by ticket number
- **Pillar Filter**: Multi-select tag filtering

### 📋 Smart Table
| Column | Source | Notes |
|--------|--------|-------|
| Intake | Ticket + Summary + Date | Clickable Jira link |
| Pillar | Labels | Multi-select filter |
| Type | Components | TBD if empty |
| SLA | Days since creation | Yellow >7d, Red >14d |
| Status | Status | Color-coded badges |
| Assignee | Assignee | - |
| Cost | InitiativeChildCount × Rate | CNY & USD |
| Approver | Affects Versions | - |
| Scope | Description | Expandable |

### 🔍 Expandable Rows
- Click any row to expand
- Full scope description
- Follow up links (linked Jira tickets)

## Data Mapping
```
Intake    = Ticket + Summary + Create Date
Type      = Components (default: TBD)
SLA       = Days from Create Date
Status    = Status
Assignee  = Assignee
Cost      = InitiativeChildCount × Exchange Rate
Approver  = Affects Versions
Scope     = Description
Follow Up = Linked Issues
```

## Technical Stack
- **Backend**: Python 3 + SQLite
- **Frontend**: Vanilla JavaScript + CSS Grid
- **Charts**: SVG (custom implementation)
- **i18n**: JSON-based translation

## File Structure
```
fy26-intake-cost/
├── scripts/
│   ├── fetch_intake_cost.py   # Jira data fetching
│   ├── generate_html.py       # Interactive HTML generator
│   └── send_email.py          # Email delivery
├── reports/                   # Generated reports
├── logs/                      # Execution logs
└── intake_cost.db            # SQLite database
```

## Database Schema
```sql
CREATE TABLE intakes (
    key TEXT PRIMARY KEY,
    summary TEXT,
    description TEXT,
    status TEXT,
    status_category TEXT,
    assignee TEXT,
    reporter TEXT,
    created TEXT,
    updated TEXT,
    labels TEXT,              -- Pillars
    components TEXT,          -- Type
    affects_versions TEXT,    -- Approver
    fix_versions TEXT,
    initiative_child_count INTEGER,  -- Cost base
    linked_issues TEXT,       -- Follow up
    issue_links TEXT
);
```

## Configuration
```bash
# Exchange rate (CNY → USD)
export EXCHANGE_RATE=0.135

# Jira credentials
export JIRA_API_TOKEN="your_token"
export QQ_EMAIL_PASSWORD="your_password"
```

## Launchd Setup
```bash
# Install定时任务
cp com.openclaw.fy26-intake-cost.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-intake-cost.plist

# 检查状态
launchctl list | grep fy26-intake-cost
```

## Manual Execution
```bash
cd fy26-intake-cost

# Full pipeline
./run.sh

# Or individual steps
python3 scripts/fetch_intake_cost.py
python3 scripts/generate_html.py
```

## Security
- AES-256 encrypted ZIP attachment
- Password: `lulupmo`
- No sensitive data in HTML comments

## Version History
- **v1.0** (2026-03-26) - Initial release
  - Interactive HTML with expandable rows
  - Real-time exchange rate
  - Chinese/English switching
  - Pillar-based filtering
