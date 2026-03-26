# FY26_PMO Daily Epic Report

## Overview
Daily automated report for FY26 Project Management Office tracking all Epics across 22 Jira projects.

## Schedule
- **Frequency**: Daily (including weekends)
- **Time**: 18:00 (6:00 PM)
- **Recipient**: chinatechpmo@lululemon.com

## Data Source
### Epic Projects (22 total)
CNTEC, CNTOM, CNTDM, CNTMM, CNTD, CNTEST, CNENG, CNINFA, CNCA, CPR, EPCH, CNCRM, CNDIN, SWMP, CDM, CMDM, CNSCM, OF, CNRTPRJ, CSCPVT, CNPMO, CYBERPJT

### CNTIN Initiatives
- All Initiatives with `FY26_INIT` label
- Parent-child relationships tracked

## Report Features
- 4,800+ Epics tracked
- Hierarchy: Initiative → Feature → Epic
- Status distribution by project
- SLA tracking (>7 days yellow, >14 days red)
- Interactive HTML with filtering

## Technical Details
### Data Flow
1. **Fetch Epics** - Query 22 projects via Jira API
2. **Fetch Initiatives** - Get CNTIN FY26_INIT items
3. **Build Hierarchy** - Link Epics to Features to Initiatives
4. **Generate HTML** - Create interactive report
5. **Send Email** - Encrypt and deliver

## File Structure
```
fy26_pmo/
├── scripts/
│   ├── fetch_data.py          # Main data fetching
│   ├── generate_html_v5.py    # HTML report generator (V5.7)
│   ├── send_email.py          # Email with AES-256 encryption
│   └── run.sh                 # Main execution script
├── jira_report.db             # SQLite database
├── reports/                   # Generated HTML reports
└── logs/                      # Execution logs
```

## Database Schema
- `epics` - All epics from 22 projects
- `features` - CNTIN features
- `initiatives` - CNTIN initiatives
- `fetch_log` - Execution tracking

## Configuration
```bash
# Environment variables
export JIRA_API_TOKEN="your_token"
export JIRA_EMAIL="rcheng2@lululemon.com"
export QQ_EMAIL_PASSWORD="your_password"
```

## Installation
```bash
# Install dependencies
pip install requests urllib3

# Setup launchd (macOS)
cp com.openclaw.fy26-pmo-report.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-pmo-report.plist
```

## Manual Execution
```bash
cd fy26_pmo
./run.sh
```

## Version History
- **v5.7** (2026-03-26) - Current stable version
  - Added pagination support for >100 epics
  - Date filter: created >= 2025-11-01
  - Encrypted ZIP delivery
