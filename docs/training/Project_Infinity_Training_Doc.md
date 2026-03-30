# Project Infinity - 培训文档

> **培训对象**: 技术团队成员  
> **文档来源**: https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/6121816068/Project+Charter+-+Infinity  
> **生成日期**: 2026-03-30  
> **版本**: v1.0

---

## 1. 项目概述

### 1.1 项目名称
**Project Infinity** - Enterprise Taskforce for Deployment Excellence

### 1.2 项目愿景
建立一个未来的运维环境：
- ✅ **零常驻人类管理员权限** (Zero Standing Human Admins)
- ✅ **零因人工错误导致的 Sev1 事故**

### 1.3 核心问题
lululemon 面临的主要风险：
- 分散的权限管理
- 广泛的 admin 权限暴露
- 不一致的生产环境控制

我们需要转向：**零常驻管理权限** + **受控的临时权限提升** + **标准化的自动化访问路径**

---

## 2. 团队结构

| 角色 | 成员 |
|------|------|
| **执行发起人 (Executive Sponsor)** | Ranju Das (SLT) |
| **执行支持者** | Jebin Zacharia, Nigel Storey, Jean-Neol Filippi, Rahul Botika |
| **项目负责人 (Lead)** | Ravi Kesapragada |
| **核心团队** | Alissa Allard, Craig Henderson, Vijayanarayanan Ramanujam, Sitanshu Maheshwari, TBH - India |
| **扩展核心团队** | Ravi Sharma, Evan Hickey, Rajiv Gandhi |
| **项目经理** | Aditya Davalbhakta |

---

## 3. 目标与成果 (Objectives & Outcomes)

| 目标 | 指标 |
|------|------|
| 移除常驻生产环境人类管理员 | 接近 100% |
| 自动化 SNOW change 创建 | ≥ 1,060 个 pipelines |
| 强制 2 人审核 (仅限 FTE) | 100% 生产变更 |
| 标准化 Runbook | 覆盖所有非 IaC 操作 |
| 收紧 JIT 权限提升 | 1-2 小时窗口期 |

---

## 4. 项目范围

### 4.1 In Scope (范围内)
- ✅ AWS 管理权限合理化
- ✅ GitLab → ServiceNow 自动化变更创建
- ✅ DEA/PIM 权限治理
- ✅ 基于 SSM/自动化框架的 Runbook 标准化
- ✅ 领导层沟通与报告

### 4.2 Out of Scope (范围外)
- ❌ Azure, Kafka, 其他平台
- ❌ 非 GitLab CI/CD 系统

---

## 5. 限制与假设

| 类别 | 详情 |
|------|------|
| **限制** | DEA 限制、高峰期限制、多团队依赖、无专项预算、无专属资源 |
| **假设** | 团队迁移到 runbooks/pipelines；CAB 保留审批权限 |

---

## 6. 路线图 (Roadmap)

### Phase 1
- 所有 AWS admin 账户移除
- DEA 收紧
- GitLab→SNOW pilot

### Phase 2
- 常驻管理员消除
- 环境级别强制

### Phase 3
- Runbook 自动化
- 集中 IAM roles

### Phase 4
- GitOps-only 生产部署
- 黄金路径模板

---

## 7. 完成定义 (Definition of Done)

- ✅ 零常驻生产环境人类管理员
- ✅ 100% 生产变更需 2-FTE 审批
- ✅ 所有 pipelines 与 SNOW 集成
- ✅ 完整 Runbook 覆盖
- ✅ 合规仪表盘发布

---

## 8. KPIs

| KPI 类别 | 指标 |
|----------|------|
| **事故 (Incidents)** | 人工错误导致的 Sev1 数量 |
| **权限 (Access)** | Admin 数量；DEA 使用量 |
| **治理 (Governance)** | 2-FTE 审核遵守率 |
| **自动化 (Automation)** | 自动变更采用率 |

---

## 9. 推广波次 (Rollout Waves)

| 波次 | 团队 | 备注 |
|------|------|------|
| **Wave 1** | OMS, B2B, PoS/Xstore | Terraform-ready |
| **Wave 2** | 其他工程域 | DEA 标准化 |
| **Wave 3** | 企业平台 | Pipeline-only PRD |

---

## 10. 快速问答 (FAQ)

### Q1: 为什么要移除常驻管理员权限？
**A**: 降低风险、改善治理、预防 Sev1 事故。

### Q2: 紧急情况下如何获取管理员权限？
**A**: 通过 DEA/PIM，需 **2-FTE 审批**，**1-2 小时时限**，完整审计追踪。

### Q3: 如果需要进行手动修复怎么办？
**A**: 使用批准的 **Runbook** + 限时访问；然后创建 backlog 项用于自动化。

### Q4: 事故响应会因此变慢吗？
**A**: 不会 — DEA 支持批准后近乎即时的权限提升。

---

## 11. 时间线 (Timeline)

### 11.1 关键里程碑

| 时间 | 里程碑 | 描述 |
|------|--------|------|
| **Jan 2026** | Phase 1 启动 | 启动自动化工作流 (OMS, B2B, PoS/Xstore) |
| **Jan 13, 2026** | CHG0090256 执行 | 移除 278 个不活跃 AWS PRD admin 用户 |
| **Jan-Feb 2026** | Admin 清理扩大 | 移除 700+ admin 账户；DEA guardrail 收紧 |
| **Feb-Mar 2026** | Phase 2 准备 | 识别剩余企业 admin 用户 |
| **Mar 2026** | Phase 2 执行 | 开始移除所有常驻 AWS admins |
| **Mar-Apr 2026** | 自动化扩展 | 接入更多团队；标准化 runbooks |
| **Apr-May 2026** | GitOps + Runbook 集成 | 所有 pipelines 自动生成 SNOW change tickets |
| **May 2026** | 企业对齐 | 所有 org 对齐自动化路线图 |
| **June 2026** | **VOC 目标达成** | **100% 移除所有常驻 AWS 人类管理员** |
| **Post-June 2026** | Phase 4 | GitOps-only PRD 路径；黄金路径模板 |

### 11.2 6月底 VOC 目标

#### 1. 消除所有常驻人类管理员权限
- 100% AWS PRD + NPD 人类管理员已移除
- 仅允许即时权限提升 (DEA/PIM)
- 访问时长限制在 1-2 小时
- 完整的证据捕获和审计日志

#### 2. 自动化采用（所有识别团队）
- 所有生产变更通过以下方式路由：
  - **Terraform + CI/CD pipelines**, 或
  - **Runbook 驱动的自动化 (SSM, Datadog, AWS SDK 等)**
- 不允许手动控制台或临时 API 变更
- 所有 pipelines 生成自动化 ServiceNow change 记录

#### 3. 移除个人类管理员权限的生产访问
- 任何用户不得使用个人提升权限直接执行 PRD 变更
- 例外仅限紧急场景（需 2-FTE 审批）
- 通过 GitLab、SNOW、IAM 和 DEA guardrails 强制执行策略

#### 4. EW (Engineering Workstreams) PRD 变更自动化
- Engineering Workstreams 完全过渡到自动化验证+执行
- 部署前需同行评审，部署后需验证
- 可重复的 runbooks 已创建并在低环境中演练

---

## 12. 关键行动项

| # | 行动项 | 负责人 |
|---|--------|--------|
| 1 | 完成当前 admin 账户审计 | Core Team |
| 2 | 制定 DEA 标准操作流程 | Security |
| 3 | 接入 GitLab→SNOW 集成 | Platform Team |
| 4 | 创建 Runbook 模板 | SRE |
| 5 | 沟通计划制定 | PMO |

---

## 附录 A: 术语表

| 术语 | 解释 |
|------|------|
| **DEA** | Dynamic Elevation Authorization - 动态权限提升授权 |
| **PIM** | Privileged Identity Management - 特权身份管理 |
| **SNOW** | ServiceNow - 变更管理工具 |
| **FTE** | Full-Time Employee - 全职员工 |
| **Sev1** | Severity 1 - P0 级别事故 |
| **Runbook** | 标准操作流程文档 |
| **GitOps** | 基于 Git 的运维模式 |

---

*本培训文档基于 Confluence 页面自动生成，如需更新请联系项目团队。*
