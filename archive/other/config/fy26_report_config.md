# FY26_INIT Epic 报告自动化任务配置
# 创建时间: 2026-03-10
# 版本: v1.0.0

## 任务说明
- 任务名称: FY26_INIT Epic 日报
- 执行频率: 每天 18:00 (晚上6点)
- 收件人: chinatechpmo@lululemon.com
- 报告内容: CNTIN FY26_INIT Initiatives 层级结构

## 版本历史

### v1.0.0 (2026-03-10)
- 初始版本
- 支持所有 Initiatives 显示（包括无 Epic 的）
- 添加 Warning 标记功能
- 支持筛选：全部 / 有 Epic / 无 Epic
- 红色系背景层级显示
- 包含 Plan Start/End Date（如有）
- 包含 Scope、负责人、状态等信息

## 数据依赖
- Jira API Token: 已配置在 ~/.jira-config
- 源数据项目: CNTIN (Initiatives), 其他项目 (Epics)
- 标签筛选: FY26_INIT

## 报告统计
- 总 Initiatives: 53
- 有 Epic 的: 3 (CNTIN-680, CNTIN-686, CNTIN-924)
- 无 Epic 的: 50
- 总 Features: 100
- 总 Epics: 34
- 涉及项目: 5 (CNDIN, CNTD, EPCH, OF, RMS)

## 技术栈
- 语言: Python 3 + Bash
- API: Jira REST API v3
- 输出格式: HTML (内嵌 CSS + JavaScript)
- 邮件: mail 命令

## 维护信息
- 脚本路径: /Users/admin/.openclaw/workspace/scripts/fy26_daily_report.sh
- 报告保存: /Users/admin/.openclaw/workspace/jira-reports/
- 日志文件: /Users/admin/.openclaw/workspace/logs/fy26_daily_report.log

## 更新计划
- [ ] 添加更多自定义字段支持
- [ ] 添加数据趋势分析
- [ ] 支持邮件模板自定义
- [ ] 添加异常告警机制
