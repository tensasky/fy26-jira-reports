# Changelog

All notable changes to the FY26 Jira Reports project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.0] - 2026-03-18

### Architecture - Pipeline Orchestration (FY26_INIT)
- **True Pipeline Architecture**: Producer-Consumer pattern with multiprocessing
  - Producer: Parallel fetching (5 workers)
  - Consumer-1: DB writer (immediate persistence)
  - Consumer-2: AI processor (background processing)
  - Consumer-3: HTML renderer (progressive rendering)
  
- **Queue-Based Data Flow**:
  - `result_queue`: Raw fetch results
  - `db_queue`: Persisted data
  - `ai_queue`: AI-processed data
  - Real-time handoff between stages
  
- **Progressive HTML Rendering**:
  - Start generating HTML immediately (no waiting for all projects)
  - Dynamic progress display in generated HTML
  - Component-based rendering
  
- **Monitor Process**:
  - Real-time stats every 5 seconds
  - Track fetch/processing/render progress
  - Performance metrics

### Expected Performance
- Before: Sequential 4 steps (5 min total)
- After: Parallel pipeline with overlap (3-3.5 min total)
- Time reduction: 30-50%

## [1.4.0] - 2026-03-18

### Performance - Database & IO Optimization (FY26_INIT)
- **SQLite WAL Mode**: Write-Ahead Logging for concurrent read/write
  - `PRAGMA journal_mode=WAL`
  - `PRAGMA synchronous=NORMAL`
  - 64MB cache for faster queries
  - Added `updated` column to all tables for delta tracking
  
- **Optimized Database Schema**:
  - Added composite indexes on (project, status, updated)
  - Statistics views: `v_epic_stats`, `v_daily_changes`
  - Foreign key constraints for integrity
  
- **Memory-Optimized HTML Generation**:
  - `io.StringIO` buffer instead of string concatenation
  - Batch data queries (single query for all stats)
  - Pre-defined HTML templates
  - Write to disk only once (90%+ IO reduction)

### Expected Performance
- Before: Multiple DB round trips, frequent disk writes
- After: Single batch query, memory buffer, one disk write
- HTML Generation: ~2-3x faster

## [1.3.0] - 2026-03-18

### Performance - Data Fetch Optimization (FY26_INIT)
- **Parallel Project Fetching**: 4-5 concurrent workers for 22 projects
  - Replaced sequential fetching with ThreadPoolExecutor
  - Real-time progress display per project
  - Individual retry logic for each project
  - ~4x speedup for Step 4 (project Epic fetching)
  
- **Incremental Update Strategy (Delta Updates)**: Only fetch changed issues
  - FetchState class tracks last update time per project
  - JQL optimized: `project=X AND updated >= "YYYY-MM-DD HH:MM"`
  - Full fetch every 7 days for data integrity
  - State persisted to `.fetch_state.json`
  - 90%+ time reduction when few changes

### Expected Performance
- Before: ~5 min for 22 projects (sequential)
- After Parallel: ~1.5 min (5 concurrent workers)
- After Incremental: ~30s (when only 10% changed)

## [1.2.0] - 2026-03-18

### Performance - AI Summary Optimization
- **Semantic Hash Cache**: MD5-based content caching instead of Issue Key
  - Cache key = hash(summary + description)
  - Auto-invalidation on content change
  - Cross-issue content reuse
  - Persistent index with TTL support
- **Asyncio Processing**: Replaced ThreadPoolExecutor with asyncio + aiohttp
  - Concurrency: 5 threads → 30 async workers (6x improvement)
  - Rate limiting: 0.1s between requests
  - Real-time progress tracking
- **Prompt Pre-cleaning**: Strip ADF/HTML before AI processing
  - Recursive ADF text extraction
  - HTML tag removal
  - Content limit reduced: 1000 → 800 chars (20% token reduction)
  
### Expected Performance
- Before: ~10 min for 100 initiatives
- After: ~3-5 min for 100 initiatives (with caching)

## [1.1.0] - 2026-03-18

### Added
- CNTIN-730 Initiative Weekly Report with AI-powered summaries
- AI Summary generation using Claude API with natural language (verb-first, no AI tone)
- Frozen columns (first 3 columns) with horizontal scroll support
- Dual-mode SMTP (SSL/STARTTLS) for improved email reliability
- Comprehensive documentation (BRD, PRD, Design) for both reports

### Changed
- Updated QQ Mail password for SMTP authentication
- Improved .gitignore to exclude generated files and cache

### Fixed
- SMTP connection issues with fallback mechanism
- CSS sticky positioning for frozen columns

## [1.0.0] - 2026-03-18

### Added
- FY26_INIT Epic Daily Report v5.0.0
- SQLite-based data persistence (fy26_data.db)
- Full fetch from 22 Jira projects (CNTEC, CNTOM, CNTDM, etc.)
- Interactive HTML report with status/project/label filtering
- Automated email delivery via QQ Mail SMTP
- macOS LaunchAgent for daily 6PM execution
- SLA Alert highlighting (issues inactive > 2 weeks)
- Data aggregation by project and status
- Hierarchical data model (Initiative → Feature → Epic)

### Technical Features
- Python 3.8+ with SQLite3
- Jira REST API v3 integration
- Concurrent processing (5 workers for AI summaries)
- Caching mechanism for AI summaries (/tmp/ai_summary_cache)
- Error handling with exponential backoff
- HTML5/CSS3/JS frontend with responsive design

### Documentation
- Business Requirements Document (BRD)
- Product Requirements Document (PRD)
- Detailed Design Document
- README with setup instructions

## [0.9.0] - 2026-03-12

### Added
- FY26_INIT v5.0.0 SQLite architecture
- Migration from JSON file merging to SQLite database
- Database schema for epics, features, initiatives
- Fetch logging table for debugging

### Changed
- Data persistence layer from JSON to SQLite
- Report generation now reads from database

### Fixed
- Data loss issues in v4.x JSON merging
- Missing Epic data from multiple projects

## [0.8.0] - 2026-03-11

### Added
- FY26_INIT v4.0-v4.7 incremental fixes
- JSON file merging improvements
- Cross-project Epic linking

### Fixed
- Various JSON merge bugs
- Data completeness issues

## [0.7.0] - 2026-03-11

### Added
- FY26_INIT v3.0 correct data structure
- Proper Initiative → Feature → Epic hierarchy
- 22-project scanning logic

### Changed
- Data structure from Epic-centric to Initiative-centric

## [0.6.0] - 2026-03-11

### Added
- FY26_INIT v2.0 reverse scanning attempt

## [0.5.0] - 2026-03-10

### Added
- FY26_INIT v1.0 initial version
- Basic Epic data fetching
- HTML report generation
- Email sending capability

---

## Release Notes

### Version 1.1.0 Highlights

**CNTIN-730 Initiative Weekly Report**
- 🤖 AI-powered What/Why summaries for 100+ Initiatives
- 📊 Frozen columns design for better data navigation
- 🔄 Concurrent processing (5x speed improvement)
- 📧 Dual-mode SMTP for reliable email delivery
- 📚 Complete documentation (BRD/PRD/Design)

**FY26_INIT Epic Daily Report (v5.0.0)**
- 🗄️ SQLite persistence for data integrity
- 📈 Daily automated execution at 6PM
- 🎯 SLA Alert for stale issues
- 🔍 Interactive filtering and search

### Migration Notes

**From v0.x to v1.0+**
- Database migration: JSON files → SQLite
- Configuration: Added environment variables
- Execution: LaunchAgent for automation

**From v1.0.0 to v1.1.0**
- New: AI API configuration required
- New: QQ Mail password updated
- No breaking changes to existing reports

---

## Documentation Index

- [FY26_INIT BRD](docs/brd/FY26_INIT_Epic_Report_BRD.md)
- [FY26_INIT PRD](docs/prd/FY26_INIT_Epic_Report_PRD.md)
- [FY26_INIT Design](docs/design/FY26_INIT_Epic_Report_Design.md)
- [CNTIN730 BRD](docs/brd/CNTIN730_Initiative_Report_BRD.md)
- [CNTIN730 PRD](docs/prd/CNTIN730_Initiative_Report_PRD.md)
- [CNTIN730 Design](docs/design/CNTIN730_Initiative_Report_Design.md)
