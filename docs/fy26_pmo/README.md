# FY26 PMO 日报系统 v5.7

## 系统概述

FY26_PMO 日报系统用于生成 lululemon China Technology 的 PMO 日报，包含：
- 53 个 FY26_INIT Initiatives
- 235 个 Features
- 200 个 Epics（来自 22 个项目）

## 核心文件

| 文件 | 功能 |
|------|------|
| `fetch_data.py` | 从 Jira API 抓取数据（22个项目） |
| `generate_html_v5.py` | 生成 HTML 报告 V5.7（Status Trend 修复） |
| `send_email.py` | 发送邮件（附件方式） |
| `send_resend.py` | 使用 Resend API 发送 |
| `db_schema.sql` | SQLite 数据库结构 |
| `run.sh` | 一键执行脚本 |

## Status Trend V5.7 修复

- ✅ Status Trend 标签文字颜色从白色改为黑色
- ✅ 有值时：彩色底色 + 黑色文字
- ✅ 无值时 (None Trend)：浅红色底色 + 深红色文字

**显示效果：**
- 🟢 On track → 绿色底 + 黑字
- 🟠 At risk → 橙色底 + 黑字
- 🔴 Off track → 红色底 + 黑字
- ⚪️ Not started → 黑色底 + 黑字
- 🔵 Complete → 蓝色底 + 黑字
- 🟤 On hold → 棕色底 + 黑字

## 使用方式

### 手动执行

```bash
# 1. 抓取数据
python3 fetch_data.py

# 2. 生成报告
python3 generate_html_v5.py

# 3. 发送邮件
python3 send_email.py --type fy26 --path fy26_pmo_report_v5_latest.html
```

### 一键执行

```bash
bash run.sh
```

## 定时任务

文件：`com.openclaw.fy26-pmo-report.plist`

执行时间：工作日 18:00

安装：
```bash
cp com.openclaw.fy26-pmo-report.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-pmo-report.plist
```

## 配置

### 环境变量

```bash
export JIRA_API_TOKEN="your_token"
export JIRA_EMAIL="rcheng2@lululemon.com"
export QQ_MAIL_PASSWORD="your_auth_code"
```

### 数据库

SQLite 数据库：`jira_report.db`

表结构：
- `initiatives` - CNTIN Initiatives
- `features` - CNTIN Features
- `epics` - 各项目 Epics
- `fetch_log` - 抓取日志

## 抓取范围

**Epic 项目（18个）：**
CNTD, CNTEST, CNENG, CNINFA, CNCA, CPR, EPCH, CNCRM, CNDIN, SWMP, CDM, CMDM, CNSCM, OF, CNRTPRJ, CSCPVT, CNPMO, CYBERPJT

**CNTIN：**
带 `FY26_INIT` 标签的 Initiatives 及其 Features

## 报告特性

- 📊 Status Trend 彩色显示
- 🗂️ Initiative → Feature → Epic 三级视图
- 🔍 折叠/展开功能
- 📁 按项目分组
- ⚠️ 未关联 Epic 列表

## 邮件配置

- SMTP: smtp.qq.com:587 (STARTTLS)
- 发件人: 3823810468@qq.com
- 收件人: chinatechpmo@lululemon.com
- 抄送: rcheng2@lululemon.com
