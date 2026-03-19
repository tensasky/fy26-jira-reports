const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE_URL = 'https://lululemon.atlassian.net/wiki/spaces/TPMO/pages/5550408024/Technology+Jira+Standardization+Governance';
const OUTPUT_DIR = '/Users/admin/.openclaw/workspace/confluence_export';

// 全局状态
const scrapedUrls = new Map(); // url -> { level, index }
const pageTree = []; // 存储树形结构

(async () => {
  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }
  
  console.log('连接到 Chrome...');
  const browser = await chromium.connectOverCDP('http://localhost:9222');
  console.log('✓ 已连接');
  
  const context = browser.contexts()[0];
  const pages = await context.pages();
  let page = pages.find(p => p.url().includes('atlassian.net')) || await context.newPage();
  
  // 从主页面开始递归抓取
  console.log('\\n开始递归抓取页面树...\\n');
  await scrapePageRecursive(page, BASE_URL, 1, 1);
  
  // 生成树形索引
  generateTreeIndex();
  
  console.log('\\n========================================');
  console.log('✓ 递归抓取完成！');
  console.log(`总页数: ${scrapedUrls.size}`);
  console.log(`输出目录: ${OUTPUT_DIR}`);
  console.log('========================================');
  
  await browser.close();
})();

async function scrapePageRecursive(page, url, level, index) {
  // 避免重复抓取
  if (scrapedUrls.has(url)) {
    console.log(`  [跳过] 已抓取: ${url.substring(0, 60)}...`);
    return scrapedUrls.get(url);
  }
  
  // 限制最大层级和总数
  if (level > 5) {
    console.log(`  [跳过] 超过最大层级: ${url.substring(0, 60)}...`);
    return null;
  }
  
  if (scrapedUrls.size >= 100) {
    console.log(`  [跳过] 达到最大页数限制`);
    return null;
  }
  
  const indent = '  '.repeat(level - 1);
  console.log(`${indent}[Level ${level}-${index}] 抓取: ${url.substring(0, 70)}`);
  
  try {
    await page.goto(url, { timeout: 60000 });
    await page.waitForTimeout(3000);
    
    const data = await page.evaluate(() => {
      const titleEl = document.querySelector('h1#title-text') || 
                     document.querySelector('[data-testid="page-title"]') ||
                     document.querySelector('h1');
      const title = titleEl ? titleEl.innerText.trim() : document.title;
      
      const isLoginPage = document.title.toLowerCase().includes('log in') ||
                         document.body.innerText.includes('登录以继续');
      
      if (isLoginPage) {
        return { isLoginPage: true, title: title };
      }
      
      let contentEl = document.querySelector('[data-testid="content-wrapper"]') || 
                     document.querySelector('#main-content') ||
                     document.querySelector('.wiki-content') ||
                     document.querySelector('#content-body') ||
                     document.querySelector('[role="main"]') ||
                     document.body;
      
      // 获取页面中的所有子页面链接
      const links = [];
      const linkEls = document.querySelectorAll('a[href*="/pages/"]');
      linkEls.forEach(a => {
        const href = a.getAttribute('href');
        if (href && href.includes('/pages/') && a.innerText.trim()) {
          const fullUrl = href.startsWith('http') ? href : 'https://lululemon.atlassian.net' + href;
          // 只抓取同一空间的页面
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
        childLinks: links.slice(0, 50) // 限制每页最多50个子链接
      };
    });
    
    if (data.isLoginPage) {
      console.log(`${indent}  ✗ 遇到登录页，跳过`);
      return null;
    }
    
    // 保存页面
    const savedFile = saveMarkdown(data, level, index);
    const pageInfo = {
      title: data.title,
      url: data.url,
      level: level,
      index: index,
      file: savedFile,
      children: []
    };
    
    scrapedUrls.set(url, pageInfo);
    pageTree.push(pageInfo);
    
    console.log(`${indent}  ✓ 已保存: ${data.title.substring(0, 50)} (${data.text.length} 字符, ${data.childLinks.length} 个子页面)`);
    
    // 递归抓取子页面
    if (data.childLinks.length > 0) {
      let childIndex = 1;
      for (const link of data.childLinks) {
        const childInfo = await scrapePageRecursive(page, link.url, level + 1, childIndex++);
        if (childInfo) {
          pageInfo.children.push(childInfo);
        }
      }
    }
    
    return pageInfo;
    
  } catch (e) {
    console.log(`${indent}  ✗ 错误: ${e.message}`);
    return null;
  }
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
    markdown += `\n\n---\n\n## 子页面链接 (${data.childLinks.length})\n\n`;
    data.childLinks.forEach((link, i) => {
      markdown += `${i+1}. [${link.title}](${link.url})\n`;
    });
  }
  
  fs.writeFileSync(mdFile, markdown);
  return path.basename(mdFile);
}

function generateTreeIndex() {
  let index = '# Confluence 页面树形索引\n\n';
  index += `**生成时间:** ${new Date().toISOString()}\n\n`;
  index += `**总页数:** ${pageTree.length}\n\n`;
  index += `**层级结构:**\\n`;
  index += '- Level 1: 根页面\n';
  index += '- Level 2: 一级子页面\n';
  index += '- Level 3+: 更深层级\n\n';
  index += '---\n\n';
  
  // 按层级排序
  const sortedPages = [...pageTree].sort((a, b) => {
    if (a.level !== b.level) return a.level - b.level;
    return a.index - b.index;
  });
  
  // 生成树形结构
  function printTree(page, indent = 0) {
    const prefix = '  '.repeat(indent);
    let line = `${prefix}- **L${page.level}** [${page.title}](${page.file})\n`;
    
    if (page.children && page.children.length > 0) {
      for (const child of page.children) {
        line += printTree(child, indent + 1);
      }
    }
    return line;
  }
  
  // 找到根页面
  const rootPages = sortedPages.filter(p => p.level === 1);
  for (const root of rootPages) {
    index += printTree(root, 0);
    index += '\n';
  }
  
  // 添加平面列表
  index += '---\n\n## 平面列表（按层级）\n\n';
  sortedPages.forEach(p => {
    const indent = '  '.repeat(p.level - 1);
    index += `${indent}L${p.level}: [${p.title}](${p.file})\n`;
  });
  
  fs.writeFileSync(path.join(OUTPUT_DIR, 'TREE_INDEX.md'), index);
  console.log('✓ 树形索引已生成: TREE_INDEX.md');
}
