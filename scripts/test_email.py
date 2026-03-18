#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
EMAIL_SENDER = "3823810468@qq.com"
EMAIL_PASSWORD = "aqcstretdofvcefi"

# 发送到 Robert 的 lululemon 邮箱
EMAIL_RECIPIENT = "rcheng2@lululemon.com"

msg = MIMEMultipart()
msg['From'] = EMAIL_SENDER
msg['To'] = EMAIL_RECIPIENT
msg['Subject'] = "【测试】FY2620260316Intake 报告"

body = """Hi Roberto,

这是一封测试邮件，验证邮件发送功能是否正常。

如果收到此邮件，说明邮件配置正确，请检查 chinapmo@lululemon.com 的垃圾邮件箱。

测试时间: 2026-03-16
"""
msg.attach(MIMEText(body, 'plain'))

# 添加附件
with open('/Users/admin/.openclaw/workspace/reports/FY2620260316Intake.html', 'rb') as f:
    attachment = MIMEBase('application', 'octet-stream')
    attachment.set_payload(f.read())
    encoders.encode_base64(attachment)
    attachment.add_header('Content-Disposition', 'attachment; filename="FY2620260316Intake.html"')
    msg.attach(attachment)

with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    server.starttls()
    server.login(EMAIL_SENDER, EMAIL_PASSWORD)
    server.send_message(msg)

print(f"✅ 测试邮件已发送到 {EMAIL_RECIPIENT}")
