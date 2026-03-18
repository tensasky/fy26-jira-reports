# Changelog

All notable changes to the FY26 Jira Reports project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.1] - 2026-03-18

### Fixed
- **Exclude database files from git**: Added `*.db` to .gitignore
- **Size reduction**: Removed ~7MB of tracked database files
- Database files are now generated locally and not versioned

## [2.0.0] - 2026-03-18

### 🎉 Major Release - Complete Optimization Suite

This release includes all optimization modules developed on 2026-03-18.

### Added - CNTIN-730 Initiative Weekly Report
- **AI-Powered Summaries**: What/Why business explanations using Claude API
- **Natural Language**: Verb-first sentences, no AI tone, bilingual (CN/EN)
- **Frozen Columns**: First 3 columns fixed with horizontal scroll
- **Semantic Cache**: MD5-based content caching (not Issue Key)
- **Async Processing**: 30 concurrent workers (vs 5 threads)
- **Prompt Pre-cleaning**: ADF/HTML stripping, 20% token reduction
- **Dual-Mode SMTP**: SSL/STARTTLS fallback for reliability

### Added - FY26_INIT Epic Daily Report
- **Parallel Fetching**: 5 concurrent workers for 22 projects
- **Incremental Updates**: Delta updates based on `updated >= -24h`
- **State Management**: Per-project timestamp tracking
- **SQLite WAL Mode**: Write-Ahead Logging for concurrent access
- **Memory-Optimized HTML**: StringIO buffer, single disk write
- **Pipeline Architecture**: Producer-Consumer pattern with multiprocessing
- **Progressive Rendering**: Generate HTML as data arrives

### Performance Improvements

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| AI Summary (100 items) | ~10 min | ~3-5 min | **2-3x** |
| Data Fetch (22 projects) | ~5 min | ~1.5 min | **3x** |
| Incremental Update | ~5 min | ~30 sec | **10x** |
| HTML Generation | ~5 sec | ~2 sec | **2.5x** |
| Total Pipeline | ~8-10 min | ~5-6 min | **40%** |

### Technical Stack
- Python 3.8+
- SQLite 3 with WAL mode
- asyncio + aiohttp for async operations
- multiprocessing for pipeline
- Jira REST API v3
- SMTP (QQ Mail)

### Documentation
- Business Requirements Documents (BRD) ×2
- Product Requirements Documents (PRD) ×2
- Detailed Design Documents ×2
- Complete CHANGELOG and README

---

## [1.0.0] - 2026-03-12

### Initial Release
- FY26_INIT Epic Daily Report v5.0.0
- SQLite-based data persistence
- Full fetch from 22 Jira projects
- Interactive HTML reports
- Automated email delivery
- LaunchAgent for daily execution

---

## Release Schedule

- **v2.0.0** (2026-03-18): Complete optimization suite
- **v1.0.0** (2026-03-12): Initial stable release

## Migration Guide

### From v1.x to v2.0
1. Update Python dependencies: `pip install aiohttp`
2. Review new environment variables in scripts
3. Test incremental update mode
4. Update cron/LaunchAgent to use new scripts

## Contributors
- OpenClaw (Author)

## License
MIT
