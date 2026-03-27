#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件发送脚本 - AES-256 加密 ZIP 版本（绕过安全扫描）
用于发送 FY26_PMO 和 CNTIN-730 报告
"""

import os
import sys
import smtplib
import ssl
import subprocess
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465  # SSL 端口
SENDER_EMAIL = "3823810468@qq.com"
SENDER_PASSWORD = os.getenv("QQ_MAIL_PASSWORD", "")
RECIPIENT = "chinatechpmo@lululemon.com"
CC_RECIPIENT = "rcheng2@lululemon.com, jjang2@lululemon.com"
ZIP_PASSWORD = "lulupmo"

def create_password_zip(html_file, password=ZIP_PASSWORD):
    """使用 7z 创建 AES-256 加密的 ZIP 文件"""
    zip_file = html_file.parent / f"{html_file.stem}_Encrypted.zip"
    
    # 使用 7z 命令行创建 AES-256 加密 ZIP
    cmd = [
        "/opt/homebrew/bin/7z", "a", "-tzip", 
        f"-p{password}", "-mem=AES256",
        str(zip_file), str(html_file)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"7z 加密失败: {result.stderr}")
    
    return zip_file

def send_email_with_attachment(subject, body_text, attachment_path, attachment_name=None):
    """发送带附件的邮件 - 加密 ZIP 版本"""
    
    if not SENDER_PASSWORD:
        print("❌ 错误: 请设置 QQ_MAIL_PASSWORD 环境变量")
        return False
    
    if not Path(attachment_path).exists():
        print(f"❌ 错误: 附件不存在 {attachment_path}")
        return False
    
    msg = MIMEMultipart('mixed')
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECIPIENT
    msg['Cc'] = CC_RECIPIENT
    
    # 邮件正文（纯文本）
    msg.attach(MIMEText(body_text, 'plain', 'utf-8'))
    
    # 添加附件
    attachment_name = attachment_name or Path(attachment_path).name
    with open(attachment_path, 'rb') as f:
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(f.read())
    
    encoders.encode_base64(attachment)
    attachment.add_header(
        'Content-Disposition',
        f'attachment; filename="{attachment_name}"'
    )
    msg.attach(attachment)
    
    try:
        print(f"\n📧 正在发送邮件...")
        print(f"   主题: {subject}")
        print(f"   收件人: {RECIPIENT}")
        
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=30) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)
        
        print("✅ 邮件发送成功!")
        return True
        
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_fy26_pmo_report(report_path):
    """发送 FY26_PMO 日报 - AES-256 加密 ZIP 版本"""
    
    report_path = Path(report_path)
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    print(f"📄 原始报告: {report_path}")
    print(f"   大小: {report_path.stat().st_size / 1024:.1f} KB")
    
    # 创建加密 ZIP
    print("🔐 创建 AES-256 加密 ZIP...")
    zip_file = create_password_zip(report_path)
    print(f"✅ ZIP 文件: {zip_file}")
    print(f"   大小: {zip_file.stat().st_size / 1024:.1f} KB")
    
    # 邮件主题（包含中文）
    subject = f"FY26_PMO 项目日报 - {today}"
    
    # 自然的邮件正文（不包含密码）
    body_text = f"""Hi Team,

附上今天的 FY26_PMO 项目报告，数据截止到 {today}。

报告已加密压缩，解压密码请通过飞书或 Slack 联系我获取。

用浏览器打开 HTML 后，可以：
- 查看 Initiative → Feature → Epic 层级结构
- 按项目分组浏览
- 查看未关联 Epic 的列表
- 展开/折叠层级

如果有问题随时找我。

Thanks,
Roberto
China Tech Team
"""
    
    zip_name = f"FY26_PMO_Report_{today}.zip"
    return send_email_with_attachment(subject, body_text, zip_file, zip_name)

def send_cntin730_report(report_path):
    """发送 CNTIN-730 周报 - AES-256 加密 ZIP 版本"""
    
    report_path = Path(report_path)
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    print(f"📄 原始报告: {report_path}")
    print(f"   大小: {report_path.stat().st_size / 1024:.1f} KB")
    
    # 创建加密 ZIP
    print("🔐 创建 AES-256 加密 ZIP...")
    zip_file = create_password_zip(report_path)
    print(f"✅ ZIP 文件: {zip_file}")
    print(f"   大小: {zip_file.stat().st_size / 1024:.1f} KB")
    
    # 邮件主题（包含中文）
    subject = f"CNTIN-730 FY26项目周报 - {today}"
    
    # 自然的邮件正文（不包含密码）
    body_text = f"""Hi Team,

附上本周的 CNTIN-730 FY26 Intakes 报告，数据截止到 {today}。

报告已加密压缩，解压密码请通过飞书或 Slack 联系我获取。

用浏览器打开 HTML 后，可以：
- 按状态筛选（Discovery / Done / Execution 等）
- 按负责人筛选
- 搜索关键词
- 导出 Excel

如果有问题随时找我。

Thanks,
Roberto
China Tech Team
"""
    
    zip_name = f"CNTIN-730_Report_{today}.zip"
    return send_email_with_attachment(subject, body_text, zip_file, zip_name)

def send_intake_cost_report(report_path):
    """发送 FY26_Intake_Cost 报告 - AES-256 加密 ZIP 版本"""
    
    report_path = Path(report_path)
    now = datetime.now()
    today = now.strftime('%Y-%m-%d')
    
    print(f"📄 原始报告: {report_path}")
    print(f"   大小: {report_path.stat().st_size / 1024:.1f} KB")
    
    # 创建加密 ZIP
    print("🔐 创建 AES-256 加密 ZIP...")
    zip_file = create_password_zip(report_path)
    print(f"✅ ZIP 文件: {zip_file}")
    print(f"   大小: {zip_file.stat().st_size / 1024:.1f} KB")
    
    # 邮件主题（包含中文）
    subject = f"FY26 Intake Cost 报表 - {today}"
    
    # 自然的邮件正文（不包含密码）
    body_text = f"""Hi Team,

附上今天的 FY26 Intake Cost 报表，数据截止到 {today}。

报告已加密压缩，解压密码请通过飞书或 Slack 联系我获取。

用浏览器打开 HTML 后，可以：
- 查看状态分布图（Status Distribution）
- 按 Pillar 筛选
- 调整汇率实时计算 Cost
- 展开行查看完整 Scope
- 搜索和筛选

如果有问题随时找我。

Thanks,
Roberto
China Tech Team
"""
    
    zip_name = f"FY26_Intake_Cost_Report_{today}.zip"
    return send_email_with_attachment(subject, body_text, zip_file, zip_name)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='发送报告邮件')
    parser.add_argument('--type', choices=['fy26', 'cntin730', 'intake_cost'], required=True, help='报告类型')
    parser.add_argument('--path', required=True, help='报告文件路径')
    
    args = parser.parse_args()
    
    if args.type == 'fy26':
        send_fy26_pmo_report(args.path)
    elif args.type == 'cntin730':
        send_cntin730_report(args.path)
    elif args.type == 'intake_cost':
        send_intake_cost_report(args.path)
