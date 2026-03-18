# CNTIN-730 Initiative 周报 - 产品需求文档 (PRD)

**文档版本**: v1.0.0  
**创建日期**: 2026-03-18  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 产品概述

### 1.1 产品目标
构建一个自动化的周报系统，从 Jira CNTIN-730 抓取所有 Initiative 数据，使用 AI 生成标准化的 What/Why 业务解释，生成可交互的 HTML 报告，并自动发送给 PMO 团队。

### 1.2 用户画像

#### 主要用户: China Tech PMO
- **角色**: 项目经理、项目协调员
- **目标**: 快速了解所有 CNTIN-730 Initiatives 的状态和业务背景
- **痛点**: 
  - 100+ Initiatives 难以理解
  - 每个 Initiative 描述风格各异
  - 缺乏统一的业务语言
- **使用场景**: 每周查看邮件中的周报，准备项目会议

#### 次要用户: 技术负责人
- **角色**: Roberto Cheng 等技术领导
- **目标**: 监督整体项目组合健康状况
- **使用场景**: 查看 SLA Alert，识别需要关注的 Initiative

### 1.3 产品范围

**包含**:
- CNTIN-730 下所有 Initiative 数据抓取
- AI 智能摘要生成（What/Why）
- 冻结列表格设计
- 交互式筛选和搜索
- 自动邮件发送

**不包含**:
- 实时数据同步（非日报/周报级别）
- Initiative 编辑功能
- 多语言支持
- 移动端 App

---

## 2. 功能规格

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
| fields.description | description | 提取文本 |
| fields.labels | labels | 逗号分隔 |

### 2.2 AI 摘要模块

#### 2.2.1 Prompt 工程

**系统角色**:
```
你是一个专业的业务分析师，擅长将技术描述转化为清晰的业务语言。
```

**任务指令**:
```
请根据以下 Initiative 的标题和描述，用简洁自然的语言总结 What 和 Why。

要求：
1. What 部分：用动词开头，直接说明要做什么
2. Why 部分：说明业务价值和原因，用自然的口语化表达
3. 避免 AI 腔调，不要出现"旨在"、"致力于"、"通过...实现"这种套话
4. 中英混合使用，术语保留英文（如 API、POS、OMS）
5. 每部分 1-2 句话，简洁直接
```

**示例**:
```
<b>What:</b> 把线下门店的 POS 系统从旧版升级到 Cloud POS，支持全渠道退货和实时库存查询
<b>Why:</b> 现在门店退货要查好几个系统，太慢了，升级后一个界面搞定，提升顾客体验和店员效率
```

#### 2.2.2 并发处理

```python
from concurrent.futures import ThreadPoolExecutor, as_completed

def batch_generate_ai_summaries(issues_data, max_workers=5):
    """
    并发生成 AI Summary
    
    Strategy:
    - 5 线程并发
    - 每个请求间隔 0.3 秒避免限流
    - 失败重试 3 次
    - 缓存结果避免重复调用
    """
    results = {}
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(generate_ai_summary_one, args): args[2] 
            for args in issues_with_desc
        }
        
        for future in as_completed(futures):
            key, summary = future.result()
            results[key] = summary
            
    return results
```

#### 2.2.3 缓存机制

```python
CACHE_DIR = Path("/tmp/ai_summary_cache")

def get_cached_summary(key):
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)['ai_summary']
    return None

def save_cached_summary(key, summary):
    cache_file = CACHE_DIR / f"{key}.json"
    with open(cache_file, 'w') as f:
        json.dump({
            'ai_summary': summary,
            'cached_at': datetime.now().isoformat()
        }, f)
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

#### 2.4.1 双模式 SMTP

```python
def send_email_with_fallback(html_file):
    """
    双模式 SMTP 发送
    
    1. 先尝试 SSL (port 465)
    2. 失败时回退到 STARTTLS (port 587)
    """
    try:
        return send_ssl(html_file)
    except Exception as ssl_error:
        logger.warning(f"SSL failed: {ssl_error}")
        return send_starttls(html_file)
```

---

## 3. 用户界面设计

### 3.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│  Header                                                             │
│  - Title: CNTIN-730 Initiative Report                              │
│  - Timestamp: Generated: 2026-03-18 18:00                          │
│  - Stats: 100 Initiatives | 5 Labels                               │
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
│  - Generated by OpenClaw | Data source: Jira API                   │
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

### 4.2 内部模块接口

```python
# 数据抓取
def fetch_cntin730_initiatives() -> List[Dict]:
    """抓取 CNTIN-730 下所有 Initiatives"""
    pass

# AI 摘要
def generate_ai_summary(description, summary, key) -> str:
    """生成 AI Summary"""
    pass

# 报告生成
def generate_html_report(data, ai_summaries) -> str:
    """生成 HTML 报告"""
    pass

# 邮件发送
def send_email(html_file, recipients) -> bool:
    """发送邮件"""
    pass
```

---

## 5. 性能需求

### 5.1 响应时间

| 操作 | 目标 | 最大可接受 |
|------|------|-----------|
| Jira 抓取 | < 2 分钟 | 5 分钟 |
| AI 摘要（100 个） | < 10 分钟 | 20 分钟 |
| HTML 生成 | < 30 秒 | 1 分钟 |
| 邮件发送 | < 10 秒 | 30 秒 |
| **总计** | **< 15 分钟** | **30 分钟** |

### 5.2 并发控制

- AI 摘要: 5 并发线程
- 每个请求间隔: 0.3 秒
- 重试次数: 3 次
- 重试间隔: 指数退避

---

## 6. 发布计划

### 6.1 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v1.0.0 | 2026-03-18 | 初始版本，AI 摘要，冻结列，双模式 SMTP |

### 6.2 发布检查清单

- [x] 代码推送到 GitHub
- [x] 文档编写完成 (BRD, PRD, Design)
- [x] 环境变量配置验证
- [x] 测试运行通过
- [x] 邮件发送验证
- [x] AI 摘要质量验证

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
**解决**: 检查缓存命中率，确认并发设置

**问题**: 邮件发送失败  
**解决**: 验证 QQ_MAIL_PASSWORD 是否为最新授权码

**问题**: 冻结列不生效  
**解决**: 确认浏览器支持 CSS `position: sticky`
