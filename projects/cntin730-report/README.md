# CNTIN-730 FY26 Initiatives Weekly Report

## Overview
Weekly automated report for CNTIN-730 FY26 Initiatives tracking.

## Schedule
- **Frequency**: Weekdays (Mon-Fri)
- **Time**: 12:00 (Noon)
- **Recipient**: chinatechpmo@lululemon.com

## Data Source
- **Jira Project**: CNTIN
- **Filter**: Initiatives with `FY26_INIT` label
- **Parent**: CNTIN-730 (Roadmap container)

## Report Features
- 155+ Initiatives tracking
- Status distribution
- SLA monitoring
- Pillar categorization
- Linked issues tracking

## File Structure
```
cntin730-report/
├── scripts/
│   ├── fetch_data.py         # Jira data fetching
│   ├── generate_html.py      # HTML report generation
│   └── send_report.py        # Email delivery with AES-256 encryption
├── reports/                   # Generated reports
├── logs/                      # Execution logs
└── config/                    # Configuration files
```

## Configuration
Environment variables required:
- `JIRA_API_TOKEN` - Jira authentication
- `QQ_EMAIL_PASSWORD` - Email sender password

## Security
- Reports sent as AES-256 encrypted ZIP files
- Password: `lulupmo`
- ZIP created using 7z with `-mem=AES256` option

## Version History
- **v1.0** (2026-03-26) - Initial release with encrypted email delivery
