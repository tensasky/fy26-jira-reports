# FY26 Jira Reports - Product Requirements Document (PRD)

## 1. Product Overview

### 1.1 Product Vision
An automated, intelligent reporting system that transforms raw Jira data into actionable insights for the China Technology team.

### 1.2 Product Goals
1. **Automation**: Zero-touch report generation and delivery
2. **Intelligence**: Smart filtering and status mapping
3. **Accessibility**: Mobile-responsive with multi-language support
4. **Security**: Enterprise-grade encryption and access control

## 2. Feature Requirements

### 2.1 Core Features

#### 2.1.1 Automated Data Collection
**Description**: Automatically fetch data from Jira API on scheduled intervals

**User Stories**:
- As a PMO member, I want reports to be generated automatically so I don't need to manually create them
- As a stakeholder, I want the data to be fresh (within 1 hour) when I receive the report

**Acceptance Criteria**:
- [x] Data fetched from Jira API before each report generation
- [x] Support for pagination (handle >100 records)
- [x] Error handling with retry logic (3 attempts)
- [x] Data validation before report generation

#### 2.1.2 Multi-Report Generation
**Description**: Support three distinct report types with different schedules

**Report Specifications**:

**CNTIN-730 Report**:
- Scope: Initiatives with FY26_INIT label under CNTIN-730
- Schedule: Weekdays 12:00
- Metrics: Status distribution, SLA tracking, pillar categorization

**FY26_PMO Report**:
- Scope: All epics from 22 projects + CNTIN initiatives
- Schedule: Daily 18:00
- Metrics: Epic status, hierarchy (Initiative→Feature→Epic), project breakdown

**FY26_Intake_Cost Report**:
- Scope: CNTIN-730 child initiatives
- Schedule: Weekdays 10:00 and 15:00
- Metrics: Cost in CNY/USD, SLA, assignee workload

#### 2.1.3 Interactive HTML Reports
**Description**: Generate mobile-friendly interactive HTML reports

**Features**:
- **Expandable Rows**: Click to view full scope and linked issues
- **Status Filtering**: Click status cards to filter table
- **Pillar Filtering**: Multi-select tag-based filtering
- **Search**: Real-time ticket number search
- **Language Toggle**: Switch between Chinese and English

**UI Components**:
```
┌─────────────────────────────────────────────┐
│ Header (Title + Language Toggle)           │
├─────────────────────────────────────────────┤
│ Exchange Rate Setting                       │
├─────────────────────────────────────────────┤
│ Filter Bar (Search + Status + Pillar)      │
├─────────────────────────────────────────────┤
│ Status Cards (Clickable)                    │
├─────────────────────────────────────────────┤
│ Charts (Status + Pillar Distribution)      │
├─────────────────────────────────────────────┤
│ Data Table (Expandable Rows)               │
└─────────────────────────────────────────────┘
```

#### 2.1.4 Cost Calculation
**Description**: Dynamic cost calculation with exchange rate adjustment

**Formula**:
```
USD Cost = InitiativeChildCount × Exchange Rate
```

**Features**:
- Default rate: 0.135 (CNY to USD)
- Real-time adjustment via UI
- Dual currency display (¥CNY / $USD)
- Scientific notation for large numbers

#### 2.1.5 Secure Email Delivery
**Description**: AES-256 encrypted ZIP email delivery

**Security Features**:
- ZIP encryption using 7z with AES-256
- Password: `lulupmo`
- SMTP with TLS
- No sensitive data in email body

### 2.2 Status Mapping

#### 2.2.1 Jira to Report Status Mapping
| Jira Status | Report Category | CSS Class |
|-------------|-----------------|-----------|
| New | 未开始 (Not Started) | status-todo |
| Discovery | 进行中 (In Progress) | status-progress |
| Strategy | 进行中 (In Progress) | status-progress |
| Execution | 进行中 (In Progress) | status-progress |
| Done | 已关闭 (Closed) | status-done |
| Cancelled | 已取消 (Cancelled) | status-cancel |

#### 2.2.2 SLA Calculation
- **Active Statuses**: Days from creation to now
- **Done Status**: Days from creation to status change date
- **Warning**: > 7 days (yellow)
- **Critical**: > 14 days (red)
- **Completed**: Green badge

## 3. Technical Requirements

### 3.1 System Architecture
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Jira API  │───▶│  Python     │───▶│   SQLite    │
│             │    │  Scripts    │    │   Database  │
└─────────────┘    └─────────────┘    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   HTML      │
                    │   Generator │
                    └─────────────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Email     │
                    │   Sender    │
                    └─────────────┘
```

### 3.2 Technology Stack
| Component | Technology |
|-----------|------------|
| Backend | Python 3.9+ |
| Database | SQLite 3 |
| Frontend | Vanilla JavaScript |
| Styling | CSS Grid/Flexbox |
| Charts | SVG (custom) |
| Email | SMTP + 7z AES-256 |
| Scheduling | macOS launchd |

### 3.3 API Requirements
| API | Purpose | Rate Limit |
|-----|---------|------------|
| Jira REST API v3 | Data fetching | 1000 req/5min |
| QQ Email SMTP | Report delivery | 100 emails/day |

### 3.4 Data Model

#### 3.4.1 Intakes Table (FY26_Intake_Cost)
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

## 4. User Interface Requirements

### 4.1 Desktop Layout
- Minimum width: 1200px
- Responsive table with horizontal scroll if needed
- Fixed header during scroll

### 4.2 Mobile Layout
- Minimum width: 375px
- Collapsible filters
- Vertical scrolling for table
- Touch-friendly buttons (min 44px)

### 4.3 Color Scheme
| Element | Color | Hex |
|---------|-------|-----|
| Primary | Blue | #1890ff |
| Success | Green | #52c41a |
| Warning | Orange | #fa8c16 |
| Danger | Red | #ff4d4f |
| Background | Light Gray | #f5f7fa |

## 5. Performance Requirements

### 5.1 Report Generation
- Data fetch: < 3 minutes
- HTML generation: < 30 seconds
- Total: < 5 minutes

### 5.2 UI Performance
- Initial load: < 2 seconds
- Filter response: < 100ms
- Page transitions: < 300ms

## 6. Security Requirements

### 6.1 Data Protection
- API tokens in environment variables
- Database file permissions: 600
- Log file rotation (7 days)

### 6.2 Email Security
- AES-256 ZIP encryption
- TLS 1.2+ for SMTP
- No PII in email subject

## 7. Deployment Requirements

### 7.1 Environment
- macOS 12+ (for launchd)
- Python 3.9+
- 7z command-line tool
- Network access to Jira and SMTP

### 7.2 Configuration Files
```
~/Library/LaunchAgents/
├── com.openclaw.cntin730-report.plist
├── com.openclaw.fy26-pmo-report.plist
└── com.openclaw.fy26-intake-cost.plist
```

## 8. Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Report generation time | < 5 min | 3 min |
| Delivery success rate | > 99% | 100% |
| Data accuracy | 100% | 100% |
| User satisfaction | > 4.5/5 | Pending |

## 9. Future Enhancements

### 9.1 Phase 2 Features
- [ ] Slack integration for alerts
- [ ] Dashboard with historical trends
- [ ] Custom date range filtering
- [ ] Export to Excel/CSV

### 9.2 Phase 3 Features
- [ ] Machine learning for SLA prediction
- [ ] Automated anomaly detection
- [ ] Integration with financial systems
- [ ] Mobile app

## 10. Appendix

### 10.1 Glossary
- **SLA**: Service Level Agreement (days to completion)
- **Pillar**: Project category from Jira labels
- **Intake**: Project/initiative in the system

### 10.2 Reference Documents
- Jira API Documentation: https://developer.atlassian.com/cloud/jira/platform/rest/v3/
- 7z Encryption: https://www.7-zip.org/7z.html
