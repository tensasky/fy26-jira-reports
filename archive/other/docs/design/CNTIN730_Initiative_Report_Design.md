# CNTIN-730 Initiative 周报 - 详细设计文档

**文档版本**: v1.0.0  
**创建日期**: 2026-03-18  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 系统架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CNTIN-730 Initiative 周报系统                     │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │    Jira     │──▶│   Fetch     │──▶│  AI Summary │──▶│   Report    │    │
│  │    API      │  │   Script    │  │  Generator  │  │  Generator  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│         │                │                │                │            │
│         ▼                ▼                ▼                ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ CNTIN-730   │  │  Python     │  │  Claude API │  │  HTML/CSS   │    │
│  │ Initiatives │  │  Requests   │  │  (5 workers)│  │  JS         │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                              │          │
│                                                              ▼          │
│                                                       ┌─────────────┐   │
│                                                       │  SMTP/QQ    │   │
│                                                       │  Mail       │   │
│                                                       └─────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 组件清单

| 组件 | 文件 | 职责 |
|------|------|------|
| 主控脚本 | `cntin730_weekly_report.py` | 协调全流程 |
| 数据抓取 | `fetch_jira_data()` | 从 Jira API 获取 Initiatives |
| AI 摘要 | `batch_generate_ai_summaries()` | 并发生成 What/Why |
| 报告生成 | `generate_html_report()` | 生成 HTML |
| 邮件发送 | `send_email()` | 发送邮件 |

---

## 2. 数据流设计

### 2.1 数据流程

```
Jira API
   │
   ▼
┌─────────────────────┐
│ fetch_jira_data()   │
│ - JQL query         │
│ - Pagination        │
│ - Error handling    │
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│ issues_data[]       │
│ [{key, summary,    │
│   description, ...}]│
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│ batch_generate_     │
│ ai_summaries()      │
│ - 5 workers         │
│ - Cache check       │
│ - API call          │
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│ ai_summary_results  │
│ {key: summary_text} │
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│ generate_html_      │
│ report()            │
│ - Frozen columns    │
│ - Filters           │
│ - Styling           │
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│ HTML File           │
│ + Email             │
└─────────────────────┘
```

### 2.2 AI 摘要缓存

```
Request comes in
      │
      ▼
Check cache ──Cache hit?──┬──Yes──▶ Return cached
      │                   │
      No                  │
      │                   │
      ▼                   │
Call AI API               │
      │                   │
      ▼                   │
Save to cache ◀───────────┘
      │
      ▼
Return result
```

---

## 3. 模块详细设计

### 3.1 数据抓取模块

#### 3.1.1 JQL 构造

```python
JQL_QUERY = 'project = CNTIN AND issuetype = Initiative AND "Parent Link" = CNTIN-730'

# API 调用参数
params = {
    'jql': JQL_QUERY,
    'startAt': start_at,
    'maxResults': 100,
    'fields': 'summary,status,assignee,priority,created,updated,duedate,description,labels'
}
```

#### 3.1.2 分页处理

```python
def fetch_all_initiatives():
    """
    分页抓取所有 Initiatives
    
    Algorithm:
    1. 初始请求，获取第一页和总数
    2. while 循环直到获取全部
    3. 每次请求后 startAt += 100
    4. 异常时指数退避重试
    """
    all_issues = []
    start_at = 0
    max_results = 100
    
    while True:
        response = jira_api.search(jql=JQL_QUERY, startAt=start_at)
        issues = response['issues']
        all_issues.extend(issues)
        
        if len(all_issues) >= response['total']:
            break
            
        start_at += max_results
        time.sleep(0.5)  # 避免限流
    
    return all_issues
```

### 3.2 AI 摘要模块

#### 3.2.1 Prompt 模板

```python
AI_SUMMARY_PROMPT = """请根据以下 Initiative 的标题和描述，用简洁自然的语言总结 What 和 Why。

【Initiative 标题】: {summary}
【描述内容】: {description}

要求：
1. What 部分：用动词开头，直接说明要做什么。比如"搭建...系统"、"优化...流程"、"迁移...数据"
2. Why 部分：说明业务价值和原因，用自然的口语化表达
3. 避免 AI 腔调，不要出现"旨在"、"致力于"、"通过...实现"这种套话
4. 中英混合使用，术语保留英文（如 API、POS、OMS）
5. 每部分 1-2 句话，简洁直接

格式：
<b>What:</b> [动词开头，直接说明做什么]
<b>Why:</b> [自然解释为什么要做]

示例：
<b>What:</b> 把线下门店的 POS 系统从旧版升级到 Cloud POS，支持全渠道退货和实时库存查询
<b>Why:</b> 现在门店退货要查好几个系统，太慢了，升级后一个界面搞定，提升顾客体验和店员效率

输出格式用 <b> 标签加粗标题。"""
```

#### 3.2.2 并发处理

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def batch_generate_ai_summaries(issues_data, max_workers=5):
    """
    并发生成 AI Summary
    
    Design decisions:
    - 5 workers: 平衡速度和 API 限流
    - 0.3s delay: 避免触发限流
    - Cache first: 减少 API 调用
    - Fallback: 失败时返回占位符
    """
    results = {}
    
    # 过滤出有描述的 issues
    issues_with_desc = [
        (d['description'], d['summary'], d['key'])
        for d in issues_data
        if d.get('description') and len(d['description']) >= 10
    ]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(generate_one, args): args[2]
            for args in issues_with_desc
        }
        
        for future in as_completed(futures):
            key = futures[future]
            try:
                summary = future.result()
                results[key] = summary
            except Exception as e:
                logger.error(f"Failed for {key}: {e}")
                results[key] = "<span class='ai-summary-error'>生成失败</span>"
    
    return results

def generate_one(args):
    """单个 AI Summary 生成"""
    description, summary, key = args
    
    # 检查缓存
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        return load_cache(cache_file)
    
    # 调用 AI API
    prompt = AI_SUMMARY_PROMPT.format(
        summary=summary,
        description=description[:1000]  # 限制长度
    )
    
    response = ai_client.chat.completions.create(
        model="claude-sonnet-4-6",
        messages=[
            {"role": "system", "content": "你是一个专业的业务分析师..."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=300
    )
    
    ai_summary = response.choices[0].message.content.strip()
    
    # 保存缓存
    save_cache(cache_file, ai_summary)
    
    # 延迟避免限流
    time.sleep(0.3)
    
    return ai_summary
```

### 3.3 冻结列实现

#### 3.3.1 CSS 架构

```css
/* 容器 */
.issues-table {
    overflow-x: auto;
    max-width: 100%;
}

table {
    border-collapse: separate;
    border-spacing: 0;
    table-layout: auto;
    min-width: 1600px; /* 强制滚动 */
}

/* 基础单元格 */
th, td {
    background: white;
    position: relative;
}

/* 冻结列基础 */
.col-key-summary,
.col-status,
.col-assignee {
    position: sticky;
    background: white;
    z-index: 10;
}

/* 第一列 - Key/Summary */
.col-key-summary {
    left: 0;
    min-width: 280px;
    max-width: 350px;
    z-index: 30; /* 最高 */
}

/* 第二列 - Status */
.col-status {
    left: 280px; /* 第一列宽度 */
    width: 90px;
    border-left: 1px solid #EBECF0;
    z-index: 20;
}

/* 第三列 - Assignee */
.col-assignee {
    left: 370px; /* 280 + 90 */
    width: 110px;
    border-left: 1px solid #EBECF0;
    z-index: 20;
}

/* 表头特殊处理 */
th.col-key-summary,
th.col-status,
th.col-assignee {
    background: #F4F5F7;
    z-index: 40; /* 表头在最上层 */
}

/* 悬停效果 */
tr:hover .col-key-summary,
tr:hover .col-status,
tr:hover .col-assignee {
    background: #F4F5F7;
}
```

#### 3.3.2 浏览器兼容性

```css
/* 标准语法 */
position: sticky;

/* Safari 前缀（旧版本） */
position: -webkit-sticky;

/* 检查支持 */
@supports (position: sticky) or (position: -webkit-sticky) {
    .frozen-col {
        position: sticky;
    }
}

/* 不支持 sticky 的降级方案 */
@supports not ((position: sticky) or (position: -webkit-sticky)) {
    .issues-table {
        overflow-x: scroll;
    }
    .frozen-col {
        position: static;
    }
}
```

### 3.4 交互功能

#### 3.4.1 行展开

```javascript
function toggleRow(row) {
    const summary = row.querySelector('.issue-summary');
    const description = row.querySelector('.description-cell');
    const aiSummary = row.querySelector('.ai-summary-cell');
    
    // 切换展开状态
    const isExpanded = row.classList.toggle('expanded');
    
    // 同步更新内部元素
    if (summary) summary.classList.toggle('expanded', isExpanded);
    if (description) description.classList.toggle('expanded', isExpanded);
    if (aiSummary) aiSummary.classList.toggle('expanded', isExpanded);
}
```

#### 3.4.2 筛选系统

```javascript
class FilterManager {
    constructor() {
        this.filters = {
            status: 'all',
            label: 'all',
            alert: null,
            search: ''
        };
        this.init();
    }
    
    init() {
        // 状态筛选
        document.querySelectorAll('.filter-btn[data-status]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setFilter('status', e.target.dataset.status);
            });
        });
        
        // Label 筛选
        document.querySelectorAll('.filter-btn[data-label]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setFilter('label', e.target.dataset.label);
            });
        });
        
        // 搜索
        const searchInput = document.getElementById('searchInput');
        searchInput.addEventListener('keyup', debounce((e) => {
            this.setFilter('search', e.target.value.toLowerCase());
        }, 300));
    }
    
    applyFilters() {
        const rows = document.querySelectorAll('tbody tr');
        
        rows.forEach(row => {
            const matches = this.checkRowMatches(row);
            row.style.display = matches ? '' : 'none';
        });
    }
    
    checkRowMatches(row) {
        const status = row.dataset.status;
        const labels = row.dataset.labels.split(',');
        const hasSla = row.dataset.hasSla === 'true';
        const text = row.textContent.toLowerCase();
        
        // 状态匹配
        if (this.filters.status !== 'all' && status !== this.filters.status) {
            return false;
        }
        
        // Label 匹配
        if (this.filters.label !== 'all' && !labels.includes(this.filters.label)) {
            return false;
        }
        
        // SLA Alert 匹配
        if (this.filters.alert === 'sla' && !hasSla) {
            return false;
        }
        
        // 搜索匹配
        if (this.filters.search && !text.includes(this.filters.search)) {
            return false;
        }
        
        return true;
    }
}

// 防抖函数
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
```

### 3.5 邮件发送

#### 3.5.1 双模式 SMTP

```python
class DualModeSMTP:
    """
    双模式 SMTP 发送器
    
    支持 SSL (465) 和 STARTTLS (587) 两种模式
    自动选择最优连接方式
    """
    
    def __init__(self, host, ssl_port=465, tls_port=587):
        self.host = host
        self.ssl_port = ssl_port
        self.tls_port = tls_port
        self.username = os.environ.get('SENDER_EMAIL')
        self.password = os.environ.get('QQ_MAIL_PASSWORD')
    
    def send(self, recipients, subject, html_content, attachment_path):
        """
        发送邮件，自动选择最佳 SMTP 模式
        
        Strategy:
        1. 优先尝试 SSL (更稳定)
        2. SSL 失败时回退到 STARTTLS
        3. 记录失败原因
        """
        try:
            return self._send_ssl(recipients, subject, html_content, attachment_path)
        except smtplib.SMTPException as ssl_error:
            logger.warning(f"SSL connection failed: {ssl_error}")
            try:
                return self._send_starttls(recipients, subject, html_content, attachment_path)
            except smtplib.SMTPException as tls_error:
                logger.error(f"Both SSL and STARTTLS failed: {tls_error}")
                raise
    
    def _send_ssl(self, recipients, subject, html_content, attachment_path):
        """SSL 模式发送"""
        with smtplib.SMTP_SSL(self.host, self.ssl_port, timeout=30) as server:
            server.login(self.username, self.password)
            msg = self._build_message(recipients, subject, html_content, attachment_path)
            server.sendmail(self.username, recipients, msg.as_string())
            logger.info("Email sent via SSL")
            return True
    
    def _send_starttls(self, recipients, subject, html_content, attachment_path):
        """STARTTLS 模式发送"""
        with smtplib.SMTP(self.host, self.tls_port, timeout=30) as server:
            server.starttls()
            server.login(self.username, self.password)
            msg = self._build_message(recipients, subject, html_content, attachment_path)
            server.sendmail(self.username, recipients, msg.as_string())
            logger.info("Email sent via STARTTLS")
            return True
    
    def _build_message(self, recipients, subject, html_content, attachment_path):
        """构建 MIME 邮件"""
        msg = MIMEMultipart('alternative')
        msg['From'] = self.username
        msg['To'] = ', '.join(recipients['to'])
        msg['Cc'] = ', '.join(recipients['cc'])
        msg['Subject'] = subject
        
        # HTML 内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 附件
        with open(attachment_path, 'rb') as f:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(f.read())
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="{attachment_path.name}"'
        )
        msg.attach(attachment)
        
        return msg
```

---

## 4. 配置管理

### 4.1 环境变量

```bash
# Jira API
export JIRA_API_TOKEN="your_jira_token"
export JIRA_EMAIL="rcheng2@lululemon.com"

# AI API
export AI_API_KEY="your_ai_key"
export AI_BASE_URL="http://newapi.200m.997555.xyz/v1"
export AI_MODEL="claude-sonnet-4-6"

# SMTP
export SENDER_EMAIL="3823810468@qq.com"
export QQ_MAIL_PASSWORD="ftbabipdlxliceai"
```

### 4.2 常量配置

```python
# config.py

# Jira 配置
JIRA_URL = "https://lululemon.atlassian.net"
JQL_QUERY = 'project = CNTIN AND issuetype = Initiative AND "Parent Link" = CNTIN-730'

# AI 配置
AI_MAX_WORKERS = 5
AI_DELAY_BETWEEN_REQUESTS = 0.3  # seconds
AI_MAX_TOKENS = 300
AI_TEMPERATURE = 0.3

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_SSL_PORT = 465
SMTP_TLS_PORT = 587
RECIPIENTS = ["chinatechpmo@lululemon.com"]
CC_RECIPIENTS = ["rcheng2@lululemon.com"]

# 路径配置
CACHE_DIR = Path("/tmp/ai_summary_cache")
REPORTS_DIR = Path("/Users/admin/.openclaw/workspace/reports")
```

---

## 5. 错误处理

### 5.1 错误分类与处理

```python
class ErrorHandler:
    """统一错误处理"""
    
    @staticmethod
    def handle_jira_error(error, context):
        """处理 Jira API 错误"""
        if error.status_code == 429:
            # 限流，指数退避
            return 'retry_with_backoff'
        elif error.status_code == 401:
            # 认证失败
            send_alert("Jira API Token 失效")
            raise SystemExit(1)
        else:
            logger.error(f"Jira API error: {error}")
            return 'continue'
    
    @staticmethod
    def handle_ai_error(error, initiative_key):
        """处理 AI API 错误"""
        if 'rate limit' in str(error).lower():
            time.sleep(5)
            return 'retry'
        else:
            logger.error(f"AI summary failed for {initiative_key}: {error}")
            return 'fallback'
    
    @staticmethod
    def handle_smtp_error(error):
        """处理 SMTP 错误"""
        if 'authentication' in str(error).lower():
            send_alert("SMTP 认证失败，检查密码")
        else:
            logger.error(f"SMTP error: {error}")
        return 'failed'
```

---

## 6. 性能优化

### 6.1 缓存策略

```python
class AISummaryCache:
    """
    AI Summary 缓存管理
    
    - 文件系统缓存
    - JSON 格式存储
    - TTL: 7 天
    """
    
    def __init__(self, cache_dir, ttl_days=7):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = timedelta(days=ttl_days)
    
    def get(self, key):
        cache_file = self.cache_dir / f"{key}.json"
        
        if not cache_file.exists():
            return None
        
        # 检查 TTL
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        if datetime.now() - mtime > self.ttl:
            cache_file.unlink()
            return None
        
        with open(cache_file) as f:
            data = json.load(f)
            return data.get('summary')
    
    def set(self, key, summary):
        cache_file = self.cache_dir / f"{key}.json"
        with open(cache_file, 'w') as f:
            json.dump({
                'summary': summary,
                'cached_at': datetime.now().isoformat()
            }, f)
```

### 6.2 并发控制

```python
from concurrent.futures import ThreadPoolExecutor
import threading

class RateLimiter:
    """API 调用速率限制器"""
    
    def __init__(self, max_calls_per_second=3):
        self.min_interval = 1.0 / max_calls_per_second
        self.last_call_time = 0
        self.lock = threading.Lock()
    
    def acquire(self):
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_call_time
            
            if time_since_last < self.min_interval:
                time.sleep(self.min_interval - time_since_last)
            
            self.last_call_time = time.time()
```

---

## 7. 测试策略

### 7.1 单元测试

```python
# test_ai_summary.py
def test_prompt_building():
    """测试 Prompt 构建"""
    description = "Implement new feature"
    summary = "Feature X"
    
    prompt = build_prompt(summary, description)
    
    assert "Feature X" in prompt
    assert "Implement new feature" in prompt
    assert "<b>What:</b>" in prompt

def test_cache_operations():
    """测试缓存读写"""
    cache = AISummaryCache("/tmp/test_cache")
    
    # 写
    cache.set("TEST-1", "Summary text")
    
    # 读
    result = cache.get("TEST-1")
    assert result == "Summary text"
    
    # 不存在的 key
    assert cache.get("NONEXISTENT") is None
```

### 7.2 集成测试

```python
# test_integration.py
def test_full_pipeline():
    """端到端测试"""
    # 准备测试数据
    test_issues = [
        {
            'key': 'CNTIN-TEST-1',
            'summary': 'Test Initiative',
            'description': 'Test description',
            'status': 'Discovery'
        }
    ]
    
    # 执行流程
    ai_results = batch_generate_ai_summaries(test_issues)
    html = generate_html_report(test_issues, ai_results)
    
    # 验证
    assert 'CNTIN-TEST-1' in html
    assert '<b>What:</b>' in html or '生成失败' in html
```

---

## 8. 部署与运维

### 8.1 手动执行

```bash
# 设置环境变量
export JIRA_API_TOKEN="your_token"
export QQ_MAIL_PASSWORD="your_password"

# 执行周报生成
python3 scripts/cntin730_weekly_report.py
```

### 8.2 定时任务（可选）

```bash
# 每周一 9:00 执行
crontab -e

# 添加
0 9 * * 1 cd /Users/admin/.openclaw/workspace && \
  export JIRA_API_TOKEN="your_token" && \
  export QQ_MAIL_PASSWORD="your_password" && \
  python3 scripts/cntin730_weekly_report.py >> logs/cntin730-cron.log 2>&1
```

### 8.3 监控

```python
# 健康检查脚本
def health_check():
    checks = {
        'jira_api': test_jira_connection(),
        'ai_api': test_ai_connection(),
        'smtp': test_smtp_connection(),
        'cache_dir': check_cache_writable(),
    }
    
    for name, status in checks.items():
        if not status:
            send_alert(f"Health check failed: {name}")
    
    return all(checks.values())
```

---

## 9. 附录

### 9.1 版本历史

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v1.0.0 | 2026-03-18 | 初始版本，AI 摘要，冻结列 | OpenClaw |

### 9.2 参考资料

- [CSS Position Sticky](https://developer.mozilla.org/en-US/docs/Web/CSS/position#sticky)
- [Python Concurrent Futures](https://docs.python.org/3/library/concurrent.futures.html)
- [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)

### 9.3 故障排查

| 问题 | 症状 | 解决方案 |
|------|------|----------|
| AI 摘要慢 | 生成时间 > 20 分钟 | 检查缓存，减少并发数 |
| 冻结列失效 | 列随滚动移动 | 检查浏览器支持 CSS sticky |
| 邮件失败 | Connection closed | 更新 QQ_MAIL_PASSWORD |
| 数据不完整 | Initiative 数量少 | 检查 Jira API Token 权限 |

### 9.4 AI 提示词优化记录

**v1.0.0 提示词**:
- 动词开头要求
- 避免 AI 腔调
- 中英混合示例
- 自然语言表达

**未来优化方向**:
- 按领域定制提示词（技术/业务/数据）
- Few-shot 学习优化
- 输出格式模板化
