# FY26_INIT Epic 日报 - 业务需求文档 (BRD)

**文档版本**: v5.4  
**创建日期**: 2026-03-18  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 业务背景

### 1.1 问题陈述
China Technology PMO 团队需要每日跟踪 FY26 财年的所有 Epic 进展。这些 Epic 分散在 22 个 Jira 项目中，通过 CNTIN Feature 关联到 CNTIN-730 Initiative。当前面临以下挑战：

- **项目数量多**: 22 个 Jira 项目需要监控
- **数据量大**: 超过 100 个 Epics 每日更新
- **抓取时间长**: 全量抓取需要 5 分钟以上
- **重复工作**: 大部分 Epic 每日无变化，但仍需全量抓取
- **内存占用高**: 大型 JSON 文件处理导致内存压力
- **生成延迟**: 等待所有数据完成后才能生成报告

### 1.2 业务目标

| 目标 | 描述 | 成功指标 |
|------|------|----------|
| 每日自动报告 | 每天 18:00 自动生成并发送 Epic 日报 | 100% 自动执行 |
| 快速数据抓取 | 减少全量抓取时间 | 从 5 min → **1.5 min** |
| 增量更新 | 只抓取有变化的 Epic | 增量更新 **~30 sec** |
| 流水线处理 | 边抓取边生成，减少等待 | 总时间 **~5-6 min** |
| 降低内存占用 | 优化大数据处理 | 内存使用 **减少 60%** |

### 1.3 利益相关者

| 角色 | 姓名/团队 | 职责 |
|------|-----------|------|
| 主要用户 | China Tech PMO | 接收日报，跟踪 Epic 进展 |
| 抄送用户 | Roberto Cheng | 监督和技术领导 |
| 最终用户 | 各 Epic 负责人 | 查看自己的 Epic 状态 |
| 系统维护 | OpenClaw | 系统开发和维护 |

---

## 2. 业务需求

### 2.1 功能需求

#### FR-001: 多项目 Epic 抓取
- **描述**: 从 22 个 Jira 项目抓取所有 Epic 数据
- **优先级**: 高
- **验收标准**: 
  - 覆盖全部 22 个项目
  - 通过 parent 字段关联到 CNTIN Feature
  - 全量抓取时间 < 2 分钟

#### FR-002: 并行抓取 (v5.3)
- **描述**: 使用多线程并行抓取多个项目
- **优先级**: 高
- **验收标准**:
  - 5 并发 workers
  - 异常项目自动重试
  - 整体抓取时间 < 2 分钟

#### FR-003: 增量更新 (v5.3)
- **描述**: 基于 updated 时间戳只抓取变化的 Epic
- **优先级**: 高
- **验收标准**:
  - 记录每个项目的最后更新时间
  - 只抓取 `updated >= -24h` 的 Epic
  - 增量更新时间 ~30 秒

#### FR-004: 流水线处理 (v5.4)
- **描述**: 边抓取边生成，实现真正的并行处理
- **优先级**: 高
- **验收标准**:
  - 生产者-消费者模式
  - 渐进式 HTML 渲染
  - 完成部分项目即可开始生成

#### FR-005: 内存优化 (v5.3)
- **描述**: 使用 StringIO 和生成器减少内存占用
- **优先级**: 中
- **验收标准**:
  - HTML 使用 StringIO 缓冲区
  - 单次磁盘写入
  - 内存使用减少 60%

#### FR-006: SQLite WAL 模式
- **描述**: 使用 Write-Ahead Logging 支持并发读写
- **优先级**: 中
- **验收标准**:
  - 抓取和查询可并发执行
  - 数据持久化存储
  - 支持增量更新

#### FR-007: 自动邮件发送
- **描述**: 自动发送日报到指定邮箱
- **优先级**: 高
- **验收标准**:
  - 收件人：chinatechpmo@lululemon.com
  - 抄送：rcheng2@lululemon.com
  - 包含 HTML 报告附件

### 2.2 非功能需求

#### NFR-001: 性能
- 全量抓取: < 2 分钟 (22 个项目)
- 增量更新: < 30 秒
- 报告生成: < 1 分钟
- 总流水线时间: ~5-6 分钟

#### NFR-002: 可靠性
- 系统可用性 > 95%
- 数据抓取成功率 > 95%
- 邮件发送成功率 > 95%

#### NFR-003: 可维护性
- 代码模块化
- 配置外部化
- 日志完整

---

## 3. 业务流程

### 3.1 日报生成流程 (v5.4 流水线)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          FY26_INIT Epic 日报流水线 v5.4                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│   ┌─────────────┐                                                           │
│   │ Project 1   │──┐                                                        │
│   ├─────────────┤  │                                                        │
│   │ Project 2   │──┤                                                        │
│   ├─────────────┤  │    ┌─────────────┐    ┌─────────────┐    ┌─────────┐  │
│   │ Project 3   │──┼───▶│   Queue     │───▶│  Consumer   │───▶│  HTML   │  │
│   ├─────────────┤  │    │  (Epics)    │    │  (Generate) │    │ Output  │  │
│   │ ...         │──┤    └─────────────┘    └─────────────┘    └─────────┘  │
│   ├─────────────┤  │         ▲                    ▲                        │
│   │ Project 22  │──┘         │                    │                        │
│   └─────────────┘            │                    │                        │
│                              │                    │                        │
│                         ┌────┴────┐         ┌────┴────┐                    │
│                         │ Producer│         │Progress │                    │
│                         │(Fetch)  │         │ Tracker │                    │
│                         └─────────┘         └─────────┘                    │
│                                                                             │
│   Key Features:                                                             │
│   - 5 并发 Producers 抓取                                                    │
│   - Queue 缓冲 Epic 数据                                                     │
│   - Consumer 边接收边生成 HTML                                                │
│   - 渐进式渲染，无需等待全部完成                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 数据抓取流程

```
全量模式:                              增量模式 (v5.3):
┌─────────────┐                       ┌─────────────┐
│ 读取项目列表 │                       │ 读取状态文件 │
└─────────────┘                       └─────────────┘
      │                                     │
      ▼                                     ▼
┌─────────────┐                       ┌─────────────┐
│ 5 并发抓取  │                       │ 检查更新时间 │
│ 22 个项目  │                       │ (updated>=  │
└─────────────┘                       │ -24h)       │
      │                               └─────────────┘
      ▼                                     │
┌─────────────┐                             ▼
│ 存储到      │                       ┌─────────────┐
│ SQLite     │                       │ 只抓变化项目 │
└─────────────┘                       └─────────────┘
                                            │
                                            ▼
                                      ┌─────────────┐
                                      │ 更新状态文件 │
                                      └─────────────┘
```

---

## 4. 数据结构

### 4.1 Jira 数据模型

```
CNTIN-730 (Initiative)
    └── CNTIN Features (22 个项目的 Epic 通过 parent 关联)
            ├── CNTEC Epics
            ├── CNTOM Epics
            ├── CNTDM Epics
            └── ... (22 个项目)
```

### 4.2 数据库 Schema (v5.3)

```sql
-- Epics 表
CREATE TABLE epics (
    key TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    parent_key TEXT,  -- 关联的 CNTIN Feature
    created TEXT,
    updated TEXT,
    labels TEXT
);

-- Features 表
CREATE TABLE features (
    key TEXT PRIMARY KEY,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    parent_key TEXT,  -- 关联的 CNTIN Initiative
    labels TEXT
);

-- Initiatives 表
CREATE TABLE initiatives (
    key TEXT PRIMARY KEY,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    labels TEXT
);

-- 抓取日志
CREATE TABLE fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT,
    issue_type TEXT,
    count INTEGER,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 5. 成功指标

### 5.1 定量指标

| 指标 | v5.0 | v5.3 | v5.4 | 目标 |
|------|------|------|------|------|
| 全量抓取时间 | 5 min | **1.5 min** | 1.5 min | < 2 min |
| 增量更新时间 | 5 min | **~30 sec** | ~30 sec | < 1 min |
| 内存占用 | 100% | **40%** | 40% | < 50% |
| 总流水线时间 | 8-10 min | 6-7 min | **5-6 min** | < 7 min |
| 并发项目数 | 1 | **5** | 5 | 5 |

### 5.2 定性指标
- PMO 团队日报及时性提升
- 系统资源占用降低
- 代码可维护性提升

---

## 6. 风险与缓解措施

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| Jira API 限流 | 高 | 中 | 指数退避重试，并发控制 |
| 数据抓取不完整 | 高 | 低 | 日志记录，异常告警 |
| 邮件发送失败 | 中 | 低 | 双模式 SMTP，失败告警 |
| 流水线死锁 | 中 | 低 | 超时机制，队列大小限制 |
| SQLite 并发冲突 | 低 | 低 | WAL 模式，连接池 |

---

## 7. 发布记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v5.4 | 2026-03-18 | **流水线架构**: 生产者-消费者模式，渐进式渲染 |
| v5.3 | 2026-03-18 | **性能优化**: 并行抓取(5 workers)，增量更新，内存优化 |
| v5.0 | 2026-03-12 | 初始版本: SQLite 架构，全量抓取，基础报告 |

---

## 8. 附录

### 8.1 术语表

| 术语 | 定义 |
|------|------|
| Epic | Jira 中的大型用户故事，包含多个 Story |
| Feature | Jira 中的功能单元，介于 Initiative 和 Epic 之间 |
| Initiative | Jira 中的战略级工作单元 |
| Pipeline | 流水线处理，边抓取边生成 |
| Producer | 生产者，负责抓取数据 |
| Consumer | 消费者，负责处理数据 |
| WAL | Write-Ahead Logging，SQLite 的并发支持模式 |
| StringIO | Python 内存缓冲区，减少磁盘 I/O |

### 8.2 项目列表 (22 个)

1. CNTEC - China Tech E-Commerce
2. CNTOM - China Tech Order Management
3. CNTDM - China Tech Data & Marketing
4. CNTMM - China Tech Membership & Marketing
5. CNTD - China Tech Data
6. CNTEST - China Test
7. CNENG - China Engineering
8. CNINFA - China Infrastructure
9. CNCA - China Customer Analytics
10. CPR - China Product
11. EPCH - Enterprise Platform China
12. CNCRM - China CRM
13. CNDIN - China Digital Innovation
14. SWMP - Software Marketplace
15. CDM - China Data Management
16. CMDM - China Master Data Management
17. CNSCM - China Supply Chain Management
18. OF - Order Fulfillment
19. CNRTPRJ - China Retail Project
20. CSCPVT - China Supply Chain Private
21. CNPMO - China PMO
22. CYBERPJT - Cyber Project

### 8.3 参考资料

- [GitHub Repository](https://github.com/tensasky/fy26-jira-reports)
- [Jira REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [SQLite WAL Mode](https://www.sqlite.org/wal.html)
