#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNTIN-730 Initiative 周报自动化脚本 - v5.1 (Final)
格式要求：
- Key/Summary 合并列
- 移除 Creator 和 Reporter
- Description 列宽 500-700px
- Alerts 图标显示在 Key 后
"""

import json
import html
import os
import sys
import time
import shutil
import asyncio
import aiohttp
import requests
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib

# ==================== 配置 ====================
JIRA_URL = "https://lululemon.atlassian.net"
JIRA_EMAIL = "rcheng2@lululemon.com"
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

# AI API 配置
AI_API_KEY = os.environ.get("AI_API_KEY", "sk-5tLeZUj3QbkSlHPRJrPRXObQtI1JcDYNLtA2cnvq6heP5kxs")
AI_BASE_URL = os.environ.get("AI_BASE_URL", "http://newapi.200m.997555.xyz/v1")
AI_MODEL = os.environ.get("AI_MODEL", "claude-sonnet-4-6")
AI_MAX_CONCURRENT = 30
AI_RATE_LIMIT = 0.1

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
SENDER_EMAIL = "3823810468@qq.com"
SENDER_PASSWORD = os.environ.get("QQ_MAIL_PASSWORD", "ftbabipdlxliceai")
RECIPIENTS = ["chinatechpmo@lululemon.com"]
CC_RECIPIENTS = ["rcheng2@lululemon.com"]

# 路径配置
CACHE_DIR = Path("/tmp/ai_summary_cache_semantic")
CACHE_INDEX = CACHE_DIR / "index.json"
REPORTS_DIR = Path("/Users/admin/.openclaw/workspace/reports")
JIRA_DATA_FILE = Path("/tmp/cntin_initiatives.json")

# ==================== 日志 ====================
def log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ==================== 语义哈希缓存 ====================
class SemanticCache:
    def __init__(self, cache_dir, ttl_days=7):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()
        self.ttl = ttl_days * 24 * 3600
        self.stats = {"hits": 0, "misses": 0, "saves": 0}
    
    def _load_index(self):
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_index(self):
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
    
    def _compute_hash(self, summary, description):
        content = f"{summary}:{description}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get(self, summary, description):
        content_hash = self._compute_hash(summary, description)
        if content_hash not in self.index:
            self.stats["misses"] += 1
            return None
        
        cache_entry = self.index[content_hash]
        cache_file = self.cache_dir / cache_entry['file']
        
        if not cache_file.exists():
            del self.index[content_hash]
            self._save_index()
            self.stats["misses"] += 1
            return None
        
        if time.time() - cache_entry['created'] > self.ttl:
            cache_file.unlink()
            del self.index[content_hash]
            self._save_index()
            self.stats["misses"] += 1
            return None
        
        with open(cache_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.stats["hits"] += 1
            return data.get('ai_summary')
    
    def set(self, summary, description, ai_summary):
        content_hash = self._compute_hash(summary, description)
        cache_file = self.cache_dir / f"{content_hash[:8]}.json"
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'ai_summary': ai_summary,
                'hash': content_hash,
                'cached_at': datetime.now().isoformat()
            }, f, ensure_ascii=False)
        
        self.index[content_hash] = {
            'file': cache_file.name,
            'created': time.time(),
            'ttl': self.ttl
        }
        self._save_index()
        self.stats["saves"] += 1
    
    def get_stats(self):
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        return {
            **self.stats,
            "total": total,
            "hit_rate": f"{hit_rate:.1f}%"
        }

# ==================== 步骤 1: 清空缓存 ====================
def clear_cache():
    log("🧹 步骤 1: 清空历史缓存...")
    try:
        if CACHE_DIR.exists():
            shutil.rmtree(CACHE_DIR)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        log("   ✅ 已清空语义缓存目录")
        return True
    except Exception as e:
        log(f"   ❌ 清空缓存失败: {e}")
        return False

# ==================== 步骤 2: 从 Jira 获取数据 ====================
def fetch_jira_data():
    log("📥 步骤 2: 从 Jira 全量获取数据...")
    
    if not JIRA_API_TOKEN:
        log("   ❌ 错误: 未设置 JIRA_API_TOKEN 环境变量")
        return None
    
    jql = 'project = CNTIN AND issuetype = Initiative AND parent = CNTIN-730 AND status != Cancelled'
    
    # Jira Cloud 使用 Basic Auth
    import base64
    auth_str = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/json'
    }
    
    all_issues = []
    max_results = 100
    next_page_token = None
    page_count = 0
    
    try:
        while True:
            url = f"{JIRA_URL}/rest/api/3/search/jql"
            params = {
                "jql": jql,
                "maxResults": max_results,
                "fields": "summary,status,assignee,priority,created,updated,duedate,description,labels"
            }
            
            # 如果有 nextPageToken，添加到请求参数
            if next_page_token:
                params["nextPageToken"] = next_page_token
            
            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            issues = data.get('issues', [])
            all_issues.extend(issues)
            page_count += 1
            
            log(f"   ✅ 第 {page_count} 页: 获取 {len(issues)} 条，累计 {len(all_issues)} 条")
            
            # 检查是否还有更多数据
            is_last = data.get('isLast', True)
            if is_last:
                break
            
            # 获取下一页的 token
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
        
        log(f"   📊 总共获取 {len(all_issues)} 个 Initiative")
        
        result_data = {
            'issues': all_issues,
            'total': len(all_issues),
            'timestamp': datetime.now().isoformat()
        }
        
        with open(JIRA_DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(result_data, f, ensure_ascii=False, indent=2)
        
        log(f"   ✅ 数据已保存到: {JIRA_DATA_FILE}")
        return result_data
        
    except Exception as e:
        log(f"   ❌ 获取数据失败: {e}")
        import traceback
        log(f"   错误详情: {traceback.format_exc()}")
        return None

# ==================== 步骤 3: 生成 AI Summary ====================
def pre_clean_description(description):
    """预清理描述内容"""
    if not description:
        return ""
    if isinstance(description, str):
        text = re.sub(r'<[^>]+>', ' ', description)
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:1000]
    return str(description)[:1000]

async def generate_ai_summary_async(session, semaphore, issue, cache):
    """异步生成单个 AI Summary"""
    key = issue.get('key', '')
    fields = issue.get('fields', {})
    summary = fields.get('summary', '')
    description = pre_clean_description(fields.get('description', ''))
    
    cached = cache.get(summary, description)
    if cached:
        return key, cached
    
    async with semaphore:
        prompt = f"""请根据以下 Initiative 的标题和描述，用简洁自然的语言总结 What 和 Why。

【Initiative 标题】: {summary}
【描述内容】: {description}

要求：
1. What 部分：用动词开头，直接说明要做什么
2. Why 部分：说明业务价值和原因，用自然的口语化表达
3. 避免 AI 腔调，不要出现"旨在"、"致力于"这种套话
4. 中英混合使用，术语保留英文
5. 每部分 1-2 句话，简洁直接

格式：
<b>What:</b> [动词开头，直接说明做什么]
<b>Why:</b> [自然解释为什么要做]"""
        
        try:
            headers = {
                'Authorization': f'Bearer {AI_API_KEY}',
                'Content-Type': 'application/json'
            }
            payload = {
                'model': AI_MODEL,
                'messages': [
                    {'role': 'system', 'content': '你是专业的业务分析师'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.3,
                'max_tokens': 300
            }
            
            async with session.post(f'{AI_BASE_URL}/chat/completions', headers=headers, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    ai_summary = data['choices'][0]['message']['content'].strip()
                    cache.set(summary, description, ai_summary)
                    return key, ai_summary
                else:
                    error_text = await response.text()
                    return key, f"<span class='error'>API Error {response.status}</span>"
                    
        except Exception as e:
            return key, f"<span class='error'>{str(e)[:50]}</span>"
        
        finally:
            await asyncio.sleep(AI_RATE_LIMIT)

async def batch_generate_ai_summaries(issues_data):
    """批量生成 AI Summary"""
    log("🤖 步骤 3: 批量异步生成 AI Summary...")
    log(f"   ⚙️ 并发数: {AI_MAX_CONCURRENT}, 速率限制: {AI_RATE_LIMIT}s/请求")
    
    cache = SemanticCache(CACHE_DIR)
    
    issues_with_desc = []
    for issue in issues_data.get('issues', []):
        fields = issue.get('fields', {})
        summary = fields.get('summary', '')
        description = pre_clean_description(fields.get('description', ''))
        if summary or description:
            issues_with_desc.append(issue)
    
    cached_count = 0
    for issue in issues_with_desc:
        fields = issue.get('fields', {})
        summary = fields.get('summary', '')
        description = pre_clean_description(fields.get('description', ''))
        cached = cache.get(summary, description)
        if cached:
            cached_count += 1
    
    need_generation = len(issues_with_desc) - cached_count
    log(f"   📊 需要生成 AI Summary: {need_generation} 个 (已缓存: {cached_count})")
    
    connector = aiohttp.TCPConnector(limit=AI_MAX_CONCURRENT)
    timeout = aiohttp.ClientTimeout(total=300)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        semaphore = asyncio.Semaphore(AI_MAX_CONCURRENT)
        
        tasks = [
            generate_ai_summary_async(session, semaphore, issue, cache)
            for issue in issues_with_desc
        ]
        
        results = {}
        completed = 0
        failed = 0
        
        for coro in asyncio.as_completed(tasks):
            key, summary = await coro
            results[key] = summary
            completed += 1
            
            if '失败' in summary or 'error' in summary.lower():
                failed += 1
            
            if completed % 10 == 0 or completed == len(tasks):
                log(f"   ✅ 进度: {completed}/{len(tasks)} ({failed} 失败)")
    
    stats = cache.get_stats()
    log(f"   📈 缓存统计: 命中 {stats['hits']}, 未命中 {stats['misses']}, 命中率 {stats['hit_rate']}")
    
    return results

# ==================== 步骤 4: 生成 HTML 报告 (v5.1 格式) ====================
def check_sla_alert(fields):
    """检查是否需要 SLA Alert"""
    status = fields.get('status', {})
    status_name = status.get('name', '')
    
    if status_name in ['Done', 'Closed', 'Resolved']:
        return False
    
    updated_str = fields.get('updated')
    if updated_str:
        try:
            updated = datetime.fromisoformat(updated_str.replace('Z', '+00:00').replace('+00:00', ''))
            if updated:
                days_since = (datetime.now(timezone.utc) - updated).days
                return days_since > 14
        except:
            pass
    return False

def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
    except:
        return None

def generate_html_report(data, ai_summary_results):
    """生成 v5.1 格式的 HTML 报告"""
    log("📄 步骤 4: 生成 HTML 报告 (v5.1 格式)...")
    
    issues = data.get('issues', [])
    
    # 统计
    status_counts = {}
    label_counts = {}
    sla_alert_count = 0
    
    for issue in issues:
        fields = issue.get('fields', {})
        status_name = fields.get('status', {}).get('name', 'Unknown')
        status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        labels = fields.get('labels', [])
        for label in labels:
            label_counts[label] = label_counts.get(label, 0) + 1
        
        if check_sla_alert(fields):
            sla_alert_count += 1
    
    sorted_labels = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)
    
    # 生成状态筛选按钮
    status_buttons = []
    for status, count in sorted(status_counts.items()):
        status_buttons.append(f'<button class="filter-btn" data-status="{status}" onclick="filterByStatus(\'{status}\')">{status}<span class="count-badge">{count}</span></button>')
    
    # 生成 Label 筛选按钮
    label_buttons = []
    for label, count in sorted_labels[:10]:
        label_buttons.append(f'<button class="filter-btn" data-label="{label}" onclick="filterByLabel(\'{label}\')">{label}<span class="count-badge">{count}</span></button>')
    
    # 构建数据表格行
    table_rows = []
    for issue in issues:
        fields = issue.get('fields', {})
        key = issue.get('key', '')
        summary = html.escape(fields.get('summary', ''))
        status = fields.get('status', {}).get('name', 'Unknown')
        assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
        priority = fields.get('priority', {}).get('name', '')
        created = fields.get('created', '')[:10] if fields.get('created') else ''
        updated = fields.get('updated', '')[:10] if fields.get('updated') else ''
        due_date = fields.get('duedate', '') or '-'
        labels = fields.get('labels', [])
        
        # 获取 AI Summary
        ai_summary = ai_summary_results.get(key, '')
        
        # 清理描述 - 处理 ADF 格式
        description = fields.get('description', '')
        if isinstance(description, dict):
            desc_text = extract_text_from_adf(description)
        elif isinstance(description, str):
            desc_text = re.sub(r'<[^>]+>', ' ', description)
            desc_text = re.sub(r'\s+', ' ', desc_text).strip()
        else:
            desc_text = str(description)
        
        # SLA Alert - 图标显示在 Key 后
        has_sla = check_sla_alert(fields)
        sla_icon = '⚠️ ' if has_sla else ''
        row_class = 'has-sla-alert' if has_sla else ''
        
        # Label tags
        label_tags = ''.join([f'<span class="label-tag">{html.escape(l)}</span>' for l in labels[:3]])
        
        row = f'''<tr class="{row_class}" data-status="{status}" data-key="{key.lower()}" data-summary="{summary.lower()}" data-labels="{','.join(labels)}" onclick="toggleRow(this)">
            <td class="col-key-summary">
                <span class="issue-key">{sla_icon}{key}</span>
                <span class="issue-summary" title="{summary}">{summary}</span>
                <div class="labels-list">{label_tags}</div>
            </td>
            <td class="col-status"><span class="status-badge" style="background: {get_status_color(status)}">{status}</span></td>
            <td class="col-assignee"><span class="field-text">{assignee}</span></td>
            <td class="col-priority"><span class="field-text">{priority}</span></td>
            <td class="col-date"><span class="field-text">{created}</span></td>
            <td class="col-date"><span class="field-text">{updated}</span></td>
            <td class="col-due"><span class="field-text">{due_date}</span></td>
            <td class="col-desc"><div class="description-cell">{html.escape(desc_text[:500])}</div></td>
            <td class="col-ai-summary"><div class="ai-summary-cell">{ai_summary}</div></td>
        </tr>'''
        table_rows.append(row)
    
    # HTML 内容 - v5.1 格式
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNTIN-730 FY26 Intakes - Initiative 报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #F4F5F7; color: #172B4D; line-height: 1.6; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #0052CC 0%, #0747A6 100%); color: white; padding: 25px 30px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 13px; opacity: 0.9; }}
        .filter-section {{ background: white; padding: 15px 20px; border-radius: 8px; margin-bottom: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .filter-row {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }}
        .filter-row:last-child {{ margin-bottom: 0; }}
        .filter-row input {{ padding: 8px 12px; border: 1px solid #DFE1E6; border-radius: 4px; font-size: 14px; flex: 1; min-width: 200px; }}
        .filter-label {{ font-size: 13px; color: #5E6C84; font-weight: 500; min-width: 60px; }}
        .filter-group {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; flex: 1; }}
        .filter-btn {{ padding: 6px 14px; border: 1px solid #DFE1E6; border-radius: 16px; font-size: 12px; font-weight: 500; cursor: pointer; background: white; color: #5E6C84; transition: all 0.2s; }}
        .filter-btn:hover {{ border-color: #0052CC; color: #0052CC; }}
        .filter-btn.active {{ background: #0052CC; color: white; border-color: #0052CC; }}
        .count-badge {{ background: #EBECF0; color: #172B4D; padding: 2px 6px; border-radius: 10px; font-size: 11px; margin-left: 4px; }}
        .filter-btn.active .count-badge {{ background: rgba(255,255,255,0.3); color: white; }}
        .issues-table {{ background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow-x: auto; }}
        table {{ width: 100%; border-collapse: collapse; min-width: 1400px; }}
        th {{ padding: 12px 16px; background: #FAFBFC; border-bottom: 1px solid #EBECF0; font-size: 11px; font-weight: 600; color: #5E6C84; text-transform: uppercase; letter-spacing: 0.5px; text-align: left; white-space: nowrap; }}
        td {{ padding: 14px 16px; border-bottom: 1px solid #EBECF0; vertical-align: top; }}
        tr {{ cursor: pointer; transition: background 0.2s; }}
        tr:hover td {{ background: #F4F5F7; }}
        tr.has-sla-alert td {{ background: #FFFAF5; }}
        tr.has-sla-alert:hover td {{ background: #FFF0E0; }}
        .col-key-summary {{ min-width: 280px; max-width: 350px; }}
        .col-status {{ width: 90px; }}
        .col-assignee {{ width: 110px; }}
        .col-priority, .col-due {{ width: 80px; }}
        .col-date {{ width: 90px; }}
        .col-desc {{ min-width: 500px; max-width: 700px; }}
        .col-ai-summary {{ min-width: 350px; max-width: 450px; }}
        .issue-key {{ display: block; color: #0052CC; font-weight: 600; font-size: 13px; margin-bottom: 4px; }}
        .issue-summary {{ display: block; font-size: 14px; color: #172B4D; line-height: 1.4; word-break: break-word; }}
        .status-badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 600; color: white; text-transform: uppercase; }}
        .field-text {{ font-size: 13px; color: #172B4D; }}
        .description-cell {{ font-size: 12px; color: #5E6C84; line-height: 1.5; max-height: 80px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; word-break: break-word; }}
        .ai-summary-cell {{ font-size: 12px; color: #172B4D; line-height: 1.6; max-height: 100px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 5; -webkit-box-orient: vertical; word-break: break-word; background: #F6F8FA; padding: 10px; border-radius: 6px; border-left: 3px solid #0052CC; }}
        .ai-summary-cell b {{ color: #0052CC; }}
        .labels-list {{ display: flex; flex-wrap: wrap; gap: 4px; margin-top: 6px; }}
        .label-tag {{ background: #E9F2FF; color: #0052CC; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 500; }}
        .legend {{ background: white; padding: 12px 20px; border-radius: 8px; margin-bottom: 15px; font-size: 12px; color: #5E6C84; }}
        .hidden {{ display: none !important; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 CNTIN-730 FY26 Intakes</h1>
        <div class="subtitle">Parent = CNTIN-730 | Status ≠ Cancelled | Type = Initiative</div>
        <div class="subtitle">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>

    <div class="filter-section">
        <div class="filter-row">
            <input type="text" id="searchInput" placeholder="🔍 搜索 Key、Summary、Description..." onkeyup="filterIssues()">
        </div>
        <div class="filter-row">
            <span class="filter-label">状态:</span>
            <div class="filter-group">
                <button class="filter-btn active" data-status="all" onclick="filterByStatus('all')">全部<span class="count-badge">{len(issues)}</span></button>
                {''.join(status_buttons)}
            </div>
        </div>
        <div class="filter-row">
            <span class="filter-label">Label:</span>
            <div class="filter-group">
                {''.join(label_buttons)}
            </div>
        </div>
    </div>

    <div class="legend">
        ⚠️ Missing SLA: 状态 ≠ Done 且更新时间超过2周
    </div>

    <div class="issues-table">
        <table>
            <thead>
                <tr>
                    <th class="col-key-summary">Key / Summary</th>
                    <th class="col-status">Status</th>
                    <th class="col-assignee">Assignee</th>
                    <th class="col-priority">Priority</th>
                    <th class="col-date">Created</th>
                    <th class="col-date">Updated</th>
                    <th class="col-due">Due Date</th>
                    <th class="col-desc">Description</th>
                    <th class="col-ai-summary">🤖 AI Summary</th>
                </tr>
            </thead>
            <tbody id="issuesContainer">
                {''.join(table_rows)}
            </tbody>
        </table>
    </div>

    <script>
        function filterByStatus(status) {{
            document.querySelectorAll('.filter-btn[data-status]').forEach(btn => btn.classList.remove('active'));
            document.querySelector(`.filter-btn[data-status="${{status}}"]`).classList.add('active');
            filterIssues();
        }}
        
        function filterByLabel(label) {{
            const btn = document.querySelector(`.filter-btn[data-label="${{label}}"]`);
            btn.classList.toggle('active');
            filterIssues();
        }}
        
        function filterIssues() {{
            const search = document.getElementById('searchInput').value.toLowerCase();
            const activeStatus = document.querySelector('.filter-btn[data-status].active')?.dataset.status || 'all';
            const activeLabels = Array.from(document.querySelectorAll('.filter-btn[data-label].active')).map(btn => btn.dataset.label);
            
            document.querySelectorAll('tbody tr').forEach(row => {{
                const key = row.dataset.key;
                const summary = row.dataset.summary;
                const status = row.dataset.status;
                const labels = row.dataset.labels.split(',');
                
                const matchSearch = key.includes(search) || summary.includes(search);
                const matchStatus = activeStatus === 'all' || status === activeStatus;
                const matchLabel = activeLabels.length === 0 || activeLabels.some(l => labels.includes(l));
                
                row.classList.toggle('hidden', !(matchSearch && matchStatus && matchLabel));
            }});
        }}
        
        function toggleRow(row) {{
            row.classList.toggle('expanded');
        }}
    </script>
</body>
</html>'''
    
    # 保存 HTML 文件
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = REPORTS_DIR / f"cntin_730_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    log(f"   ✅ HTML 报告已保存: {output_file}")
    return output_file

def get_status_color(status):
    """获取状态颜色"""
    colors = {
        'Done': '#36B37E',
        'In Progress': '#FF8B00',
        'Discovery': '#6554C0',
        'New': '#0052CC',
        'Strategy': '#00B8D9',
        'Closed': '#626F86',
        'Resolved': '#36B37E'
    }
    return colors.get(status, '#97A0AF')

def extract_text_from_adf(adf):
    """从 ADF 格式提取文本"""
    if not isinstance(adf, dict):
        return str(adf)
    
    texts = []
    def extract(node):
        if isinstance(node, dict):
            if 'text' in node:
                texts.append(node['text'])
            for key in ['content', 'marks', 'attrs']:
                if key in node:
                    extract(node[key])
        elif isinstance(node, list):
            for item in node:
                extract(item)
    
    extract(adf)
    return ' '.join(texts)[:500]

# ==================== 步骤 5: 发送邮件 ====================
def send_email(html_file):
    """发送邮件"""
    log("📧 步骤 5: 发送邮件...")
    
    if not SENDER_PASSWORD:
        log("   ⚠️ 警告: 未设置 QQ_MAIL_PASSWORD 环境变量，跳过邮件发送")
        return False
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = ', '.join(RECIPIENTS)
        msg['Cc'] = ', '.join(CC_RECIPIENTS)
        msg['Subject'] = f"[CNTIN-730 Initiative Report] {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        with open(html_file, 'rb') as f:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(f.read())
        
        encoders.encode_base64(attachment)
        attachment.add_header('Content-Disposition', f'attachment; filename="{html_file.name}"')
        msg.attach(attachment)
        
        try:
            log("   🔄 尝试 SSL 连接...")
            with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                all_recipients = RECIPIENTS + CC_RECIPIENTS
                server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())
            log("   ✅ SSL 连接发送成功")
        except Exception as ssl_error:
            log(f"   ⚠️ SSL 连接失败，尝试 STARTTLS...")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                all_recipients = RECIPIENTS + CC_RECIPIENTS
                server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())
            log("   ✅ STARTTLS 连接发送成功")
        
        log(f"   ✅ 邮件已发送至: {', '.join(RECIPIENTS)}")
        return True
        
    except Exception as e:
        log(f"   ❌ 邮件发送失败: {e}")
        return False

# ==================== 主函数 ====================
def main():
    log("=" * 60)
    log("🚀 CNTIN-730 Initiative 周报生成工具 v5.1")
    log("=" * 60)
    
    start_time = time.time()
    
    # 步骤 1: 清空缓存
    if not clear_cache():
        return 1
    
    # 步骤 2: 获取 Jira 数据
    data = fetch_jira_data()
    if not data:
        return 1
    
    # 步骤 3: 生成 AI Summary
    ai_results = asyncio.run(batch_generate_ai_summaries(data))
    
    # 步骤 4: 生成 HTML 报告
    html_file = generate_html_report(data, ai_results)
    
    # 步骤 5: 发送邮件
    send_email(html_file)
    
    elapsed = time.time() - start_time
    log("=" * 60)
    log(f"✅ 全部完成! 耗时: {elapsed:.1f} 秒")
    log(f"📄 报告文件: {html_file}")
    log("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
