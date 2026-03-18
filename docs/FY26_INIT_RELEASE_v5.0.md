# FY26_INIT Epic Daily Report - v5.0 持久化版本发布

**发布日期**: 2026-03-12  
**版本**: v5.0  
**状态**: ✅ 已发布

---

## 发布内容

### 1. 核心系统 (v5.0)

| 组件 | 文件 | 功能 |
|------|------|------|
| 数据抓取 | `fetch_fy26_v5.py` | 从 22 个 Jira 项目抓取数据 |
| 报告生成 | `generate_fy26_report_v5.py` | 生成 JSON 结构化报告 |
| HTML 生成 | `generate_fy26_html_v5.py` | 生成交互式 HTML 报表 |
| 邮件发送 | `send_fy26_report_v5.py` | 通过 QQ 邮箱发送报告 |
| 主脚本 | `fy26_daily_report_v5.sh` | 一键执行完整流程 |

### 2. 数据架构

**SQLite 数据库**: `fy26_data.db`
- `epics` 表 - 存储所有 Epic 数据
- `features` 表 - 存储 CNTIN Feature 数据
- `initiatives` 表 - 存储 CNTIN Initiative 数据
- `fetch_log` 表 - 记录抓取操作日志

### 3. 交互式报表功能

- ✅ 显示全部 Initiatives
- ✅ 有 Epic / 无 Epic 筛选
- 🔗 无 Parent Epic 筛选
- 📅 创建时间范围筛选
- 📄 分页显示（每页 10 条）

### 4. 定时任务

**LaunchAgent**: `com.openclaw.fy26-daily-report.plist`
- **执行时间**: 每天 18:00 (Asia/Shanghai)
- **执行脚本**: `fy26_daily_report_v5.sh`
- **日志文件**: `logs/fy26_daily_report.log`

---

## 发布位置

```
/Users/admin/.openclaw/workspace/
├── scripts/
│   ├── fetch_fy26_v5.py
│   ├── generate_fy26_report_v5.py
│   ├── generate_fy26_html_v5.py
│   ├── send_fy26_report_v5.py
│   └── fy26_daily_report_v5.sh
├── jira-reports/
│   └── fy26_data.db
├── logs/
│   └── fy26_daily_report.log
└── config/
    └── .jira-config
```

---

## 打包版本

**位置**: `/Users/admin/fy26-report-package/`
**压缩包**: `/Users/admin/fy26-report-package.tar.gz`

包含:
- 完整可移植版本
- setup.sh - 环境检查和安装
- run.sh - 一键执行
- README.md - 使用文档

---

## 文档

- **PRD**: `/Users/admin/.openclaw/workspace/docs/FY26_INIT_Epic_Report_PRD.md`
- **README**: `/Users/admin/fy26-report-package/README.md`

---

## 收件人配置

- **主要收件人**: chinatechpmo@lululemon.com
- **抄送**: rcheng2@lululemon.com
- **发件邮箱**: 3823810468@qq.com (QQ 邮箱 SMTP)

---

## 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v5.0 | 2026-03-12 | SQLite 架构重构，交互式报表，日期筛选 |
| v4.x | 2026-03-11 | JSON 文件存储（已废弃） |
| v3.0 | 2026-03-11 | 正确数据结构 |
| v1.0 | 2026-03-10 | 初始版本 |

---

## 维护记录

- **2026-03-12 18:07** - 持久化版本发布
- **2026-03-12 18:04** - 修复定时任务 PATH 问题，补发报告
- **2026-03-12 15:23** - 手动发送 v5 报告
- **2026-03-12 15:21** - 更新定时任务使用 v5 版本

---

**发布者**: Tensasky  
**审核者**: Roberto
