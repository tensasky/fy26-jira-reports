#!/usr/bin/env node
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  // 加载本地HTML文件
  await page.goto('file:///Users/admin/.openclaw/workspace/project-management-flowchart.html', {
    waitUntil: 'networkidle'
  });
  
  // 等待mermaid渲染完成
  await page.waitForTimeout(3000);
  
  // 生成PDF
  await page.pdf({
    path: '/Users/admin/.openclaw/workspace/项目管理标准实施流程.pdf',
    format: 'A4',
    printBackground: true,
    margin: {
      top: '20px',
      right: '20px',
      bottom: '20px',
      left: '20px'
    }
  });
  
  await browser.close();
  console.log('PDF generated successfully!');
})();
