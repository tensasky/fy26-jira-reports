const { chromium } = require('playwright');

(async () => {
  // 尝试连接已运行的 Chrome
  const browser = await chromium.connectOverCDP('http://localhost:9222').catch(async () => {
    // 如果没有，启动新浏览器
    console.log('CDP not available, launching new browser...');
    return await chromium.launch({ headless: false });
  });
  
  const context = browser.contexts()[0] || await browser.newContext();
  const page = context.pages()[0] || await context.newPage();
  
  await page.goto('https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance');
  
  // 等待页面加载
  await page.waitForLoadState('networkidle');
  
  // 提取内容
  const content = await page.evaluate(() => {
    const mainContent = document.querySelector('[data-testid="content-wrapper"]') || 
                       document.querySelector('#main-content') ||
                       document.body;
    return {
      title: document.title,
      html: mainContent.innerHTML,
      text: mainContent.innerText
    };
  });
  
  console.log(JSON.stringify(content, null, 2));
  
  await browser.close();
})();
