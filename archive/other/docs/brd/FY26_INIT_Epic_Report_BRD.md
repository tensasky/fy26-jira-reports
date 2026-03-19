# FY26_INIT Epic 日报 - 业务需求文档 (BRD)

**文档版本**: v5.0.0  
**创建日期**: 2026-03-18  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 业务背景

### 1.1 问题陈述
lululemon China Technology 团队管理着 FY26 财年的大量技术项目，涉及 22 个 Jira 项目。PMO 团队需要每天跟踪这些项目的 Epic、Feature 和 Initiative 的进展，但面临以下挑战：

- **数据分散**: 信息分散在 22 个不同的 Jira 项目中
- **手动汇总困难**: 人工收集和汇总数据耗时且容易出错
- **实时性不足**: 无法及时获取最新的项目状态更新
- **缺乏统一视图**: 没有一个集中的仪表板查看所有 FY26_INIT 相关的工作

### 1.2 业务目标

| 目标 | 描述 | 成功指标 |
|------|------|----------|
| 自动化日报 | 每天自动生成并发送 Epic 状态报告 | 100% 自动执行，无需人工干预 |
| 数据准确性 | 确保从所有 22 个项目完整抓取数据 | 数据完整率 > 99% |
| 实时可见性 | 提供最新的项目状态视图 | 数据时效性 < 24 小时 |
| 提升效率 | 减少 PMO 手动收集数据的时间 | 节省 90% 的数据收集时间 |

### 1.3 利益相关者

| 角色 | 姓名/团队 | 职责 |
|------|-----------|------|
| 主要用户 | China Tech PMO | 接收并使用日报进行项目管理 |
| 抄送用户 | Roberto Cheng | 监督和技术领导 |
| 系统维护 | OpenClaw | 系统开发和维护 |

---

## 2. 业务需求

### 2.1 功能需求

#### FR-001: 全量数据抓取
- **描述**: 系统必须从所有 22 个 Jira 项目抓取 Epic、Feature 和 Initiative 数据
- **优先级**: 高
- **验收标准**: 
  - 覆盖 22 个项目：CNTEC, CNTOM, CNTDM, CNTMM, CNTD, CNTEST, CNENG, CNINFA, CNCA, CPR, EPCH, CNCRM, CNDIN, SWMP, CDM, CMDM, CNSCM, OF, CNRTPRJ, CSCPVT, CNPMO, CYBERPJT
  - 抓取时间 < 5 分钟

#### FR-002: 数据持久化
- **描述**: 使用 SQLite 数据库存储抓取的数据，确保数据不丢失
- **优先级**: 高
- **验收标准**:
  - 数据库包含 epics, features, initiatives 三个表
  - 支持历史数据查询
  - 数据可重复生成报告

#### FR-003: 交互式 HTML 报告
- **描述**: 生成可交互的 HTML 报告，支持筛选和查看详情
- **优先级**: 高
- **验收标准**:
  - 响应式设计，支持桌面和移动设备
  - 支持按状态、项目、标签筛选
  - 显示数据更新时间

#### FR-004: 自动邮件发送
- **描述**: 每天 18:00 自动发送报告到指定邮箱
- **优先级**: 高
- **验收标准**:
  - 收件人：chinatechpmo@lululemon.com
  - 抄送：rcheng2@lululemon.com
  - 邮件包含 HTML 附件

#### FR-005: 定时任务调度
- **描述**: 使用 macOS LaunchAgent 实现定时执行
- **优先级**: 中
- **验收标准**:
  - 每天 18:00 自动触发
  - 支持手动触发
  - 执行日志记录

### 2.2 非功能需求

#### NFR-001: 性能
- 数据抓取时间 < 5 分钟
- 报告生成时间 < 30 秒
- 邮件发送时间 < 10 秒

#### NFR-002: 可靠性
- 系统可用性 > 95%
- 数据抓取成功率 > 99%
- 邮件发送成功率 > 95%

#### NFR-003: 安全性
- Jira API Token 安全存储
- 邮箱密码环境变量管理
- 不记录敏感信息到日志

---

## 3. 业务流程

### 3.1 日报生成流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  定时触发   │───▶│  清空缓存   │───▶│  Jira抓取   │───▶│  数据存储   │───▶│  生成报告   │
│ (18:00 daily)│   │             │   │ (22 projects)│   │  (SQLite)   │   │  (HTML/JSON) │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                                                          │
                                                                                          ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐                                    ┌─────────────┐
│  完成通知   │◀───│  发送邮件   │◀───│  生成HTML   │◀───────────────────────────────────│  生成JSON   │
│             │    │(QQ Mail)   │    │             │                                    │             │
└─────────────┘    └─────────────┘    └─────────────┘                                    └─────────────┘
```

### 3.2 数据流

```
Jira API (22 projects)
    │
    ▼
Python Fetch Script (fetch_fy26_v5.py)
    │
    ▼
SQLite Database (fy26_data.db)
    │
    ▼
Report Generator (generate_fy26_report_v5.py)
    │
    ▼
HTML Generator (generate_fy26_html_v5.py)
    │
    ▼
Email Sender (send_fy26_report_v5.py)
    │
    ▼
Recipients (chinatechpmo@lululemon.com)
```

---

## 4. 数据模型

### 4.1 数据结构

**CNTIN 项目 (Initiative → Feature)**
```
Initiative (CNTIN)
  └── Feature (CNTIN)
```

**其他项目 (Epic → CNTIN Feature)**
```
Epic (CNTEC, CNTOM, etc.)
  └── parent: Feature (CNTIN)
        └── parent: Initiative (CNTIN)
```

### 4.2 数据库表结构

**epics 表**
| 字段 | 类型 | 说明 |
|------|------|------|
| key | TEXT | Epic 编号 (e.g., CPR-123) |
| project | TEXT | 项目代码 |
| summary | TEXT | 标题 |
| status | TEXT | 状态 |
| assignee | TEXT | 负责人 |
| parent_key | TEXT | 关联的 Feature |
| created | TEXT | 创建时间 |
| labels | TEXT | 标签 |

**features 表**
| 字段 | 类型 | 说明 |
|------|------|------|
| key | TEXT | Feature 编号 |
| summary | TEXT | 标题 |
| status | TEXT | 状态 |
| assignee | TEXT | 负责人 |
| parent_key | TEXT | 关联的 Initiative |
| labels | TEXT | 标签 |

**initiatives 表**
| 字段 | 类型 | 说明 |
|------|------|------|
| key | TEXT | Initiative 编号 |
| summary | TEXT | 标题 |
| status | TEXT | 状态 |
| assignee | TEXT | 负责人 |
| labels | TEXT | 标签 |

---

## 5. 报表内容

### 5.1 统计概览
- 总 Initiatives 数量
- 总 Features 数量
- 总 Epics 数量
- 已关联 Epics 数量
- 孤儿 Feature 数量
- SLA Alert 数量（超过 2 周未更新）

### 5.2 项目分布
- 每个项目的 Epic 数量
- 无 Epic 的项目列表

### 5.3 状态分布
- Discovery
- Execution
- Done
- New
- Strategy
- To Do

---

## 6. 成功指标

### 6.1 定量指标

| 指标 | 目标 | 当前 |
|------|------|------|
| 数据完整率 | > 99% | 100% |
| 日报生成成功率 | > 95% | 100% |
| 平均生成时间 | < 5 分钟 | ~3 分钟 |
| PMO 手动工作时间 | 减少 90% | 已实现 |

### 6.2 定性指标
- PMO 团队满意度 > 4/5
- 技术团队可见性提升
- 项目透明度改善

---

## 7. 风险与缓解措施

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| Jira API 限流 | 高 | 中 | 实现指数退避重试机制 |
| 邮箱 SMTP 故障 | 中 | 低 | 双模式 SMTP (SSL/STARTTLS) |
| 数据库损坏 | 高 | 低 | 定期备份，可从 Jira 重新抓取 |
| 网络中断 | 高 | 低 | 执行日志记录，失败告警 |

---

## 8. 发布记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| v5.0.0 | 2026-03-12 | SQLite 架构重构，解决数据丢失问题 |
| v4.0-v4.7 | 2026-03-11 | JSON 合并 bug 修复 |
| v3.0 | 2026-03-11 | 正确的数据结构实现 |
| v2.0 | 2026-03-11 | 反向扫描尝试 |
| v1.0 | 2026-03-10 | 初始版本 |

---

## 9. 附录

### 9.1 术语表

| 术语 | 定义 |
|------|------|
| Epic | Jira 中的大型工作单元，通常跨越多个 Sprint |
| Feature | 产品功能，位于 Epic 和 Story 之间 |
| Initiative | 战略级工作单元，包含多个 Feature |
| FY26_INIT | FY26 财年初始化标签，用于标记相关工作 |
| SLA Alert | 服务级别协议警报，此处指超过 2 周未更新的 ticket |

### 9.2 参考资料

- [Jira REST API v3 文档](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [SQLite Python 文档](https://docs.python.org/3/library/sqlite3.html)
- [GitHub Release v5.0.0](docs/FY26_INIT_RELEASE_v5.0.md)
