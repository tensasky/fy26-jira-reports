# Tensasky 长期记忆 - FY26_INIT Epic 日报任务 (2026-03-10)

## 任务配置
- **任务名称**: FY26_INIT Epic 日报
- **执行频率**: 每天晚上 6:00 (18:00)
- **收件人**: chinatechpmo@lululemon.com
- **发件人**: 3823810468@qq.com (QQ 邮箱)
- **任务类型**: 定时邮件发送

## 技术实现
- **脚本路径**: `/Users/admin/.openclaw/workspace/scripts/fy26_daily_report.sh`
- **QQ 发送脚本**: `/Users/admin/.openclaw/workspace/scripts/send_fy26_report_qq.py`
- **配置文件**: `/Users/admin/.openclaw/workspace/config/fy26_report_config.md`
- **定时任务**: `~/Library/LaunchAgents/com.openclaw.fy26-daily-report.plist`
- **执行日志**: `/Users/admin/.openclaw/workspace/logs/fy26_daily_report.log`

## 邮件配置
- **SMTP 服务器**: smtp.qq.com:587
- **邮箱**: 3823810468@qq.com
- **密码类型**: QQ 邮箱独立密码
- **密码**: aqcstretdofvcefi（已配置在定时任务中）

## 报告内容
- **数据源**: CNTIN 项目 FY26_INIT 标签的 Initiatives
- **层级结构**: Initiative → Feature → Epic（跨项目）
- **包含信息**:
  - Initiative/Feature/Epic 标题和状态
  - 负责人信息
  - Plan Start/End Date（如有）
  - Scope (Labels + Components)
  - 创建时间
  
## 报告特点
- ✅ 显示所有 53 个 Initiatives
- ⚠️ Warning 标记（50 个无 Epic 的 Initiative）
- 🔍 筛选功能（全部/有 Epic/无 Epic）
- 🎨 红色系背景层级显示
- 📊 数据统计摘要

## 数据统计
- 总 Initiatives: **53**
- 有 Epic 的: **3** (CNTIN-680, CNTIN-686, CNTIN-924)
- 无 Epic 的: **50**
- 总 Features: **100**
- 总 Epics: **34**
- 涉及项目: **5** (CNDIN, CNTD, EPCH, OF, RMS)

## 版本信息
- **当前版本**: v1.0.0
- **创建日期**: 2026-03-10
- **邮件配置更新**: 2026-03-10（切换到 QQ 邮箱）

## 管理命令
```bash
# 查看任务状态
launchctl list | grep fy26

# 手动执行
/Users/admin/.openclaw/workspace/scripts/fy26_daily_report.sh

# 查看日志
tail -f /Users/admin/.openclaw/workspace/logs/fy26_daily_report.log

# 停止任务
launchctl unload ~/Library/LaunchAgents/com.openclaw.fy26-daily-report.plist

# 启动任务
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-daily-report.plist

# 测试邮件发送
export QQ_EMAIL_PASSWORD="aqcstretdofvcefi"
python3 /Users/admin/.openclaw/workspace/scripts/send_fy26_report_qq.py \
    /Users/admin/.openclaw/workspace/jira-reports/fy26_daily_report_*.html \
    rcheng2@lululemon.com
```

## 维护记录
- 2026-03-10: 初始版本部署
- 2026-03-10: 配置 QQ 邮箱 SMTP，测试发送成功

## 更新计划
- [ ] 添加更多自定义字段支持
- [ ] 添加数据趋势分析
- [ ] 支持邮件模板自定义
- [ ] 添加异常告警机制
