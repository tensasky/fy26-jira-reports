# CNTIN-730 Initiative 周报系统 - PRD 文档

**版本**: v1.0  
**创建日期**: 2026-03-16  
**作者**: OpenClaw  
**状态**: 已上线

---

## 1. 项目背景

### 1.1 需求概述
China PMO 团队需要定期跟踪 CNTIN-730 (FY26 Intakes) 下的所有 Initiative 状态，用于项目管理和进度汇报。

### 1.2 业务目标
- 自动化获取 Jira 数据，减少手工操作
- 提供多维度筛选，方便数据分析
- 定期发送报告邮件，确保信息同步
- 支持数据导出，便于离线分析

### 1.3 目标用户
- China PMO 团队 (chinatechpmo@lululemon.com)
- 项目管理人员
- Initiative 负责人

---

## 2. 数据抓取逻辑

### 2.1 JQL 查询条件
```sql
project = CNTIN 
AND parent = "CNTIN-730" 
AND status != Cancelled 
AND issuetype = Initiative
```

### 2.2 分页机制
由于 Jira API 限制（每页最大 100 条），系统采用分页抓取：

| 参数 | 值 |
|------|-----|
| 每页数量 | 100 |
| 分页方式 | nextPageToken |
| 最大页数 | 无限制（自动获取全部）|

### 2.3 数据字段
抓取所有字段 (`fields: [*all]`)，包含：
- 基础信息: key, summary, status, priority
- 人员信息: assignee, creator, reporter
- 时间信息: created, updated, duedate
- 描述: description (ADF 格式)
- 标签: labels
- 自定义字段: 所有 customfield_*

### 2.4 数据转换
```python
# ADF 描述格式 → 纯文本
def extract_description(fields):
    # 递归遍历 ADF 节点，提取 text 内容
    # 返回拼接后的纯文本
```

---

## 3. 筛选功能

### 3.1 筛选维度

#### 3.1.1 Status（状态）
- 类型: 单选
- 选项: 动态获取所有存在的 status
- 默认值: All

#### 3.1.2 Assignee（负责人）
- 类型: 单选
- 选项: 动态获取所有 assignee + Unassigned
- 默认值: All
- 显示: Assignee 名称 + 数量徽章

#### 3.1.3 Label（标签）
- 类型: 单选
- 选项: 动态获取所有 labels
- 默认值: All

#### 3.1.4 Missing SLA（警报）
- 类型: 开关
- 规则: `status != Done AND updated > 14 days ago`
- 视觉效果: 红色标记行

#### 3.1.5 关键词搜索
- 类型: 文本输入
- 搜索范围: Key, Summary, Description
- 匹配方式: 包含（不区分大小写）

### 3.2 组合筛选逻辑
```javascript
matches = 
  (status === 'all' || row.status === status) AND
  (assignee === 'all' || row.assignee === assignee) AND
  (label === 'all' || row.labels.includes(label)) AND
  (alert === null || (alert === 'sla' && row.hasSla))
```

---

## 4. 报告展示

### 4.1 表格列定义

| 列名 | 宽度 | 说明 |
|------|------|------|
| Key / Summary | 280-350px | Key 为超链接，Summary 悬停显示完整标题 |
| Status | 90px | 带颜色徽章 |
| Assignee | 110px | 负责人姓名 |
| Priority | 80px | 优先级 |
| Creator | 110px | 创建人 |
| Reporter | 110px | 报告人 |
| Created | 90px | 创建日期 |
| Updated | 90px | 更新日期 |
| Due Date | 80px | 截止日期 |
| Description | 300-400px | **完整显示**（不截断）|
| Alerts | 100px | Missing SLA 标记 |

### 4.2 超链接
- **Key 列**: `https://lululemon.atlassian.net/browse/{KEY}`
- **打开方式**: 新标签页

### 4.3 状态颜色
| Status | 颜色 |
|--------|------|
| New / To Do | #0052CC (蓝) |
| Discovery | #6554C0 (紫) |
| In Progress / Execution | #FF8B00 (橙) |
| Done / Closed | #36B37E (绿) |
| Cancelled / Blocked | #FF5630 (红) |

---

## 5. 导出功能

### 5.1 导出按钮
- 位置: 筛选栏下方
- 样式: 绿色按钮
- 文本: "📊 Export to Excel"

### 5.2 导出逻辑
1. 获取当前可见行（未隐藏）
2. 转换为 CSV 格式
3. 添加 UTF-8 BOM 支持中文
4. 触发浏览器下载

### 5.3 CSV 格式
- **分隔符**: 逗号 (,)
- **编码**: UTF-8
- **换行**: \n
- **引号处理**: 包含逗号/换行的字段用双引号包裹

### 5.4 文件名
```
CNTIN730_Initiatives_{YYYYMMDD}_{count}.csv
```

---

## 6. 邮件发送

### 6.1 收件配置
| 项目 | 值 |
|------|-----|
| SMTP 服务器 | smtp.qq.com:587 |
| 发件人 | 3823810468@qq.com |
| 收件人 | chinatechpmo@lululemon.com |
| 抄送 | rcheng2@lululemon.com |

### 6.2 邮件主题
```
FY26{YYYYMMDD}Intake
```

### 6.3 附件命名
```
FY26{YYYYMMDD}Intake.html
```

### 6.4 邮件正文
- 报告摘要（总数、状态分布、Missing SLA 数量）
- HTML 报告交互说明
- 发件人签名

---

## 7. 定时任务

### 7.1 执行频率
- 每周一 15:00 (GMT+8)

### 7.2 Cron 表达式
```
0 15 * * 1
```

### 7.3 执行流程
```
1. 从 Jira 抓取数据（分页获取全部）
2. 生成 HTML 报告
3. 保存本地备份
4. 发送邮件
5. 记录日志
```

### 7.4 日志路径
```
/Users/admin/.openclaw/workspace/logs/cntin730-cron.log
```

---

## 8. 技术实现

### 8.1 技术栈
| 组件 | 技术 |
|------|------|
| 后端 | Python 3 |
| Jira API | REST API v3 |
| 邮件 | smtplib + email |
| 定时任务 | Cron |
| 前端 | HTML + CSS + JavaScript |

### 8.2 核心依赖
```python
import json
import html
import smtplib
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import urllib.request
import base64
```

### 8.3 文件结构
```
/Users/admin/.openclaw/workspace/
├── scripts/
│   └── cntin730_weekly_report.py    # 主脚本
├── reports/
│   └── FY26{date}Intake.html        # 生成报告
└── logs/
    └── cntin730-cron.log            # 执行日志
```

### 8.4 配置参数
```python
JIRA_BASE_URL = "https://lululemon.atlassian.net"
JIRA_USER_EMAIL = "rcheng2@lululemon.com"
JIRA_API_TOKEN = "***"
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
EMAIL_SENDER = "3823810468@qq.com"
EMAIL_PASSWORD = "***"
EMAIL_RECIPIENT = "chinatechpmo@lululemon.com"
```

---

## 9. 数据统计示例

### 9.1 当前数据量
- **Total Initiatives**: 139
- **Discovery**: 47
- **Done**: 5
- **Execution**: 1
- **New**: 5
- **Missing SLA**: 1

### 9.2 Assignee 分布（Top 5）
| Assignee | Count |
|----------|-------|
| James Chen | 45 |
| Yolanda Xiao | 12 |
| Unassigned | 8 |
| ... | ... |

---

## 10. 变更历史

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-03-16 | v1.0 | 初始版本，包含完整功能 |

---

## 附录

### A. API 响应示例
```json
{
  "issues": [...],
  "nextPageToken": "...",
  "isLast": false
}
```

### B. 错误处理
- Jira API 失败: 抛出异常，记录日志
- 邮件发送失败: 重试 3 次
- 分页失败: 中断并记录已获取数据

### C. 安全说明
- API Token 存储在脚本中（需限制文件权限）
- 邮件密码使用 QQ 邮箱授权码
- 报告文件权限: 600
