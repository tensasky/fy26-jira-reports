const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const URL = 'https://lululemon.atlassian.net/wiki/x/3YSySwE';
const OUTPUT_DIR = '/Users/admin/.openclaw/workspace/confluence_export';

(async () => {
  console.log('连接到 Chrome...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  console.log('✓ 已连接');
  
  const context = browser.contexts()[0];
  const page = await context.newPage();
  
  console.log('打开页面:', URL);
  await page.goto(URL, { timeout: 60000 });
  await page.waitForTimeout(3000);
  
  // 获取真实 URL（短链接会跳转）
  const actualUrl = page.url();
  console.log('实际 URL:', actualUrl);
  
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
  
  // 生成安全文件名
  const safeTitle = data.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_').substring(0, 50);
  const mdFile = path.join(OUTPUT_DIR, `${safeTitle}.md`);
  
  // 保存为 Markdown
  const mdContent = `# ${data.title}\n\n` +
    `**Source:** ${data.url}\n\n` +
    `**Exported:** ${new Date().toISOString()}\n\n` +
    `---\n\n` +
    data.text;
  
  fs.writeFileSync(mdFile, mdContent);
  
  console.log(`✓ 已保存: ${path.basename(mdFile)}`);
  console.log(`  标题: ${data.title}`);
  console.log(`  内容: ${data.text.length} 字符`);
  
  // 同时保存内容供生成 PPT 使用
  const contentFile = path.join(OUTPUT_DIR, 'page_content.txt');
  fs.writeFileSync(contentFile, JSON.stringify(data, null, 2));
  
  await browser.close();
})();
