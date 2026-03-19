# CNTIN-730 FY26 Intakes 周报系统

> 自动化生成 CNTIN-730 Initiative 周报，包含统计卡片、Assignee 筛选、冻结列、行展开、Excel 导出功能。

## 版本信息

- **当前版本**: v5.2
- **最后更新**: 2026-03-19
- **作者**: OpenClaw

## 功能特性

- ✅ **统计卡片**: 显示 Total、Done、Discovery、Missing SLA 统计
- ✅ **Assignee 筛选**: 点击负责人按钮快速筛选
- ✅ **状态筛选**: 按 Status 筛选，支持 Missing SLA 告警筛选
- ✅ **Label 筛选**: 按标签筛选
- ✅ **冻结列**: Key/Summary、Status、Assignee 列固定
- ✅ **行展开**: 点击行展开显示完整 Summary、Description 和 AI Summary
- ✅ **AI Summary**: 自动从 Description 提取 What/Why
- ✅ **Excel 导出**: 一键导出当前筛选结果到 CSV

## 数据结构

- **Parent**: CNTIN-730
- **Issue Type**: Initiative
- **Status**: ≠ Cancelled

## 使用方式

### 手动执行

```bash
# 设置环境变量
export JIRA_EMAIL="rcheng2@lululemon.com"
export JIRA_API_TOKEN="your_token"

# 执行脚本
python3 scripts/cntin730_report.py
```

### 定时任务

每周一至周五中午 12:00 自动执行，发送报告邮件。

## 报告输出

- **文件**: `CNTIN-730_FY26_Intakes_Report_Latest.html`
- **位置**: `~/.openclaw/workspace/reports/`

## AI Summary 逻辑

根据 Description 内容智能提取：

- **What**: 寻找 "aim to/build/develop/implement/构建/开发" 等关键词
- **Why**: 寻找 "because/to enable/benefit/为了/以便" 等关键词

## 依赖

- Python 3.9+
- requests
- 飞书 / QQ 邮箱（用于发送）

## 配置

编辑 `~/.openclaw/workspace/.jira-config`:

```bash
JIRA_BASE_URL="https://lululemon.atlassian.net"
JIRA_USER_EMAIL="rcheng2@lululemon.com"
JIRA_API_TOKEN="your_token"
```

## 历史版本

| 版本 | 日期 | 说明 |
|------|------|------|
| v5.2 | 2026-03-19 | 修复展开功能，完整显示 Summary/Description，AI Summary 自动生成 |
| v5.1 | 2026-03-18 | 移除 Creator/Reporter，优化列宽，Alerts 改为图标 |
| v5.0 | 2026-03-12 | SQLite 架构，持久化存储 |

## 许可证

Internal Use Only - lululemon China Tech
