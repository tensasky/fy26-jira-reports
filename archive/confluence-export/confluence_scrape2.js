const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance';

(async () => {
  // 启动浏览器
  const browser = await chromium.launch({ 
    headless: false,
    args: ['--start-maximized']
  });
  
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });
  
  const page = await context.newPage();
  
  console.log('正在打开页面（60秒超时）...');
  try {
    await page.goto(BASE_URL, { 
      waitUntil: 'domcontentloaded',
      timeout: 60000 
    });
    
    // 等待内容加载
    console.log('等待页面内容加载...');
    await page.waitForTimeout(5000);
    
    // 保存登录状态
    await context.storageState({ path: '/Users/admin/.openclaw/workspace/confluence_auth.json' });
    console.log('登录状态已保存');
    
  } catch (e) {
    console.log('页面加载警告:', e.message);
    console.log('继续尝试提取内容...');
  }
  
  // 提取页面内容
  console.log('提取页面内容...');
  const pageData = await page.evaluate(() => {
    // 获取标题
    const titleEl = document.querySelector('h1#title-text') || 
                   document.querySelector('[data-testid="page-title"]') ||
                   document.querySelector('h1');
    const title = titleEl ? titleEl.innerText.trim() : document.title;
    
    // 获取主要内容 - 尝试多个选择器
    let contentEl = document.querySelector('[data-testid="content-wrapper"]') || 
                   document.querySelector('#main-content') ||
                   document.querySelector('.wiki-content') ||
                   document.querySelector('#content-body') ||
                   document.querySelector('[role="main"]') ||
                   document.body;
    
    // 获取所有子页面链接
    const links = [];
    const linkEls = document.querySelectorAll('a[href*="/pages/"]');
    linkEls.forEach(a => {
      const href = a.getAttribute('href');
      if (href && href.includes('/pages/') && a.innerText.trim()) {
        const fullUrl = href.startsWith('http') ? href : 'https://lululemon.atlassian.net' + href;
        if (!links.find(l => l.url === fullUrl)) {
          links.push({
            title: a.innerText.trim(),
            url: fullUrl
          });
        }
      }
    });
    
    return {
      title: title,
      html: contentEl ? contentEl.innerHTML.substring(0, 50000) : '',
      text: contentEl ? contentEl.innerText : '',
      childLinks: links.slice(0, 30)
    };
  });
  
  console.log('页面标题:', pageData.title);
  console.log('内容长度:', pageData.text.length, '字符');
  console.log('找到子页面链接:', pageData.childLinks.length);
  
  // 保存内容
  const outputDir = '/Users/admin/.openclaw/workspace/confluence_export';
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  // 生成文件名
  const safeTitle = pageData.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_').substring(0, 50);
  const mdFile = path.join(outputDir, `1_${safeTitle}.md`);
  
  // 转换为 Markdown
  let markdown = `# ${pageData.title}\n\n`;
  markdown += `**Source:** ${BASE_URL}\n\n`;
  markdown += `**Exported:** ${new Date().toISOString()}\n\n`;
  markdown += `---\n\n`;
  markdown += pageData.text;
  
  // 添加子页面链接
  if (pageData.childLinks.length > 0) {
    markdown += `\n\n---\n\n## 子页面链接\n\n`;
    pageData.childLinks.forEach((link, i) => {
      markdown += `${i+1}. [${link.title}](${link.url})\n`;
    });
  }
  
  fs.writeFileSync(mdFile, markdown);
  console.log('\\n✅ 已保存:', mdFile);
  
  // 保存页面数据
  fs.writeFileSync(
    path.join(outputDir, 'page_data.json'), 
    JSON.stringify(pageData, null, 2)
  );
  
  console.log('\\n抓取完成！输出目录:', outputDir);
  
  await browser.close();
})();
