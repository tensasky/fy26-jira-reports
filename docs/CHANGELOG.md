# CHANGELOG

All notable changes to the CNTIN-730 Initiative Weekly Report project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.2.0] - 2026-03-19

### Added
- **API Pagination Support**: Adapted to Jira API v3 `nextPageToken` pagination mechanism for 100% data integrity
- **Stats Cards**: Added dashboard cards showing Total Initiatives, Done, Discovery, and Missing SLA counts
- **Assignee Filter**: Added filter buttons for top 20 assignees
- **Missing SLA Filter**: Added orange alert button to filter initiatives exceeding 2-week update threshold
- **Row Expansion**: Click any row to expand/collapse full description and AI summary
- **Excel Export**: Floating export button to download filtered data as CSV
- **Cancelled Status Exclusion**: Automatically exclude Cancelled status initiatives from reports

### Changed
- **JQL Query**: Changed from `"Parent Link" = CNTIN-730` to `parent = CNTIN-730` for better compatibility
- **Data Fetcher**: Updated to handle new Jira API pagination with nextPageToken
- **SLA Calculation**: Improved date parsing to handle Jira's ISO 8601 format with timezone

### Fixed
- **Data Completeness**: Fixed issue where only 100 items were fetched due to API pagination change
- **Status Filter**: Now correctly excludes Cancelled initiatives (was including 2 cancelled items)

---

## [1.1.0] - 2026-03-18

### Added
- **Semantic Cache**: MD5 hash-based content caching for AI summaries, reducing API calls by ~60%
- **Async Concurrency**: 30 concurrent workers for AI processing (up from 5 threads)
- **Prompt Pre-cleaning**: ADF/HTML tag removal to reduce token consumption by 20%
- **Feishu File Send**: Support for sending reports via Feishu file upload
- **Dual Channel Distribution**: Email + Feishu simultaneous sending

### Changed
- **AI Processing Time**: Reduced from ~10 minutes to ~5 minutes for 100 initiatives
- **Cache Strategy**: Changed from key-based to content-based hashing for automatic invalidation

### Fixed
- **Token Efficiency**: Reduced OpenAI API token usage through pre-cleaning
- **Memory Usage**: Optimized with StringIO for large HTML generation

---

## [1.0.0] - 2026-03-18

### Added
- **Initial Release**: Complete weekly report generation system
- **Data Fetching**: Full CNTIN-730 initiative data retrieval from Jira
- **AI Summarization**: GPT-4 powered What/Why generation for each initiative
- **Frozen Columns**: First three columns (Key/Summary, Status, Assignee) fixed during horizontal scroll
- **Interactive Filtering**: Status and Label filter buttons with real-time search
- **Email Distribution**: Automated email sending to chinatechpmo@lululemon.com
- **HTML Reports**: Self-contained HTML files with embedded CSS/JS
- **SLA Alerts**: Visual indicators for initiatives not updated in 2+ weeks

---

## Planned Features

### [1.3.0] - TBD
- [ ] Interactive charts (status distribution pie chart, trend line)
- [ ] Historical comparison (week-over-week changes)
- [ ] Initiative detail modal with full information
- [ ] Mobile-responsive design improvements
- [ ] Slack integration

### [2.0.0] - TBD
- [ ] Web dashboard with real-time data
- [ ] User authentication and personalization
- [ ] Initiative editing interface
- [ ] Advanced analytics and reporting
- [ ] Multi-project support

---

## Legend

- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
