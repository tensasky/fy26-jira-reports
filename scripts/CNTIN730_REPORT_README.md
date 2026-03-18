# CNTIN-730 Initiative Weekly Report v1.0.0

## 📋 功能概述

CNTIN-730 Initiative 周报自动化脚本，包含完整的端到端流程：

1. **清空历史缓存** - 每次运行时自动清理 AI Summary 缓存和 Jira 数据
2. **全量获取数据** - 从 Jira API 获取 CNTIN-730 下所有 Initiatives
3. **AI Summary 生成** - 使用 LLM 自动生成 What/Why 标准化解释
4. **HTML 报告生成** - 生成可交互的 HTML 报告
5. **邮件自动发送** - 发送到指定邮箱

## 🚀 快速开始

### 环境变量配置

```bash
export JIRA_API_TOKEN="your_jira_api_token"
export AI_API_KEY="your_ai_api_key"  # 可选，有默认值
export AI_BASE_URL="http://newapi.200m.997555.xyz/v1"  # 可选
export AI_MODEL="claude-sonnet-4-6"  # 可选
export QQ_MAIL_PASSWORD="your_qq_mail_password"
```

### 运行

```bash
python3 cntin730_weekly_report.py
```

## 📁 文件说明

| 文件 | 说明 |
|------|------|
| `cntin730_weekly_report.py` | 主脚本文件 |
| `/tmp/cntin_initiatives.json` | Jira 原始数据缓存 |
| `/tmp/ai_summary_cache/` | AI Summary 缓存目录 |
| `cntin_730_report_YYYYMMDD_HHMM.html` | 生成的 HTML 报告 |

## ✨ 主要特性

- **并发处理** - 使用 5 线程并发生成 AI Summary，大幅提升效率
- **智能缓存** - 支持缓存 AI Summary 结果，避免重复调用 API
- **点击展开** - HTML 报告支持点击行展开完整内容
- **多维度筛选** - 支持按状态、Label、搜索词筛选
- **SLA Alert** - 自动标记超过 2 周未更新的非 Done 状态 Initiative

## 📧 邮件配置

- **发件人**: 3823810468@qq.com
- **收件人**: chinatechpmo@lululemon.com
- **抄送**: rcheng2@lululemon.com

## 📝 更新日志

### v1.0.0 (2026-03-18)
- 初始版本发布
- 集成全流程自动化
- 支持 AI Summary 生成
- 支持邮件自动发送

## 🔧 技术栈

- Python 3.8+
- Jira REST API v3
- OpenAI-compatible API
- SMTP (QQ Mail)
- HTML5 + JavaScript

## 👤 作者

OpenClaw

## 📄 License

MIT
