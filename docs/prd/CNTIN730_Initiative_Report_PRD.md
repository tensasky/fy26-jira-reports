# CNTIN-730 Initiative 周报 - 产品需求文档 (PRD)

**文档版本**: v1.2.0  
**创建日期**: 2026-03-18  
**更新日期**: 2026-03-19  
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
- **适配 Jira API v3 `nextPageToken` 分页机制**
- **排除 Cancelled 状态的 Initiative**
- AI 智能摘要生成（What/Why）
- 语义哈希缓存（基于内容 MD5）
- 冻结列表格设计
- **统计卡片** (v1.2.0)
- **Assignee 筛选** (v1.2.0)
- **Missing SLA 筛选** (v1.2.0)
- **行展开功能** (v1.2.0)
- **Excel 导出** (v1.2.0)
- 交互式筛选和搜索
- 邮件 + 飞书双渠道发送

**不包含**:
- 实时数据同步（非日报/周报级别）
- Initiative 编辑功能
- 多语言支持
- 移动端 App

---

## 2. 功能规格

### 2.1 数据抓取模块 (v1.2.0 更新)

#### 2.1.1 Jira API 查询
```python
# JQL 查询 (v1.2.0 更新: 使用 parent 字段，排除 Cancelled)
jql = 'project = CNTIN AND issuetype = Initiative AND parent = CNTIN-730 AND status != Cancelled'

# API 调用
GET /rest/api/3/search/jql
Params:
  - jql: {jql}
  - fields: summary, status, assignee, priority, created, updated, duedate, description, labels
  - maxResults: 100
  
# 分页处理 (v1.2.0 新增)
while not isLast:
    response = GET /rest/api/3/search/jql
    issues.extend(response.issues)
    nextPageToken = response.nextPageToken  # Jira API v3 新分页机制
```

#### 2.1.2 数据映射

| Jira 字段 | 数据库字段 | 转换逻辑 |
|-----------|-----------|----------|
| key | key | 直接存储 |
| fields.summary | summary | 直接存储 |
| fields.status.name | status | 直接存储 |
| fields.assignee.displayName | assignee | 空值处理 → "Unassigned" |
| fields.priority.name | priority | 直接存储 |
| fields.created | created | ISO 8601 → YYYY-MM-DD |
| fields.updated | updated | ISO 8601 → YYYY-MM-DD |
| fields.duedate | duedate | 直接存储 |
| fields.description | description | ADF 提取文本 |
| fields.labels | labels | 数组 → 逗号分隔 |

### 2.2 AI 摘要模块

#### 2.2.1 Prompt 预精简
```python
def pre_clean_description(description):
    """Prompt 预精简 - 减少 20% Token 消耗"""
    if isinstance(description, dict):  # ADF 格式
        text = extract_text_from_adf(description)
    else:
        text = str(description)
    # 移除 HTML 标签
    text = re.sub(r'<[^>]+>', '', text)
    # 规范化空白
    text = re.sub(r'\s+', ' ', text).strip()
    # 限制长度
    return text[:1000]
```

#### 2.2.2 语义哈希缓存
```python
class SemanticCache:
    """基于内容 MD5 的语义缓存"""
    
    def _compute_hash(self, summary, description):
        content = f"{summary}:{description}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get(self, summary, description):
        content_hash = self._compute_hash(summary, description)
        # 查找缓存...
```

#### 2.2.3 异步并发处理
```python
AI_MAX_CONCURRENT = 30  # 30 异步并发
AI_RATE_LIMIT = 0.1     # 每请求间隔 0.1 秒

async def batch_generate_ai_summaries(issues_data):
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
            cache.set(cache_key, summary)
            await asyncio.sleep(AI_RATE_LIMIT)
            return summary
    
    tasks = [generate_one(issue) for issue in issues_data]
    return await asyncio.gather(*tasks)
```

### 2.3 报告生成模块

#### 2.3.1 统计卡片 (v1.2.0 新增)
```html
<div class="stats-container">
    <div class="stat-card">
        <div class="stat-value">143</div>
        <div class="stat-label">Total Initiatives</div>
    </div>
    <div class="stat-card done">
        <div class="stat-value">34</div>
        <div class="stat-label">Done</div>
    </div>
    <div class="stat-card discovery">
        <div class="stat-value">96</div>
        <div class="stat-label">Discovery</div>
    </div>
    <div class="stat-card sla">
        <div class="stat-value">30</div>
        <div class="stat-label">Missing SLA</div>
    </div>
</div>
```

#### 2.3.2 冻结列实现
```css
/* 冻结列 CSS */
.col-key-summary {
    position: sticky;
    left: 0;
    z-index: 10;
    background: white;
    min-width: 280px;
}

.col-status {
    position: sticky;
    left: 280px;
    z-index: 10;
    background: white;
    border-left: 1px solid #EBECF0;
}

.col-assignee {
    position: sticky;
    left: 370px;
    z-index: 10;
    background: white;
    border-left: 1px solid #EBECF0;
}

/* 表头冻结列 */
th.col-key-summary,
th.col-status,
th.col-assignee {
    z-index: 30;
    background: #FAFBFC;
}
```

#### 2.3.3 筛选功能 (v1.2.0 更新)
```javascript
// 状态筛选
function filterByStatus(status) {
    currentStatusFilter = status;
    filterIssues();
}

// Assignee 筛选 (v1.2.0 新增)
function filterByAssignee(assignee) {
    currentAssigneeFilter = assignee;
    filterIssues();
}

// Label 筛选
function filterByLabel(label) {
    currentLabelFilter = label;
    filterIssues();
}

// Missing SLA 筛选 (v1.2.0 新增)
function filterByAlert(alertType) {
    currentAlertFilter = alertType;
    filterIssues();
}
```

#### 2.3.4 行展开功能 (v1.2.0 新增)
```javascript
function toggleRow(row) {
    const isExpanded = row.classList.toggle('expanded');
    
    const summary = row.querySelector('.issue-summary');
    const description = row.querySelector('.description-cell');
    const aiSummary = row.querySelector('.ai-summary-cell');
    
    if (summary) summary.classList.toggle('expanded', isExpanded);
    if (description) description.classList.toggle('expanded', isExpanded);
    if (aiSummary) aiSummary.classList.toggle('expanded', isExpanded);
}
```

#### 2.3.5 Excel 导出 (v1.2.0 新增)
```javascript
function exportToExcel() {
    const visibleRows = document.querySelectorAll('tbody tr:not(.hidden)');
    let csv = 'Key,Summary,Status,Assignee,Priority,Created,Updated,Due Date,Labels\n';
    
    visibleRows.forEach(row => {
        // 提取数据...
        csv += `"${key}","${summary}","${status}",...\n`;
    });
    
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = 'CNTIN-730_Initiatives_YYYYMMDD.csv';
    link.click();
}
```

### 2.4 Missing SLA 计算 (v1.2.0)
```python
def check_sla_alert(issue):
    """检查是否 Missing SLA"""
    status = issue['fields']['status']['name']
    updated_str = issue['fields']['updated']
    
    if status == 'Done':
        return False
    
    # 解析 Jira 日期格式
    updated_str = updated_str[:19]  # 移除毫秒和时区
    updated_dt = datetime.fromisoformat(updated_str)
    
    two_weeks_ago = datetime.now() - timedelta(days=14)
    return updated_dt < two_weeks_ago
```

---

## 3. 定时任务配置

### 3.1 LaunchAgent 配置
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" 
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.openclaw.cntin730-weekly-report</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>-c</string>
        <string>export PATH="..." &amp;&amp; 
               export JIRA_API_TOKEN="..." &amp;&amp; 
               export AI_API_KEY="..." &amp;&amp; 
               cd /Users/admin/.openclaw/workspace/scripts &amp;&amp; 
               python3 cntin730_weekly_report.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <array>
        <!-- 周一至周五 12:00 -->
        <dict><key>Hour</key><integer>12</integer>
              <key>Minute</key><integer>0</integer>
              <key>Weekday</key><integer>1</integer></dict>
        <dict><key>Hour</key><integer>12</integer>
              <key>Minute</key><integer>0</integer>
              <key>Weekday</key><integer>2</integer></dict>
        <dict><key>Hour</key><integer>12</integer>
              <key>Minute</key><integer>0</integer>
              <key>Weekday</key><integer>3</integer></dict>
        <dict><key>Hour</key><integer>12</integer>
              <key>Minute</key><integer>0</integer>
              <key>Weekday</key><integer>4</integer></dict>
        <dict><key>Hour</key><integer>12</integer>
              <key>Minute</key><integer>0</integer>
              <key>Weekday</key><integer>5</integer></dict>
    </array>
</dict>
</plist>
```

---

## 4. 性能规格

### 4.1 响应时间

| 操作 | 目标 | v1.2.0 |
|------|------|--------|
| 数据抓取 | < 2 分钟 | ~1 分钟 |
| AI 摘要生成 | < 5 分钟 | ~5 分钟 |
| HTML 生成 | < 5 秒 | ~3 秒 |
| 邮件发送 | < 30 秒 | ~10 秒 |

### 4.2 资源消耗

| 资源 | 规格 |
|------|------|
| 内存 | < 500 MB |
| 磁盘 | < 100 MB (缓存) |
| API 调用 | ~150 次/运行 |
| Token 消耗 | ~80% of v1.0.0 |

---

## 5. 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.2.0 | 2026-03-19 | 适配 Jira API `nextPageToken` 分页、新增统计卡片、Assignee 筛选、Missing SLA 筛选、行展开、Excel 导出 |
| v1.1.0 | 2026-03-18 | 语义缓存、30 异步并发、Prompt 预精简、飞书文件发送 |
| v1.0.0 | 2026-03-18 | 初始版本 |

---

## 6. 附录

### 6.1 API 端点

- Jira: `GET /rest/api/3/search/jql`
- AI: `POST /chat/completions`
- SMTP: `smtp.qq.com:587`

### 6.2 文件位置

- 脚本: `~/.openclaw/workspace/scripts/cntin730_weekly_report.py`
- 报告: `~/.openclaw/workspace/reports/`
- 缓存: `~/.openclaw/workspace/jira-reports/cache/`
- 日志: `~/.openclaw/workspace/logs/`
- 定时任务: `~/Library/LaunchAgents/com.openclaw.cntin730-weekly-report.plist`
