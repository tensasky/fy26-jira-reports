const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance';
const USER_DATA_DIR = '/Users/admin/.openclaw/workspace/chrome_confluence_data';
const OUTPUT_DIR = '/Users/admin/.openclaw/workspace/confluence_export';
const LOG_FILE = path.join(OUTPUT_DIR, 'scrape.log');

// 日志函数
function log(msg) {
  const timestamp = new Date().toISOString();
  const line = `[${timestamp}] ${msg}`;
  console.log(line);
  fs.appendFileSync(LOG_FILE, line + '\n');
}

(async () => {
  // 清理旧的锁文件
  const lockFile = path.join(USER_DATA_DIR, 'SingletonLock');
  if (fs.existsSync(lockFile)) {
    fs.unlinkSync(lockFile);
  }
  
  // 确保输出目录存在
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  log('========================================');
  log('启动自动化 Confluence 抓取');
  log('========================================');
  
  // 检查是否有已保存的登录状态
  const authFile = path.join(USER_DATA_DIR, 'auth.json');
  let useSavedAuth = fs.existsSync(authFile);
  
  // 启动浏览器
  log('启动浏览器...');
  const browser = await chromium.launch({
    headless: false,
    args: ['--start-maximized']
  });
  
  let context;
  if (useSavedAuth) {
    log('使用已保存的登录状态');
    context = await browser.newContext({
      storageState: authFile,
      viewport: { width: 1440, height: 900 }
    });
  } else {
    log('创建新上下文');
    context = await browser.newContext({
      viewport: { width: 1440, height: 900 }
    });
  }
  
  const page = await context.newPage();
  
  // 打开页面
  log('打开目标页面...');
  await page.goto(BASE_URL, { timeout: 120000 });
  
  // 等待页面加载
  log('等待页面加载（60秒）...');
  await page.waitForTimeout(60000);
  
  // 检查是否已登录
  let isLoggedIn = await checkLogin(page);
  
  if (!isLoggedIn && !useSavedAuth) {
    log('未检测到登录状态，再等待60秒...');
    await page.waitForTimeout(60000);
    isLoggedIn = await checkLogin(page);
  }
  
  if (!isLoggedIn) {
    log('✗ 仍未登录，保存截图并退出');
    await page.screenshot({ path: path.join(OUTPUT_DIR, 'login_check.png') });
    await browser.close();
    log('提示: 请在浏览器中登录后重新运行脚本');
    process.exit(1);
  }
  
  log('✓ 检测到已登录状态');
  
  // 保存登录状态供下次使用
  await context.storageState({ path: authFile });
  log('✓ 登录状态已保存');
  
  // 开始递归抓取
  const pagesToScrape = [{ 
    url: BASE_URL, 
    title: 'Technology Jira Standardization Governance',
    level: 1,
    index: 1
  }];
  const scrapedUrls = new Set();
  const allPages = [];
  
  // 抓取所有页面（广度优先）
  while (pagesToScrape.length > 0 && scrapedUrls.size < 50) {
    const current = pagesToScrape.shift();
    
    if (scrapedUrls.has(current.url)) {
      continue;
    }
    
    log(`\\n[${scrapedUrls.size + 1}] 抓取: ${current.title} (Level ${current.level})`);
    
    try {
      const data = await scrapePage(page, current.url);
      
      if (data.isLoginPage) {
        log('  ✗ 遇到登录页，可能会话已过期');
        break;
      }
      
      // 保存页面
      const savedFile = saveMarkdown(data, current.level, current.index);
      allPages.push({
        ...current,
        contentLength: data.text.length,
        savedFile: savedFile
      });
      scrapedUrls.add(current.url);
      log(`  ✓ 已保存 (${data.text.length} 字符)`);
      
      // 添加子页面到队列
      if (data.childLinks && data.childLinks.length > 0) {
        let childIndex = 1;
        for (const link of data.childLinks) {
          if (!scrapedUrls.has(link.url) && !pagesToScrape.find(p => p.url === link.url)) {
            pagesToScrape.push({
              url: link.url,
              title: link.title,
              level: current.level + 1,
              index: childIndex++
            });
          }
        }
        log(`  → 发现 ${data.childLinks.length} 个子页面`);
      }
      
      // 延迟，避免请求过快
      await page.waitForTimeout(3000);
      
    } catch (e) {
      log(`  ✗ 错误: ${e.message}`);
    }
  }
  
  // 生成索引文件
  generateIndex(allPages);
  
  log('\\n========================================');
  log('✓ 抓取完成！');
  log(`共抓取 ${scrapedUrls.size} 个页面`);
  log(`输出目录: ${OUTPUT_DIR}`);
  log('========================================');
  
  // 关闭浏览器
  await browser.close();
  
})();

async function checkLogin(page) {
  return await page.evaluate(() => {
    const title = document.title.toLowerCase();
    const hasContent = document.querySelector('[data-testid="content-wrapper"]') ||
                      document.querySelector('#main-content') ||
                      document.querySelector('.wiki-content');
    return hasContent && 
           !title.includes('log in') && 
           !title.includes('登录') &&
           document.body.innerText.length > 2000;
  });
}

async function scrapePage(page, url) {
  await page.goto(url, { timeout: 120000 });
  await page.waitForTimeout(3000);
  
  return await page.evaluate(() => {
    const titleEl = document.querySelector('h1#title-text') || 
                   document.querySelector('[data-testid="page-title"]') ||
                   document.querySelector('h1');
    const title = titleEl ? titleEl.innerText.trim() : document.title;
    
    const isLoginPage = document.title.toLowerCase().includes('log in') ||
                       document.body.innerText.includes('登录以继续') ||
                       document.querySelector('input[type="password"]') !== null;
    
    if (isLoginPage) {
      return { isLoginPage: true, title: title };
    }
    
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
      isLoginPage: false,
      text: contentEl ? contentEl.innerText : '',
      childLinks: links.slice(0, 30)
    };
  });
}

function saveMarkdown(data, level, index) {
  const safeTitle = data.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_').substring(0, 50);
  const prefix = level === 1 
    ? '1_' 
    : `${level}_${index.toString().padStart(2, '0')}_`;
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
  return mdFile;
}

function generateIndex(pages) {
  let index = '# Confluence 页面索引\n\n';
  index += `**生成时间:** ${new Date().toISOString()}\n\n`;
  index += `**总页数:** ${pages.length}\n\n`;
  index += '---\n\n';
  
  pages.forEach(p => {
    const indent = '  '.repeat(p.level - 1);
    const fileName = path.basename(p.savedFile);
    index += `${indent}- [${p.title}](${fileName}) - ${p.contentLength} 字符\n`;
  });
  
  fs.writeFileSync(path.join(OUTPUT_DIR, 'INDEX.md'), index);
  log('✓ 索引文件已生成: INDEX.md');
}
