# FY26_INIT Epic 日报 - 产品需求文档 (PRD)

**文档版本**: v5.0.0  
**创建日期**: 2026-03-18  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 产品概述

### 1.1 产品目标
构建一个自动化的日报系统，从 22 个 Jira 项目抓取 FY26_INIT 相关的 Epic、Feature 和 Initiative 数据，生成可视化的 HTML 报告，并自动发送给 PMO 团队。

### 1.2 用户画像

#### 主要用户: China Tech PMO
- **角色**: 项目经理、项目协调员
- **目标**: 快速了解所有 FY26 项目的 Epic 状态
- **痛点**: 手动收集 22 个项目的数据太耗时
- **使用场景**: 每天查看邮件中的日报，跟踪项目进展

#### 次要用户: 技术负责人
- **角色**: Roberto Cheng 等技术领导
- **目标**: 监督整体项目健康状况
- **使用场景**: 查看 SLA Alert，识别风险项目

### 1.3 产品范围

**包含**:
- 22 个 Jira 项目的 Epic 数据抓取
- CNTIN 项目的 Feature 和 Initiative 抓取
- SQLite 数据持久化存储
- 交互式 HTML 报告生成
- 自动邮件发送
- 定时任务调度

**不包含**:
- 实时数据同步（日报级别）
- 数据编辑功能（只读报告）
- 多语言支持（仅英文）
- 移动端 App（仅响应式 Web）

---

## 2. 功能规格

### 2.1 数据抓取模块

#### 2.1.1 Jira API 集成
```python
# 核心 API 调用
GET /rest/api/3/search
Params:
  - jql: project in (CNTEC, CNTOM, ...) AND issuetype = Epic
  - fields: summary, status, assignee, parent, created, updated, labels
  - maxResults: 100
  - startAt: 0, 100, 200...
```

**分页处理**:
- 每次最多 100 条记录
- 自动处理分页直到获取所有数据
- 错误时指数退避重试

#### 2.1.2 数据映射

| Jira 字段 | 数据库字段 | 转换逻辑 |
|-----------|-----------|----------|
| key | key | 直接存储 |
| fields.summary | summary | 直接存储 |
| fields.status.name | status | 直接存储 |
| fields.assignee.displayName | assignee | 空值处理为 "-" |
| fields.parent.key | parent_key | 关联上级 |
| fields.created | created | ISO 8601 格式 |
| fields.labels | labels | JSON 数组转字符串 |

### 2.2 数据存储模块

#### 2.2.1 SQLite 架构

```sql
-- epics 表
CREATE TABLE epics (
    key TEXT PRIMARY KEY,
    project TEXT NOT NULL,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    parent_key TEXT,
    created TEXT,
    labels TEXT
);

-- features 表
CREATE TABLE features (
    key TEXT PRIMARY KEY,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    parent_key TEXT,
    labels TEXT
);

-- initiatives 表
CREATE TABLE initiatives (
    key TEXT PRIMARY KEY,
    summary TEXT,
    status TEXT,
    assignee TEXT,
    labels TEXT
);

-- 抓取日志表
CREATE TABLE fetch_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT,
    issue_type TEXT,
    count INTEGER,
    status TEXT,
    error_message TEXT,
    fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 2.2.2 数据生命周期

```
每次执行:
1. 清空临时表
2. 抓取新数据 → 插入数据库
3. 生成报告（从数据库读取）
4. 保留历史数据用于调试
```

### 2.3 报告生成模块

#### 2.3.1 报告结构

**头部统计区**:
```
┌─────────────────────────────────────────────────────────┐
│  📊 FY26_INIT Epic Daily Report                         │
│  Generated: 2026-03-18 18:00                           │
│                                                         │
│  📈 75 Initiatives  │  📋 78 Features  │  🎯 110 Epics  │
└─────────────────────────────────────────────────────────┘
```

**数据表区**:
- 可折叠的项目分组
- 状态筛选按钮
- 搜索框
- 分页显示

#### 2.3.2 交互功能

| 功能 | 描述 | 实现方式 |
|------|------|----------|
| 状态筛选 | 按 Discovery/Execution/Done 等筛选 | JavaScript filter |
| 项目筛选 | 按项目代码筛选 | JavaScript filter |
| 搜索 | 关键词搜索 Key/Summary | JavaScript search |
| 展开/折叠 | 展开单个项目查看详情 | CSS + JS toggle |
| SLA Alert | 高亮显示超期 Epic | CSS 样式 |

#### 2.3.3 SLA Alert 逻辑

```javascript
function checkSLAAlert(updated, status) {
  if (status === 'Done') return false;
  
  const lastUpdated = new Date(updated);
  const now = new Date();
  const daysSince = (now - lastUpdated) / (1000 * 60 * 60 * 24);
  
  return daysSince > 14; // 超过 2 周
}
```

### 2.4 邮件发送模块

#### 2.4.1 邮件格式

**主题**: `[FY26_INIT Epic Report] 2026-03-18 18:00`

**收件人**:
- To: chinatechpmo@lululemon.com
- CC: rcheng2@lululemon.com

**附件**:
- `fy26_daily_report_v5_20260318_1800.html`

#### 2.4.2 SMTP 配置

| 配置项 | 值 |
|--------|-----|
| Server | smtp.qq.com |
| Port | 587 (STARTTLS) / 465 (SSL) |
| Username | 3823810468@qq.com |
| Password | 环境变量 QQ_MAIL_PASSWORD |
| From | 3823810468@qq.com |

**双模式 SMTP**:
1. 首先尝试 SSL (port 465)
2. 失败时回退到 STARTTLS (port 587)

### 2.5 定时任务模块

#### 2.5.1 LaunchAgent 配置

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" ...>
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.fy26-daily-report</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/admin/.openclaw/workspace/scripts/fy26_daily_report_v5.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>18</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/admin/.openclaw/workspace/logs/fy26_daily_report.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/admin/.openclaw/workspace/logs/fy26_daily_report_error.log</string>
</dict>
</plist>
```

#### 2.5.2 执行流程

```bash
# fy26_daily_report_v5.sh
#!/bin/bash
export PATH="/opt/homebrew/bin:$PATH"
export JIRA_API_TOKEN="..."
export QQ_MAIL_PASSWORD="..."

python3 fetch_fy26_v5.py
python3 generate_fy26_report_v5.py
python3 generate_fy26_html_v5.py
python3 send_fy26_report_v5.py
```

---

## 3. 用户界面设计

### 3.1 报告页面布局

```
┌─────────────────────────────────────────────────────────────┐
│  Header                                                     │
│  - Title: FY26_INIT Epic Daily Report                      │
│  - Timestamp                                               │
│  - Quick Stats Cards                                       │
├─────────────────────────────────────────────────────────────┤
│  Filters                                                    │
│  - Search box                                              │
│  - Status buttons (All | Discovery | Execution | Done...) │
│  - Project dropdown                                        │
├─────────────────────────────────────────────────────────────┤
│  Content                                                    │
│  ┌─────────────┐                                            │
│  │ Project A   │ - Epic 1 (Status) [Assignee]              │
│  │             │ - Epic 2 (Status) [Assignee] ⚠️           │
│  │             │ - Epic 3 (Status) [Assignee]              │
│  ├─────────────┤                                            │
│  │ Project B   │ - Epic 4 (Status) [Assignee]              │
│  └─────────────┘                                            │
├─────────────────────────────────────────────────────────────┤
│  Footer                                                     │
│  - Generated by OpenClaw                                   │
│  - Data source: Jira API                                   │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 视觉设计规范

**颜色方案**:
| 用途 | 颜色 | Hex |
|------|------|-----|
| 主色 | lululemon 红 | #E31937 |
| 背景 | 浅灰 | #F4F5F7 |
| 文字 | 深灰 | #172B4D |
| 次要文字 | 中灰 | #5E6C84 |
| 边框 | 浅灰 | #DFE1E6 |
| SLA Alert | 橙 | #FF8B00 |
| 成功 | 绿 | #36B37E |

**字体**:
- 标题: -apple-system, BlinkMacSystemFont, 'Segoe UI'
- 正文: 同上
- 等宽: 'Courier New', monospace

---

## 4. API 接口

### 4.1 内部 API

**数据抓取**:
```python
def fetch_project_epics(project_key: str) -> List[Dict]:
    """从指定项目抓取 Epic 数据"""
    pass

def fetch_cntin_features() -> List[Dict]:
    """抓取 CNTIN Feature 数据"""
    pass

def fetch_cntin_initiatives() -> List[Dict]:
    """抓取 CNTIN Initiative 数据"""
    pass
```

**数据库操作**:
```python
def save_epics(epics: List[Dict]) -> None:
    """批量保存 Epic 到数据库"""
    pass

def get_epics_by_project(project: str) -> List[Dict]:
    """按项目查询 Epic"""
    pass

def get_all_stats() -> Dict:
    """获取全局统计"""
    pass
```

**报告生成**:
```python
def generate_json_report() -> Dict:
    """生成 JSON 格式报告"""
    pass

def generate_html_report(json_data: Dict) -> str:
    """生成 HTML 报告"""
    pass
```

### 4.2 外部 API

**Jira REST API v3**:
- Base URL: `https://lululemon.atlassian.net/rest/api/3`
- Authentication: Basic Auth (email + API token)
- Endpoints:
  - `GET /search` - 搜索 issues
  - `GET /issue/{key}` - 获取单个 issue

**QQ Mail SMTP**:
- Server: `smtp.qq.com`
- Authentication: Password (授权码)

---

## 5. 性能需求

### 5.1 响应时间

| 操作 | 目标 | 最大可接受 |
|------|------|-----------|
| 数据抓取 | < 3 分钟 | 5 分钟 |
| 数据库写入 | < 10 秒 | 30 秒 |
| 报告生成 | < 20 秒 | 60 秒 |
| 邮件发送 | < 10 秒 | 30 秒 |
| **总计** | **< 5 分钟** | **10 分钟** |

### 5.2 并发处理

- 数据抓取: 单线程顺序执行（避免 Jira API 限流）
- 数据库操作: 批量插入（每批 100 条）

### 5.3 资源使用

| 资源 | 峰值 | 平均 |
|------|------|------|
| CPU | 50% | 20% |
| 内存 | 500 MB | 200 MB |
| 磁盘 | 100 MB | 50 MB |
| 网络 | 10 Mbps | 2 Mbps |

---

## 6. 安全需求

### 6.1 数据安全

- **API Token**: 存储在环境变量，不提交到代码库
- **邮箱密码**: 使用 QQ 邮箱授权码，环境变量管理
- **数据库**: 本地 SQLite，无网络暴露
- **日志**: 不记录敏感信息

### 6.2 访问控制

- Jira API: 使用只读权限的 API Token
- 邮件发送: 仅发送到预配置的白名单邮箱

---

## 7. 发布计划

### 7.1 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v5.0.0 | 2026-03-12 | SQLite 架构重构，解决数据丢失 |
| v4.0-v4.7 | 2026-03-11 | JSON 合并 bug 修复 |
| v3.0 | 2026-03-11 | 正确数据结构实现 |
| v2.0 | 2026-03-11 | 反向扫描尝试 |
| v1.0 | 2026-03-10 | 初始版本 |

### 7.2 发布检查清单

- [x] 代码推送到 GitHub
- [x] 文档编写完成 (BRD, PRD, Design)
- [x] LaunchAgent 配置安装
- [x] 环境变量配置验证
- [x] 测试运行通过
- [x] 邮件发送验证

---

## 8. 附录

### 8.1 项目列表 (22个)

| 项目代码 | 项目名称 |
|----------|----------|
| CNTEC | China Tech E-Commerce |
| CNTOM | China Tech Order Management |
| CNTDM | China Tech Data & Marketing |
| CNTMM | China Tech Membership & Marketing |
| CNTD | China Tech Data |
| CNTEST | China Test |
| CNENG | China Engineering |
| CNINFA | China Infrastructure |
| CNCA | China Customer Analytics |
| CPR | China Product |
| EPCH | Enterprise Platform China |
| CNCRM | China CRM |
| CNDIN | China Digital Innovation |
| SWMP | Software Marketplace |
| CDM | China Data Management |
| CMDM | China Master Data Management |
| CNSCM | China Supply Chain Management |
| OF | Order Fulfillment |
| CNRTPRJ | China Retail Project |
| CSCPVT | China Supply Chain Private |
| CNPMO | China PMO |
| CYBERPJT | Cyber Project |

### 8.2 状态映射

| Jira 状态 | 颜色 | 说明 |
|-----------|------|------|
| New | 🔵 Blue | 新建 |
| Discovery | 🟣 Purple | 调研中 |
| Execution | 🟠 Orange | 执行中 |
| Done | 🟢 Green | 已完成 |
| Strategy | 🔵 Cyan | 策略阶段 |
| To Do | ⚪ Gray | 待处理 |

### 8.3 故障排查

**问题**: 数据抓取不完整  
**解决**: 
```bash
sqlite3 fy26_data.db "SELECT project, COUNT(*) FROM epics GROUP BY project ORDER BY COUNT(*) DESC"
```

**问题**: 邮件发送失败  
**解决**: 检查 QQ_MAIL_PASSWORD 环境变量是否为最新授权码

**问题**: 定时任务未执行  
**解决**: 
```bash
launchctl list | grep fy26
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-daily-report.plist
```
