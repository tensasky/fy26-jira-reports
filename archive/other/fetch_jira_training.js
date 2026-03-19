const { chromium } = require('playwright');
const fs = require('fs');

const URL = 'https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5884149806/Jira+Training';
const OUTPUT_FILE = '/Users/admin/.openclaw/workspace/confluence_export/Jira_Training.md';

(async () => {
  console.log('连接到 Chrome...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  console.log('✓ 已连接');
  
  const context = browser.contexts()[0];
  const page = await context.newPage();
  
  console.log('打开页面:', URL);
  await page.goto(URL, { timeout: 60000 });
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
  
  fs.writeFileSync(OUTPUT_FILE, mdContent);
  
  console.log(`✓ 已保存: ${OUTPUT_FILE}`);
  console.log(`  标题: ${data.title}`);
  console.log(`  内容: ${data.text.length} 字符`);
  
  await browser.close();
})();
