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
  
  let context;
  
  // 检查是否有已保存的登录状态
  if (fs.existsSync('/Users/admin/.openclaw/workspace/confluence_auth.json')) {
    console.log('使用已保存的登录状态...');
    context = await browser.newContext({
      storageState: '/Users/admin/.openclaw/workspace/confluence_auth.json',
      viewport: { width: 1440, height: 900 }
    });
  } else {
    console.log('没有保存的登录状态，使用新上下文...');
    context = await browser.newContext({
      viewport: { width: 1440, height: 900 }
    });
  }
  
  const page = await context.newPage();
  
  console.log('正在打开页面...');
  await page.goto(BASE_URL, { waitUntil: 'networkidle' });
  
  // 保存登录状态供下次使用
  await context.storageState({ path: '/Users/admin/.openclaw/workspace/confluence_auth.json' });
  
  // 提取页面内容
  console.log('提取页面内容...');
  const pageData = await page.evaluate(() => {
    // 获取标题
    const titleEl = document.querySelector('h1#title-text') || 
                   document.querySelector('[data-testid="page-title"]') ||
                   document.querySelector('h1');
    const title = titleEl ? titleEl.innerText.trim() : document.title;
    
    // 获取主要内容
    const contentEl = document.querySelector('[data-testid="content-wrapper"]') || 
                     document.querySelector('#main-content') ||
                     document.querySelector('.wiki-content') ||
                     document.querySelector('#content-body');
    
    // 获取所有子页面链接
    const links = [];
    const linkEls = document.querySelectorAll('a[href*="/wiki/spaces/TPMO/pages/"]');
    linkEls.forEach(a => {
      if (a.href.includes('/pages/') && !links.find(l => l.url === a.href)) {
        links.push({
          title: a.innerText.trim(),
          url: a.href
        });
      }
    });
    
    return {
      title: title,
      html: contentEl ? contentEl.innerHTML : '',
      text: contentEl ? contentEl.innerText : '',
      childLinks: links.slice(0, 20) // 限制前20个链接
    };
  });
  
  console.log('页面标题:', pageData.title);
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
  
  // 简单 HTML 到 Markdown 转换
  let textContent = pageData.text;
  
  // 清理多余空行
  textContent = textContent.replace(/\n{3,}/g, '\n\n');
  
  markdown += textContent;
  
  // 添加子页面链接
  if (pageData.childLinks.length > 0) {
    markdown += `\n\n---\n\n## 子页面链接\n\n`;
    pageData.childLinks.forEach(link => {
      markdown += `- [${link.title}](${link.url})\n`;
    });
  }
  
  fs.writeFileSync(mdFile, markdown);
  console.log('已保存:', mdFile);
  
  // 保存页面数据供后续处理
  fs.writeFileSync(
    path.join(outputDir, 'page_data.json'), 
    JSON.stringify(pageData, null, 2)
  );
  
  console.log('\\n抓取完成！');
  console.log('输出目录:', outputDir);
  
  // 等待用户确认
  console.log('\\n按 Enter 关闭浏览器...');
  process.stdin.once('data', async () => {
    await browser.close();
  });
})();
