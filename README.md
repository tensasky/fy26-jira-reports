# FY26 Jira Reports v2.0.0

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](CHANGELOG.md)
[![Python](https://img.shields.io/badge/python-3.8+-green.svg)](https://www.python.org/)

自动化 Jira 报告生成系统，为 lululemon China Technology 团队提供高性能的数据报告服务。

---

## 📋 项目概览

| 报告 | 频率 | 核心特性 | 性能 |
|------|------|----------|------|
| **CNTIN-730 Initiative 周报** | 按需 | AI 智能摘要、冻结列、异步处理 | 3-5 min / 100 items |
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
# CNTIN-730 周报 (AI 摘要)
python3 scripts/cntin730_weekly_report.py

# FY26_INIT 日报 (标准版)
python3 scripts/fy26_daily_report.sh

# FY26_INIT 日报 (流水线版 - 更快)
python3 scripts/fy26_pipeline_v5.4.py
```

---

## 📊 核心特性

### CNTIN-730 周报

| 特性 | 描述 |
|------|------|
| 🤖 AI 摘要 | 自动生成 What/Why 业务解释 |
| 📝 自然语言 | 动词开头，无 AI 腔调 |
| 📊 冻结列 | 前 3 列固定，横向滚动 |
| ⚡ 异步处理 | 30 并发 workers |
| 💾 语义缓存 | MD5 内容哈希缓存 |

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
fy26-jira-reports/
├── scripts/
│   ├── cntin730_weekly_report.py      # CNTIN-730 周报 (AI)
│   ├── fetch_fy26.py                   # 数据抓取 (并行+增量)
│   ├── generate_fy26_html.py           # HTML 生成 (内存优化)
│   ├── generate_fy26_report_v5.py      # JSON 报告生成
│   ├── send_fy26_report_v5.py          # 邮件发送
│   ├── fy26_pipeline_v5.4.py           # 流水线主控
│   ├── fy26_daily_report.sh            # 标准主控脚本
│   └── fy26_db_schema.sql              # 数据库 Schema
├── docs/
│   ├── brd/                            # 业务需求文档
│   ├── prd/                            # 产品需求文档
│   └── design/                         # 详细设计文档
├── CHANGELOG.md
└── README.md
```

---

## 📚 文档

- [CHANGELOG](CHANGELOG.md) - 版本历史
- [CNTIN-730 BRD](docs/brd/CNTIN730_Initiative_Report_BRD.md)
- [CNTIN-730 PRD](docs/prd/CNTIN730_Initiative_Report_PRD.md)
- [FY26_INIT BRD](docs/brd/FY26_INIT_Epic_Report_BRD.md)
- [FY26_INIT PRD](docs/prd/FY26_INIT_Epic_Report_PRD.md)

---

## ⚙️ 配置

### Jira API
- URL: `https://lululemon.atlassian.net`
- Auth: Basic Auth (email + API token)

### SMTP (QQ Mail)
- Server: `smtp.qq.com:465` (SSL) / `:587` (STARTTLS)
- From: `3823810468@qq.com`
- To: `chinatechpmo@lululemon.com`

---

## 📈 性能基准

### CNTIN-730 周报
```
100 Initiatives:
├── 首次生成: ~5 min
├── 缓存命中: ~2 min
└── Token 节省: 20%
```

### FY26_INIT 日报
```
22 Projects:
├── 全量抓取: ~1.5 min (vs 5 min)
├── 增量更新: ~30 sec (vs 5 min)
└── HTML 生成: ~2 sec (vs 5 sec)
```

---

## 🛠️ 故障排查

### 常见问题

**Q: 日报未收到**  
A: `launchctl list | grep fy26`

**Q: AI 生成慢**  
A: 检查缓存命中率 `ls /tmp/ai_summary_cache_semantic/`

**Q: 抓取失败**  
A: 检查 `JIRA_API_TOKEN` 权限

**Q: 邮件失败**  
A: 更新 `QQ_MAIL_PASSWORD` 授权码

---

## 📝 版本历史

| 版本 | 日期 | 主要更新 |
|------|------|----------|
| v2.0.0 | 2026-03-18 | 完整优化套件 |
| v1.0.0 | 2026-03-12 | 初始稳定版 |

---

## 👥 作者

- **OpenClaw** - 系统设计 & 开发

---

## 📄 License

MIT License

---

**GitHub**: https://github.com/tensasky/fy26-jira-reports
