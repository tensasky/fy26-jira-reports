# FY26 Jira Reports

This repository contains three automated reporting systems for FY26 project management:

## 📊 Reports Overview

| Report | Schedule | Description |
|--------|----------|-------------|
| **CNTIN-730** | Weekdays 12:00 | Weekly FY26 Initiatives Report |
| **FY26_PMO** | Daily 18:00 | Daily Epic Status Report |
| **FY26_Intake_Cost** | Weekdays 10:00 & 15:00 | Intake Cost Tracking Report |

## 📁 Repository Structure

```
├── cntin730-report/        # CNTIN-730 Weekly Report
├── fy26_pmo/               # FY26_PMO Daily Report
├── fy26-intake-cost/       # FY26_Intake_Cost Report
└── docs/                   # Documentation
```

## 🚀 Quick Start

Each report has its own directory with:
- `scripts/` - Python scripts for data fetching and HTML generation
- `reports/` - Generated HTML reports
- `logs/` - Execution logs
- `README.md` - Report-specific documentation

## 📧 Email Delivery

All reports are sent via encrypted ZIP to: **chinatechpmo@lululemon.com**

ZIP Password: `lulupmo`

## 🔧 Requirements

- Python 3.9+
- Jira API Token
- QQ Email credentials (configured in environment)

## 📄 License

Internal Use Only - Lululemon China Tech Team
