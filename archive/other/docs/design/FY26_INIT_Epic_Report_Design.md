# FY26_INIT Epic 日报 - 详细设计文档

**文档版本**: v5.0.0  
**创建日期**: 2026-03-18  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 系统架构

### 1.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FY26_INIT Epic 日报系统                        │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Data Fetch  │──▶│  Storage    │──▶│  Generator  │──▶│   Email     │    │
│  │   Layer     │  │   Layer     │  │   Layer     │  │   Layer     │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│         │                │                │                │            │
│         ▼                ▼                ▼                ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Jira API    │  │  SQLite     │  │   HTML/     │  │  QQ Mail    │    │
│  │ (22 proj)   │  │  Database   │  │   JSON      │  │   SMTP      │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │   macOS LaunchAgent │
                    │   (Daily @ 18:00)   │
                    └─────────────────────┘
```

### 1.2 组件清单

| 组件 | 文件 | 职责 |
|------|------|------|
| 主控脚本 | `fy26_daily_report_v5.sh` | 协调执行流程 |
| 数据抓取 | `fetch_fy26_v5.py` | 从 Jira API 获取数据 |
| 报告生成 | `generate_fy26_report_v5.py` | 生成 JSON 报告 |
| HTML 生成 | `generate_fy26_html_v5.py` | 生成 HTML 报告 |
| 邮件发送 | `send_fy26_report_v5.py` | 发送邮件 |
| 数据库 | `fy26_data.db` | SQLite 数据存储 |

---

## 2. 数据流设计

### 2.1 数据流图 (DFD)

```
Level 0:
┌─────────────────┐         ┌─────────────────┐         ┌─────────────────┐
│   Jira Cloud    │────────▶│  Report System  │────────▶│  PMO Team       │
│   (22 projects) │         │  (v5.0.0)       │         │  (Email)        │
└─────────────────┘         └─────────────────┘         └─────────────────┘

Level 1:
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│  Fetch   │───▶│  Store   │───▶│  Process │───▶│  Format  │───▶│  Send    │
│  Script  │    │  SQLite  │    │  Script  │    │  Script  │    │  Script  │
└──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
     │               │               │               │               │
     ▼               ▼               ▼               ▼               ▼
  Jira API       Database        Aggregation     HTML/CSS        SMTP
```

### 2.2 数据转换流程

```
Raw Jira JSON
     │
     │ Python: json.loads()
     ▼
Python Dict/List
     │
     │ Extract fields
     ▼
Structured Objects
     │
     │ SQLite INSERT
     ▼
SQLite Tables
     │
     │ SQL SELECT
     ▼
Report Data Structure
     │
     │ Jinja2/HTML
     ▼
Final HTML Report
```

---

## 3. 模块详细设计

### 3.1 数据抓取模块 (fetch_fy26_v5.py)

#### 3.1.1 类图

```
┌─────────────────────┐
│    JiraClient       │
├─────────────────────┤
│ - base_url: str     │
│ - auth_token: str   │
│ - email: str        │
├─────────────────────┤
│ + search_issues(jql)│
│ + get_issue(key)    │
│ + fetch_all_pages() │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   DataTransformer   │
├─────────────────────┤
│                     │
├─────────────────────┤
│ + extract_epics()   │
│ + extract_features()│
│ + extract_initiatives│
│ + flatten_fields()  │
└─────────────────────┘
         │
         ▼
┌─────────────────────┐
│   DatabaseWriter    │
├─────────────────────┤
│ - conn: sqlite3     │
├─────────────────────┤
│ + save_epics()      │
│ + save_features()   │
│ + save_initiatives()│
│ + commit()          │
└─────────────────────┘
```

#### 3.1.2 核心算法

**分页抓取算法**:
```python
def fetch_all_issues(jql, batch_size=100):
    """
    分页抓取所有符合条件的 issues
    
    Algorithm:
    1. 初始请求获取第一页和总数量
    2. 计算总页数
    3. 顺序请求剩余页面
    4. 合并所有结果
    5. 异常处理：指数退避重试
    """
    all_issues = []
    start_at = 0
    
    while True:
        try:
            response = jira.search_issues(
                jql=jql,
                startAt=start_at,
                maxResults=batch_size
            )
            
            issues = response['issues']
            all_issues.extend(issues)
            
            if start_at + len(issues) >= response['total']:
                break
                
            start_at += batch_size
            
        except RateLimitError:
            time.sleep(2 ** attempt)  # 指数退避
            attempt += 1
            
    return all_issues
```

**数据提取算法**:
```python
def extract_epic_data(issue):
    """
    从 Jira issue 提取 Epic 相关字段
    
    Input: Jira API response dict
    Output: Clean dict for database
    """
    fields = issue.get('fields', {})
    
    return {
        'key': issue['key'],
        'project': issue['key'].split('-')[0],
        'summary': fields.get('summary', ''),
        'status': fields.get('status', {}).get('name', 'Unknown'),
        'assignee': fields.get('assignee', {}).get('displayName') if fields.get('assignee') else '-',
        'parent_key': fields.get('parent', {}).get('key') if fields.get('parent') else None,
        'created': fields.get('created', ''),
        'labels': ','.join(fields.get('labels', []))
    }
```

### 3.2 数据存储模块

#### 3.2.1 数据库 ERD

```
┌───────────────┐       ┌───────────────┐       ┌───────────────┐
│    epics      │       │   features    │       │  initiatives  │
├───────────────┤       ├───────────────┤       ├───────────────┤
│ PK key        │       │ PK key        │       │ PK key        │
│    project    │       │    summary    │       │    summary    │
│    summary    │       │    status     │       │    status     │
│    status     │       │    assignee   │       │    assignee   │
│    assignee   │       │ FK parent_key │◀──────│    labels     │
│ FK parent_key │──────▶│    labels     │       │               │
│    created    │       │               │       │               │
│    labels     │       │               │       │               │
└───────────────┘       └───────────────┘       └───────────────┘

┌───────────────┐
│  fetch_log    │
├───────────────┤
│ PK id         │
│    project    │
│    issue_type │
│    count      │
│    status     │
│    error_msg  │
│    fetched_at │
└───────────────┘
```

#### 3.2.2 SQL 查询优化

**统计查询**:
```sql
-- 项目 Epic 数量统计（带索引优化）
CREATE INDEX idx_epics_project ON epics(project);

SELECT 
    project, 
    COUNT(*) as epic_count,
    COUNT(CASE WHEN status != 'Done' THEN 1 END) as active_count
FROM epics 
GROUP BY project 
ORDER BY epic_count DESC;

-- SLA Alert 查询
SELECT key, summary, status, updated
FROM epics
WHERE status != 'Done'
  AND datetime(updated) < datetime('now', '-14 days');
```

### 3.3 报告生成模块

#### 3.3.1 HTML 模板结构

```html
<!-- 模板层次结构 -->
<!DOCTYPE html>
<html>
  <head>
    <!-- CSS 样式 -->
    <style>
      /* 基础样式 */
      /* 响应式布局 */
      /* 动画效果 */
    </style>
  </head>
  <body>
    <div class="container">
      <header><!-- 头部统计 --></header>
      <nav><!-- 筛选器 --></nav>
      <main><!-- 数据表格 --></main>
      <footer><!-- 页脚 --></footer>
    </div>
    <script>
      // 交互逻辑
    </script>
  </body>
</html>
```

#### 3.3.2 JavaScript 交互模块

**筛选模块**:
```javascript
class ReportFilter {
    constructor() {
        this.filters = {
            status: 'all',
            project: 'all',
            search: ''
        };
        this.init();
    }
    
    init() {
        // 绑定事件监听器
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleFilter(e));
        });
        
        document.querySelector('#search').addEventListener('input', 
            debounce((e) => this.handleSearch(e), 300)
        );
    }
    
    applyFilters() {
        const rows = document.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const matchStatus = this.filters.status === 'all' || 
                               row.dataset.status === this.filters.status;
            const matchProject = this.filters.project === 'all' || 
                                row.dataset.project === this.filters.project;
            const matchSearch = !this.filters.search || 
                               row.textContent.toLowerCase().includes(this.filters.search);
            
            row.style.display = matchStatus && matchProject && matchSearch ? '' : 'none';
        });
    }
}
```

### 3.4 邮件发送模块

#### 3.4.1 SMTP 连接管理

```python
class EmailSender:
    """
    双模式 SMTP 邮件发送器
    
    模式 1: SSL (port 465) - 推荐
    模式 2: STARTTLS (port 587) - 备选
    """
    
    def __init__(self, host, port, username, password):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        
    def send(self, to_addrs, subject, html_content, attachment):
        # 尝试 SSL 模式
        try:
            return self._send_ssl(to_addrs, subject, html_content, attachment)
        except Exception as ssl_error:
            logger.warning(f"SSL failed: {ssl_error}, trying STARTTLS")
            return self._send_starttls(to_addrs, subject, html_content, attachment)
    
    def _send_ssl(self, to_addrs, subject, html_content, attachment):
        with smtplib.SMTP_SSL(self.host, 465, timeout=30) as server:
            server.login(self.username, self.password)
            msg = self._build_message(to_addrs, subject, html_content, attachment)
            server.sendmail(self.username, to_addrs, msg.as_string())
    
    def _send_starttls(self, to_addrs, subject, html_content, attachment):
        with smtplib.SMTP(self.host, 587, timeout=30) as server:
            server.starttls()
            server.login(self.username, self.password)
            msg = self._build_message(to_addrs, subject, html_content, attachment)
            server.sendmail(self.username, to_addrs, msg.as_string())
```

---

## 4. 配置管理

### 4.1 环境变量

```bash
# ~/.zshrc 或 ~/.bash_profile
export JIRA_API_TOKEN="ATATT3xFfGF0..."
export JIRA_EMAIL="rcheng2@lululemon.com"
export QQ_MAIL_PASSWORD="ftbabipdlxliceai"
```

### 4.2 配置文件

**数据库配置** (`config/fy26_db.conf`):
```ini
[database]
path = /Users/admin/.openclaw/workspace/jira-reports/fy26_data.db
backup_enabled = true
backup_retention_days = 7

[fetch]
batch_size = 100
max_retries = 3
retry_delay = 2

[report]
output_dir = /Users/admin/.openclaw/workspace/reports
template = default
```

### 4.3 LaunchAgent 配置

```xml
<!-- com.openclaw.fy26-daily-report.plist -->
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
        <key>Hour</key><integer>18</integer>
        <key>Minute</key><integer>0</integer>
    </dict>
    
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
        <key>JIRA_API_TOKEN</key>
        <string>${JIRA_API_TOKEN}</string>
        <key>QQ_MAIL_PASSWORD</key>
        <string>${QQ_MAIL_PASSWORD}</string>
    </dict>
    
    <key>StandardOutPath</key>
    <string>/Users/admin/.openclaw/workspace/logs/fy26_daily_report.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/admin/.openclaw/workspace/logs/fy26_daily_report_error.log</string>
</dict>
</plist>
```

---

## 5. 错误处理

### 5.1 错误分类

| 级别 | 类型 | 示例 | 处理策略 |
|------|------|------|----------|
| 致命 | 系统错误 | 数据库连接失败 | 记录日志，发送告警，退出 |
| 错误 | 业务错误 | Jira API 限流 | 重试 3 次，指数退避 |
| 警告 | 数据问题 | 部分项目抓取失败 | 记录警告，继续执行 |
| 信息 | 正常信息 | 任务完成 | 记录日志 |

### 5.2 错误处理流程

```python
def handle_error(error, context):
    """
    统一的错误处理入口
    
    Flow:
    1. 记录错误日志
    2. 根据错误类型决定策略
    3. 发送告警（如果需要）
    4. 执行恢复或退出
    """
    logger.error(f"[{context}] {error}", exc_info=True)
    
    if isinstance(error, JiraAPIError):
        if error.status_code == 429:  # Rate Limit
            return retry_with_backoff()
        elif error.status_code == 401:  # Auth Error
            send_alert("Jira API Token 失效")
            raise SystemExit(1)
            
    elif isinstance(error, SMTPError):
        send_alert(f"邮件发送失败: {error}")
        return False
        
    elif isinstance(error, DatabaseError):
        send_alert(f"数据库错误: {error}")
        raise SystemExit(1)
```

---

## 6. 性能优化

### 6.1 数据库优化

**索引策略**:
```sql
-- 查询优化索引
CREATE INDEX idx_epics_project ON epics(project);
CREATE INDEX idx_epics_status ON epics(status);
CREATE INDEX idx_epics_parent ON epics(parent_key);
CREATE INDEX idx_features_parent ON features(parent_key);

-- 查询计划分析
EXPLAIN QUERY PLAN 
SELECT * FROM epics WHERE project = 'CPR' AND status != 'Done';
```

**批量插入**:
```python
def batch_insert_epics(epics, batch_size=100):
    """
    批量插入优化，减少数据库往返
    
    Optimization: 使用 executemany 代替多次 execute
    """
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        for i in range(0, len(epics), batch_size):
            batch = epics[i:i+batch_size]
            cursor.executemany(
                'INSERT OR REPLACE INTO epics VALUES (?,?,?,?,?,?,?,?)',
                [(e['key'], e['project'], e['summary'], 
                  e['status'], e['assignee'], e['parent_key'],
                  e['created'], e['labels']) for e in batch]
            )
            conn.commit()
```

### 6.2 API 调用优化

**并发控制**:
```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def fetch_all_projects_parallel(projects, max_workers=3):
    """
    并行抓取多个项目，但限制并发数避免限流
    
    Strategy: 有限并发 + 指数退避
    """
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_project_epics, proj): proj 
            for proj in projects
        }
        
        for future in as_completed(futures):
            project = futures[future]
            try:
                results[project] = future.result()
            except Exception as e:
                logger.error(f"Failed to fetch {project}: {e}")
                results[project] = []
                
    return results
```

---

## 7. 测试策略

### 7.1 单元测试

```python
# test_fetch.py
import unittest
from unittest.mock import Mock, patch

class TestJiraClient(unittest.TestCase):
    def setUp(self):
        self.client = JiraClient(
            base_url="https://test.atlassian.net",
            auth_token="test_token"
        )
    
    @patch('requests.get')
    def test_search_issues_success(self, mock_get):
        mock_get.return_value.json.return_value = {
            'issues': [{'key': 'TEST-1'}],
            'total': 1
        }
        
        results = self.client.search_issues('project = TEST')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['key'], 'TEST-1')
    
    @patch('requests.get')
    def test_search_issues_rate_limit(self, mock_get):
        mock_get.side_effect = [
            Mock(status_code=429),  # Rate limit
            Mock(status_code=200, json=lambda: {'issues': [], 'total': 0})
        ]
        
        results = self.client.search_issues('project = TEST')
        
        self.assertEqual(mock_get.call_count, 2)

# test_database.py
class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database(':memory:')
        self.db.init_schema()
    
    def test_insert_and_query(self):
        epic = {
            'key': 'TEST-1',
            'project': 'TEST',
            'summary': 'Test Epic',
            'status': 'In Progress',
            'assignee': 'Test User',
            'parent_key': None,
            'created': '2026-03-18T10:00:00Z',
            'labels': 'fy26_init'
        }
        
        self.db.save_epics([epic])
        results = self.db.get_epics_by_project('TEST')
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['key'], 'TEST-1')
```

### 7.2 集成测试

```python
# test_integration.py
def test_full_pipeline():
    """
    端到端集成测试
    
    Steps:
    1. 启动测试 Jira 服务器 (mock)
    2. 执行完整抓取流程
    3. 验证数据库内容
    4. 生成报告
    5. 验证邮件发送
    """
    with MockJiraServer() as jira:
        # 准备测试数据
        jira.create_issue('CPR-1', 'Epic 1', 'Discovery')
        jira.create_issue('CPR-2', 'Epic 2', 'Done')
        
        # 执行流程
        fetch_fy26_v5.main()
        generate_fy26_report_v5.main()
        generate_fy26_html_v5.main()
        
        # 验证
        db = sqlite3.connect('test.db')
        count = db.execute('SELECT COUNT(*) FROM epics').fetchone()[0]
        assert count == 2
        
        # 验证报告
        with open('test_report.html') as f:
            content = f.read()
            assert 'CPR-1' in content
            assert 'CPR-2' in content
```

---

## 8. 部署指南

### 8.1 安装步骤

```bash
# 1. 克隆仓库
git clone https://github.com/tensasky/fy26-jira-reports.git
cd fy26-jira-reports

# 2. 安装依赖
pip3 install requests

# 3. 配置环境变量
echo 'export JIRA_API_TOKEN="your_token"' >> ~/.zshrc
echo 'export QQ_MAIL_PASSWORD="your_password"' >> ~/.zshrc
source ~/.zshrc

# 4. 安装 LaunchAgent
cp config/com.openclaw.fy26-daily-report.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.openclaw.fy26-daily-report.plist

# 5. 验证
launchctl list | grep fy26
```

### 8.2 监控与告警

```python
# monitoring.py
def check_system_health():
    """系统健康检查"""
    checks = {
        'database': check_database_connection(),
        'jira_api': check_jira_connectivity(),
        'smtp': check_smtp_connection(),
        'disk_space': check_disk_space(),
    }
    
    for name, status in checks.items():
        if not status:
            send_alert(f"Health check failed: {name}")
    
    return all(checks.values())

def check_last_execution():
    """检查上次执行状态"""
    log_file = 'logs/fy26_daily_report.log'
    last_line = tail(log_file, 1)
    
    if 'success' not in last_line.lower():
        send_alert("Last execution may have failed")
```

---

## 9. 附录

### 9.1 版本历史

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v5.0.0 | 2026-03-12 | SQLite 架构重构 | OpenClaw |
| v4.0-v4.7 | 2026-03-11 | JSON 合并 bug 修复 | OpenClaw |
| v3.0 | 2026-03-11 | 正确数据结构 | OpenClaw |
| v2.0 | 2026-03-11 | 反向扫描 | OpenClaw |
| v1.0 | 2026-03-10 | 初始版本 | OpenClaw |

### 9.2 参考资料

- [Jira REST API v3](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- [SQLite Python Docs](https://docs.python.org/3/library/sqlite3.html)
- [macOS LaunchAgents](https://developer.apple.com/library/archive/documentation/MacOSX/Conceptual/BPSystemStartup/Chapters/CreatingLaunchdJobs.html)
- [SMTP Protocol](https://tools.ietf.org/html/rfc5321)

### 9.3 故障排查指南

| 症状 | 可能原因 | 解决方案 |
|------|----------|----------|
| 日报未收到 | LaunchAgent 未加载 | `launchctl load` |
| 数据不完整 | Jira API 限流 | 检查日志，增加重试 |
| 邮件失败 | SMTP 密码过期 | 更新 QQ_MAIL_PASSWORD |
| 报告格式错误 | 模板损坏 | 重新生成模板 |
