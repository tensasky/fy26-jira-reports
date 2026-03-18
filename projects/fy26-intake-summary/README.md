# FY26 Intake Summary

自动化生成 CNTIN-730 FY26 Intakes Initiative 周报系统。

## 功能特性

- 📊 **数据抓取**: 从 Jira 自动抓取 CNTIN-730 下的所有 Initiative
- 🔍 **多维度筛选**: 支持 Status、Assignee、Label、Missing SLA 筛选
- 🔗 **超链接**: Key 可直接跳转到 Jira 详情页
- 📤 **导出功能**: 支持导出筛选后的数据为 CSV/Excel
- 📧 **邮件发送**: 自动生成并发送报告邮件
- ⏰ **定时任务**: 每周一自动执行

## 快速开始

### 1. 安装依赖

```bash
# Python 3.8+ 已内置所需库，无需额外安装
```

### 2. 配置

编辑 `scripts/generate_report.py` 中的配置区域：

```python
# Jira API 配置
JIRA_CONFIG = {
    "base_url": "https://lululemon.atlassian.net",
    "user_email": "your-email@lululemon.com",
    "api_token": "your-api-token"
}

# 邮件配置
EMAIL_CONFIG = {
    "smtp_server": "smtp.qq.com",
    "smtp_port": 587,
    "sender": "your-qq@qq.com",
    "password": "your-auth-code",
    "recipients": ["chinatechpmo@lululemon.com"],
    "cc": ["rcheng2@lululemon.com"]
}
```

### 3. 运行

```bash
cd projects/fy26-intake-summary
python3 scripts/generate_report.py
```

### 4. 查看报告

- HTML 报告: `reports/FY26{date}Intake.html`
- 日志: `logs/`

## 定时任务配置

### Linux/Mac (Cron)

```bash
# 编辑 crontab
crontab -e

# 添加每周一 15:00 执行
0 15 * * 1 /usr/bin/python3 /path/to/fy26-intake-summary/scripts/generate_report.py >> /path/to/fy26-intake-summary/logs/cron.log 2>&1
```

### Mac (LaunchAgent)

```bash
# 加载定时任务
launchctl load ~/Library/LaunchAgents/com.fy26.intake.summary.plist
```

## 项目结构

```
fy26-intake-summary/
├── scripts/
│   └── generate_report.py    # 主脚本
├── reports/                   # 生成的报告
├── logs/                      # 执行日志
├── docs/                      # 文档
└── config/                    # 配置文件
```

## 数据抓取逻辑

### JQL 查询

```sql
project = CNTIN 
AND parent = "CNTIN-730" 
AND status != Cancelled 
AND issuetype = Initiative
```

### 分页机制

- 每页最大: 100 条
- 自动分页: 支持多页数据合并
- 当前数据量: ~139 条

## 筛选功能

| 筛选类型 | 说明 |
|---------|------|
| Status | 状态筛选 (Discovery, Done, Execution, New...) |
| Assignee | 负责人筛选 (带数量徽章) |
| Label | 标签筛选 |
| Missing SLA | 更新时间>2周且状态≠Done |
| 关键词 | 搜索 Key, Summary, Description |

## Missing SLA 规则

```python
if status != 'Done' and days_since_updated > 14:
    mark_as_missing_sla()
```

## 邮件格式

- **主题**: `FY26{YYYYMMDD}Intake`
- **附件**: `FY26{YYYYMMDD}Intake.html`
- **收件人**: chinatechpmo@lululemon.com
- **抄送**: rcheng2@lululemon.com

## 导出格式

CSV 文件包含以下列：
- Key, Summary, Status, Assignee, Priority
- Creator, Reporter, Created, Updated, Due Date
- Description, Alerts

## 更新日志

### v1.0.0 (2026-03-16)
- 初始版本
- 完整的数据抓取、报告生成、邮件发送功能
- 多维度筛选和导出功能

## License

Internal Use Only - lululemon
