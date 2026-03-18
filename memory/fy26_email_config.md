# Tensasky 长期记忆 - 邮件配置更新 (2026-03-10)

## FY26_INIT Epic 日报邮件发送配置

### 当前状态
- ✅ 报告生成: 正常
- ⚠️ 邮件发送: 需要配置 SMTP 密码

### 邮件发送方式（优先级）

1. **Office 365 SMTP** (推荐)
   - 需要设置环境变量: `export O365_PASSWORD='your_password'`
   - 脚本: `send_fy26_report_o365.py`

2. **本地 mail 命令** (备用)
   - 不需要额外配置
   - 依赖系统邮件配置
   - 可能无法直接发送到外部邮箱

3. **手动发送**
   - 报告每天生成在: `/Users/admin/.openclaw/workspace/jira-reports/`
   - 可以手动复制内容发送

### 配置步骤

```bash
# 1. 设置 Office 365 密码
export O365_PASSWORD='your_password'

# 2. 添加到 ~/.zshrc 使其持久化
echo 'export O365_PASSWORD="your_password"' >> ~/.zshrc

# 3. 测试邮件发送
python3 /Users/admin/.openclaw/workspace/scripts/send_fy26_report_o365.py \
    /Users/admin/.openclaw/workspace/jira-reports/fy26_daily_report_*.html \
    rcheng2@lululemon.com
```

### 文件清单
- 主脚本: `/Users/admin/.openclaw/workspace/scripts/fy26_daily_report.sh`
- O365 发送脚本: `/Users/admin/.openclaw/workspace/scripts/send_fy26_report_o365.py`
- 通用发送脚本: `/Users/admin/.openclaw/workspace/scripts/send_fy26_report.py`
- 配置指南: `/Users/admin/.openclaw/workspace/config/email_setup_guide.md`

### 注意事项
- 如果使用 MFA，需要生成应用专用密码
- 密码不要硬编码，使用环境变量
- 定时任务已设置，每天晚上 6:00 执行
