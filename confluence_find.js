const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = '/Users/admin/.openclaw/workspace/confluence_export';

(async () => {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  console.log('连接到 Chrome...');
  
  // 使用用户数据目录启动持久化上下文
  const context = await chromium.launchPersistentContext(
    '/Users/admin/.openclaw/workspace/chrome_debug_profile',
    {
      headless: false,
      args: ['--start-maximized'],
      viewport: { width: 1440, height: 900 }
    }
  );
  
  console.log('✓ 已连接');
  console.log('查找所有页面...');
  
  const pages = context.pages();
  console.log(`找到 ${pages.length} 个页面:`);
  
  pages.forEach((p, i) => {
    console.log(`  ${i+1}. ${p.url().substring(0, 80)}...`);
  });
  
  // 查找 Confluence 页面
  let confluencePage = pages.find(p => 
    p.url().includes('atlassian.net') && 
    p.url().includes('/pages/')
  );
  
  if (!confluencePage) {
    console.log('未找到 Confluence 页面，查找任何 atlassian 页面...');
    confluencePage = pages.find(p => p.url().includes('atlassian.net'));
  }
  
  if (!confluencePage) {
    console.log('✗ 未找到 Confluence 页面');
    console.log('尝试打开目标页面...');
    confluencePage = await context.newPage();
    await confluencePage.goto('https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance');
    await confluencePage.waitForTimeout(5000);
  }
  
  console.log('使用页面:', confluencePage.url());
  
  // 检查登录状态
  const info = await confluencePage.evaluate(() => {
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
      bodyLength: document.body.innerText.length
    };
  });
  
  console.log('页面状态:', JSON.stringify(info, null, 2));
  
  if (info.isLoginPage) {
    console.log('✗ 仍在登录页，可能需要手动登录');
    return;
  }
  
  console.log('✓ 已登录，开始抓取主页面...');
  
  // 抓取主页面
  const mainData = await scrapePage(confluencePage);
  saveMarkdown(mainData, 1, OUTPUT_DIR);
  
  console.log(`✓ 主页面已保存: ${mainData.title}`);
  console.log(`  内容: ${mainData.text.length} 字符`);
  console.log(`  发现 ${mainData.childLinks.length} 个子页面`);
  
  // 抓取子页面（最多10个）
  if (mainData.childLinks.length > 0) {
    console.log('\\n开始抓取子页面...');
    let successCount = 0;
    
    for (let i = 0; i < Math.min(mainData.childLinks.length, 10); i++) {
      const link = mainData.childLinks[i];
      console.log(`\\n[${i+1}/10] 抓取: ${link.title}`);
      
      try {
        const data = await scrapePage(confluencePage, link.url);
        
        if (data.isLoginPage) {
          console.log('  ✗ 遇到登录页，跳过');
          continue;
        }
        
        saveMarkdown(data, 2, OUTPUT_DIR, i + 1);
        console.log(`  ✓ 已保存 (${data.text.length} 字符)`);
        successCount++;
        
        await confluencePage.waitForTimeout(2000);
      } catch (e) {
        console.log(`  ✗ 错误: ${e.message}`);
      }
    }
    
    console.log(`\\n✓ 成功抓取 ${successCount} 个子页面`);
  }
  
  console.log('\\n========================================');
  console.log('完成！');
  console.log(`输出目录: ${OUTPUT_DIR}`);
  console.log('========================================');
  
})();

async function scrapePage(page, url) {
  if (url) {
    await page.goto(url, { timeout: 60000 });
    await page.waitForTimeout(3000);
  }
  
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

function saveMarkdown(data, level, outputDir, index = 1) {
  const safeTitle = data.title.replace(/[^a-zA-Z0-9\u4e00-\u9fa5]/g, '_').substring(0, 50);
  const prefix = level === 1 ? '1_' : `2_${index.toString().padStart(2, '0')}_`;
  const mdFile = path.join(outputDir, `${prefix}${safeTitle}.md`);
  
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
