const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    headless: false,
    args: ['--start-maximized']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  
  const page = await context.newPage();
  
  console.log('打开页面...');
  await page.goto('https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance', { timeout: 60000 });
  
  // 等待一下
  await page.waitForTimeout(5000);
  
  // 截图
  await page.screenshot({ path: '/Users/admin/.openclaw/workspace/confluence_current.png', fullPage: true });
  console.log('截图已保存: confluence_current.png');
  
  // 检查登录状态
  const info = await page.evaluate(() => {
    return {
      title: document.title,
      url: window.location.href,
      hasContent: !!document.querySelector('[data-testid="content-wrapper"]'),
      bodyText: document.body.innerText.substring(0, 500)
    };
  });
  
  console.log('页面信息:', JSON.stringify(info, null, 2));
  
  await browser.close();
})();
