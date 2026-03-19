# FY26_INIT Epic 日报 - 产品需求文档 (PRD)

**文档版本**: v5.4  
**创建日期**: 2026-03-18  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 产品概述

### 1.1 产品目标
构建一个高效的 Epic 日报系统，从 22 个 Jira 项目抓取所有 FY26 相关的 Epic 数据，使用流水线架构实现边抓取边生成，大幅减少报告生成时间，并通过邮件自动发送给 PMO 团队。

### 1.2 用户画像

#### 主要用户: China Tech PMO
- **角色**: 项目经理、项目协调员
- **目标**: 每日快速了解所有 FY26 Epic 的状态
- **痛点**: 
  - 22 个项目分散，难以统一跟踪
  - Epic 数量多（100+），手动整理耗时
- **使用场景**: 每天 18:00 查收日报邮件

### 1.3 产品范围

**包含**:
- 22 个项目 Epic 数据抓取
- 并行抓取（5 workers）
- 增量更新（24h delta）
- 流水线处理（Producer-Consumer）
- 渐进式 HTML 渲染
- 邮件自动发送

**不包含**:
- AI 摘要（仅基础 Epic 数据）
- 实时数据同步
- 多语言支持
- 移动端 App

---

## 2. 功能规格

### 2.1 数据抓取模块

#### 2.1.1 JQL 查询构造

```python
# 项目列表
PROJECTS = [
    "CNTEC", "CNTOM", "CNTDM", "CNTMM", "CNTD", "CNTEST", "CNENG", "CNINFA",
    "CNCA", "CPR", "EPCH", "CNCRM", "CNDIN", "SWMP", "CDM", "CMDM",
    "CNSCM", "OF", "CNRTPRJ", "CSCPVT", "CNPMO", "CYBERPJT"
]

# JQL - 全量抓取
jql = f'project in ({", ".join(PROJECTS)}) AND issuetype = Epic'

# JQL - 增量更新 (v5.3)
last_fetch_time = load_fetch_state()
jql = f'project in ({", ".join(PROJECTS)}) AND issuetype = Epic AND updated >= -24h'
```

#### 2.1.2 并行抓取 (v5.3)

```python
from concurrent.futures import ThreadPoolExecutor
import threading

def fetch_project_epics(project):
    """抓取单个项目的 Epics"""
    jql = f'project = {project} AND issuetype = Epic'
    # API 调用
    # 异常处理 + 重试
    return results

def parallel_fetch_all_projects(projects, max_workers=5):
    """
    并行抓取所有项目
    
    优化点:
    - 5 并发 workers
    - 每个项目独立重试
    - 进度追踪
    """
    results = {}
    errors = {}
    
    def fetch_with_retry(project):
        for attempt in range(3):
            try:
                return project, fetch_project_epics(project)
            except Exception as e:
                if attempt == 2:
                    return project, e
                time.sleep(2 ** attempt)  # 指数退避
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(fetch_with_retry, p): p 
            for p in projects
        }
        
        for future in as_completed(futures):
            project, result = future.result()
            if isinstance(result, Exception):
                errors[project] = str(result)
            else:
                results[project] = result
    
    return results, errors
```

### 2.2 流水线模块 (v5.4)

#### 2.2.1 架构设计

```python
from multiprocessing import Process, Queue, Manager

def producer_fetch_projects(project_queue, result_queue, stop_event):
    """
    生产者: 并行抓取项目数据
    
    流程:
    1. 从 project_queue 获取待抓取项目
    2. 并行抓取
    3. 将结果放入 result_queue
    4. 通知消费者有新数据
    """
    while not stop_event.is_set():
        try:
            project = project_queue.get(timeout=1)
            if project is None:  # 结束信号
                break
            
            # 抓取项目数据
            epics = fetch_project_epics(project)
            
            # 存入数据库
            save_to_sqlite(epics)
            
            # 通知消费者
            result_queue.put({'project': project, 'count': len(epics)})
            
        except queue.Empty:
            continue

def consumer_generate_html(result_queue, html_queue, total_projects, stop_event):
    """
    消费者: 渐进式生成 HTML
    
    流程:
    1. 从 result_queue 获取完成的抓取结果
    2. 从数据库读取对应项目数据
    3. 生成 HTML 片段
    4. 累积到 html_queue
    """
    completed = 0
    
    while completed < total_projects and not stop_event.is_set():
        try:
            result = result_queue.get(timeout=5)
            
            # 从数据库读取数据
            epics = load_from_sqlite(result['project'])
            
            # 生成 HTML 片段
            html_fragment = generate_html_fragment(epics)
            
            html_queue.put(html_fragment)
            completed += 1
            
        except queue.Empty:
            continue
```

#### 2.2.2 渐进式渲染

```python
class ProgressiveHTMLRenderer:
    """渐进式 HTML 渲染器"""
    
    def __init__(self, output_path):
        self.output_path = output_path
        self.buffer = StringIO()
        self.write_header()
    
    def write_header(self):
        """写入 HTML 头部"""
        self.buffer.write("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>FY26_INIT Epic 日报</title>
            <style>
                /* CSS 样式 */
            </style>
        </head>
        <body>
            <h1>FY26_INIT Epic 日报</h1>
            <div id="content">
        """)
    
    def add_project_section(self, project, epics):
        """添加项目区块"""
        html = f"""
        <section class="project" data-project="{project}">
            <h2>{project} ({len(epics)} Epics)</h2>
            <table>
                <thead>...</thead>
                <tbody>
                    {''.join(self.render_epic_row(e) for e in epics)}
                </tbody>
            </table>
        </section>
        """
        self.buffer.write(html)
    
    def finalize(self):
        """完成 HTML"""
        self.buffer.write("""
            </div>
        </body>
        </html>
        """)
        
        # 一次性写入磁盘
        with open(self.output_path, 'w', encoding='utf-8') as f:
            f.write(self.buffer.getvalue())
```

### 2.3 增量更新 (v5.3)

```python
import json
from pathlib import Path

FETCH_STATE_FILE = Path.home() / ".openclaw" / "workspace" / "fetch_state.json"

def load_fetch_state():
    """加载上次抓取状态"""
    if FETCH_STATE_FILE.exists():
        with open(FETCH_STATE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_fetch_state(state):
    """保存抓取状态"""
    FETCH_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FETCH_STATE_FILE, 'w') as f:
        json.dump(state, f)

def fetch_with_incremental(projects):
    """
    增量抓取
    
    策略:
    1. 读取上次抓取时间
    2. 只抓取 updated >= -24h 的 Epic
    3. 合并到现有数据库
    4. 更新状态文件
    """
    state = load_fetch_state()
    
    for project in projects:
        last_fetch = state.get(project, '1970-01-01')
        
        # 构建增量查询
        jql = f'project = {project} AND issuetype = Epic AND updated >= -24h'
        
        # 抓取
        new_epics = fetch_epics(jql)
        
        # 更新数据库
        upsert_epics(new_epics)
        
        # 更新状态
        state[project] = datetime.now().isoformat()
    
    save_fetch_state(state)
```

### 2.4 内存优化 (v5.3)

```python
from io import StringIO

def generate_html_optimized(data):
    """
    内存优化的 HTML 生成
    
    优化点:
    1. 使用 StringIO 内存缓冲区
    2. 生成器 yield 数据
    3. 单次磁盘写入
    """
    buffer = StringIO()
    
    # 写入头部
    buffer.write(generate_html_header())
    
    # 逐项目生成
    for project in data:
        # 使用生成器避免全量加载
        buffer.write(generate_project_html(project))
    
    # 写入尾部
    buffer.write(generate_html_footer())
    
    # 一次性写入磁盘
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(buffer.getvalue())
    
    # 清空缓冲区
    buffer.close()
```

### 2.5 SQLite WAL 模式

```python
import sqlite3

def init_sqlite_wal(db_path):
    """
    初始化 SQLite WAL 模式
    
    优势:
    - 支持读写并发
    - 性能更好
    - 自动恢复
    """
    conn = sqlite3.connect(db_path)
    
    # 启用 WAL 模式
    conn.execute('PRAGMA journal_mode=WAL')
    conn.execute('PRAGMA synchronous=NORMAL')
    conn.execute('PRAGMA cache_size=10000')
    conn.execute('PRAGMA temp_store=MEMORY')
    
    conn.commit()
    conn.close()

def get_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
```

### 2.6 邮件发送模块

```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

def send_email(html_file, recipients, cc_recipients):
    """发送邮件"""
    msg = MIMEMultipart()
    msg['From'] = SENDER_EMAIL
    msg['To'] = ', '.join(recipients)
    msg['CC'] = ', '.join(cc_recipients)
    msg['Subject'] = f"FY26_INIT Epic 日报 - {datetime.now().strftime('%Y-%m-%d')}"
    
    # 添加 HTML 附件
    with open(html_file, 'rb') as f:
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(f.read())
    
    encoders.encode_base64(attachment)
    attachment.add_header(
        'Content-Disposition',
        f'attachment; filename={html_file.name}'
    )
    msg.attach(attachment)
    
    # 发送
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
```

---

## 3. 用户界面设计

### 3.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header                                                             │
│  - Title: FY26_INIT Epic 日报                                      │
│  - Timestamp: Generated: 2026-03-18 18:00                          │
│  - Stats: 22 Projects | 110 Epics | Pipeline v5.4                  │
├─────────────────────────────────────────────────────────────────────┤
│  Summary                                                            │
│  - Status Distribution: Done: 30 | In Progress: 50 | New: 30       │
│  - Projects with Epics: 12 / 22                                    │
│  - Fetch Mode: Incremental (24h delta)                             │
├─────────────────────────────────────────────────────────────────────┤
│  Project Sections (collapsible)                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ ▼ CPR (25 Epics)                                           │    │
│  │ ┌─────────┬──────────┬──────────┬────────┬─────────────────┐ │    │
│  │ │ Key     │ Summary  │ Status   │ Parent │ Assignee        │ │    │
│  │ ├─────────┼──────────┼──────────┼────────┼─────────────────┤ │    │
│  │ │ CPR-001 │ Feature  │ Done     │ CNTIN-1│ John Doe        │ │    │
│  │ │ CPR-002 │ Feature  │ In Prog  │ CNTIN-1│ Jane Doe        │ │    │
│  │ └─────────┴──────────┴──────────┴────────┴─────────────────┘ │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │ ▶ CNTEC (17 Epics)                                         │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │ ▶ CNTOM (9 Epics)                                          │    │
│  └────────────────────────────────────────────────────────────┘    │
├─────────────────────────────────────────────────────────────────────┤
│  Footer                                                             │
│  - Generated by OpenClaw v5.4 | Data source: Jira API              │
│  - Fetch time: 1.2s | Render time: 0.8s | Mode: Pipeline           │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 交互功能

| 功能 | 实现 | 事件 |
|------|------|------|
| 项目折叠 | CSS + JS | click |
| 状态筛选 | JavaScript | click |
| 关键词搜索 | JavaScript | keyup (debounce) |
| 导出 CSV | JavaScript | click |

---

## 4. API 接口

### 4.1 外部 API

**Jira REST API v3**:
- Base URL: `https://lululemon.atlassian.net/rest/api/3`
- Authentication: Basic Auth
- Endpoint: `GET /search/jql`

**SMTP**:
- Server: smtp.qq.com:587
- Authentication: Basic Auth
- Protocol: STARTTLS

### 4.2 内部模块接口

```python
# 数据抓取
def parallel_fetch_projects(projects, max_workers=5) -> Tuple[Dict, Dict]:
    """并行抓取项目数据"""
    pass

def fetch_with_incremental(projects) -> None:
    """增量抓取"""
    pass

# 流水线 (v5.4)
def producer_fetch_projects(queue, stop_event) -> None:
    """生产者：抓取数据"""
    pass

def consumer_generate_html(queue, html_queue, stop_event) -> None:
    """消费者：生成 HTML"""
    pass

# 报告生成
def generate_html_report(data, output_path) -> str:
    """生成 HTML 报告"""
    pass

def generate_html_optimized(data, output_path) -> str:
    """内存优化的 HTML 生成"""
    pass

# 邮件发送
def send_email(html_file, recipients, cc_recipients) -> bool:
    """发送邮件"""
    pass
```

---

## 5. 性能需求

### 5.1 响应时间

| 操作 | v5.0 | v5.3 | v5.4 | 目标 |
|------|------|------|------|------|
| 全量抓取 | 5 min | **1.5 min** | 1.5 min | < 2 min |
| 增量更新 | 5 min | **~30 sec** | ~30 sec | < 1 min |
| HTML 生成 | 2 min | **1 min** | 1 min | < 2 min |
| 总时间 | 8-10 min | 6-7 min | **5-6 min** | < 7 min |

### 5.2 并发控制

- 项目抓取: 5 并发 workers
- 数据库连接: 连接池复用
- 队列大小: 10 (缓冲)

### 5.3 资源使用

| 资源 | v5.0 | v5.3/v5.4 | 优化 |
|------|------|-----------|------|
| 内存峰值 | 500MB | **200MB** | **60%** |
| CPU 使用 | 单核 | 多核并行 | **提升** |
| 磁盘 I/O | 多次写入 | 单次写入 | **减少** |

---

## 6. 发布计划

### 6.1 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v5.4 | 2026-03-18 | **流水线架构**: 生产者-消费者模式，渐进式渲染，后台 AI 预热 |
| v5.3 | 2026-03-18 | **性能优化**: 并行抓取(5 workers)，增量更新(24h)，内存优化(StringIO) |
| v5.0 | 2026-03-12 | 初始版本: SQLite 架构，全量抓取，基础报告 |

### 6.2 发布检查清单

- [x] 代码推送到 GitHub
- [x] 文档编写完成 (BRD, PRD, Design)
- [x] 环境变量配置验证
- [x] 全量抓取测试通过
- [x] 增量更新测试通过
- [x] 流水线测试通过
- [x] 邮件发送验证
- [x] 性能指标达标

---

## 7. 附录

### 7.1 状态映射

| Jira 状态 | 颜色 | Badge |
|-----------|------|-------|
| New | #0052CC | 🔵 |
| In Progress | #FF8B00 | 🟠 |
| Done | #36B37E | 🟢 |
| Closed | #505F79 | ⚫ |

### 7.2 故障排查

**问题**: 抓取时间长  
**解决**: 启用增量更新模式，检查网络连接

**问题**: 内存占用高  
**解决**: 使用 StringIO 模式，减少并发数

**问题**: 流水线卡住  
**解决**: 检查队列大小，查看日志是否有异常

**问题**: 邮件发送失败  
**解决**: 验证 QQ_MAIL_PASSWORD 是否为最新授权码

**问题**: 数据库锁定  
**解决**: 确认 WAL 模式已启用，检查并发连接数

### 7.3 配置示例

```python
# config.py

# 项目列表
PROJECTS = ["CNTEC", "CNTOM", ...]  # 22 个项目

# 流水线配置
MAX_WORKERS = 5
PIPELINE_QUEUE_SIZE = 10
INCREMENTAL_MODE = True

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
SENDER_EMAIL = "3823810468@qq.com"
RECIPIENTS = ["chinatechpmo@lululemon.com"]
CC_RECIPIENTS = ["rcheng2@lululemon.com"]

# SQLite 配置
DB_PATH = "~/.openclaw/workspace/jira-reports/fy26_data.db"
WAL_MODE = True
```
