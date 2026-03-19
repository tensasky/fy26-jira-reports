#!/bin/bash
# CNTIN-730 Initiative 周报定时任务脚本
# 每天中午 12:00 执行
# 收件人: chinatechpmo@lululemon.com

export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:$PATH"
export HOME="/Users/admin"

# 日志文件
LOG_FILE="$HOME/.openclaw/workspace/logs/cntin730_cron.log"
REPORTS_DIR="$HOME/.openclaw/workspace/reports"

# 记录开始时间
echo "========================================" >> "$LOG_FILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') CNTIN-730 周报生成开始" >> "$LOG_FILE"

# 进入工作目录
cd "$HOME/.openclaw/workspace"

# 生成报告
echo "$(date '+%Y-%m-%d %H:%M:%S') 正在生成报告..." >> "$LOG_FILE"
python3 scripts/cntin730_weekly_report.py >> "$LOG_FILE" 2>&1

# 检查报告是否生成成功
LATEST_REPORT=$(ls -t "$REPORTS_DIR"/cntin_730_report_*.html 2>/dev/null | head -1)

if [ -z "$LATEST_REPORT" ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ❌ 报告生成失败" >> "$LOG_FILE"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') ✅ 报告生成成功: $LATEST_REPORT" >> "$LOG_FILE"

# 发送邮件
python3 << 'PYEOF'
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from datetime import datetime
import os

# 配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
SENDER_EMAIL = "3823810468@qq.com"
SENDER_PASSWORD = os.environ.get("QQ_MAIL_PASSWORD", "ftbabipdlxliceai")
RECIPIENTS = ["chinatechpmo@lululemon.com"]
CC_RECIPIENTS = []

# 找到最新报告
reports_dir = Path("/Users/admin/.openclaw/workspace/reports")
latest_report = max(reports_dir.glob("cntin_730_report_*.html"), key=lambda p: p.stat().st_mtime)

# 创建邮件
msg = MIMEMultipart()
msg['From'] = SENDER_EMAIL
msg['To'] = ', '.join(RECIPIENTS)
msg['Subject'] = f"CNTIN-730 Initiative Weekly Report - {datetime.now().strftime('%Y-%m-%d')}"

# 邮件正文
body = f"""
Hi Team,

请查收今日 CNTIN-730 Initiative 周报。

报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
数据来源: Jira API

如有问题请联系 China Tech PMO。

Best,
OpenClaw Automation
"""
msg.attach(MIMEText(body, 'plain', 'utf-8'))

# 附件
with open(latest_report, 'rb') as f:
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(f.read())
    encoders.encode_base64(attachment)
    attachment.add_header(
        'Content-Disposition',
        f'attachment; filename="{latest_report.name}"'
    )
    msg.attach(attachment)

# 发送
with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(SENDER_EMAIL, SENDER_PASSWORD)
    server.sendmail(SENDER_EMAIL, RECIPIENTS, msg.as_string())

print(f"✅ 邮件发送成功: {latest_report.name}")
PYEOF

if [ $? -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') ✅ 邮件发送成功" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') ❌ 邮件发送失败" >> "$LOG_FILE"
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') 任务完成" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
