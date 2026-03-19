# FY26_INIT Epic 日报 - 邮件发送配置指南

## 当前状态
- 报告生成: ✅ 正常
- 邮件发送: ⚠️ 需要配置

## 邮件发送方式（按优先级）

### 方式1: Office 365 SMTP（推荐）

**优点**: 最可靠，直接通过 lululemon 邮件服务器发送

**配置步骤**:

1. 设置环境变量（添加到你的 ~/.zshrc 或 ~/.bash_profile）:
```bash
export O365_PASSWORD='你的邮箱密码'
```

2. 重新加载配置:
```bash
source ~/.zshrc
```

3. 更新定时任务脚本，使用 o365 版本:
```bash
# 编辑脚本
nano /Users/admin/.openclaw/workspace/scripts/fy26_daily_report.sh

# 修改邮件发送部分，使用 send_fy26_report_o365.py
```

### 方式2: 配置本地邮件服务器

**安装 postfix**:
```bash
# macOS
brew install postfix

# 配置 postfix 使用外部 SMTP
sudo nano /etc/postfix/main.cf

# 添加以下配置
relayhost = [smtp.office365.com]:587
smtp_sasl_auth_enable = yes
smtp_sasl_password_maps = hash:/etc/postfix/sasl_passwd
smtp_sasl_security_options = noanonymous
smtp_tls_security_level = encrypt
```

### 方式3: 使用现有邮件客户端

如果不配置 SMTP，报告仍会每天生成并保存到:
```
/Users/admin/.openclaw/workspace/jira-reports/fy26_daily_report_YYYYMMDD_HHMMSS.html
```

你可以:
1. 手动打开报告文件
2. 复制内容或附件
3. 通过 Outlook/其他邮件客户端发送

## 测试邮件发送

### 测试 Office 365 SMTP
```bash
export O365_PASSWORD='你的密码'
python3 /Users/admin/.openclaw/workspace/scripts/send_fy26_report_o365.py \
    /Users/admin/.openclaw/workspace/jira-reports/fy26_daily_report_*.html \
    rcheng2@lululemon.com
```

### 测试本地 mail 命令
```bash
echo "测试邮件" | mail -s "测试" rcheng2@lululemon.com
```

## 安全建议

1. **不要将密码硬编码在脚本中**
   - 使用环境变量
   - 或使用 macOS Keychain

2. **使用应用专用密码**（如果 Office 365 启用了 MFA）
   - 登录 https://account.activedirectory.windowsazure.com/
   - 生成应用密码
   - 使用应用密码代替主密码

3. **限制脚本权限**
   ```bash
   chmod 700 /Users/admin/.openclaw/workspace/scripts/send_fy26_report_o365.py
   ```

## 故障排查

### 问题: "SMTP AUTH extension not supported"
**解决**: 确保使用正确的端口 (587) 和 STARTTLS

### 问题: "Authentication unsuccessful"
**解决**: 
- 检查用户名和密码
- 如果使用 MFA，需要生成应用密码
- 检查账户是否允许 SMTP 发送

### 问题: "Connection refused"
**解决**: 检查网络连接，或尝试使用 VPN

## 联系支持

如果配置遇到问题，可以:
1. 联系 lululemon IT 部门获取 SMTP 配置
2. 使用手动发送方式
3. 配置其他邮件服务（如 SendGrid、AWS SES）
