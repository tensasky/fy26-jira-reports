const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance';
const OUTPUT_DIR = '/Users/admin/.openclaw/workspace/confluence_export';

(async () => {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  console.log('启动浏览器...');
  const browser = await chromium.launch({
    headless: false,
    args: ['--start-maximized']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  
  const page = await context.newPage();
  
  console.log('打开页面...');
  await page.goto(BASE_URL, { timeout: 120000 });
  
  // 等待120秒给自动登录时间
  console.log('等待自动登录（120秒）...');
  await page.waitForTimeout(120000);
  
  // 检查是否已登录
  const info = await page.evaluate(() => {
    const titleEl = document.querySelector('h1#title-text') || 
                   document.querySelector('[data-testid="page-title"]') ||
                   document.querySelector('h1');
    const hasContent = !!document.querySelector('[data-testid="content-wrapper"]');
    return {
      title: titleEl ? titleEl.innerText.trim() : document.title,
      url: window.location.href,
      isLoginPage: document.title.toLowerCase().includes('log in') || 
                   document.body.innerText.includes('登录以继续'),
      hasContent: hasContent,
      bodyPreview: document.body.innerText.substring(0, 1000)
    };
  });
  
  console.log('页面状态:', JSON.stringify(info, null, 2));
  
  if (info.isLoginPage) {
    console.log('✗ 仍在登录页，自动登录未生效');
    await browser.close();
    return;
  }
  
  console.log('✓ 检测到已登录！开始抓取...');
  
  // 保存登录状态
  await context.storageState({ path: path.join(OUTPUT_DIR, 'auth.json') });
  
  // 抓取页面内容
  const data = await page.evaluate(() => {
    const titleEl = document.querySelector('h1#title-text') || 
                   document.querySelector('[data-testid="page-title"]') ||
                   document.querySelector('h1');
    const title = titleEl ? titleEl.innerText.trim() : document.title;
    
    let contentEl = document.querySelector('[data-testid="content-wrapper"]') || 
                   document.querySelector('#main-content') ||
                   document.querySelector('.wiki-content') ||
                   document.body;
    
    // 收集子页面链接
    const links = [];
    const linkEls = document.querySelectorAll('a[href*="/pages/"]');
    linkEls.forEach(a => {
      const href = a.getAttribute('href');
      if (href && href.includes('/pages/') && a.innerText.trim()) {
        const fullUrl = href.startsWith('http') ? href : 'https://lululemon.atlassian.net' + href;
        if (fullUrl.includes('/TPMO/') && !links.find(l => l.url === fullUrl)) {
          links.push({
            title: a.innerText.trim(),
            url: fullUrl
          });
        }
      }
    });
    
    return {
      title: title,
      url: window.location.href,
      text: contentEl ? contentEl.innerText : '',
      childLinks: links.slice(0, 30)
    };
  });
  
  // 保存为 Markdown
  const safeTitle = data.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_').substring(0, 50);
  const mdFile = path.join(OUTPUT_DIR, `1_${safeTitle}.md`);
  
  let markdown = `# ${data.title}\n\n`;
  markdown += `**Source:** ${data.url}\n\n`;
  markdown += `**Exported:** ${new Date().toISOString()}\n\n`;
  markdown += `---\n\n`;
  markdown += data.text;
  
  if (data.childLinks.length > 0) {
    markdown += `\n\n---\n\n## 子页面链接\n\n`;
    data.childLinks.forEach((link, i) => {
      markdown += `${i+1}. [${link.title}](${link.url})\n`;
    });
  }
  
  fs.writeFileSync(mdFile, markdown);
  console.log(`✓ 已保存: ${mdFile}`);
  console.log(`  内容: ${data.text.length} 字符`);
  console.log(`  子页面: ${data.childLinks.length} 个`);
  
  await browser.close();
  console.log('\\n完成！');
})();
