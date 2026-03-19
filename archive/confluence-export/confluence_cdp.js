const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = '/Users/admin/.openclaw/workspace/confluence_export';
const CONFLUENCE_URL = 'https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance';

(async () => {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  console.log('尝试通过 CDP 连接到 Chrome...');
  
  let browser;
  try {
    browser = await chromium.connectOverCDP('http://localhost:9222');
    console.log('✓ 已连接到 Chrome CDP');
  } catch (e) {
    console.log('✗ CDP 连接失败:', e.message);
    console.log('请确保 Chrome 已启动并开启远程调试端口 9222');
    process.exit(1);
  }
  
  const context = browser.contexts()[0] || browser;
  const pages = await context.pages();
  
  console.log(`\\n找到 ${pages.length} 个页面:`);
  pages.forEach((p, i) => {
    const url = p.url();
    console.log(`  ${i+1}. ${url.substring(0, 70)}${url.length > 70 ? '...' : ''}`);
  });
  
  // 查找 Confluence 页面
  let page = pages.find(p => p.url().includes('/pages/') && p.url().includes('atlassian'));
  
  if (!page) {
    page = pages.find(p => p.url().includes('atlassian.net'));
  }
  
  if (!page) {
    console.log('\\n未找到 Confluence 页面，创建新页面...');
    page = await context.newPage();
  }
  
  // 导航到目标页面
  if (!page.url().includes('/pages/5550408024')) {
    console.log('导航到目标页面...');
    await page.goto(CONFLUENCE_URL, { timeout: 60000 });
    await page.waitForTimeout(5000);
  }
  
  console.log('\\n当前页面:', page.url());
  
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
      bodyLength: document.body.innerText.length
    };
  });
  
  console.log('页面状态:', JSON.stringify(info, null, 2));
  
  if (info.isLoginPage) {
    console.log('\\n✗ 仍在登录页');
    await browser.close();
    return;
  }
  
  console.log('\\n✓ 已登录，开始抓取...');
  
  // 抓取主页面
  console.log('\\n[1] 抓取主页面...');
  const mainData = await scrapePage(page);
  saveMarkdown(mainData, 1, OUTPUT_DIR);
  console.log(`✓ 已保存: ${mainData.title} (${mainData.text.length} 字符)`);
  console.log(`  发现 ${mainData.childLinks.length} 个子页面`);
  
  // 抓取子页面
  if (mainData.childLinks.length > 0) {
    console.log('\\n开始抓取子页面（最多10个）...');
    let successCount = 0;
    
    for (let i = 0; i < Math.min(mainData.childLinks.length, 10); i++) {
      const link = mainData.childLinks[i];
      console.log(`\\n[${i+2}] 抓取: ${link.title.substring(0, 60)}`);
      
      try {
        await page.goto(link.url, { timeout: 60000 });
        await page.waitForTimeout(3000);
        
        const data = await scrapePage(page);
        
        if (data.isLoginPage) {
          console.log('  ✗ 遇到登录页，跳过');
          continue;
        }
        
        saveMarkdown(data, 2, OUTPUT_DIR, i + 1);
        console.log(`  ✓ 已保存 (${data.text.length} 字符)`);
        successCount++;
        
      } catch (e) {
        console.log(`  ✗ 错误: ${e.message}`);
      }
    }
    
    console.log(`\\n✓ 成功抓取 ${successCount} 个子页面`);
  }
  
  // 生成索引
  generateIndex(OUTPUT_DIR);
  
  console.log('\\n========================================');
  console.log('✓ 抓取完成！');
  console.log(`输出目录: ${OUTPUT_DIR}`);
  console.log('========================================');
  
  await browser.close();
})();

async function scrapePage(page) {
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

function generateIndex(outputDir) {
  const files = fs.readdirSync(outputDir).filter(f => f.endsWith('.md') && f !== 'INDEX.md');
  
  let index = '# Confluence 导出索引\n\n';
  index += `**生成时间:** ${new Date().toISOString()}\n\n`;
  index += `**总页数:** ${files.length}\n\n`;
  index += '---\n\n';
  
  files.sort().forEach(f => {
    index += `- [${f}](${f})\n`;
  });
  
  fs.writeFileSync(path.join(outputDir, 'INDEX.md'), index);
  console.log('✓ 索引文件已生成: INDEX.md');
}
