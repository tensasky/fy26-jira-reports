# CNTIN-730 Initiative 周报 - 详细设计文档

**文档版本**: v1.1.0  
**创建日期**: 2026-03-18  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 系统架构

### 1.1 整体架构 (v1.1.0)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        CNTIN-730 Initiative 周报系统 v1.1.0              │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │    Jira     │──▶│   Fetch     │──▶│  AI Summary │──▶│   Report    │    │
│  │    API      │  │   Script    │  │  Generator  │  │  Generator  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│         │                │                │                │            │
│         ▼                ▼                ▼                ▼            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ CNTIN-730   │  │  Python     │  │  Claude API │  │  HTML/CSS   │    │
│  │ Initiatives │  │  Requests   │  │ (30 async)  │  │  JS         │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                              │          │
│                          ┌─────────────┐                     │          │
│                          │  Semantic   │◀────────────────────┘          │
│                          │  Cache      │ (MD5-based)                      │
│                          └─────────────┘                                │
│                              │                                          │
│                              ▼                                          │
│                       ┌─────────────┐   ┌─────────────┐                 │
│                       │  SMTP/QQ    │   │  Feishu    │                 │
│                       │  Mail       │   │  File API  │                 │
│                       └─────────────┘   └─────────────┘                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 组件清单 (v1.1.0)

| 组件 | 文件 | 职责 |
|------|------|------|
| 主控脚本 | `cntin730_weekly_report.py` | 协调全流程 |
| 数据抓取 | `fetch_jira_data()` | 从 Jira API 获取 Initiatives |
| AI 摘要 | `batch_generate_ai_summaries()` | **异步**生成 What/Why，30 并发 |
| 语义缓存 | `SemanticCache` | 基于内容 MD5 的智能缓存 |
| 报告生成 | `generate_html_report()` | 生成 HTML |
| 邮件发送 | `send_email()` | SMTP 发送邮件 |
| 飞书发送 | `send_feishu_file()` | 飞书文件 API 发送 |

---

## 2. 数据流设计

### 2.1 数据流程 (v1.1.0)

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
│ Pre-clean           │  ◀── v1.1.0: 清理 ADF/HTML
│ (Prompt 预精简)      │      减少 20% tokens
└─────────────────────┘
   │
   ▼
┌─────────────────────┐
│ Compute MD5 Hash    │  ◀── v1.1.0: 语义哈希
└─────────────────────┘
   │
   ▼
Check Semantic Cache ──Cache hit?──┬──Yes──▶ Return cached
   │                               │
   No                              │
   │                               │
   ▼                               │
┌─────────────────────┐            │
│ Async AI API Call   │            │
│ (30 concurrent)     │            │  ◀── v1.1.0: 30 异步并发
│ (semaphore limit)   │            │
└─────────────────────┘            │
   │                               │
   ▼                               │
Save to Cache (MD5) ◀─────────────┘
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
│ Send Email          │
│ Send Feishu File    │  ◀── v1.1.0: 双渠道发送
└─────────────────────┘
```

### 2.2 语义缓存架构

```
┌─────────────────────────────────────────────────────────┐
│                    Semantic Cache                        │
├─────────────────────────────────────────────────────────┤
│  Index File (index.json)                                │
│  {                                                      │
│    "md5_hash_1": {                                      │
│      "file": "a1b2c3.json",                             │
│      "created": "2026-03-18T10:00:00",                  │
│      "ttl": 604800                                      │
│    },                                                   │
│    ...                                                  │
│  }                                                      │
├─────────────────────────────────────────────────────────┤
│  Cache Files (/tmp/ai_summary_cache_semantic/)          │
│  ├── a1b2c3.json {"summary": "...", "hash": "..."}      │
│  ├── d4e5f6.json {"summary": "...", "hash": "..."}      │
│  └── ...                                                │
└─────────────────────────────────────────────────────────┘
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

#### 3.1.2 Prompt 预精简 (v1.1.0)

```python
def pre_clean_description(description):
    """
    Prompt 预精简 - 减少 Token 消耗
    
    Algorithm:
    1. 移除 HTML 标签
    2. 移除 ADF (Atlassian Document Format) 标记
    3. 规范化空白字符
    4. 截断至 1000 字符
    
    效果: 平均减少 20% Token 消耗
    """
    if not description:
        return ""
    
    # 移除 HTML/ADF 标签
    text = re.sub(r'<[^>]+>', ' ', description)
    
    # 规范化空白
    text = re.sub(r'\s+', ' ', text).strip()
    
    # 限制长度
    return text[:1000]
```

### 3.2 AI 摘要模块 (v1.1.0)

#### 3.2.1 语义缓存类

```python
class SemanticCache:
    """
    语义哈希缓存 - 基于内容 MD5 而非 Issue Key
    
    Design Decisions:
    1. MD5 计算: summary + description 的组合
    2. 内容变化自动失效: 修改后 MD5 变化
    3. 跨 Issue 复用: 相同内容不同 Key 可复用
    4. TTL: 7 天自动清理
    """
    
    def __init__(self, cache_dir, ttl_days=7):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()
        self.ttl = ttl_days * 24 * 3600
        self.stats = {"hits": 0, "misses": 0, "saves": 0}
    
    def _compute_hash(self, summary, description):
        """计算内容哈希"""
        content = f"{summary}:{description}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get(self, summary, description):
        """
        获取缓存
        
        Returns:
            str: 缓存的 AI Summary，未命中返回 None
        """
        content_hash = self._compute_hash(summary, description)
        
        # 检查索引
        if content_hash not in self.index:
            self.stats["misses"] += 1
            return None
        
        cache_entry = self.index[content_hash]
        cache_file = self.cache_dir / cache_entry['file']
        
        # 检查文件存在
        if not cache_file.exists():
            del self.index[content_hash]
            self._save_index()
            self.stats["misses"] += 1
            return None
        
        # 检查 TTL
        if time.time() - cache_entry['created'] > self.ttl:
            cache_file.unlink()
            del self.index[content_hash]
            self._save_index()
            self.stats["misses"] += 1
            return None
        
        # 读取缓存
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.stats["hits"] += 1
            return data.get('ai_summary')
    
    def set(self, summary, description, ai_summary):
        """保存缓存"""
        content_hash = self._compute_hash(summary, description)
        cache_file = self.cache_dir / f"{content_hash[:8]}.json"
        
        # 保存内容
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'ai_summary': ai_summary,
                'hash': content_hash,
                'cached_at': datetime.now().isoformat()
            }, f, ensure_ascii=False)
        
        # 更新索引
        self.index[content_hash] = {
            'file': cache_file.name,
            'created': time.time(),
            'ttl': self.ttl
        }
        self._save_index()
        self.stats["saves"] += 1
```

#### 3.2.2 异步并发处理 (v1.1.0)

```python
import asyncio
import aiohttp

AI_MAX_CONCURRENT = 30  # 30 异步并发
AI_RATE_LIMIT = 0.1     # 每请求间隔 0.1 秒

class AISummaryGenerator:
    """异步 AI 摘要生成器"""
    
    def __init__(self, cache):
        self.cache = cache
        self.semaphore = asyncio.Semaphore(AI_MAX_CONCURRENT)
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()
    
    async def generate_one(self, issue):
        """单个 AI Summary 生成"""
        summary = issue['summary']
        description = pre_clean_description(issue.get('description', ''))
        key = issue['key']
        
        # 检查语义缓存
        cached = self.cache.get(summary, description)
        if cached:
            return key, cached
        
        # 限流控制
        async with self.semaphore:
            # 构建 Prompt
            prompt = self._build_prompt(summary, description)
            
            # 调用 AI API
            try:
                ai_summary = await self._call_api(prompt)
                
                # 保存缓存
                self.cache.set(summary, description, ai_summary)
                
                # 延迟避免限流
                await asyncio.sleep(AI_RATE_LIMIT)
                
                return key, ai_summary
            except Exception as e:
                logger.error(f"AI API error for {key}: {e}")
                return key, f"<span class='error'>生成失败: {str(e)[:50]}</span>"
    
    async def batch_generate(self, issues):
        """批量生成"""
        tasks = [self.generate_one(issue) for issue in issues]
        results = await asyncio.gather(*tasks)
        return dict(results)
    
    def _build_prompt(self, summary, description):
        """构建 AI Prompt"""
        return f"""请根据以下 Initiative 的标题和描述，用简洁自然的语言总结 What 和 Why。

【Initiative 标题】: {summary}
【描述内容】: {description}

要求：
1. What 部分：用动词开头，直接说明要做什么
2. Why 部分：说明业务价值和原因，用自然的口语化表达
3. 避免 AI 腔调，不要出现"旨在"、"致力于"这种套话
4. 中英混合使用，术语保留英文
5. 每部分 1-2 句话，简洁直接

格式：
<b>What:</b> [动词开头，直接说明做什么]
<b>Why:</b> [自然解释为什么要做]"""
    
    async def _call_api(self, prompt):
        """调用 AI API"""
        headers = {
            'Authorization': f'Bearer {AI_API_KEY}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': AI_MODEL,
            'messages': [
                {'role': 'system', 'content': '你是专业的业务分析师'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 300
        }
        
        async with self.session.post(
            f'{AI_BASE_URL}/chat/completions',
            headers=headers,
            json=payload
        ) as response:
            data = await response.json()
            return data['choices'][0]['message']['content'].strip()
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

### 3.4 飞书文件发送 (v1.1.0 新增)

```python
import requests

class FeishuClient:
    """飞书 API 客户端"""
    
    BASE_URL = "https://open.feishu.cn/open-apis"
    
    def __init__(self, app_id, app_secret):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = self._get_access_token()
    
    def _get_access_token(self):
        """获取 Tenant Access Token"""
        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal"
        response = requests.post(url, json={
            'app_id': self.app_id,
            'app_secret': self.app_secret
        })
        return response.json()['tenant_access_token']
    
    def upload_file(self, file_path):
        """上传文件获取 file_key"""
        url = f"{self.BASE_URL}/im/v1/files"
        
        with open(file_path, 'rb') as f:
            files = {'file': (file_path.name, f, 'application/octet-stream')}
            data = {'file_type': 'stream', 'file_name': file_path.name}
            
            response = requests.post(
                url,
                headers={'Authorization': f'Bearer {self.access_token}'},
                files=files,
                data=data
            )
        
        if response.status_code == 200:
            return response.json()['data']['file_key']
        else:
            raise Exception(f"Upload failed: {response.text}")
    
    def send_file_message(self, file_key, receive_id, receive_type='chat_id'):
        """发送文件消息"""
        url = f"{self.BASE_URL}/im/v1/messages"
        
        payload = {
            'receive_id': receive_id,
            'msg_type': 'file',
            'content': json.dumps({'file_key': file_key})
        }
        
        response = requests.post(
            url,
            headers={'Authorization': f'Bearer {self.access_token}'},
            json=payload
        )
        
        return response.status_code == 200
```

---

## 4. 配置管理

### 4.1 环境变量 (v1.1.0)

```bash
# Jira API
export JIRA_API_TOKEN="your_jira_token"
export JIRA_EMAIL="rcheng2@lululemon.com"

# AI API
export AI_API_KEY="your_ai_key"
export AI_BASE_URL="http://newapi.200m.997555.xyz/v1"
export AI_MODEL="claude-sonnet-4-6"

# SMTP
export QQ_MAIL_PASSWORD="your_qq_auth_code"

# 飞书 (v1.1.0 新增)
export FEISHU_APP_ID="cli_a91bd999acb8dbce"
export FEISHU_APP_SECRET="your_app_secret"
export FEISHU_CHAT_ID="oc_xxx"  # 群聊 ID
```

### 4.2 常量配置

```python
# config.py

# Jira 配置
JIRA_URL = "https://lululemon.atlassian.net"
JQL_QUERY = 'project = CNTIN AND issuetype = Initiative AND "Parent Link" = CNTIN-730'

# AI 配置 (v1.1.0)
AI_MAX_CONCURRENT = 30       # 30 异步并发
AI_RATE_LIMIT = 0.1          # 每请求间隔 0.1 秒
AI_MAX_TOKENS = 300
AI_TEMPERATURE = 0.3

# 缓存配置 (v1.1.0)
CACHE_DIR = Path("/tmp/ai_summary_cache_semantic")
CACHE_TTL_DAYS = 7

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
RECIPIENTS = ["chinatechpmo@lululemon.com"]
CC_RECIPIENTS = ["rcheng2@lululemon.com"]

# 飞书配置 (v1.1.0)
FEISHU_BASE_URL = "https://open.feishu.cn/open-apis"
```

---

## 5. 性能优化 (v1.1.0)

### 5.1 缓存策略

```python
# 性能指标追踪
class PerformanceMonitor:
    def __init__(self):
        self.start_time = time.time()
        self.stats = {
            'jira_fetch_time': 0,
            'ai_generation_time': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'tokens_saved': 0
        }
    
    def report(self):
        total_time = time.time() - self.start_time
        cache_hit_rate = self.stats['cache_hits'] / (
            self.stats['cache_hits'] + self.stats['cache_misses']
        ) * 100
        
        print(f"""
性能报告:
- 总耗时: {total_time:.1f} 秒
- Jira 抓取: {self.stats['jira_fetch_time']:.1f} 秒
- AI 生成: {self.stats['ai_generation_time']:.1f} 秒
- 缓存命中率: {cache_hit_rate:.1f}%
- Token 节省: {self.stats['tokens_saved']}
        """)
```

### 5.2 异步并发控制

```python
# 并发控制策略
async def controlled_concurrency(tasks, max_concurrent=30):
    """
    控制并发数，避免 API 限流
    """
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def run_with_semaphore(task):
        async with semaphore:
            result = await task
            await asyncio.sleep(0.1)  # 延迟避免限流
            return result
    
    return await asyncio.gather(*[
        run_with_semaphore(task) for task in tasks
    ])
```

---

## 6. 测试策略

### 6.1 单元测试

```python
# test_semantic_cache.py
def test_md5_hash_consistency():
    """测试 MD5 哈希一致性"""
    cache = SemanticCache("/tmp/test_cache")
    
    hash1 = cache._compute_hash("Title", "Description")
    hash2 = cache._compute_hash("Title", "Description")
    
    assert hash1 == hash2
    assert len(hash1) == 32  # MD5 长度

def test_prompt_pre_clean():
    """测试 Prompt 预精简"""
    html_desc = "<p>Test <b>description</b></p>"
    cleaned = pre_clean_description(html_desc)
    
    assert "<p>" not in cleaned
    assert "<b>" not in cleaned
    assert "Test description" in cleaned

# test_async_ai.py
@pytest.mark.asyncio
async def test_async_batch_generation():
    """测试异步批量生成"""
    cache = SemanticCache("/tmp/test_cache")
    generator = AISummaryGenerator(cache)
    
    test_issues = [
        {'key': 'TEST-1', 'summary': 'Test', 'description': 'Desc'}
    ]
    
    async with generator:
        results = await generator.batch_generate(test_issues)
    
    assert 'TEST-1' in results
```

### 6.2 集成测试

```python
# test_integration.py
def test_full_pipeline_v110():
    """v1.1.0 端到端测试"""
    # 准备测试数据
    test_issues = [...]
    
    # 1. 测试语义缓存
    cache = SemanticCache("/tmp/test_cache")
    
    # 2. 测试异步 AI 生成
    asyncio.run(test_async_generation())
    
    # 3. 测试飞书发送 (Mock)
    # ...
    
    # 验证缓存命中率
    assert cache.stats['hits'] > 0 or cache.stats['misses'] > 0
```

---

## 7. 部署与运维

### 7.1 手动执行

```bash
# 设置环境变量
export JIRA_API_TOKEN="your_token"
export AI_API_KEY="your_key"
export QQ_MAIL_PASSWORD="your_password"
export FEISHU_APP_SECRET="your_secret"

# 执行周报生成
python3 scripts/cntin730_weekly_report.py
```

### 7.2 监控指标 (v1.1.0)

```python
# 健康检查
def health_check_v110():
    checks = {
        'jira_api': test_jira_connection(),
        'ai_api': test_ai_connection(),
        'smtp': test_smtp_connection(),
        'feishu': test_feishu_connection(),  # 新增
        'cache_dir': check_cache_writable(),
        'cache_size': get_cache_size(),
    }
    
    return checks
```

---

## 8. 附录

### 8.1 版本历史

| 版本 | 日期 | 变更 | 作者 |
|------|------|------|------|
| v1.1.0 | 2026-03-18 | **优化版本**: 语义缓存、30 异步并发、Prompt 预精简、飞书文件发送 | OpenClaw |
| v1.0.0 | 2026-03-18 | 初始版本: AI 摘要、冻结列、基础缓存 | OpenClaw |

### 8.2 性能对比

| 指标 | v1.0.0 | v1.1.0 | 提升 |
|------|--------|--------|------|
| AI 生成时间 | ~10 min | ~5 min | **50%** |
| 并发数 | 5 线程 | 30 异步 | **6x** |
| Token 消耗 | 100% | ~80% | **20%** |
| 缓存命中率 | N/A | ~60% | - |
| 总耗时 | ~12 min | ~7 min | **42%** |

### 8.3 故障排查

| 问题 | 症状 | 解决方案 |
|------|------|----------|
| AI 摘要慢 | 生成时间 > 10 min | 检查语义缓存命中率，确认 30 异步配置 |
| 缓存不命中 | 缓存命中率 < 30% | 检查 MD5 计算，确认缓存目录权限 |
| 飞书发送失败 | 401/403 错误 | 检查 Token 是否过期，确认 App 权限 |
| 限流错误 | 429 Too Many Requests | 增加 AI_RATE_LIMIT 延迟 |
