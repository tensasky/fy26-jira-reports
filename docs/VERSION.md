# Version Information

## Current Version

**Version**: 1.2.0  
**Codename**: "Complete Edition"  
**Release Date**: 2026-03-19  
**Status**: Production Ready

---

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 1.2.0 | 2026-03-19 | Stable | API pagination fix, stats cards, assignee filter, row expansion, Excel export |
| 1.1.0 | 2026-03-18 | Stable | Semantic cache, async concurrency, Feishu support |
| 1.0.0 | 2026-03-18 | Stable | Initial release |

---

## Version 1.2.0 Details

### Key Metrics
- **Data Completeness**: 100% (143/143 initiatives)
- **AI Success Rate**: ~98%
- **Average Generation Time**: ~5 minutes
- **Cache Hit Rate**: ~60%
- **Scheduled Execution**: Weekdays at 12:00 CST

### Components

| Component | Version | Path |
|-----------|---------|------|
| Main Script | 1.2.0 | `scripts/cntin730_weekly_report.py` |
| Report Generator | 1.2.0 | `scripts/cntin730_report_v5.2_full.py` |
| BRD | 1.2.0 | `docs/brd/CNTIN730_Initiative_Report_BRD.md` |
| PRD | 1.2.0 | `docs/prd/CNTIN730_Initiative_Report_PRD.md` |
| SDD | 1.2.0 | `docs/sdd/CNTIN730_Initiative_Report_SDD.md` |

### Dependencies

- Python 3.9+
- requests 2.31+
- aiohttp 3.9+
- Standard library: asyncio, hashlib, sqlite3, smtplib

### API Versions

- Jira REST API: v3
- OpenAI API: v1
- Feishu API: v3

---

## Upgrade Notes

### From 1.1.0 to 1.2.0
1. No breaking changes
2. Update LaunchAgent configuration if needed
3. Clear cache directory for fresh start (optional)

### From 1.0.0 to 1.2.0
1. Update all scripts
2. Install new dependencies: `pip install aiohttp`
3. Reconfigure LaunchAgent for weekday-only execution
4. Update environment variables

---

## Support

For issues or questions, contact: rcheng2@lululemon.com
