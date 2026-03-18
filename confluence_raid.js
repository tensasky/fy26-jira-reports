const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const PAGES = [
  {
    url: 'https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5567748080/RAID',
    name: 'RAID',
    filename: 'RAID.md'
  },
  {
    url: 'https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5847908830/Risk+and+Issue+Escalation+Usage+Guide',
    name: 'Risk and Issue Escalation Usage Guide',
    filename: 'Risk_Issue_Escalation_Usage_Guide.md'
  },
  {
    url: 'https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5931576147/RAID+Hierarchy+Driving+Health+Reporting',
    name: 'RAID Hierarchy Driving Health Reporting',
    filename: 'RAID_Hierarchy_Health_Reporting.md'
  }
];

const OUTPUT_DIR = '/Users/admin/.openclaw/workspace/confluence_export';

(async () => {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  console.log('连接到 Chrome...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  console.log('✓ 已连接');
  
  const context = browser.contexts()[0];
  const page = await context.newPage();
  
  const results = [];
  
  for (const target of PAGES) {
    console.log(`\n抓取: ${target.name}`);
    try {
      await page.goto(target.url, { timeout: 60000 });
      await page.waitForTimeout(3000);
      
      const data = await page.evaluate(() => {
        const titleEl = document.querySelector('h1#title-text') || 
                       document.querySelector('[data-testid="page-title"]') ||
                       document.querySelector('h1');
        const title = titleEl ? titleEl.innerText.trim() : document.title;
        
        let contentEl = document.querySelector('[data-testid="content-wrapper"]') || 
                       document.querySelector('#main-content') ||
                       document.querySelector('.wiki-content') ||
                       document.body;
        
        return {
          title: title,
          url: window.location.href,
          text: contentEl ? contentEl.innerText : ''
        };
      });
      
      // 保存为 Markdown
      const mdContent = `# ${data.title}\n\n` +
        `**Source:** ${data.url}\n\n` +
        `**Exported:** ${new Date().toISOString()}\n\n` +
        `---\n\n` +
        data.text;
      
      const filePath = path.join(OUTPUT_DIR, target.filename);
      fs.writeFileSync(filePath, mdContent);
      
      console.log(`  ✓ 已保存: ${target.filename} (${data.text.length} 字符)`);
      results.push({ ...target, ...data, charCount: data.text.length });
      
    } catch (e) {
      console.log(`  ✗ 错误: ${e.message}`);
      results.push({ ...target, error: e.message });
    }
  }
  
  await browser.close();
  
  // 生成中文培训手册
  generateChineseManual(results, OUTPUT_DIR);
  
  console.log('\n========================================');
  console.log('✓ 抓取完成！');
  console.log('========================================');
  
})();

function generateChineseManual(results, outputDir) {
  let manual = `# RAID 风险管理培训手册

## 📚 目录

1. [RAID 概述](#1-raid-概述)
2. [风险与问题升级使用指南](#2-风险与问题升级使用指南)
3. [RAID 层级驱动健康报告](#3-raid-层级驱动健康报告)
4. [最佳实践](#4-最佳实践)

---

`;

  // RAID 概述
  const raidPage = results.find(r => r.name === 'RAID');
  if (raidPage && !raidPage.error) {
    manual += `## 1. RAID 概述

**来源**: ${raidPage.url}

### 什么是 RAID？

RAID 是项目管理中用于跟踪和管理以下四个关键领域的框架：

- **R**isks (风险)
- **A**ssumptions (假设)
- **I**ssues (问题)
- **D**ependencies (依赖关系)

### 为什么使用 RAID？

RAID 日志帮助项目团队：
- 主动识别潜在风险
- 跟踪已发生的问题
- 记录关键假设
- 管理跨团队依赖关系

### 关键内容

${raidPage.text.substring(0, 3000)}

${raidPage.text.length > 3000 ? '\n*[完整内容请查看 RAID.md 文件]*\n' : ''}

---

`;
  }

  // 风险与问题升级指南
  const escalationPage = results.find(r => r.name.includes('Escalation'));
  if (escalationPage && !escalationPage.error) {
    manual += `## 2. 风险与问题升级使用指南

**来源**: ${escalationPage.url}

### 升级流程概述

本指南定义了在项目中遇到风险和问题时如何正确升级的流程和标准。

### 升级触发条件

何时应该升级风险和问题：
- 风险概率或影响增加
- 问题无法在团队层面解决
- 需要领导层决策或资源支持
- 可能影响项目里程碑或交付

### 升级路径

1. **团队层面** → 尝试在团队内解决
2. **项目经理** → 项目级决策
3. **项目群经理** → 跨项目影响
4. **领导层** → 战略决策或资源调配

### 关键内容

${escalationPage.text.substring(0, 3000)}

${escalationPage.text.length > 3000 ? '\n*[完整内容请查看 Risk_Issue_Escalation_Usage_Guide.md 文件]*\n' : ''}

---

`;
  }

  // RAID 层级驱动健康报告
  const hierarchyPage = results.find(r => r.name.includes('Hierarchy'));
  if (hierarchyPage && !hierarchyPage.error) {
    manual += `## 3. RAID 层级驱动健康报告

**来源**: ${hierarchyPage.url}

### 层级结构

RAID 条目按以下层级组织，驱动健康报告：

- **项目群级 (Program Level)**
  - 跨项目风险
  - 战略依赖关系
  
- **项目级 (Project Level)**
  - 项目特定风险
  - 项目内问题
  
- **团队级 (Team Level)**
  - 日常执行风险
  - 技术依赖关系

### 健康报告指标

基于 RAID 数据生成：
- 整体项目健康度
- 风险暴露程度
- 问题处理效率
- 依赖关系清晰度

### 关键内容

${hierarchyPage.text.substring(0, 3000)}

${hierarchyPage.text.length > 3000 ? '\n*[完整内容请查看 RAID_Hierarchy_Health_Reporting.md 文件]*\n' : ''}

---

`;
  }

  // 最佳实践
  manual += `## 4. 最佳实践

### RAID 管理最佳实践

1. **定期更新**
   - 每周审查 RAID 日志
   - 更新风险状态和影响
   - 关闭已解决的问题

2. **清晰描述**
   - 每个 RAID 条目应该有清晰的描述
   - 明确定义影响范围和应对措施
   - 指定负责人和截止日期

3. **及时升级**
   - 不要等到最后一刻才升级
   - 早期沟通可以争取更多解决时间
   - 透明沟通建立信任

4. **与利益相关方沟通**
   - 定期向团队和领导汇报 RAID 状态
   - 在关键会议（如 QBR/MBR）中审查
   - 确保所有人对风险和问题有共同理解

5. **持续改进**
   - 从已发生的问题中学习
   - 更新风险识别清单
   - 优化升级流程

### RAID 条目模板

**风险 (Risk)**:
- 描述: [风险描述]
- 概率: [高/中/低]
- 影响: [高/中/低]
- 应对措施: [缓解策略]
- 负责人: [姓名]
- 目标日期: [日期]

**问题 (Issue)**:
- 描述: [问题描述]
- 影响: [对项目的影响]
- 升级路径: [已升级给谁]
- 解决措施: [行动计划]
- 负责人: [姓名]
- 目标日期: [日期]

**假设 (Assumption)**:
- 描述: [假设内容]
- 验证方法: [如何验证]
- 风险: [如果假设不成立]
- 负责人: [姓名]

**依赖关系 (Dependency)**:
- 描述: [依赖关系]
- 依赖方: [团队/项目]
- 预期交付: [交付物]
- 截止日期: [日期]
- 负责人: [姓名]

---

## 附录

### 相关文档

- RAID.md - RAID 详细定义和框架
- Risk_Issue_Escalation_Usage_Guide.md - 风险与问题升级详细指南
- RAID_Hierarchy_Health_Reporting.md - RAID 层级与健康报告详解

### 术语表

| 术语 | 英文 | 解释 |
|------|------|------|
| RAID | Risks, Assumptions, Issues, Dependencies | 风险、假设、问题、依赖关系框架 |
| Risk | Risk | 可能影响项目目标的潜在事件 |
| Issue | Issue | 已经发生并需要解决的问题 |
| Assumption | Assumption | 被认为真实但没有验证的条件 |
| Dependency | Dependency | 项目对外部因素或其他团队的依赖 |
| Escalation | Escalation | 将问题升级到更高层级处理 |

---

**文档版本**: v1.0  
**生成日期**: ${new Date().toISOString().split('T')[0]}  
**来源**: Confluence TPMO Space - RAID 系列页面
`;

  const manualPath = path.join(outputDir, 'RAID_培训手册_中文.md');
  fs.writeFileSync(manualPath, manual);
  console.log(`\n✓ 中文培训手册已生成: RAID_培训手册_中文.md`);
}

