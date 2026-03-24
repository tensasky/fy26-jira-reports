# CNTIN-730 Initiative 周报系统 v5.2

## 系统概述

CNTIN-730 周报系统用于生成 FY26 Intakes 的 Initiative 周报，包含：
- 148 个 Initiatives（Parent = CNTIN-730）
- AI 生成的 What/Why 摘要
- 统计卡片和筛选功能

## 核心文件

| 文件 | 功能 |
|------|------|
| `scripts/cntin730_report.py` | 主脚本：抓取数据 + 生成 HTML |
| `scripts/send_report.py` | 发送邮件（附件方式，防垃圾邮件） |
| `scripts/run.sh` | 定时任务脚本 |
| `config/com.openclaw.cntin730-report.plist` | macOS 定时任务配置 |

## 使用方式

### 手动执行

```bash
# 生成报告
python3 scripts/cntin730_report.py

# 发送邮件
python3 scripts/send_report.py
```

### 一键执行

```bash
bash scripts/run.sh
```

## 定时任务

执行时间：工作日（周一至周五）12:00

安装：
```bash
cp config/com.openclaw.cntin730-report.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.openclaw.cntin730-report.plist
```

## 报告特性

| 特性 | 描述 |
|------|------|
| 🤖 AI 摘要 | 自动生成 What/Why 业务解释 |
| 📊 统计卡片 | Total/Done/Discovery/Missing SLA |
| 👤 Assignee 筛选 | 前 20 位负责人快速筛选 |
| ⚠️ Missing SLA | 超时未更新项目高亮 |
| 📊 冻结列 | 前 3 列固定 |
| 📈 行展开 | 单击展开详情 |
| 📥 Excel 导出 | CSV 格式导出 |

## 邮件发送优化

为避免被安全系统识别为垃圾邮件：

- ✅ 简化邮件主题（无方括号）
- ✅ 纯文本正文（替代 HTML）
- ✅ 自然的英文邮件格式
- ✅ 去掉"自动生成"等敏感词
- ✅ HTML 报告仅作为附件

**优化后格式：**
- 主题：`CNTIN-730 FY26 Intakes Report - 2026-03-24`
- 正文：自然英文商务邮件
- 签名：`China Tech Team`

## 配置

### 环境变量

```bash
export JIRA_API_TOKEN="your_token"
export JIRA_EMAIL="rcheng2@lululemon.com"
export QQ_EMAIL_PASSWORD="your_auth_code"
```

### 邮件配置

- SMTP: smtp.qq.com:465 (SSL)
- 发件人: 3823810468@qq.com
- 收件人: chinatechpmo@lululemon.com
- 抄送: rcheng2@lululemon.com

## 输出文件

- 报告：`~/.openclaw/workspace/reports/CNTIN-730_FY26_Intakes_Report_Latest.html`
- 日志：`logs/cntin730_cron.log`

## 数据范围

JQL: `project = CNTIN AND issuetype = Initiative AND parent = CNTIN-730 AND status != Cancelled`
