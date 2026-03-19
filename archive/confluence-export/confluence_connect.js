const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = '/Users/admin/.openclaw/workspace/confluence_export';

(async () => {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  console.log('尝试连接到已运行的 Chrome...');
  
  let browser;
  try {
    // 尝试连接 CDP
    browser = await chromium.connectOverCDP('http://localhost:9222');
    console.log('✓ 成功连接到 Chrome CDP');
  } catch (e) {
    console.log('✗ 无法连接 CDP:', e.message);
    console.log('尝试使用已保存的 profile 启动...');
    
    // 使用用户数据目录启动
    browser = await chromium.launchPersistentContext(
      '/Users/admin/.openclaw/workspace/chrome_debug_profile',
      {
        headless: false,
        args: ['--start-maximized'],
        viewport: { width: 1440, height: 900 }
      }
    );
  }
  
  const context = browser.contexts()[0];
  const pages = context.pages();
  let page = pages.find(p => p.url().includes('atlassian.net'));
  
  if (!page) {
    console.log('未找到 Confluence 页面，打开新页面...');
    page = await context.newPage();
    await page.goto('https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance');
  } else {
    console.log('找到已打开的 Confluence 页面:', page.url());
  }
  
  // 刷新页面确保最新状态
  await page.reload();
  await page.waitForTimeout(3000);
  
  // 检查登录状态
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
      bodyPreview: document.body.innerText.substring(0, 500)
    };
  });
  
  console.log('页面状态:', JSON.stringify(info, null, 2));
  
  if (info.isLoginPage) {
    console.log('✗ 仍在登录页');
    return;
  }
  
  console.log('✓ 已登录，开始抓取...');
  
  // 抓取内容
  const data = await page.evaluate(() => {
    const titleEl = document.querySelector('h1#title-text') || 
                   document.querySelector('[data-testid="page-title"]') ||
                   document.querySelector('h1');
    const title = titleEl ? titleEl.innerText.trim() : document.title;
    
    let contentEl = document.querySelector('[data-testid="content-wrapper"]') || 
                   document.querySelector('#main-content') ||
                   document.querySelector('.wiki-content') ||
                   document.body;
    
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
  
  // 保存
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
  
})();
