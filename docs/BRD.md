# FY26 Jira Reports - Business Requirements Document (BRD)

## 1. Executive Summary

### 1.1 Project Overview
The FY26 Jira Reports system is an automated reporting solution designed to provide real-time visibility into project progress, costs, and resource allocation across the China Technology team's initiatives.

### 1.2 Business Objectives
- **Transparency**: Provide stakeholders with up-to-date project status
- **Cost Control**: Track and monitor project costs in both CNY and USD
- **Resource Management**: Monitor team workload and assignment distribution
- **Decision Support**: Enable data-driven decision making for project prioritization

### 1.3 Key Stakeholders
| Role | Name/Team | Responsibility |
|------|-----------|----------------|
| Product Owner | China Tech PMO | Report requirements and review |
| Engineering Lead | China Tech Team | Technical implementation |
| End Users | chinatechpmo@lululemon.com | Daily report consumption |
| System Admin | DevOps Team | Infrastructure and maintenance |

## 2. Business Requirements

### 2.1 Report Types

#### 2.1.1 CNTIN-730 FY26 Initiatives Weekly Report
- **Frequency**: Weekdays (Monday-Friday) at 12:00
- **Audience**: PMO and Leadership
- **Content**: High-level initiative status and progress

**Business Need**: Leadership requires daily visibility into the 150+ FY26 initiatives to track overall program health and identify blockers.

#### 2.1.2 FY26_PMO Daily Epic Report
- **Frequency**: Daily at 18:00
- **Audience**: Engineering teams and PMO
- **Content**: Epic-level progress across 22 projects

**Business Need**: Engineering teams need daily updates on epic status to coordinate dependencies and track delivery progress.

#### 2.1.3 FY26_Intake_Cost Report
- **Frequency**: Weekdays at 10:00 and 15:00
- **Audience**: Finance and PMO
- **Content**: Cost tracking with exchange rate adjustments

**Business Need**: Finance team requires frequent cost updates with USD conversion for budget tracking and forecasting.

### 2.2 Functional Requirements

#### 2.2.1 Data Requirements
| Requirement | Priority | Description |
|-------------|----------|-------------|
| R1 | High | Real-time data from Jira API |
| R2 | High | Historical data retention (1 year) |
| R3 | Medium | Data encryption at rest |
| R4 | High | Automated data refresh before each report |

#### 2.2.2 Reporting Requirements
| Requirement | Priority | Description |
|-------------|----------|-------------|
| R5 | High | AES-256 encrypted email delivery |
| R6 | High | Mobile-friendly HTML format |
| R7 | Medium | Interactive filtering capabilities |
| R8 | Medium | Multi-language support (CN/EN) |
| R9 | High | Exchange rate conversion (CNY to USD) |

### 2.3 Non-Functional Requirements

#### 2.3.1 Performance
- Report generation: < 5 minutes
- Email delivery: < 2 minutes
- System availability: 99.5%

#### 2.3.2 Security
- All reports encrypted with password protection
- API tokens stored securely
- No sensitive data in plain text

#### 2.3.3 Reliability
- Automatic retry on failure (3 attempts)
- Error logging and alerting
- Backup of generated reports

## 3. Current State Analysis

### 3.1 Pain Points
1. **Manual reporting**: Previously required 2-3 hours of manual work per day
2. **Inconsistent data**: Different teams using different data sources
3. **Delayed visibility**: Reports often 1-2 days behind
4. **Security concerns**: Unencrypted email attachments

### 3.2 Expected Benefits
- **Time savings**: 15+ hours per week of manual work eliminated
- **Data accuracy**: Single source of truth from Jira
- **Real-time visibility**: Reports generated automatically on schedule
- **Enhanced security**: Encrypted delivery with password protection

## 4. Success Criteria

### 4.1 KPIs
| Metric | Target | Measurement |
|--------|--------|-------------|
| Report delivery success rate | > 99% | Daily monitoring |
| Data accuracy | 100% | Weekly audit |
| User satisfaction | > 4.5/5 | Monthly survey |
| Time savings | 15+ hours/week | Time tracking |

### 4.2 Acceptance Criteria
- [x] All three reports generated automatically on schedule
- [x] Reports delivered successfully for 30 consecutive days
- [x] No data discrepancies identified in weekly audits
- [x] Stakeholder sign-off received

## 5. Risks and Mitigation

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Jira API downtime | High | Medium | Retry logic with exponential backoff |
| Email delivery failure | High | Low | Alternative delivery methods (Slack) |
| Data corruption | High | Low | Daily backups and integrity checks |
| Exchange rate volatility | Medium | High | Configurable rate with manual override |

## 6. Timeline

| Phase | Duration | Deliverables |
|-------|----------|--------------|
| Phase 1 | 1 week | FY26_PMO daily report |
| Phase 2 | 1 week | CNTIN-730 weekly report |
| Phase 3 | 2 weeks | FY26_Intake_Cost with interactive features |
| Phase 4 | 1 week | Documentation and deployment |

**Go-Live Date**: March 26, 2026

## 7. Approval

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | | | |
| Engineering Lead | | | |
| Stakeholder | | | |
