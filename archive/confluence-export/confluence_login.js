const { chromium } = require('playwright');
const fs = require('fs');

(async () => {
  // 启动浏览器（非 headless，方便你登录）
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--start-maximized']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  
  const page = await context.newPage();
  
  console.log('正在打开 Confluence 页面...');
  await page.goto('https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance');
  
  // 等待 2 分钟让用户登录
  console.log('请在 2 分钟内完成登录...');
  await page.waitForTimeout(120000);
  
  // 保存登录状态
  await context.storageState({ path: '/Users/admin/.openclaw/workspace/confluence_auth.json' });
  console.log('登录状态已保存');
  
  // 检查是否登录成功（通过页面内容）
  const content = await page.evaluate(() => {
    const title = document.querySelector('h1')?.innerText || document.title;
    const mainContent = document.querySelector('[data-testid="content-wrapper"]') || 
                       document.querySelector('#main-content') ||
                       document.body;
    return {
      title: title,
      hasContent: mainContent.innerText.length > 500,
      textPreview: mainContent.innerText.substring(0, 500)
    };
  });
  
  console.log('页面信息:', JSON.stringify(content, null, 2));
  
  // 保持浏览器打开，等待用户确认
  console.log('浏览器保持打开，确认登录成功后按 Enter 继续...');
  process.stdin.once('data', async () => {
    await browser.close();
    console.log('浏览器已关闭');
  });
})();
