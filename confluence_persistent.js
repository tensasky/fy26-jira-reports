const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance';
const USER_DATA_DIR = '/Users/admin/.openclaw/workspace/chrome_user_data';
const OUTPUT_DIR = '/Users/admin/.openclaw/workspace/confluence_export';

(async () => {
  // 确保输出目录存在
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  console.log('启动持久化浏览器...');
  console.log('用户数据目录:', USER_DATA_DIR);
  
  // 使用持久化上下文 - 登录状态会保存在用户数据目录中
  const context = await chromium.launchPersistentContext(USER_DATA_DIR, {
    headless: false,
    args: ['--start-maximized'],
    viewport: { width: 1440, height: 900 }
  });
  
  const page = context.pages()[0] || await context.newPage();
  
  // 检查是否已登录
  console.log('\\n正在检查页面...');
  await page.goto(BASE_URL, { timeout: 60000 });
  await page.waitForTimeout(3000);
  
  const isLoggedIn = await page.evaluate(() => {
    const title = document.title;
    const content = document.body.innerText;
    // 检查是否有登录相关的关键词
    return !title.includes('登录') && 
           !title.includes('Log in') && 
           !content.includes('登录以继续') &&
           content.length > 1000;
  });
  
  if (!isLoggedIn) {
    console.log('\\n========================================');
    console.log('需要登录 - 请在浏览器窗口中完成 SSO 登录');
    console.log('登录完成后，回到这里按 Enter 继续');
    console.log('========================================\\n');
    
    // 等待用户按 Enter
    await new Promise(resolve => {
      process.stdin.once('data', resolve);
    });
    
    // 等待页面加载
    await page.waitForTimeout(3000);
    console.log('继续处理...\\n');
  } else {
    console.log('✓ 检测到已登录状态\\n');
  }
  
  // 现在开始抓取
  const pagesToScrape = [{ 
    url: BASE_URL, 
    title: 'Technology Jira Standardization Governance',
    level: 1 
  }];
  const scrapedUrls = new Set();
  const childPages = [];
  
  // 抓取主页面
  console.log('抓取主页面...');
  const mainData = await scrapePage(page, BASE_URL);
  saveMarkdown(mainData, 1);
  scrapedUrls.add(BASE_URL);
  
  // 收集子页面链接
  if (mainData.childLinks && mainData.childLinks.length > 0) {
    console.log(`\\n发现 ${mainData.childLinks.length} 个子页面链接`);
    for (const link of mainData.childLinks) {
      if (!scrapedUrls.has(link.url)) {
        childPages.push({
          url: link.url,
          title: link.title,
          level: 2
        });
      }
    }
  }
  
  // 询问是否抓取子页面
  if (childPages.length > 0) {
    console.log(`\\n准备抓取 ${childPages.length} 个子页面`);
    console.log('按 Enter 开始抓取子页面（或 Ctrl+C 取消）...');
    
    await new Promise(resolve => {
      process.stdin.once('data', resolve);
    });
    
    // 抓取子页面
    for (let i = 0; i < childPages.length; i++) {
      const childPage = childPages[i];
      console.log(`\\n[${i+1}/${childPages.length}] 抓取: ${childPage.title}`);
      
      try {
        const data = await scrapePage(page, childPage.url);
        saveMarkdown(data, childPage.level, i + 1);
        scrapedUrls.add(childPage.url);
        
        // 短暂等待，避免请求过快
        await page.waitForTimeout(2000);
      } catch (e) {
        console.log(`  ✗ 抓取失败: ${e.message}`);
      }
    }
  }
  
  console.log('\\n========================================');
  console.log('✓ 抓取完成！');
  console.log(`共抓取 ${scrapedUrls.size} 个页面`);
  console.log(`输出目录: ${OUTPUT_DIR}`);
  console.log('\\n浏览器保持打开，你可以手动关闭');
  console.log('========================================');
  
})();

async function scrapePage(page, url) {
  await page.goto(url, { timeout: 60000 });
  await page.waitForTimeout(3000);
  
  return await page.evaluate(() => {
    const titleEl = document.querySelector('h1#title-text') || 
                   document.querySelector('[data-testid="page-title"]') ||
                   document.querySelector('h1');
    const title = titleEl ? titleEl.innerText.trim() : document.title;
    
    let contentEl = document.querySelector('[data-testid="content-wrapper"]') || 
                   document.querySelector('#main-content') ||
                   document.querySelector('.wiki-content') ||
                   document.querySelector('#content-body') ||
                   document.querySelector('[role="main"]') ||
                   document.body;
    
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
      url: window.location.href,
      html: contentEl ? contentEl.innerHTML.substring(0, 100000) : '',
      text: contentEl ? contentEl.innerText : '',
      childLinks: links.slice(0, 50)
    };
  });
}

function saveMarkdown(data, level, index = 1) {
  const safeTitle = data.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_').substring(0, 50);
  const prefix = level === 1 ? '1_' : `2_${index.toString().padStart(2, '0')}_`;
  const mdFile = path.join(OUTPUT_DIR, `${prefix}${safeTitle}.md`);
  
  let markdown = `# ${data.title}\n\n`;
  markdown += `**Source:** ${data.url}\n\n`;
  markdown += `**Level:** ${level}\n\n`;
  markdown += `**Exported:** ${new Date().toISOString()}\n\n`;
  markdown += `---\n\n`;
  markdown += data.text;
  
  if (data.childLinks && data.childLinks.length > 0) {
    markdown += `\n\n---\n\n## 子页面链接\n\n`;
    data.childLinks.forEach((link, i) => {
      markdown += `${i+1}. [${link.title}](${link.url})\n`;
    });
  }
  
  fs.writeFileSync(mdFile, markdown);
  console.log(`  ✓ 已保存: ${path.basename(mdFile)}`);
  return mdFile;
}
