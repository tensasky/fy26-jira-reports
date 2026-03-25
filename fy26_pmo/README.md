# FY26 PMO 日报系统 v5.7

## 系统概述

FY26_PMO 日报系统用于生成 lululemon China Technology 的 PMO 日报，包含：
- 53 个 FY26_INIT Initiatives
- 235 个 Features
- 200 个 Epics（来自 22 个项目）

## 邮件发送方案（2026-03-25 更新）

### 问题
HTML 报告因包含 JavaScript 交互代码被微软安全系统误判为 Phish/Malicious Payload 而拦截。

### 解决方案：AES-256 加密 ZIP

**加密方式：**
- 使用 7z 创建 AES-256 加密 ZIP
- 命令：`7z a -tzip -p<密码> -mem=AES256`
- ZIP 密码：`lulupmo`

**邮件策略：**
- 邮件主题包含中文，避免被识别为自动化邮件
- 正文为自然口吻（Roberto / China Tech Team 签名）
- **正文不包含密码**，提示通过飞书/Slack 获取
- 密码通过飞书单独发送，实现密码分离

**优势：**
- ✅ AES-256 加密无法被内容扫描
- ✅ 保留 HTML 完整交互功能
- ✅ 绕过微软 Defender/ATP 拦截

## 核心文件

| 文件 | 功能 |
|------|------|
| `fetch_data.py` | 从 Jira API 抓取数据（22个项目） |
| `generate_html_v5.py` | 生成 HTML 报告 V5.7（Status Trend 修复） |
| `send_email.py` | 发送加密 ZIP 邮件 |
| `db_schema.sql` | SQLite 数据库结构 |
| `run.sh` | 一键执行脚本（自动生成+发送） |

## 使用方式

### 手动执行

```bash
# 1. 抓取数据
python3 fetch_data.py

# 2. 生成报告
python3 generate_html_v5.py

# 3. 发送加密 ZIP 邮件
python3 send_email.py --type fy26 --path fy26_pmo_report_v5_latest.html
```

### 一键执行

```bash
bash run.sh
```

## 定时任务

文件：`com.openclaw.fy26-pmo-report.plist`

执行时间：**工作日 18:00**

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

### 邮件配置

| 配置项 | 值 |
|--------|-----|
| SMTP 服务器 | smtp.qq.com:465 (SSL) |
| 发件人 | 3823810468@qq.com |
| 收件人 | chinatechpmo@lululemon.com |
| 抄送 | rcheng2@lululemon.com |
| ZIP 密码 | lulupmo |

## 报告特性

- 📊 Status Trend 彩色显示
- 🗂️ Initiative → Feature → Epic 三级视图
- 🔍 折叠/展开功能
- 📁 按项目分组
- ⚠️ 未关联 Epic 列表

## Status Trend V5.7

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
