# CNTIN-730 Initiative 周报 - 业务需求文档 (BRD)

**文档版本**: v1.2.0  
**创建日期**: 2026-03-18  
**更新日期**: 2026-03-19  
**作者**: OpenClaw  
**状态**: 已发布

---

## 1. 业务背景

### 1.1 问题陈述
China Technology PMO 团队需要每周跟踪 CNTIN-730 下的所有 Initiative 进展。CNTIN-730 是一个大型项目容器，包含 100+ 个 Initiatives，涉及多个技术领域的战略工作。当前面临以下挑战：

- **Initiative 数量多**: 超过 100 个 Initiatives 需要跟踪
- **描述理解困难**: 每个 Initiative 描述各异，团队难以统一理解
- **缺乏标准化解释**: 没有统一的 What/Why 解释框架
- **手动汇总耗时**: 人工整理周报需要 2-3 小时
- **分发渠道单一**: 仅支持邮件发送，缺少即时通讯集成
- **API 分页变更**: Jira API 升级到 `nextPageToken` 分页机制

### 1.2 业务目标

| 目标 | 描述 | 成功指标 |
|------|------|----------|
| 自动化周报 | 每周自动生成并发送 Initiative 状态报告 | 100% 自动执行 |
| 标准化理解 | AI 生成统一的 What/Why 解释 | 团队理解一致性提升 80% |
| 提升效率 | 减少 PMO 手动整理时间 | 节省 95% 的周报制作时间 |
| 增强可见性 | 提供统一的 Initiative 视图 | 覆盖 100% CNTIN-730 Initiatives |
| 多渠道分发 | 支持邮件 + 飞书双渠道 | 飞书文件发送成功率 > 95% |
| API 兼容性 | 适配 Jira API 新分页机制 | 100% 数据完整性 |

### 1.3 利益相关者

| 角色 | 姓名/团队 | 职责 |
|------|-----------|------|
| 主要用户 | China Tech PMO | 接收周报，跟踪 Initiative 进展 |
| 抄送用户 | Roberto Cheng | 监督和技术领导 |
| 最终用户 | 各 Initiative 负责人 | 查看自己的 Initiative 状态 |
| 系统维护 | OpenClaw | 系统开发和维护 |

---

## 2. 业务需求

### 2.1 功能需求

#### FR-001: 全量 Initiative 抓取 (v1.2.0 更新)
- **描述**: 从 CNTIN-730 下抓取所有 Initiative 数据
- **优先级**: 高
- **验收标准**: 
  - 抓取所有 CNTIN-730 子 Initiative
  - 包含完整描述、状态、负责人信息
  - **适配 Jira API `nextPageToken` 分页机制**
  - **排除 Cancelled 状态的 Initiative**
  - 抓取时间 < 2 分钟

#### FR-002: AI 智能摘要 (v1.1.0 优化)
- **描述**: 使用 AI 为每个 Initiative 生成标准化的 What/Why 解释
- **优先级**: 高
- **验收标准**:
  - What: 动词开头，直接说明做什么
  - Why: 业务价值，自然语言表达
  - 避免 AI 腔调（"旨在"、"致力于"）
  - 中英混合，术语保留英文
  - **语义缓存**: 基于内容 MD5 哈希，内容变化自动失效
  - **并发处理**: 30 异步并发 workers
  - **Prompt 预精简**: 清理 ADF/HTML 标签，减少 20% Token 消耗

#### FR-003: 冻结列表格
- **描述**: HTML 报告中前三列冻结，支持横向滚动
- **优先级**: 高
- **验收标准**:
  - Key/Summary 列固定
  - Status 列固定
  - Assignee 列固定
  - 其他列可横向滚动

#### FR-004: 交互式筛选 (v1.2.0 更新)
- **描述**: 支持按状态、Label、Assignee 筛选和搜索
- **优先级**: 中
- **验收标准**:
  - 状态筛选按钮
  - **Assignee 筛选按钮** (v1.2.0 新增)
  - Label 筛选
  - **Missing SLA 筛选** (v1.2.0 新增)
  - 关键词搜索
  - 实时过滤

#### FR-005: 统计卡片 (v1.2.0 新增)
- **描述**: 顶部显示关键统计指标卡片
- **优先级**: 中
- **验收标准**:
  - Total Initiatives 卡片
  - Done 卡片 (绿色)
  - Discovery 卡片 (紫色)
  - Missing SLA 卡片 (橙色警示)

#### FR-006: 行展开功能 (v1.2.0 新增)
- **描述**: 单击行展开/收起完整内容
- **优先级**: 中
- **验收标准**:
  - 单击任意行切换展开状态
  - 展开时显示完整 Description
  - 展开时显示完整 AI Summary

#### FR-007: Excel 导出 (v1.2.0 新增)
- **描述**: 导出筛选后的数据为 CSV
- **优先级**: 中
- **验收标准**:
  - 右下角浮动导出按钮
  - 仅导出当前可见（筛选后）的数据
  - CSV 格式，包含所有字段

#### FR-008: 多渠道发送 (v1.1.0 新增)
- **描述**: 支持邮件 + 飞书文件双渠道发送
- **优先级**: 高
- **验收标准**:
  - 邮件: 收件人 chinatechpmo@lululemon.com，抄送 rcheng2@lululemon.com
  - 飞书: 文件发送到指定群聊/个人
  - 包含 HTML 报告附件

### 2.2 非功能需求

#### NFR-001: AI 摘要质量 (v1.1.0 优化)
- 生成时间 < 5 分钟（100 个 Initiatives，缓存命中率 60%+）
- 准确率 > 90%（基于描述生成有效摘要）
- 并发处理：30 异步 workers（原 5 线程）
- Token 消耗减少 20%

#### NFR-002: 性能
- 数据抓取 < 2 分钟
- HTML 生成 < 5 秒
- 邮件发送 < 30 秒
- 页面加载 < 3 秒（100+ 行数据）

#### NFR-003: 可用性
- 报告必须可离线查看
- 支持主流浏览器（Chrome, Safari, Edge）
- 移动端可查看（响应式）

---

## 3. 报表规格

### 3.1 数据源

```
JQL: project = CNTIN AND issuetype = Initiative AND parent = CNTIN-730 AND status != Cancelled
```

**字段需求:**
- key: Initiative 编号
- summary: 标题
- status: 状态
- assignee: 负责人
- priority: 优先级
- created: 创建日期
- updated: 更新日期
- duedate: 截止日期
- description: 描述（ADF 格式）
- labels: 标签

### 3.2 数据转换

| 源字段 | 目标字段 | 转换规则 |
|--------|----------|----------|
| fields.summary | summary | 直接存储 |
| fields.status.name | status | 直接存储 |
| fields.assignee.displayName | assignee | Unassigned 处理 |
| fields.priority.name | priority | 直接存储 |
| fields.created | created | ISO 8601 → YYYY-MM-DD |
| fields.updated | updated | ISO 8601 → YYYY-MM-DD |
| fields.duedate | duedate | 直接存储 |
| fields.description | description | ADF 提取文本 |
| fields.labels | labels | 数组 → 逗号分隔 |

### 3.3 Missing SLA 规则

**条件:**
- 状态 ≠ Done
- 更新时间 > 当前时间 - 14 天

**标识:**
- Key 后显示 ⚠️ 图标
- 整行背景色高亮（#FFFAF5）

---

## 4. 用户界面

### 4.1 页面布局

```
┌─────────────────────────────────────────────────────────────────────┐
│ Header                                                              │
│ - Title: CNTIN-730 FY26 Intakes                                     │
│ - Subtitle: Parent = CNTIN-730 | Status ≠ Cancelled                 │
│ - Timestamp: Generated: 2026-03-19 12:00                           │
├─────────────────────────────────────────────────────────────────────┤
│ Stats Cards                                                         │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│ │ 143      │ │ 34       │ │ 96       │ │ 30       │                │
│ │ Total    │ │ Done     │ │ Discovery│ │ Missing  │                │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘                │
├─────────────────────────────────────────────────────────────────────┤
│ Filter Section                                                      │
│ - Search Input                                                      │
│ - Status Filter (All, Discovery, Done, Execution, New, Strategy)   │
│ - Assignee Filter (Top 20 assignees)                                │
│ - Label Filter (Top 10 labels)                                      │
│ - Missing SLA Filter                                                │
├─────────────────────────────────────────────────────────────────────┤
│ Legend: Missing SLA: 状态 ≠ Done 且更新时间超过2周                   │
├─────────────────────────────────────────────────────────────────────┤
│ Issues Table                                                        │
│ - Frozen columns: Key/Summary, Status, Assignee                     │
│ - Scrollable columns: Priority, Created, Updated, Due Date         │
│                     Description, AI Summary                         │
│ - Click row to expand                                               │
├─────────────────────────────────────────────────────────────────────┤
│ Export Button (Fixed bottom-right)                                  │
├─────────────────────────────────────────────────────────────────────┤
│ Footer                                                              │
│ - Generated by OpenClaw | Source: Jira API                          │
└─────────────────────────────────────────────────────────────────────┘
```

### 4.2 表格设计

| 列 | 说明 | 宽度 | 冻结 | 展开行为 |
|---|------|------|------|----------|
| Key / Summary | Initiative 编号和标题 | 280-350px | 是 | Summary 展开显示完整 |
| Status | 状态 | 90px | 是 | - |
| Assignee | 负责人 | 110px | 是 | - |
| Priority | 优先级 | 80px | 否 | - |
| Created | 创建日期 | 90px | 否 | - |
| Updated | 更新日期 | 90px | 否 | - |
| Due Date | 截止日期 | 80px | 否 | - |
| Description | 原始描述 | 400-500px | 否 | 展开显示完整描述 |
| AI Summary | What/Why 摘要 | 350-450px | 否 | 展开显示完整摘要 |

---

## 5. 成功指标

### 5.1 定量指标

| 指标 | 目标 | v1.0.0 | v1.1.0 | v1.2.0 |
|------|------|--------|--------|--------|
| 数据完整率 | 100% | 100% | 100% | **100%** |
| AI 摘要成功率 | > 95% | 98% | 98% | 98% |
| 平均生成时间 | < 10 分钟 | ~10 分钟 | ~5 分钟 | **~5 分钟** |
| 缓存命中率 | > 50% | N/A | ~60% | ~60% |
| Token 消耗 | 基准 | 100% | ~80% | ~80% |
| 飞书发送成功率 | > 95% | N/A | > 95% | > 95% |
| **API 分页正确率** | 100% | N/A | N/A | **100%** |

### 5.2 定性指标
- PMO 团队理解一致性提升
- 会议讨论效率提升
- Initiative 上下文切换成本降低

---

## 6. 定时任务

### 6.1 执行计划

- **频率**: 工作日（周一至周五）
- **时间**: 中午 12:00
- **时区**: Asia/Shanghai (GMT+8)

### 6.2 任务流程

1. 清空历史缓存
2. 从 Jira API 全量抓取数据（适配 nextPageToken）
3. 生成 AI Summary（语义缓存优先）
4. 生成 HTML 报告
5. 发送邮件给 chinatechpmo@lululemon.com
6. 抄送 rcheng2@lululemon.com

---

## 7. 风险与缓解措施

| 风险 | 影响 | 可能性 | 缓解措施 |
|------|------|--------|----------|
| AI API 限流/故障 | 高 | 中 | 语义缓存机制，失败时显示占位符 |
| Jira API 变更 | 中 | 低 | **已适配 nextPageToken 分页**，监控 API 版本 |
| 描述质量差 | 中 | 中 | Prompt 预精简，标注"信息不足" |
| 邮件发送失败 | 中 | 低 | 双模式 SMTP，失败告警 |
| 飞书 API 变更 | 中 | 低 | 监控飞书开放平台更新 |

---

## 8. 发布记录

| 版本 | 日期 | 变更内容 |
|------|------|----------|
| **v1.2.0** | **2026-03-19** | **重大更新**: 适配 Jira API 分页、新增统计卡片、Assignee 筛选、Missing SLA 筛选、行展开、Excel 导出 |
| v1.1.0 | 2026-03-18 | 优化版本: 语义缓存、30 异步并发、Prompt 预精简、飞书文件发送 |
| v1.0.0 | 2026-03-18 | 初始版本: AI 摘要、冻结列、基础缓存 |

---

## 9. 附录

### 9.1 术语表

| 术语 | 定义 |
|------|------|
| Initiative | Jira 中的战略级工作单元，包含多个 Feature |
| CNTIN-730 | China Technology 的 Initiative 容器 |
| AI Summary | AI 生成的 What/Why 业务解释 |
| SLA Alert | 超过 2 周未更新的非 Done 状态 Initiative |
| Frozen Column | 表格中固定不随滚动移动的列 |
| Semantic Cache | 基于内容 MD5 哈希的智能缓存 |
| ADF | Atlassian Document Format，Jira 富文本格式 |
| nextPageToken | Jira API v3 新分页机制令牌 |

### 9.2 参考资料

- [Jira REST API v3 - Search](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-get)
- [CHANGELOG.md](./CHANGELOG.md)
- [VERSION.md](./VERSION.md)
