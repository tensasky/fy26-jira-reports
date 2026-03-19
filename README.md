# FY26 Jira Reports v2.2.0

[![Version](https://img.shields.io/badge/version-2.2.0-blue.svg)](docs/VERSION.md)
[![Python](https://img.shields.io/badge/python-3.9+-green.svg)](https://www.python.org/)

自动化 Jira 报告生成系统，为 lululemon China Technology 团队提供高性能的数据报告服务。

---

## 📋 项目概览

| 报告 | 频率 | 核心特性 | 性能 |
|------|------|----------|------|
| **CNTIN-730 Initiative 周报** | 工作日 12:00 | AI 智能摘要、统计卡片、冻结列、行展开、Excel 导出 | 5 min / 143 items |
| **FY26_INIT Epic 日报** | 每日 18:00 | 并行抓取、增量更新、流水线 | 1.5 min (全量) / 30s (增量) |

---

## 🚀 快速开始

### 安装依赖

```bash
pip3 install requests aiohttp
```

### 配置环境变量

```bash
# ~/.zshrc
export JIRA_API_TOKEN="your_jira_token"
export JIRA_EMAIL="your_email@lululemon.com"
export QQ_MAIL_PASSWORD="your_qq_auth_code"
export AI_API_KEY="your_ai_key"  # optional
```

### 运行报告

```bash
# CNTIN-730 周报 (AI 摘要 + 完整功能)
python3 scripts/cntin730_weekly_report.py

# 或快速版 (无 AI，纯数据)
python3 scripts/cntin730_report_v5.2_full.py

# FY26_INIT 日报 (标准版)
bash scripts/fy26_daily_report.sh

# FY26_INIT 日报 (流水线版 - 更快)
python3 scripts/fy26_pipeline_v5.4.py
```

---

## 📊 核心特性

### CNTIN-730 周报 v1.2.0

| 特性 | 描述 | 状态 |
|------|------|------|
| 🤖 AI 摘要 | 自动生成 What/Why 业务解释 | ✅ |
| 📊 统计卡片 | Total/Done/Discovery/Missing SLA 概览 | ✅ v1.2.0 |
| 👤 Assignee 筛选 | 前 20 位负责人快速筛选 | ✅ v1.2.0 |
| ⚠️ Missing SLA 筛选 | 超时未更新项目高亮 | ✅ v1.2.0 |
| 📊 冻结列 | 前 3 列固定，横向滚动 | ✅ |
| 📈 行展开 | 单击展开完整描述和 AI 摘要 | ✅ v1.2.0 |
| 📥 Excel 导出 | 导出 CSV 格式数据 | ✅ v1.2.0 |
| ⚡ 异步处理 | 30 并发 workers | ✅ |
| 💾 语义缓存 | MD5 内容哈希缓存 | ✅ |
| 📧 邮件发送 | 自动发送给 PMO 团队 | ✅ |
| 📱 飞书发送 | 文件发送到飞书 | ✅ |

### FY26_INIT 日报

| 特性 | 描述 |
|------|------|
| 🔄 并行抓取 | 5 并发 workers |
| 📈 增量更新 | 只抓 24h 内变动 |
| 🗄️ WAL 模式 | SQLite 读写并发 |
| 📝 内存生成 | StringIO 缓冲区 |
| 🏭 流水线 | 边抓边生成 |

---

## 📁 项目结构

```
~/.openclaw/workspace/
├── scripts/                           # 核心脚本
│   ├── cntin730_weekly_report.py      # CNTIN-730 周报主脚本
│   ├── cntin730_report_v5.2_full.py   # CNTIN-730 完整功能版
│   ├── fy26_daily_report.sh           # FY26_INIT 日报脚本
│   ├── fy26_pipeline_v5.4.py          # 流水线主控
│   ├── fetch_fy26.py                  # 数据抓取
│   ├── generate_fy26_html.py          # HTML 生成
│   └── send_fy26_report_v5.py         # 邮件发送
├── docs/                              # 文档
│   ├── brd/                           # 业务需求文档
│   │   └── CNTIN730_Initiative_Report_BRD.md
│   ├── prd/                           # 产品需求文档
│   │   └── CNTIN730_Initiative_Report_PRD.md
│   ├── sdd/                           # 系统设计文档
│   │   └── CNTIN730_Initiative_Report_SDD.md
│   ├── CHANGELOG.md                   # 变更日志
│   └── VERSION.md                     # 版本信息
├── reports/                           # 生成的报告
│   └── cntin_730_report_YYYYMMDD.html
├── jira-reports/                      # Jira 数据
│   ├── cache/                         # AI 语义缓存
│   └── *.json                         # 原始数据
├── logs/                              # 执行日志
├── memory/                            # 每日记忆文件
└── .jira-config                       # Jira 配置文件

~/Library/LaunchAgents/                # 定时任务
├── com.openclaw.cntin730-weekly-report.plist
└── com.openclaw.fy26-daily-report.plist
```

---

## ⚙️ 配置

### Jira API
- URL: `https://lululemon.atlassian.net`
- Auth: Basic Auth (email + API token)

### SMTP (QQ Mail)
- Server: `smtp.qq.com:587` (STARTTLS)
- From: `3823810468@qq.com`
- To: `chinatechpmo@lululemon.com`
- CC: `rcheng2@lululemon.com`

### 定时任务

**CNTIN-730 周报**:
- 时间: 工作日（周一至周五）12:00
- 时区: Asia/Shanghai (GMT+8)
- 命令: `python3 scripts/cntin730_weekly_report.py`

**FY26_INIT 日报**:
- 时间: 每日 18:00
- 命令: `bash scripts/fy26_daily_report.sh`

---

## 📚 文档

| 文档 | 路径 |
|------|------|
| 版本信息 | [VERSION.md](docs/VERSION.md) |
| 变更日志 | [CHANGELOG.md](docs/CHANGELOG.md) |
| CNTIN-730 BRD | [docs/brd/CNTIN730_Initiative_Report_BRD.md](docs/brd/CNTIN730_Initiative_Report_BRD.md) |
| CNTIN-730 PRD | [docs/prd/CNTIN730_Initiative_Report_PRD.md](docs/prd/CNTIN730_Initiative_Report_PRD.md) |
| CNTIN-730 SDD | [docs/sdd/CNTIN730_Initiative_Report_SDD.md](docs/sdd/CNTIN730_Initiative_Report_SDD.md) |
| FY26_INIT BRD | [docs/brd/FY26_INIT_Epic_Report_BRD.md](docs/brd/FY26_INIT_Epic_Report_BRD.md) |
| FY26_INIT PRD | [docs/prd/FY26_INIT_Epic_Report_PRD.md](docs/prd/FY26_INIT_Epic_Report_PRD.md) |

---

## 📈 性能基准

### CNTIN-730 周报 (143 Initiatives)
```
├── 数据抓取: ~1 min
├── AI 生成: ~5 min (缓存命中: ~60%)
├── HTML 生成: ~3 sec
├── 邮件发送: ~10 sec
└── 总计: ~6 min
```

### FY26_INIT 日报 (22 Projects)
```
├── 全量抓取: ~1.5 min
├── 增量更新: ~30 sec
├── HTML 生成: ~2 sec
└── 总计: ~2 min (全量) / ~1 min (增量)
```

---

## 🛠️ 故障排查

### 常见问题

**Q: CNTIN-730 周报未收到**  
A: 检查定时任务状态: `launchctl list | grep cntin730`

**Q: 数据不完整（少于 143 条）**  
A: 检查 API 分页是否正常: `grep "nextPageToken" /tmp/cntin730.log`

**Q: AI 生成慢**  
A: 检查缓存命中率: `ls ~/.openclaw/workspace/jira-reports/cache/`

**Q: 邮件发送失败**  
A: 更新 `QQ_MAIL_PASSWORD` 授权码

**Q: 报告格式错乱**  
A: 使用 Chrome/Safari/Edge 最新版本打开

---

## 📝 版本历史

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| v2.2.0 | 2026-03-19 | CNTIN-730 v1.2.0: 统计卡片、Assignee 筛选、行展开、Excel 导出 |
| v2.1.0 | 2026-03-18 | 仓库清理，归档旧文件 |
| v2.0.0 | 2026-03-18 | 完整优化套件 |
| v1.0.0 | 2026-03-12 | 初始稳定版 |

---

## 👥 作者

- **OpenClaw** - 系统设计 & 开发
- **Roberto Cheng** - 产品负责人

---

## 📄 License

MIT License

---

**GitHub**: https://github.com/tensasky/fy26-jira-reports
