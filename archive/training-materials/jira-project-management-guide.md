# 🎯 Jira 项目管理标准实施流程手册

## 文档信息
- **版本**: V1.0
- **适用范围**: 软件研发项目
- **工具**: Atlassian Jira + Confluence (可选)
- **方法论**: Agile/Scrum + 传统项目管理结合

---

## 一、Jira 项目配置标准

### 1.1 项目创建模板
```
项目类型: Software Development
模板: Scrum 或 Kanban（根据项目特点）
项目名称规范: [部门]-[产品名]-[项目类型]
例如: TECH-PaymentGateway-v2.0
```

### 1.2 问题类型配置 (Issue Types)

| 问题类型 | 用途 | 工作流 | 必填字段 |
|---------|------|--------|----------|
| **Epic** | 大功能/里程碑 | Epic工作流 | 名称、描述、负责人、开始/结束日期 |
| **Story** | 用户故事 | 标准研发工作流 | 标题、描述、验收标准、Story Points |
| **Task** | 技术任务 | 标准研发工作流 | 标题、描述、预估工时 |
| **Bug** | 缺陷 | Bug工作流 | 标题、重现步骤、严重程度、影响范围 |
| **Sub-task** | 子任务 | 子任务工作流 | 标题、描述、父任务 |
| **Spike** | 技术调研 | 调研工作流 | 标题、调研目标、时间盒 |
| **Release** | 版本发布 | 发布工作流 | 版本号、发布日期、发布说明 |

### 1.3 工作流配置 (Workflow)

#### 标准研发工作流
```
Backlog → To Do → In Progress → Code Review → Testing → Done
   ↓                                                    ↑
   └────────────── Blocked ─────────────────────────────┘
```

**状态说明**:
- **Backlog**: 待规划，未进入当前迭代
- **To Do**: 已规划，待开发
- **In Progress**: 开发中
- **Code Review**: 代码审查中
- **Testing**: 测试中（QA验证）
- **Done**: 已完成
- **Blocked**: 被阻塞

#### Bug工作流
```
Open → Confirmed → In Progress → Fixed → Verified → Closed
  ↓                                               ↑
  └─────────────── Reopened ──────────────────────┘
```

### 1.4 字段配置标准

#### 自定义字段 (Custom Fields)

| 字段名 | 类型 | 用途 | 必填 |
|--------|------|------|------|
| **Story Points** | 数值 | 估算工作量 | Story必填 |
| **Sprint** | 标签 | 所属迭代 | 是 |
| **Acceptance Criteria** | 文本框 | 验收标准 | Story必填 |
| **Technical Notes** | 文本框 | 技术实现备注 | 否 |
| **Business Value** | 选择(1-5) | 业务价值 | Epic必填 |
| **Risk Level** | 选择(高/中/低) | 风险等级 | 是 |
| **Requirement Source** | 文本 | 需求来源 | 是 |
| **Due Date** | 日期 | 截止日期 | 是 |
| **Actual Hours** | 数值 | 实际工时 | Task必填 |
| **Test Cases** | 链接 | 测试用例链接 | Story必填 |

#### 优先级配置
- **Highest**: P0 - 阻塞性问题，必须立即处理
- **High**: P1 - 高优先级，当前迭代完成
- **Medium**: P2 - 正常优先级
- **Low**: P3 - 低优先级，可延后
- **Lowest**: P4 - 最低优先级

---

## 二、详细阶段流程与 Jira 操作

### 阶段一：项目启动 (Project Initiation)

#### 2.1.1 里程碑规划 (Milestone Planning)

**Jira 操作**:
1. 创建 Epic
   - 路径: Backlog → Create Issue → Epic
   - 标题格式: `[里程碑名称] - [目标描述]`
   - 示例: `M1-用户认证系统 - 完成登录/注册/找回密码功能`

2. Epic 字段填写标准
   ```
   Summary: [里程碑]-[功能模块]-[目标]
   Description: 
     ## 业务目标
     [描述此里程碑要达成的业务目标]
     
     ## 范围
     - 包含: [功能列表]
     - 不包含: [明确排除的内容]
     
     ## 成功标准
     - [可衡量的成功标准]
     
     ## 依赖关系
     - 前置: [依赖的其他Epic]
     - 后续: [后续Epic]
   
   Start Date: [计划开始日期]
   End Date: [计划结束日期]
   Business Value: [1-5评分]
   Risk Level: [High/Medium/Low]
   Assignee: [PO或项目负责人]
   ```

**质量标准**:
- ✅ Epic 描述必须包含业务目标和成功标准
- ✅ 每个 Epic 必须有明确的开始和结束日期
- ✅ Epic 工作量不超过 2 个 Sprint
- ✅ 必须关联到具体的业务价值

#### 2.1.2 项目初始化清单

**Jira 项目设置**:
```
□ 创建项目
□ 配置问题类型方案
□ 配置工作流方案
□ 配置字段配置方案
□ 配置屏幕方案
□ 配置权限方案
□ 创建组件 (Components)
□ 配置版本 (Versions)
□ 设置通知方案
□ 配置看板 (Board) 列
□ 设置快速过滤器
□ 配置仪表板 (Dashboard)
```

**组件 (Components) 建议**:
- Frontend / Backend / Database
- API / UI / Infrastructure
- Module A / Module B / Module C

**版本 (Versions) 命名**:
- `v1.0.0` - 主版本
- `v1.1.0` - 功能版本
- `v1.1.1` - 补丁版本

---

### 阶段二：需求分析与规划 (Requirement Analysis & Planning)

#### 2.2.1 用户故事创建标准

**Jira 操作**:
1. 在 Epic 下创建 Story
2. Story 格式遵循 **INVEST** 原则

**Story 模板**:
```
Summary: 作为[角色], 我想要[功能], 以便[价值]

Description:
## 用户故事
作为 [用户角色]
我想要 [具体功能]
以便 [获得什么价值/解决什么问题]

## 业务上下文
[背景信息，为什么需要这个功能]

## 当前痛点
[如果不做，会有什么问题]

Acceptance Criteria:
□ [验收标准1 - 必须可测试]
□ [验收标准2 - 必须可测试]
□ [验收标准3 - 必须可测试]

Technical Notes:
[技术实现建议或约束]

Attachments:
- [原型图/设计稿链接]
- [相关文档链接]
```

**Story Points 估算标准**:

| 点数 | 工作量 | 复杂度 | 风险 | 示例 |
|------|--------|--------|------|------|
| **1** | 2-4小时 | 简单 | 无 | 改文字、简单配置 |
| **2** | 半天 | 简单 | 低 | 简单API调用 |
| **3** | 1天 | 中等 | 低 | 标准功能开发 |
| **5** | 2-3天 | 中等 | 中 | 涉及多个组件 |
| **8** | 1周 | 复杂 | 中 | 新模块开发 |
| **13** | 1-2周 | 很复杂 | 高 | 需要拆分 |

> ⚠️ **规则**: Story Points > 8 的必须拆分

**质量标准**:
- ✅ Story 必须关联到 Epic
- ✅ 必须有至少 3 条可测试的验收标准
- ✅ 必须有 Story Points 估算
- ✅ 描述中必须说明业务价值
- ✅ 技术复杂度过高的需要技术方案评审

#### 2.2.2 Sprint 规划 (Sprint Planning)

**Jira 操作**:
1. 创建 Sprint
   - 路径: Backlog → Create Sprint
   - Sprint 名称格式: `Sprint [编号] - [目标]`
   - 示例: `Sprint 23 - 完成支付核心流程`

2. Sprint 字段填写:
   ```
   Sprint Name: Sprint [数字] - [目标描述]
   Duration: 2 weeks (标准)
   Start Date: [开始日期]
   End Date: [结束日期]
   Sprint Goal: [一句话描述本迭代目标]
   ```

3. Sprint 规划会议输出
   - 选择 Story 进入 Sprint
   - 分解 Task（每个 Task 不超过 8 小时）
   - 分配负责人

**Sprint 容量计算**:
```
总容量 = 团队人数 × 10 天 × 6 小时/天 × 0.8 (buffer)

示例: 5人团队
= 5 × 10 × 6 × 0.8
= 240 小时
= 约 30-35 Story Points (按 1 point = 6-8小时)
```

**质量标准**:
- ✅ Sprint Goal 必须明确且可衡量
- ✅ Sprint 工作量不超过团队容量
- ✅ 每个 Story 必须有明确的验收标准
- ✅ 高风险任务必须有应对方案
- ✅ 预留 20% Buffer 应对突发情况

#### 2.2.3 Task 分解标准

**Jira 操作**:
1. 在 Story 下创建 Sub-task
2. Task 类型分类:

| Task 类型 | 命名规范 | 预估工时 |
|-----------|----------|----------|
| **开发** | `[DEV] 具体开发内容` | 4-8小时 |
| **设计** | `[DESIGN] UI/API设计` | 2-6小时 |
| **测试** | `[TEST] 编写测试用例/执行测试` | 2-6小时 |
| **文档** | `[DOC] 技术文档/使用说明` | 1-4小时 |
| **Code Review** | `[CR] 代码审查` | 1-2小时 |

**Task 模板**:
```
Summary: [类型] 具体任务描述

Description:
## 任务目标
[要完成的具体工作]

## 验收标准
□ [完成标准1]
□ [完成标准2]

## 技术细节
[实现思路或注意事项]

## 依赖
- 依赖任务: [链接]
- 阻塞因素: [说明]

Estimated Hours: [预估工时]
Assignee: [负责人]
```

**质量标准**:
- ✅ 每个 Task 预估工时 ≤ 8 小时
- ✅ Task 描述必须包含验收标准
- ✅ 必须明确标注任务类型
- ✅ 必须指定负责人
- ✅ 有依赖关系的必须标注

---

### 阶段三：开发执行 (Development Execution)

#### 2.3.1 开发工作流标准

**日常开发流程**:
```
1. 从 To Do 列领取任务 → 移动到 In Progress
2. 创建特性分支: feature/[JIRA-ID]-[简短描述]
3. 开发完成后提交 PR/MR
4. 在 Jira 中添加 PR 链接
5. 移动到 Code Review
6. 审查通过后合并代码
7. 移动到 Testing
8. QA验证通过后移动到 Done
```

**Jira 状态更新规范**:

| 动作 | Jira 操作 | 必填字段 |
|------|----------|----------|
| 开始开发 | In Progress + 添加开始时间 | Assignee, Start Date |
| 提交代码 | 添加 PR 链接到评论 | PR Link |
| 代码审查 | Code Review | Reviewers |
| 发现问题 | 添加评论 + 标记阻塞 | Block Reason |
| 测试验证 | Testing | Test Result |
| 完成 | Done + 添加实际工时 | Actual Hours, Resolution |

#### 2.3.2 Git 与 Jira 集成

**分支命名规范**:
```
特性分支: feature/PROJ-123-add-login-page
修复分支: bugfix/PROJ-456-fix-memory-leak
热修复分支: hotfix/PROJ-789-critical-bug
发布分支: release/v1.2.0
```

**Commit Message 规范**:
```
格式: [JIRA-ID] [类型] 描述

示例:
PROJ-123 feat: 添加用户登录功能
PROJ-456 fix: 修复内存泄漏问题
PROJ-789 docs: 更新API文档

类型:
- feat: 新功能
- fix: Bug修复
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试相关
- chore: 构建/工具
```

**质量标准**:
- ✅ 每个 Commit 必须包含 Jira ID
- ✅ 分支必须从最新 develop/main 创建
- ✅ PR 必须通过所有检查（CI/CD、Code Review）
- ✅ 合并后必须删除特性分支
- ✅ Jira 状态必须与实际进度一致

#### 2.3.3 代码审查标准

**Jira Code Review 清单**:
```
□ 代码符合团队编码规范
□ 有足够的单元测试（覆盖率>80%）
□ 没有明显的性能问题
□ 没有安全漏洞
□ 日志和错误处理完善
□ 文档注释清晰
□ 符合设计模式原则
□ 通过了自动化测试
```

**Jira 操作**:
- Code Review 状态必须指定 Reviewer
- Review 意见在 PR 中回复
- 审查通过后更新状态到 Testing

---

### 阶段四：测试与质量控制 (Testing & QA)

#### 2.4.1 Bug 管理流程

**Bug 创建标准**:
```
Summary: [BUG] 简短描述问题

Description:
## 问题描述
[发生了什么]

## 重现步骤
1. [步骤1]
2. [步骤2]
3. [步骤3]

## 期望结果
[应该发生什么]

## 实际结果
[实际发生了什么]

## 环境信息
- 版本: [版本号]
- 浏览器/设备: [信息]
- 账号: [测试账号]

## 附件
- 截图: [链接]
- 日志: [链接]
- 视频: [链接]

Severity: [Blocker/Critical/Major/Minor/Trivial]
Priority: [Highest/High/Medium/Low/Lowest]
Component: [组件名]
Affected Version: [版本号]
```

**严重程度定义**:

| 级别 | 定义 | 响应时间 | 修复时间 |
|------|------|----------|----------|
| **Blocker** | 系统崩溃，完全不可用 | 立即 | 4小时内 |
| **Critical** | 核心功能不可用 | 2小时内 | 24小时内 |
| **Major** | 主要功能异常 | 当天 | 3天内 |
| **Minor** | 次要问题，有 workaround | 3天内 | 下个迭代 |
| **Trivial** | 界面/文案问题 | 1周内 | 下个迭代 |

**Bug 工作流**:
```
Open → Confirmed → In Progress → Fixed → Verified → Closed
```

**Jira 操作**:
- QA 发现 Bug → 创建 Issue，状态 Open
- 开发确认 Bug → 移动到 Confirmed
- 开发修复 → 移动到 Fixed，添加修复版本
- QA 验证 → 移动到 Verified 或 Reopened
- 上线后关闭 → Closed

#### 2.4.2 测试用例管理

**Jira + Zephyr/Xray 集成**:
```
Test Case 字段:
- Test Case ID: TC-[编号]
- Related Story: [关联的Story]
- Preconditions: [前置条件]
- Test Steps: 
  1. [步骤]
  2. [步骤]
- Expected Result: [期望结果]
- Test Data: [测试数据]
- Priority: [High/Medium/Low]
```

**测试覆盖率要求**:
- 单元测试覆盖率 ≥ 80%
- 核心流程必须有集成测试
- API 必须有自动化测试
- UI 关键路径有自动化测试

#### 2.4.3 质量门禁

**发布前检查清单 (Definition of Done)**:
```
□ 所有Story完成并通过验收
□ 代码审查100%通过
□ 单元测试通过率100%
□ 集成测试通过率100%
□ 严重Bug清零
□ 性能测试通过
□ 安全扫描通过
□ 文档更新完成
□ 产品验收通过
□ 回滚方案就绪
```

---

### 阶段五：发布与收尾 (Release & Closure)

#### 2.5.1 版本发布流程

**Jira 版本管理**:
1. 创建版本
   - 路径: Releases → Create version
   - 格式: `v[主版本].[功能版本].[补丁版本]`

2. 版本字段:
   ```
   Name: v1.2.0
   Description: 
     ## 主要功能
     - [功能1]
     - [功能2]
     
     ## 修复问题
     - [Bug1]
     - [Bug2]
     
     ## 已知问题
     - [问题1]
   
   Release Date: [计划发布日期]
   ```

3. 关联 Issues
   - 将完成的 Story/Bug 关联到版本
   - 检查版本进度: Releases → 版本名称

**发布检查清单**:
```
□ 所有功能开发和测试完成
□ Release Notes 编写完成
□ 数据库迁移脚本准备就绪
□ 配置变更清单确认
□ 监控系统配置完成
□ 回滚方案验证通过
□ 运维团队已通知
□ 产品团队已确认
```

#### 2.5.2 Sprint 回顾 (Sprint Retrospective)

**Jira 数据收集**:
```
1. Sprint 报告
   - 路径: Reports → Sprint Report
   - 查看完成率、燃尽图

2. 速度图 (Velocity Chart)
   - 路径: Reports → Velocity Chart
   - 记录团队速度

3. 累积流图 (Cumulative Flow Diagram)
   - 分析瓶颈

4. 控制图 (Control Chart)
   - 分析周期时间
```

**回顾会议模板**:
```
## Sprint [编号] 回顾

### 数据指标
- 计划完成: [X] Story Points
- 实际完成: [Y] Story Points
- 完成率: [Z]%
- Bug 数量: [N]

### 做得好的 (What went well)
- [事项1]
- [事项2]

### 需要改进的 (What needs improvement)
- [问题1]
- [问题2]

### 行动计划 (Action Items)
| 行动 | 负责人 | 截止日期 |
|------|--------|----------|
| [行动1] | [姓名] | [日期] |
| [行动2] | [姓名] | [日期] |
```

#### 2.5.3 项目归档

**Jira 项目归档清单**:
```
□ 所有Issues状态更新为Closed/Resolved
□ 未完成的Story移动到Backlog或下一版本
□ Sprint关闭
□ 版本发布标记为Released
□ 导出项目报告
□ 归档相关文档到Confluence
□ 团队权限调整
□ 经验教训总结完成
```

---

## 三、Jira 看板配置指南

### 3.1 标准看板列配置

```
Backlog | To Do | In Progress | Code Review | Testing | Done
```

**列限制 (WIP Limits)**:

| 列 | WIP Limit | 说明 |
|----|-----------|------|
| In Progress | 每人2个 | 防止并行任务过多 |
| Code Review | 每人3个 | 避免积压 |
| Testing | 团队容量 | 根据QA人数设定 |

### 3.2 快速过滤器 (Quick Filters)

推荐配置:
```
- 我的任务: assignee = currentUser()
- 当前Sprint: sprint in openSprints()
- 仅Story: type = Story
- 仅Bug: type = Bug
- 高优先级: priority in (High, Highest)
- 未分配: assignee is EMPTY
- 已逾期: duedate < now() AND status != Done
```

### 3.3 Swimlanes 配置

```
- Expedite (加急): priority = Highest
- Stories: type = Story
- Tasks: type = Task
- Bugs: type = Bug
```

---

## 四、Jira 仪表板配置

### 4.1 推荐小工具 (Gadgets)

| 小工具 | 用途 | 配置 |
|--------|------|------|
| **燃尽图** | 跟踪Sprint进度 | 显示当前Sprint |
| **累积流图** | 识别流程瓶颈 | 显示最近4周 |
| **速度图** | 团队产能趋势 | 显示最近8个Sprint |
| **饼图** | 任务分布 | 按状态/优先级/负责人 |
| **过滤器结果** | 关键列表 | 我的任务、Blockers |
| **问题统计** | Bug趋势 | 按创建/解决日期 |
| **平均周期时间** | 效率指标 | 显示趋势 |

### 4.2 管理仪表板示例

```
┌─────────────────────┬─────────────────────┐
│   燃尽图             │   速度图            │
├─────────────────────┼─────────────────────┤
│   累积流图           │   Bug趋势           │
├─────────────────────┴─────────────────────┤
│   高风险任务列表                          │
├─────────────────────┬─────────────────────┤
│   待办任务 Top 10    │   阻塞任务列表      │
└─────────────────────┴─────────────────────┘
```

---

## 五、交付物质量标准清单

### 5.1 需求阶段交付物

| 交付物 | 质量标准 | 验收人 | 存储位置 |
|--------|----------|--------|----------|
| **产品需求文档 (PRD)** | 包含用户故事、流程图、原型；所有功能点可追踪到Jira Epic | 产品经理+技术负责人 | Confluence |
| **技术方案文档** | 架构图、接口设计、数据库设计；经过技术评审 | 架构师 | Confluence |
| **UI设计稿** | 高保真设计；包含交互说明；标注完整 | 设计师+产品经理 | Figma/蓝湖 |

### 5.2 开发阶段交付物

| 交付物 | 质量标准 | 验收人 | 存储位置 |
|--------|----------|--------|----------|
| **源代码** | 通过Code Review；单元测试≥80%；符合编码规范 | Tech Lead | Git仓库 |
| **API文档** | 使用Swagger/OpenAPI；包含示例；实时同步 | 后端负责人 | Swagger UI |
| **数据库脚本** | 包含升级/回滚脚本；已测试 | DBA+开发 | Git仓库 |
| **技术文档** | 架构说明、部署文档、运维手册 | Tech Lead | Confluence |

### 5.3 测试阶段交付物

| 交付物 | 质量标准 | 验收人 | 存储位置 |
|--------|----------|--------|----------|
| **测试用例** | 覆盖所有Story；可执行；已评审 | QA Lead | Jira/Zephyr |
| **测试报告** | 包含通过率、覆盖率、遗留Bug | QA Lead | Confluence |
| **性能测试报告** | 达到性能指标；包含瓶颈分析 | 性能工程师 | Confluence |
| **安全测试报告** | 高危漏洞清零；中危有修复计划 | 安全团队 | Confluence |

### 5.4 发布阶段交付物

| 交付物 | 质量标准 | 验收人 | 存储位置 |
|--------|----------|--------|----------|
| **Release Notes** | 包含新功能、Bug修复、已知问题、破坏性变更 | 产品经理 | Jira版本 |
| **部署文档** | 详细步骤；包含回滚方案；已验证 | 运维+开发 | Confluence |
| **监控配置** | 告警规则；Dashboard；已验证 | SRE | Grafana |
| **用户手册** | 功能说明；操作步骤；截图清晰 | 产品经理 | Confluence |

---

## 六、常见问题与解决方案

### 6.1 Jira 使用问题

**Q: Story Points 怎么估算准确？**
A: 使用 Planning Poker，参考历史数据，建立团队基线

**Q: Bug 太多怎么办？**
A: 设定Bug上限，超过则停止新功能开发，先修复Bug

**Q: 任务经常延期？**
A: 减小Sprint容量，增加Buffer，拆分更细的Task

### 6.2 流程优化建议

1. **自动化集成**: 将 Git、CI/CD、Jira 集成，自动更新状态
2. **每日站会**: 15分钟，只看板，快速同步
3. **定期回顾**: 每Sprint回顾，持续改进
4. **度量驱动**: 关注 Lead Time、Cycle Time、Bug率

---

## 附录

### A. Jira JQL 常用查询

```sql
-- 我当前Sprint的任务
assignee = currentUser() AND sprint in openSprints()

-- 本周到期的任务
dueDate >= startOfWeek() AND dueDate <= endOfWeek()

-- 逾期任务
dueDate < now() AND status != Done

-- 高优先级未分配任务
priority in (High, Highest) AND assignee is EMPTY

-- 本月创建的Bug
type = Bug AND created >= startOfMonth()

-- 某个Epic下的所有任务
"Epic Link" = PROJ-123

-- 阻塞的任务
status = Blocked

-- 我参与Code Review的任务
assignee in (membersOf("developers")) AND status = "Code Review"
```

### B. Jira 字段与 Screen 配置清单

（详细配置步骤略，可根据需要补充）

### C. 培训计划建议

1. **Jira 基础培训**: 1小时（全员）
2. **工作流培训**: 30分钟（开发团队）
3. **敏捷实践培训**: 2小时（核心团队）
4. **Jira 管理员培训**: 4小时（管理员）

---

**文档维护**: 每季度更新一次
**负责人**: [指定Jira管理员]
**审核人**: [项目经理/Scrum Master]
