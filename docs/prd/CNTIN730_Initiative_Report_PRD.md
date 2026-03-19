# CNTIN-730 Initiative 周报 - 产品需求文档 (PRD)

**文档版本**: v1.1.0  
**创建日期**: 2026-03-18  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 产品概述

### 1.1 产品目标
构建一个自动化的周报系统，从 Jira CNTIN-730 抓取所有 Initiative 数据，使用 AI 生成标准化的 What/Why 业务解释，生成可交互的 HTML 报告，并通过邮件 + 飞书双渠道自动发送给 PMO 团队。

### 1.2 用户画像

#### 主要用户: China Tech PMO
- **角色**: 项目经理、项目协调员
- **目标**: 快速了解所有 CNTIN-730 Initiatives 的状态和业务背景
- **痛点**: 
  - 100+ Initiatives 难以理解
  - 每个 Initiative 描述风格各异
  - 缺乏统一的业务语言
- **使用场景**: 每周查看邮件/飞书中的周报，准备项目会议

#### 次要用户: 技术负责人
- **角色**: Roberto Cheng 等技术领导
- **目标**: 监督整体项目组合健康状况
- **使用场景**: 查看 SLA Alert，识别需要关注的 Initiative

### 1.3 产品范围

**包含**:
- CNTIN-730 下所有 Initiative 数据抓取
- AI 智能摘要生成（What/Why）
- 语义哈希缓存（基于内容 MD5）
- 冻结列表格设计
- 交互式筛选和搜索
- 邮件 + 飞书双渠道发送

**不包含**:
- 实时数据同步（非日报/周报级别）
- Initiative 编辑功能
- 多语言支持
- 移动端 App

---

## 2. 功能规格 (v1.1.0)

### 2.1 数据抓取模块

#### 2.1.1 Jira API 查询
```python
# JQL 查询
jql = 'project = CNTIN AND issuetype = Initiative AND "Parent Link" = CNTIN-730'

# API 调用
GET /rest/api/3/search/jql
Params:
  - jql: {jql}
  - fields: summary, status, assignee, priority, created, updated, duedate, description, labels
  - maxResults: 100
```

#### 2.1.2 数据映射

| Jira 字段 | 数据库字段 | 转换逻辑 |
|-----------|-----------|----------|
| key | key | 直接存储 |
| fields.summary | summary | 直接存储 |
| fields.status.name | status | 直接存储 |
| fields.assignee.displayName | assignee | 空值处理 |
| fields.priority.name | priority | 直接存储 |
| fields.created | created | ISO 8601 |
| fields.updated | updated | ISO 8601 |
| fields.duedate | duedate | 直接存储 |
| fields.description | description | 提取文本 (ADF/HTML 清理) |
| fields.labels | labels | 逗号分隔 |

### 2.2 AI 摘要模块 (v1.1.0 优化)

#### 2.2.1 Prompt 预精简

**预处理流程**:
```python
def pre_clean_description(description):
    """
    Prompt 预精简 - 减少 20% Token 消耗
    """
    # 移除 HTML/ADF 标签
    text = re.sub(r'<[^>]+>', '', description)
    # 规范化空白
    text = re.sub(r'\s+', ' ', text).strip()
    # 限制长度
    return text[:1000]
```

#### 2.2.2 语义哈希缓存

**缓存机制**:
```python
class SemanticCache:
    """
    基于内容 MD5 的语义缓存
    
    优势：
    - 内容变化自动失效
    - 相同内容不同 Issue 复用
    - 索引加速查找
    """
    
    def _compute_hash(self, summary, description):
        """计算内容哈希"""
        content = f"{summary}:{description}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, summary, description):
        """获取缓存"""
        content_hash = self._compute_hash(summary, description)
        # 查找索引...
```

#### 2.2.3 异步并发处理 (v1.1.0)

```python
import asyncio
import aiohttp

AI_MAX_CONCURRENT = 30  # 30 异步并发
AI_RATE_LIMIT = 0.1     # 每请求间隔 0.1 秒

async def batch_generate_ai_summaries(issues_data):
    """
    异步批量生成 AI Summary
    
    优化点：
    - 30 并发 (原 5 线程)
    - 语义缓存优先
    - 自动限流
    """
    semaphore = asyncio.Semaphore(AI_MAX_CONCURRENT)
    
    async def generate_one(issue):
        async with semaphore:
            # 检查语义缓存
            cache_key = compute_hash(issue['summary'], issue['description'])
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            # 调用 AI API
            summary = await call_ai_api(issue)
            
            # 保存缓存
            cache.set(cache_key, summary)
            
            # 限流延迟
            await asyncio.sleep(AI_RATE_LIMIT)
            
            return summary
    
    tasks = [generate_one(issue) for issue in issues_data]
    return await asyncio.gather(*tasks)
```

### 2.3 报告生成模块

#### 2.3.1 冻结列实现

```css
/* 冻结列 CSS */
.col-key-summary,
.col-status,
.col-assignee {
    position: sticky;
    left: 0;
    z-index: 10;
    background: white;
}

.col-key-summary { 
    left: 0; 
    z-index: 30;
}

.col-status { 
    left: 280px; 
    border-left: 1px solid #EBECF0;
}

.col-assignee { 
    left: 370px; 
    border-left: 1px solid #EBECF0;
}

/* 表头 */
th.col-key-summary,
th.col-status,
th.col-assignee {
    z-index: 40;
}
```

#### 2.3.2 表格容器

```css
.issues-table {
    overflow-x: auto;
    max-width: 100%;
}

table {
    table-layout: auto;
    min-width: 1600px; /* 确保需要滚动 */
}
```

#### 2.3.3 交互功能

| 功能 | 实现 | 事件 |
|------|------|------|
| 状态筛选 | JavaScript filter | click |
| Label 筛选 | JavaScript filter | click |
| 搜索 | JavaScript search | keyup (debounce) |
| 行展开 | CSS toggle | click |
| SLA Alert 筛选 | JavaScript filter | click |

### 2.4 邮件发送模块

#### 2.4.1 SMTP 配置

```python
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
SENDER_EMAIL = "3823810468@qq.com"
SENDER_PASSWORD = os.environ.get("QQ_MAIL_PASSWORD")
RECIPIENTS = ["chinatechpmo@lululemon.com"]
CC_RECIPIENTS = ["rcheng2@lululemon.com"]
```

### 2.5 飞书文件发送模块 (v1.1.0 新增)

#### 2.5.1 飞书 API 调用

```python
import requests

def send_feishu_file(file_path, chat_id=None, user_id=None):
    """
    发送文件到飞书
    
    支持：
    - 发送到群聊 (chat_id)
    - 发送到个人 (user_id)
    """
    # 1. 上传文件获取 file_key
    upload_url = "https://open.feishu.cn/open-apis/im/v1/files"
    
    with open(file_path, 'rb') as f:
        files = {'file': f}
        data = {
            'file_type': 'stream',
            'file_name': file_path.name
        }
        response = requests.post(
            upload_url,
            headers={'Authorization': f'Bearer {access_token}'},
            files=files,
            data=data
        )
    
    file_key = response.json()['data']['file_key']
    
    # 2. 发送文件消息
    message_url = "https://open.feishu.cn/open-apis/im/v1/messages"
    
    payload = {
        'msg_type': 'file',
        'content': json.dumps({'file_key': file_key})
    }
    
    if chat_id:
        payload['receive_id'] = chat_id
    elif user_id:
        payload['receive_id'] = user_id
    
    requests.post(
        message_url,
        headers={'Authorization': f'Bearer {access_token}'},
        json=payload
    )
```

---

## 3. 用户界面设计

### 3.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header                                                             │
│  - Title: CNTIN-730 Initiative Report                              │
│  - Timestamp: Generated: 2026-03-18 18:00                          │
│  - Stats: 100 Initiatives | Cache Hit: 65%                         │
├─────────────────────────────────────────────────────────────────────┤
│  Filters                                                            │
│  - Search: [____________________]                                  │
│  - Status: [All] [Discovery] [Done] [Execution] [New] [Strategy]  │
│  - Labels: [All] [CN-2026] [CN-FY26] [FY26] [SRE-SIG] [X-CLOSED]  │
├─────────────────────────────────────────────────────────────────────┤
│  Legend                                                             │
│  - 🟧 Missing SLA: Status ≠ Done and updated > 2 weeks             │
├─────────────────────────────────────────────────────────────────────┤
│  Table (with horizontal scroll)                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ Key/Summary | Status | Assignee | ... | AI Summary         │    │
│  ├─────────────┼────────┼──────────┼─────┼────────────────────┤    │
│  │ CNTIN-1001  │ Done   │ John Doe │ ... │ 🤖 What: ...       │    │
│  │ CNTIN-1002  │ Disc...│ Jane Doe │ ... │ 🤖 What: ...       │    │
│  └─────────────┴────────┴──────────┴─────┴────────────────────┘    │
│  ══════════════▶ (frozen columns)  ◀════════════════════════════   │
├─────────────────────────────────────────────────────────────────────┤
│  Footer                                                             │
│  - Generated by OpenClaw v1.1.0 | Data source: Jira API            │
│  - Semantic Cache: 65% hit | AI Tokens saved: 20%                  │
└─────────────────────────────────────────────────────────────────────┘
```

### 3.2 AI Summary 样式

```css
.ai-summary-cell {
    font-size: 12px;
    color: #172B4D;
    line-height: 1.6;
    max-height: 100px;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 5;
    -webkit-box-orient: vertical;
    
    /* 视觉区分 */
    background: #F6F8FA;
    padding: 10px;
    border-radius: 6px;
    border-left: 3px solid #0052CC;
}

.ai-summary-cell.expanded {
    max-height: none;
    -webkit-line-clamp: unset;
}

.ai-summary-cell b {
    color: #0052CC;
    font-weight: 600;
}
```

---

## 4. API 接口

### 4.1 外部 API

**Jira REST API v3**:
- Base URL: `https://lululemon.atlassian.net/rest/api/3`
- Authentication: Basic Auth
- Endpoint: `GET /search/jql`

**AI API**:
- Base URL: `http://newapi.200m.997555.xyz/v1`
- Authentication: Bearer Token
- Endpoint: `POST /chat/completions`
- Model: `claude-sonnet-4-6`

**飞书 API** (v1.1.0 新增):
- Base URL: `https://open.feishu.cn/open-apis`
- Authentication: Tenant Access Token
- Endpoints: 
  - `POST /im/v1/files` (文件上传)
  - `POST /im/v1/messages` (发送消息)

### 4.2 内部模块接口

```python
# 数据抓取
def fetch_cntin730_initiatives() -> List[Dict]:
    """抓取 CNTIN-730 下所有 Initiatives"""
    pass

# AI 摘要 (v1.1.0 异步)
async def generate_ai_summaries(issues_data) -> Dict[str, str]:
    """异步生成 AI Summary"""
    pass

# 报告生成
def generate_html_report(data, ai_summaries) -> str:
    """生成 HTML 报告"""
    pass

# 邮件发送
def send_email(html_file, recipients) -> bool:
    """发送邮件"""
    pass

# 飞书发送 (v1.1.0)
def send_feishu_file(file_path, chat_id=None) -> bool:
    """发送文件到飞书"""
    pass
```

---

## 5. 性能需求 (v1.1.0)

### 5.1 响应时间

| 操作 | v1.0.0 | v1.1.0 目标 | 优化手段 |
|------|--------|-------------|----------|
| Jira 抓取 | < 2 min | < 2 min | - |
| AI 摘要（100 个） | ~10 min | **~5 min** | 语义缓存 + 30 并发 |
| HTML 生成 | < 30 sec | < 30 sec | - |
| 邮件发送 | < 10 sec | < 10 sec | - |
| 飞书发送 | N/A | < 30 sec | 新增 |
| **总计** | ~12 min | **~7 min** | **42% 提升** |

### 5.2 并发控制

- AI 摘要: 30 异步并发 (原 5 线程)
- 每个请求间隔: 0.1 秒
- 重试次数: 3 次
- 重试间隔: 指数退避

### 5.3 缓存性能

- 目标缓存命中率: > 50%
- 实际预期命中率: ~60%
- Token 节省: ~20%

---

## 6. 发布计划

### 6.1 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v1.1.0 | 2026-03-18 | **优化版本**: 语义缓存、30 异步并发、Prompt 预精简、飞书文件发送 |
| v1.0.0 | 2026-03-18 | 初始版本: AI 摘要、冻结列、基础缓存 |

### 6.2 发布检查清单

- [x] 代码推送到 GitHub
- [x] 文档编写完成 (BRD, PRD, Design)
- [x] 环境变量配置验证
- [x] 测试运行通过
- [x] 邮件发送验证
- [x] 飞书发送验证
- [x] AI 摘要质量验证
- [x] 缓存命中率验证

---

## 7. 附录

### 7.1 AI 摘要示例

**输入**:
```
标题: Implement Cloud POS for China Stores
描述: We need to migrate all China stores from legacy POS to Cloud POS. 
This includes integration with OMS for order management, real-time inventory 
lookup, and support for omnichannel returns.
```

**输出**:
```
<b>What:</b> 把中国门店的 POS 系统从旧版迁移到 Cloud POS，整合 OMS 实现订单管理、实时库存查询和全渠道退货<br>
<b>Why:</b> 旧系统不支持全渠道能力，Cloud POS 能统一线上线下体验，提升运营效率和顾客满意度
```

### 7.2 状态映射

| Jira 状态 | 颜色 | Badge |
|-----------|------|-------|
| New | #0052CC | 🔵 |
| Discovery | #6554C0 | 🟣 |
| Execution | #FF8B00 | 🟠 |
| Done | #36B37E | 🟢 |
| Strategy | #00B8D9 | 🔵 |

### 7.3 故障排查

**问题**: AI 摘要生成慢  
**解决**: 检查语义缓存命中率，确认 30 异步并发配置

**问题**: 邮件发送失败  
**解决**: 验证 QQ_MAIL_PASSWORD 是否为最新授权码

**问题**: 飞书发送失败  
**解决**: 检查飞书 Token 是否过期，确认 chat_id/user_id 正确

**问题**: 冻结列不生效  
**解决**: 确认浏览器支持 CSS `position: sticky`

**问题**: 缓存不命中  
**解决**: 检查缓存目录权限，确认 MD5 计算正确
