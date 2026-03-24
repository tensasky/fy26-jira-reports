# FY26 Jira Reports v3.0.0

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](docs/VERSION.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)

自动化 Jira 报告生成系统，为 lululemon China Technology 团队提供高性能的数据报告服务。

---

## 📋 项目概览

| 报告 | 频率 | 核心特性 | 数据量 |
|------|------|----------|--------|
| **FY26_PMO 日报** | 工作日 18:00 | Status Trend 颜色修复、层级折叠/展开、按项目分组 | 53 Initiatives, 235 Features, 200 Epics |
| **CNTIN-730 Initiative 周报** | 工作日 12:00 | AI 智能摘要、统计卡片、Assignee 筛选、行展开、Excel 导出 | 148 Initiatives |

---

## 🚀 快速开始

### 安装依赖

```bash
pip3 install requests urllib3
```

### 配置环境变量

```bash
# ~/.zshrc
export JIRA_API_TOKEN="your_jira_token"
export JIRA_EMAIL="your_email@lululemon.com"
export QQ_MAIL_PASSWORD="your_qq_auth_code"
```

### 运行报告

```bash
# FY26_PMO 日报
python3 fy26_pmo/fetch_data.py
python3 fy26_pmo/generate_html_v5.py
python3 fy26_pmo/send_email.py --type fy26 --path fy26_pmo/fy26_pmo_report_v5_latest.html

# CNTIN-730 周报
python3 projects/cntin730-report/scripts/cntin730_report.py
python3 projects/cntin730-report/scripts/send_report.py
```

---

## 📊 核心特性

### FY26_PMO 日报 v5.7

| 特性 | 描述 | 状态 |
|------|------|------|
| 📊 Status Trend | 彩色底色 + 黑色文字显示趋势状态 | ✅ v5.7 |
| 🗂️ 层级结构 | Initiative → Feature → Epic 三级视图 | ✅ |
| 🔍 折叠/展开 | 一键折叠/展开所有 Feature | ✅ |
| 📁 按项目分组 | Epic 按所属项目分组显示 | ✅ |
| ⚠️ 未关联 Epic 列表 | 显示无 parent 的 Epic | ✅ |
| 📧 邮件发送 | 自动发送给 PMO 团队 | ✅ |

**Status Trend 显示效果：**
- 🟢 On track → 绿色底 + 黑字
- 🟠 At risk → 橙色底 + 黑字
- 🔴 Off track → 红色底 + 黑字
- ⚪️ Not started → 黑色底 + 黑字
- 🔵 Complete → 蓝色底 + 黑字
- 🟤 On hold → 棕色底 + 黑字
- 无值时 (None Trend)：浅红色底色 + 深红色文字

### CNTIN-730 周报 v5.2

| 特性 | 描述 | 状态 |
|------|------|------|
| 🤖 AI 摘要 | 自动生成 What/Why 业务解释 | ✅ |
| 📊 统计卡片 | Total/Done/Discovery/Missing SLA 概览 | ✅ |
| 👤 Assignee 筛选 | 前 20 位负责人快速筛选 | ✅ |
| ⚠️ Missing SLA 筛选 | 超时未更新项目高亮 | ✅ |
| 📊 冻结列 | 前 3 列固定，横向滚动 | ✅ |
| 📈 行展开 | 单击展开完整描述和 AI 摘要 | ✅ |
| 📥 Excel 导出 | 导出 CSV 格式数据 | ✅ |
| 📧 邮件发送 | 附件方式发送 HTML 报告 | ✅ |

---

## 📁 项目结构

```
~/.openclaw/workspace/
├── fy26_pmo/                          # FY26_PMO 日报系统
│   ├── fetch_data.py                  # 数据抓取（22个项目）
│   ├── generate_html_v5.py            # HTML 报告生成 V5.7
│   ├── send_email.py                  # 邮件发送（优化版）
│   ├── send_resend.py                 # Resend API 发送
│   ├── db_schema.sql                  # SQLite 数据库结构
│   ├── com.openclaw.fy26-pmo-report.plist  # 定时任务配置
│   └── run.sh                         # 一键执行脚本
│
├── projects/cntin730-report/          # CNTIN-730 周报系统
│   ├── scripts/
│   │   ├── cntin730_report.py         # 主脚本 v5.2
│   │   ├── send_report.py             # 邮件发送（附件方式）
│   │   └── run.sh                     # 定时任务脚本
│   ├── config/
│   │   └── com.openclaw.cntin730-report.plist  # 定时任务
│   └── logs/                          # 执行日志
│
├── reports/                           # 生成的报告
│   ├── fy26_pmo_report_v5_latest.html
│   └── CNTIN-730_FY26_Intakes_Report_Latest.html
│
├── docs/                              # 文档
│   ├── design/
│   ├── brd/
│   ├── prd/
│   └── sdd/
│
└── memory/                            # 长期记忆文件
    └── MEMORY.md                      # 重要决策记录

~/Library/LaunchAgents/                # macOS 定时任务
├── com.openclaw.fy26-pmo-report.plist
└── com.openclaw.cntin730-report.plist
```

---

## ⚙️ 配置

### Jira API
- URL: `https://lululemon.atlassian.net`
- Auth: Basic Auth (email + API token)
- API: `/rest/api/3/search/jql` (POST)

### SMTP (QQ Mail)
- Server: `smtp.qq.com:465` (SSL) / `587` (STARTTLS)
- From: `3823810468@qq.com`
- To: `chinatechpmo@lululemon.com`
- CC: `rcheng2@lululemon.com`

### 定时任务

**FY26_PMO 日报**:
- 时间: 工作日 18:00
- 命令: `bash fy26_pmo/run.sh`

**CNTIN-730 周报**:
- 时间: 工作日（周一至周五）12:00
- 命令: `bash projects/cntin730-report/scripts/run.sh`

---

## 📚 文档

| 文档 | 路径 |
|------|------|
| 版本信息 | [docs/VERSION.md](docs/VERSION.md) |
| 变更日志 | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| CNTIN-730 设计文档 | [docs/design/CNTIN730_Initiative_Report_Design.md](docs/design/CNTIN730_Initiative_Report_Design.md) |
| CNTIN-730 BRD | [docs/brd/CNTIN730_Initiative_Report_BRD.md](docs/brd/CNTIN730_Initiative_Report_BRD.md) |
| CNTIN-730 PRD | [docs/prd/CNTIN730_Initiative_Report_PRD.md](docs/prd/CNTIN730_Initiative_Report_PRD.md) |
| CNTIN-730 SDD | [docs/sdd/CNTIN730_Initiative_Report_SDD.md](docs/sdd/CNTIN730_Initiative_Report_SDD.md) |

---

## 📈 性能基准

### FY26_PMO 日报
```
├── 数据抓取 (22项目): ~2 min
├── HTML 生成: ~3 sec
├── 邮件发送: ~5 sec
└── 总计: ~2.5 min
```

### CNTIN-730 周报 (148 Initiatives)
```
├── 数据抓取: ~1 min
├── AI 摘要生成: ~3 min
├── HTML 生成: ~2 sec
├── 邮件发送: ~5 sec
└── 总计: ~4 min
```

---

## 🛠️ 故障排查

### 常见问题

**Q: CNTIN-730 报告被安全系统屏蔽**  
A: 邮件格式已优化，使用纯文本正文 + 简化主题

**Q: FY26_PMO 报告数据不完整**  
A: 确认使用 `generate_html_v5.py` 而非旧版脚本

**Q: 邮件发送失败**  
A: 检查 `QQ_MAIL_PASSWORD` 授权码是否过期

**Q: 定时任务未执行**  
A: 检查 Python 路径：`which python3` 应为 `/usr/bin/python3`

---

## 📝 版本历史

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| v3.0.0 | 2026-03-24 | FY26_PMO v5.7: Status Trend 文字颜色修复，CNTIN-730 邮件格式优化 |
| v2.2.0 | 2026-03-19 | CNTIN-730 v1.2.0: 统计卡片、Assignee 筛选、行展开 |
| v2.0.0 | 2026-03-18 | 完整优化套件 |
| v1.0.0 | 2026-03-12 | 初始稳定版 |

---

## 👥 作者

- **Roberto Cheng** - 产品负责人
- **Tensasky** - 系统设计 & 开发

---

## 📄 License

MIT License

---

**GitHub**: https://github.com/tensasky/fy26-jira-reports
