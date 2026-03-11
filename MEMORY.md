# Tensasky 的长期记忆

## 配置记录

### Telegram 机器人配置 (2026-02-27)

**配置步骤：**
1. 从用户获取 Bot Token（格式：`123456789:ABCdef...`）
2. 编辑 `~/.openclaw/openclaw.json`，在 `channels` 段添加：
```json
"telegram": {
  "enabled": true,
  "botToken": "YOUR_BOT_TOKEN",
  "webhook": {
    "enabled": false
  },
  "polling": {
    "enabled": true
  }
}
```
3. 重启 Gateway：`openclaw gateway restart`
4. 验证状态：`openclaw status`（应显示 Telegram ON）
5. 用户首次发送消息后会收到配对码
6. 执行批准：`openclaw pairing approve telegram <CODE>`

**当前配置：**
- Bot: @roberto_helper_bot (Token 已存储在配置中)
- 配对用户 ID: 7952042326
- 状态: ✅ 正常运行

---

### Chrome CDP 抓取方式 (2026-02-27)

当 browser 工具因扩展冲突无法使用时，使用 Chrome DevTools Protocol 直接抓取。

**完整命令：**
```bash
# 1. 启动 Chrome
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=18800 \
  --remote-allow-origins='*' \
  --user-data-dir=/Users/admin/.openclaw/browser/openclaw/user-data \
  --no-first-run \
  --no-default-browser-check \
  "URL" > /dev/null 2>&1 &

# 2. 获取页面 ID
curl -s http://127.0.0.1:18800/json/list

# 3. 用 Python websocket 获取内容
```

详细文档：`memory/chrome-cdp-crawling.md`

---

### 用户偏好

- **姓名:** Roberto
- **时区:** Asia/Shanghai (GMT+8)
- **主要沟通渠道:** 飞书 (工作), Telegram (个人)
- **飞书 App ID:** cli_a91bd999acb8dbce

### PPT 制作风格原则 (2026-02-27)

**必须遵守的样式规范：**

| 元素 | 规范 |
|------|------|
| **背景** | 简约白色背景 |
| **视觉标识** | lululemon 红竖线 |
| **目标受众** | 交付团队 |

**设计原则：**
- ✅ 简洁专业，突出内容
- ✅ 使用 lululemon 品牌红 (#E31937) 作为点缀
- ✅ 适合技术/交付团队阅读的信息架构
- ❌ 避免花哨动画和复杂背景

---

## 版本管理 (重要！)

**规则：任何配置/技能变更必须按版本化管理流程执行**

### 变更流程 (SOP)
1. **变更前** - 备份当前配置
2. **变更中** - 执行具体操作
3. **变更后** - 按规范记录变更

### 记录位置
- `config/CONFIG-VERSIONS.md` - 完整版本快照
- `config/VERSION-GUIDE.md` - 变更规范
- `config/CHANGELOG.md` - 详细变更日志
- `config/backups/` - 配置文件备份

### 版本号规则
- MAJOR: 频道增删、架构变更
- MINOR: 新增技能、功能变更
- PATCH: 配置微调

**当前版本: v1.4.0**

### 必须执行的操作清单
```bash
# 1. 备份
 cp ~/.openclaw/openclaw.json config/backups/openclaw-vX.Y.Z-$(date +%Y%m%d).json

# 2. 修改配置/安装技能
 openclaw gateway restart

# 3. 更新版本文档 (CONFIG-VERSIONS.md)
# 4. 追加变更日志 (CHANGELOG.md)
# 5. 更新 MEMORY.md 中的当前版本号
```

**注意：不记录 = 没做。所有变更必须留痕。**

---

## FY26_INIT Epic 日报任务 (永久记忆 - 2026-03-11)

**⚠️ 重要任务 - 不可遗忘**

### 任务概览
- **任务名称**: FY26_INIT Epic 日报
- **执行频率**: 每天晚上 6:00 (18:00)
- **收件人**: chinatechpmo@lululemon.com
- **发件人**: 3823810468@qq.com (QQ 邮箱)
- **当前版本**: v5.0（2026-03-11 重大更新 - SQLite 架构）

### 技术配置（v5.0 - SQLite 架构）
- **数据库**: `~/.openclaw/workspace/jira-reports/fy26_data.db`
- **数据抓取**: `/Users/admin/.openclaw/workspace/scripts/fetch_fy26_v5.py`
- **报告生成**: `/Users/admin/.openclaw/workspace/scripts/generate_fy26_report_v5.py`
- **HTML 生成**: `/Users/admin/.openclaw/workspace/scripts/generate_fy26_html_v5.py`
- **数据库架构**: `/Users/admin/.openclaw/workspace/scripts/fy26_db_schema.sql`
- **邮件发送**: `/Users/admin/.openclaw/workspace/scripts/send_fy26_report_qq.py`
- **定时任务**: `~/Library/LaunchAgents/com.openclaw.fy26-daily-report.plist`
- **执行日志**: `/Users/admin/.openclaw/workspace/logs/fy26_daily_report.log`

### 邮件配置
- **SMTP**: smtp.qq.com:587
- **邮箱**: 3823810468@qq.com
- **密码**: 已配置在定时任务中

### 架构重构（v5.0 - 2026-03-11）

**重大改进：从 JSON 文件迁移到 SQLite 数据库**

**问题背景：**
- v4.x 版本使用 JSON 文件合并，频繁出现数据丢失
- 多个项目的 Epic 抓取不完整（CNDIN、EPCH、CNRTPRJ、SWMP 等）
- JSON 合并逻辑复杂且不可靠

**新架构优势：**
1. **数据持久化** - 所有数据存储在 SQLite 数据库中
2. **避免数据丢失** - 不再依赖 JSON 文件合并
3. **可查询** - 支持 SQL 查询，方便调试和验证
4. **可重复生成** - 报告可以从数据库重复生成，无需重新抓取

**数据库表结构：**
- `epics` - 其他项目的 Epic（key, project, summary, status, assignee, parent_key, created, labels）
- `features` - CNTIN Feature（key, summary, status, assignee, parent_key, labels）
- `initiatives` - CNTIN Initiative（key, summary, status, assignee, labels）
- `fetch_log` - 抓取日志（project, issue_type, count, status, error_message）

### 数据结构（v5.0 - 正确版本）
**重要：CNTIN 项目没有 Epic！**

- **CNTIN 项目**: Initiative → Feature（无 Epic）
- **其他项目**: Epic（通过 parent 字段关联到 CNTIN Feature）

**所有需要查询的 Jira 项目（22 个）：**

**Epic 项目（22 个）：**
1. **CNTEC** - China Tech E-Commerce
2. **CNTOM** - China Tech Order Management
3. **CNTDM** - China Tech Data & Marketing
4. **CNTMM** - China Tech Membership & Marketing
5. **CNTD** - China Tech Data
6. **CNTEST** - China Test
7. **CNENG** - China Engineering
8. **CNINFA** - China Infrastructure
9. **CNCA** - China Customer Analytics
10. **CPR** - China Product
11. **EPCH** - Enterprise Platform China
12. **CNCRM** - China CRM
13. **CNDIN** - China Digital Innovation
14. **SWMP** - Software Marketplace
15. **CDM** - China Data Management
16. **CMDM** - China Master Data Management
17. **CNSCM** - China Supply Chain Management
18. **OF** - Order Fulfillment
19. **CNRTPRJ** - China Retail Project
20. **CSCPVT** - China Supply Chain Private
21. **CNPMO** - China PMO
22. **CYBERPJT** - Cyber Project

**扫描逻辑（v5.0）：**
1. 从 22 个 Epic 项目抓取所有 Epic（不过滤标签）
2. 通过 Epic 的 parent 字段找到关联的 CNTIN Feature
3. 通过 Feature 的 parent 字段找到 CNTIN Initiative
4. 额外抓取所有带 FY26_INIT 标签的 CNTIN Feature 和 Initiative

**当前统计（2026-03-11 15:32）：**
- **总 Initiatives**: 50 个
- **总 Features**: 53 个
- **总 Epics**: 85 个（11 个项目有 Epic）
  - CNTEC: 17 个
  - OF: 17 个
  - EPCH: 16 个
  - CNDIN: 9 个
  - CNTOM: 9 个
  - CNTDM: 5 个
  - CNRTPRJ: 4 个
  - SWMP: 3 个
  - CNTMM: 3 个
  - CNENG: 1 个
  - CNTD: 1 个
- **已关联的 Epics**: 50 个
- **孤儿 Feature**: 3 个
- **孤儿 Initiative**: 0 个

**无 Epic 的项目（11 个）：**
CNTEST, CNINFA, CNCA, CPR, CNCRM, CDM, CMDM, CNSCM, CSCPVT, CNPMO, CYBERPJT

### 管理命令（v5.0）
```bash
# 查看定时任务状态
launchctl list | grep fy26

# 手动执行完整流程（抓取 + 生成报告 + 发送邮件）
/Users/admin/.openclaw/workspace/scripts/fy26_daily_report.sh

# 仅抓取数据（存入数据库）
python3 /Users/admin/.openclaw/workspace/scripts/fetch_fy26_v5.py

# 仅生成报告（从数据库读取）
python3 /Users/admin/.openclaw/workspace/scripts/generate_fy26_report_v5.py

# 生成 HTML 报告
python3 /Users/admin/.openclaw/workspace/scripts/generate_fy26_html_v5.py

# 查看数据库统计
sqlite3 ~/.openclaw/workspace/jira-reports/fy26_data.db "SELECT project, COUNT(*) FROM epics GROUP BY project ORDER BY COUNT(*) DESC"

# 查看某个项目的 Epic
sqlite3 ~/.openclaw/workspace/jira-reports/fy26_data.db "SELECT key, summary FROM epics WHERE project = 'SWMP'"

# 查看抓取日志
sqlite3 ~/.openclaw/workspace/jira-reports/fy26_data.db "SELECT * FROM fetch_log ORDER BY fetched_at DESC LIMIT 10"

# 查看执行日志
tail -f /Users/admin/.openclaw/workspace/logs/fy26_daily_report.log

# 停止/启动定时任务
launchctl unload ~/Library/LaunchAgents/com.openclaw.fy26-daily-report.plist
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-daily-report.plist
```

### 版本历史
- **v1.0** (2026-03-10): 初始版本，错误的数据结构
- **v2.0** (2026-03-11): 尝试反向扫描，但仍然错误
- **v3.0** (2026-03-11): ✅ 正确的数据结构和扫描逻辑
- **v4.0-v4.7** (2026-03-11): 多次修复 JSON 合并 bug，但仍有数据丢失
- **v5.0** (2026-03-11): ✅ **重大重构 - SQLite 架构**
  - 使用 SQLite 数据库替代 JSON 文件
  - 彻底解决数据丢失问题
  - 支持数据持久化和重复查询
  - 修复了所有项目的 Epic 抓取问题

### 故障排查

**问题：某个项目的 Epic 没有抓到**
```bash
# 1. 检查数据库中是否有该项目的数据
sqlite3 ~/.openclaw/workspace/jira-reports/fy26_data.db "SELECT * FROM epics WHERE project = 'PROJECT_KEY'"

# 2. 检查抓取日志
sqlite3 ~/.openclaw/workspace/jira-reports/fy26_data.db "SELECT * FROM fetch_log WHERE project = 'PROJECT_KEY'"

# 3. 手动测试 API 请求
source ~/.openclaw/workspace/.jira-config
curl -s -H "Authorization: Basic $JIRA_AUTH" "$JIRA_URL/rest/api/3/search?jql=project%20%3D%20PROJECT_KEY%20AND%20issuetype%20%3D%20Epic&maxResults=10" | jq .

# 4. 重新抓取该项目
python3 /Users/admin/.openclaw/workspace/scripts/fetch_fy26_v5.py
```

**问题：报告数据不对**
```bash
# 1. 检查数据库统计
sqlite3 ~/.openclaw/workspace/jira-reports/fy26_data.db << SQL
SELECT 'Epics' as type, COUNT(*) as count FROM epics
UNION ALL
SELECT 'Features', COUNT(*) FROM features
UNION ALL
SELECT 'Initiatives', COUNT(*) FROM initiatives;
SQL

# 2. 重新生成报告
python3 /Users/admin/.openclaw/workspace/scripts/generate_fy26_report_v5.py
python3 /Users/admin/.openclaw/workspace/scripts/generate_fy26_html_v5.py
```

---

*最后更新: 2026-03-11*
