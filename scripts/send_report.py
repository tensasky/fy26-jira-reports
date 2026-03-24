#!/usr/bin/env python3
"""
CNTIN-730 报告邮件发送脚本
发送最新生成的报告到指定收件人
"""

import smtplib
import os
import ssl
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

def send_report():
    # 配置
    sender_email = os.getenv("QQ_EMAIL_SENDER", "3823810468@qq.com")
    sender_password = os.getenv("QQ_EMAIL_PASSWORD", "")
    recipient = "chinatechpmo@lululemon.com"
    cc = "rcheng2@lululemon.com"
    
    print(f"📧 发件人: {sender_email}")
    print(f"📧 收件人: {recipient}")
    print(f"📧 抄送: {cc}")
    
    # 找到最新报告
    workspace = Path.home() / ".openclaw" / "workspace"
    report_file = workspace / "reports" / "CNTIN-730_FY26_Intakes_Report_Latest.html"
    
    if not report_file.exists():
        print(f"❌ 报告文件不存在: {report_file}")
        return False
    
    print(f"📄 报告文件: {report_file}")
    print(f"📄 文件大小: {report_file.stat().st_size / 1024:.1f} KB")
    
    # 读取报告内容
    with open(report_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 创建邮件
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"[CNTIN-730 周报] FY26 Intakes 报告 - {datetime.now().strftime('%Y-%m-%d')}"
    msg['From'] = sender_email
    msg['To'] = recipient
    msg['Cc'] = cc
    
    # 添加 HTML 内容
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))
    
    # 发送邮件
    try:
        print("🔌 连接 SMTP 服务器...")
        context = ssl.create_default_context()
        
        with smtplib.SMTP_SSL('smtp.qq.com', 465, context=context) as server:
            print("✅ 连接成功")
            print("🔑 登录中...")
            server.login(sender_email, sender_password)
            print("✅ 登录成功")
            print("📤 发送邮件...")
            server.send_message(msg)
        
        print(f"✅ 邮件发送成功: {recipient}")
        return True
    except Exception as e:
        print(f"❌ 邮件发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    send_report()
