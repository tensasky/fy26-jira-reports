# CNTIN-730 Initiative 周报 - 系统设计文档 (SDD)

**文档版本**: v1.2.0  
**创建日期**: 2026-03-19  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 系统架构

### 1.1 架构概览

```
┌─────────────────────────────────────────────────────────────────────┐
│                          CNTIN-730 周报系统                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐             │
│  │   Data      │───>│    AI       │───>│   Report    │             │
│  │   Fetcher   │    │  Processor  │    │  Generator  │             │
│  └─────────────┘    └─────────────┘    └─────────────┘             │
│         │                  │                  │                     │
│         ▼                  ▼                  ▼                     │
│  ┌─────────────────────────────────────────────────────┐            │
│  │                   Semantic Cache                     │            │
│  │         (MD5 Hash-based Content Cache)              │            │
│  └─────────────────────────────────────────────────────┘            │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐                                │
│  │   Email     │    │   Feishu    │                                │
│  │   Sender    │    │   Sender    │                                │
│  └─────────────┘    └─────────────┘                                │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 组件说明

| 组件 | 职责 | 技术栈 |
|------|------|--------|
| Data Fetcher | 从 Jira API 抓取数据 | Python, Requests |
| AI Processor | 生成 AI Summary | Python, AsyncIO, OpenAI API |
| Semantic Cache | 基于内容哈希的缓存 | Python, File System |
| Report Generator | 生成 HTML 报告 | Python, StringIO |
| Email Sender | 发送邮件 | Python, smtplib |
| Feishu Sender | 发送飞书文件 | Python, Requests |

---

## 2. 数据流

### 2.1 正常流程

```
1. 定时触发 (工作日 12:00)
   │
   ▼
2. 清空历史缓存
   │
   ▼
3. 从 Jira 抓取数据
   │─ 构建 JQL 查询
   │─ 调用 /rest/api/3/search/jql
   │─ 处理 nextPageToken 分页
   │─ 获取全部 143 条数据
   │
   ▼
4. 数据预处理
   │─ 解析 ADF 描述
   │─ 计算 Missing SLA
   │─ 统计 Status/Label/Assignee
   │
   ▼
5. 生成 AI Summary
   │─ 检查语义缓存
   │─ 30 并发异步处理
   │─ 保存到缓存
   │
   ▼
6. 生成 HTML 报告
   │─ 统计卡片
   │─ 筛选按钮
   │─ 冻结列表格
   │─ 行展开功能
   │─ Excel 导出按钮
   │
   ▼
7. 发送报告
   │─ 邮件: chinatechpmo@lululemon.com
   │─ 抄送: rcheng2@lululemon.com
   │─ 飞书文件发送
   │
   ▼
8. 记录日志
```

### 2.2 错误处理

| 错误类型 | 处理策略 |
|----------|----------|
| Jira API 失败 | 重试 3 次，失败告警 |
| AI API 限流 | 等待 5 秒重试，降级为占位符 |
| 邮件发送失败 | 切换 SMTP 服务器，失败告警 |
| 缓存写入失败 | 降级为重新生成，记录警告 |

---

## 3. 模块设计

### 3.1 Data Fetcher 模块

```python
class JiraDataFetcher:
    """Jira 数据抓取器"""
    
    def __init__(self, email, token, base_url):
        self.email = email
        self.token = token
        self.base_url = base_url
        self.auth_headers = self._build_auth()
    
    def fetch_all_issues(self, jql):
        """抓取所有数据，处理 nextPageToken 分页"""
        all_issues = []
        next_page_token = None
        
        while True:
            data = self._fetch_page(jql, next_page_token)
            all_issues.extend(data['issues'])
            
            if data.get('isLast', True):
                break
            next_page_token = data.get('nextPageToken')
        
        return all_issues
    
    def _fetch_page(self, jql, next_page_token=None):
        """抓取单页数据"""
        params = {'jql': jql, 'maxResults': 100}
        if next_page_token:
            params['nextPageToken'] = next_page_token
        
        response = requests.get(
            f"{self.base_url}/rest/api/3/search/jql",
            headers=self.auth_headers,
            params=params
        )
        return response.json()
```

### 3.2 Semantic Cache 模块

```python
class SemanticCache:
    """基于内容 MD5 的语义缓存"""
    
    def __init__(self, cache_dir):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index = self._load_index()
    
    def _compute_hash(self, summary, description):
        """计算内容 MD5 哈希"""
        content = f"{summary}:{description}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, summary, description):
        """获取缓存"""
        content_hash = self._compute_hash(summary, description)
        
        if content_hash in self.index:
            cache_file = self.cache_dir / f"{content_hash}.json"
            if cache_file.exists():
                with open(cache_file, 'r') as f:
                    return json.load(f)['ai_summary']
        return None
    
    def set(self, summary, description, ai_summary):
        """保存缓存"""
        content_hash = self._compute_hash(summary, description)
        cache_file = self.cache_dir / f"{content_hash}.json"
        
        with open(cache_file, 'w') as f:
            json.dump({
                'hash': content_hash,
                'ai_summary': ai_summary,
                'created': datetime.now().isoformat()
            }, f)
        
        self.index[content_hash] = {
            'created': datetime.now().isoformat()
        }
        self._save_index()
```

### 3.3 AI Processor 模块

```python
class AIProcessor:
    """AI 摘要生成器"""
    
    def __init__(self, api_key, cache):
        self.api_key = api_key
        self.cache = cache
        self.semaphore = asyncio.Semaphore(30)
        self.rate_limit = 0.1
    
    async def process_batch(self, issues):
        """批量处理"""
        tasks = [self._process_one(issue) for issue in issues]
        return await asyncio.gather(*tasks)
    
    async def _process_one(self, issue):
        """处理单个 Issue"""
        summary = issue['summary']
        description = pre_clean_description(issue['description'])
        
        # 检查缓存
        cached = self.cache.get(summary, description)
        if cached:
            return issue['key'], cached
        
        async with self.semaphore:
            try:
                ai_summary = await self._call_api(summary, description)
                self.cache.set(summary, description, ai_summary)
                await asyncio.sleep(self.rate_limit)
                return issue['key'], ai_summary
            except Exception as e:
                return issue['key'], f"<span class='error'>{str(e)[:50]}</span>"
    
    async def _call_api(self, summary, description):
        """调用 AI API"""
        prompt = self._build_prompt(summary, description)
        
        headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'gpt-4o-mini',
            'messages': [
                {'role': 'system', 'content': '你是专业的业务分析师'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 300
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=payload
            ) as response:
                data = await response.json()
                return data['choices'][0]['message']['content'].strip()
```

### 3.4 Report Generator 模块

```python
class ReportGenerator:
    """HTML 报告生成器"""
    
    def __init__(self, template_dir):
        self.template_dir = template_dir
    
    def generate(self, issues, stats):
        """生成 HTML 报告"""
        html_parts = []
        
        # 头部
        html_parts.append(self._render_header())
        
        # 统计卡片
        html_parts.append(self._render_stats(stats))
        
        # 筛选区域
        html_parts.append(self._render_filters(stats))
        
        # 表格
        html_parts.append(self._render_table(issues))
        
        # 导出按钮
        html_parts.append(self._render_export_button())
        
        # 脚本
        html_parts.append(self._render_scripts())
        
        # 尾部
        html_parts.append(self._render_footer())
        
        return ''.join(html_parts)
    
    def _render_stats(self, stats):
        """渲染统计卡片"""
        return f'''
        <div class="stats-container">
            <div class="stat-card">
                <div class="stat-value">{stats['total']}</div>
                <div class="stat-label">Total Initiatives</div>
            </div>
            ...
        </div>
        '''
    
    def _render_table(self, issues):
        """渲染表格"""
        rows = [self._render_row(issue) for issue in issues]
        return f'''
        <table>
            <thead>{self._render_thead()}</thead>
            <tbody>{''.join(rows)}</tbody>
        </table>
        '''
```

---

## 4. 数据模型

### 4.1 Issue 数据结构

```python
{
    "key": "CNTIN-1096",
    "summary": "RITM1829787 - Sibling for UCS and WMP",
    "status": "Discovery",
    "assignee": "Ian Wang",
    "priority": "Minor",
    "created": "2026-03-15",
    "updated": "2026-03-15",
    "duedate": "",
    "description": "Requestor: Jimmy Chen...",
    "labels": ["ChinaEC"],
    "has_sla": false,
    "ai_summary": "<b>What:</b> ... <b>Why:</b> ..."
}
```

### 4.2 统计数据结构

```python
{
    "total": 143,
    "status_counts": {
        "Discovery": 96,
        "Done": 34,
        "Execution": 5,
        "New": 5,
        "Strategy": 3
    },
    "label_counts": {
        "ChinaTechnology": 36,
        "ChinaRetail": 23,
        ...
    },
    "assignee_counts": {
        "Alice Lang": 15,
        "Bob Chen": 12,
        ...
    },
    "sla_count": 30
}
```

### 4.3 缓存数据结构

```python
# 缓存索引
{
    "a1b2c3d4...": {
        "created": "2026-03-19T10:00:00",
        "accessed": "2026-03-19T12:00:00"
    }
}

# 缓存文件
{
    "hash": "a1b2c3d4...",
    "ai_summary": "...",
    "created": "2026-03-19T10:00:00"
}
```

---

## 5. 接口设计

### 5.1 Jira API

**Endpoint**: `GET /rest/api/3/search/jql`

**请求参数**:
```json
{
    "jql": "project = CNTIN AND issuetype = Initiative AND parent = CNTIN-730 AND status != Cancelled",
    "maxResults": 100,
    "fields": "summary,status,assignee,priority,created,updated,duedate,description,labels",
    "nextPageToken": "..."  // 可选，分页令牌
}
```

**响应**:
```json
{
    "issues": [...],
    "nextPageToken": "...",
    "isLast": false
}
```

### 5.2 AI API

**Endpoint**: `POST /v1/chat/completions`

**请求**:
```json
{
    "model": "gpt-4o-mini",
    "messages": [
        {"role": "system", "content": "你是专业的业务分析师"},
        {"role": "user", "content": "..."}
    ],
    "temperature": 0.3,
    "max_tokens": 300
}
```

### 5.3 SMTP 接口

**服务器**: `smtp.qq.com:587`
**协议**: STARTTLS

---

## 6. 部署架构

### 6.1 文件结构

```
~/.openclaw/workspace/
├── scripts/
│   ├── cntin730_weekly_report.py      # 主脚本
│   ├── cntin730_report_v5.2_full.py   # 完整版生成器
│   └── send_fy26_report_v5.py         # 邮件发送
├── docs/
│   ├── brd/CNTIN730_Initiative_Report_BRD.md
│   ├── prd/CNTIN730_Initiative_Report_PRD.md
│   └── sdd/CNTIN730_Initiative_Report_SDD.md  # 本文档
├── reports/
│   └── cntin_730_report_YYYYMMDD_HHMM.html
├── jira-reports/
│   └── cache/                         # 语义缓存
├── logs/
│   └── cntin730_weekly_report.log
└── .jira-config                       # 配置文件

~/Library/LaunchAgents/
└── com.openclaw.cntin730-weekly-report.plist  # 定时任务
```

### 6.2 配置管理

**环境变量**:
- `JIRA_API_TOKEN`: Jira API 令牌
- `AI_API_KEY`: AI API 密钥
- `QQ_MAIL_PASSWORD`: QQ 邮箱 SMTP 密码

**配置文件** (`~/.openclaw/workspace/.jira-config`):
```bash
JIRA_BASE_URL="https://lululemon.atlassian.net"
JIRA_USER_EMAIL="rcheng2@lululemon.com"
JIRA_API_TOKEN="..."
EMAIL_RECIPIENT="chinatechpmo@lululemon.com"
EMAIL_CC="rcheng2@lululemon.com"
```

---

## 7. 监控与日志

### 7.1 日志级别

| 级别 | 使用场景 |
|------|----------|
| INFO | 正常流程步骤 |
| WARNING | 降级处理，缓存失效 |
| ERROR | API 失败，发送失败 |
| DEBUG | 详细调试信息 |

### 7.2 关键指标

```python
{
    "execution_time": {
        "data_fetch": 60,      # 秒
        "ai_processing": 300,  # 秒
        "html_generation": 3,  # 秒
        "email_sending": 10    # 秒
    },
    "data_quality": {
        "total_issues": 143,
        "ai_success_rate": 0.98,
        "cache_hit_rate": 0.60
    }
}
```

---

## 8. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.2.0 | 2026-03-19 | 新增 nextPageToken 分页支持、统计卡片、Assignee 筛选、Missing SLA、行展开、Excel 导出 |
| v1.1.0 | 2026-03-18 | 语义缓存、30 并发、Prompt 预精简、飞书发送 |
| v1.0.0 | 2026-03-18 | 初始架构 |
