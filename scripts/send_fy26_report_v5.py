#!/usr/bin/env python3
"""
FY26_INIT 报告邮件发送脚本 v5.0
通过 QQ 邮箱发送 HTML 报告
"""

import os
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from datetime import datetime

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
REPORTS_DIR = WORKSPACE / "jira-reports"

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
FROM_EMAIL = "3823810468@qq.com"
FROM_PASSWORD = os.environ.get("QQ_MAIL_PASSWORD", "")  # 从环境变量读取
TO_EMAILS = [
    "chinatechpmo@lululemon.com",
    "rcheng2@lululemon.com"  # Roberto 的邮箱
]

def find_latest_report():
    """查找最新的 HTML 报告"""
    html_files = list(REPORTS_DIR.glob("fy26_daily_report_v4_*.html"))
    if not html_files:
        print("❌ 未找到 HTML 报告文件")
        return None
    
    # 按修改时间排序，返回最新的
    latest = max(html_files, key=lambda p: p.stat().st_mtime)
    return latest

def send_email(html_file):
    """发送邮件"""
    print(f"📧 准备发送邮件...")
    print(f"   HTML 报告: {html_file}")
    print(f"   收件人: {', '.join(TO_EMAILS)}")
    
    # 读取 HTML 内容
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 创建邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"FY26_INIT Epic 日报 - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = FROM_EMAIL
    msg['To'] = ', '.join(TO_EMAILS)
    
    # 添加 HTML 内容
    html_part = MIMEText(html_content, 'html', 'utf-8')
    msg.attach(html_part)
    
    # 添加附件
    with open(html_file, 'rb') as f:
        attachment = MIMEApplication(f.read(), _subtype='html')
        attachment.add_header('Content-Disposition', 'attachment', 
                            filename=html_file.name)
        msg.attach(attachment)
    
    # 发送邮件
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(FROM_EMAIL, FROM_PASSWORD)
            server.send_message(msg)
        
        print(f"✅ 邮件发送成功")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        return False

def main():
    print("📧 FY26_INIT 报告邮件发送 (v5.0)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("")
    
    # 检查密码
    if not FROM_PASSWORD:
        print("❌ 错误: 未设置 QQ_MAIL_PASSWORD 环境变量")
        sys.exit(1)
    
    # 查找最新报告
    html_file = find_latest_report()
    if not html_file:
        sys.exit(1)
    
    # 发送邮件
    if send_email(html_file):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == '__main__':
    main()
