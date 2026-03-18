#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNTIN-730 Initiative 周报自动化脚本
功能：
1. 清空历史缓存
2. 全量从 Jira 获取数据
3. 生成 AI Summary
4. 生成 HTML 报告
5. 发送邮件到指定邮箱

作者: OpenClaw
版本: v1.0.0
日期: 2026-03-18
"""

import json
import html
import os
import sys
import time
import shutil
import requests
import concurrent.futures
from datetime import datetime, timezone
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib

# ==================== 配置 ====================
# Jira 配置
JIRA_URL = "https://lululemon.atlassian.net"
JIRA_EMAIL = "rcheng2@lululemon.com"
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

# AI API 配置
AI_API_KEY = os.environ.get("AI_API_KEY", "sk-5tLeZUj3QbkSlHPRJrPRXObQtI1JcDYNLtA2cnvq6heP5kxs")
AI_BASE_URL = os.environ.get("AI_BASE_URL", "http://newapi.200m.997555.xyz/v1")
AI_MODEL = os.environ.get("AI_MODEL", "claude-sonnet-4-6")

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
SENDER_EMAIL = "3823810468@qq.com"
SENDER_PASSWORD = os.environ.get("QQ_MAIL_PASSWORD", "")
RECIPIENTS = ["chinatechpmo@lululemon.com"]
CC_RECIPIENTS = ["rcheng2@lululemon.com"]

# 路径配置
CACHE_DIR = Path("/tmp/ai_summary_cache")
REPORTS_DIR = Path("/Users/admin/.openclaw/workspace/reports")
JIRA_DATA_FILE = Path("/tmp/cntin_initiatives.json")

# ==================== 日志 ====================
def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ==================== 步骤 1: 清空历史缓存 ====================
def clear_cache():
    """清空 AI Summary 缓存和历史数据"""
    log("🧹 步骤 1: 清空历史缓存...")
    
    # 清空 AI Summary 缓存
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        log(f"   ✅ 已清空 AI Summary 缓存: {CACHE_DIR}")
    
    # 清空 Jira 数据文件
    if JIRA_DATA_FILE.exists():
        JIRA_DATA_FILE.unlink()
        log(f"   ✅ 已清空 Jira 数据文件: {JIRA_DATA_FILE}")
    
    # 重建缓存目录
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    log("   ✅ 缓存目录已重建")

# ==================== 步骤 2: 全量从 Jira 获取数据 ====================
def fetch_jira_data():
    """从 Jira 全量获取 CNTIN-730 下的所有 Initiatives"""
    log("📥 步骤 2: 从 Jira 全量获取数据...")
    
    if not JIRA_API_TOKEN:
        log("   ❌ 错误: 未设置 JIRA_API_TOKEN 环境变量")
        sys.exit(1)
    
    auth_str = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    auth_bytes = auth_str.encode('ascii')
    import base64
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    # 获取 CNTIN-730 下的所有 Initiatives
    jql = 'project = CNTIN AND issuetype = Initiative AND "Parent Link" = CNTIN-730'
    
    all_issues = []
    start_at = 0
    max_results = 100
    total = None
    
    while total is None or start_at < total:
        url = f"{JIRA_URL}/rest/api/3/search"
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,status,assignee,priority,created,updated,duedate,description,labels,creator,reporter"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            issues = data.get('issues', [])
            all_issues.extend(issues)
            
            if total is None:
                total = data.get('total', 0)
                log(f"   📊 总共 {total} 个 Initiative 需要获取")
            
            start_at += len(issues)
            log(f"   ✅ 已获取 {len(all_issues)}/{total} 个")
            
        except Exception as e:
            log(f"   ❌ 获取数据失败: {e}")
            sys.exit(1)
    
    # 保存到本地文件
    result_data = {
        "issues": all_issues,
        "total": len(all_issues),
        "fetched_at": datetime.now().isoformat()
    }
    
    with open(JIRA_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    log(f"   ✅ 数据已保存到: {JIRA_DATA_FILE}")
    return result_data

# ==================== 步骤 3: 生成 AI Summary ====================
def generate_ai_summary_one(args):
    """单个 AI Summary 生成（用于并发）"""
    description, summary, key = args
    
    # 检查缓存（虽然前面清空了，但并发时可能重复）
    cache_file = CACHE_DIR / f"{key}.json"
    if cache_file.exists():
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)
                return (key, cached.get('ai_summary', '-'))
        except:
            pass
    
    # 如果 description 为空或无效
    if not description or description == '-' or len(description) < 10:
        return (key, "<span class='ai-summary-missing'>暂无足够描述</span>")
    
    try:
        prompt = f"""请根据以下 Initiative 的标题和描述，用简洁的语言总结 What（是什么）和 Why（为什么），帮助大家用统一的语言理解这个 Initiative。

【Initiative 标题】: {summary}
【描述内容】: {description[:1000]}

请用以下格式输出（保持简洁，每部分不超过2句话）：

<b>What:</b> [一句话说明这个 Initiative 是什么，要做什么]
<b>Why:</b> [一句话说明为什么要做这个 Initiative，业务价值是什么]

注意：
- 使用业务友好的语言，避免过于技术化的术语
- 如果描述信息不足，请标注"信息不足"
- 输出格式必须是 HTML，使用 <b> 标签加粗标题
"""
        
        response = requests.post(
            f"{AI_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一个专业的业务分析师，擅长将技术描述转化为清晰的业务语言。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 300
            },
            timeout=60
        )
        
        result = response.json()
        ai_summary = result['choices'][0]['message']['content'].strip()
        
        # 缓存结果
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({'ai_summary': ai_summary, 'cached_at': datetime.now().isoformat()}, f, ensure_ascii=False)
        
        return (key, ai_summary)
        
    except Exception as e:
        return (key, f"<span class='ai-summary-error'>AI 汇总生成失败: {str(e)[:50]}</span>")

def batch_generate_ai_summaries(issues_data, max_workers=5):
    """批量并发生成 AI Summary"""
    log("🤖 步骤 3: 批量生成 AI Summary...")
    
    issues_with_desc = [
        (d['description'], d['summary'], d['key']) 
        for d in issues_data 
        if d.get('description') and d['description'] != '-' and len(d['description']) >= 10
    ]
    
    log(f"   📊 需要生成 AI Summary: {len(issues_with_desc)} 个")
    
    results = {}
    completed = 0
    failed = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(generate_ai_summary_one, args): args[2] for args in issues_with_desc}
        for future in concurrent.futures.as_completed(futures):
            key, summary = future.result()
            results[key] = summary
            completed += 1
            if '失败' in summary or 'error' in summary.lower():
                failed += 1
            if completed % 20 == 0:
                log(f"   ✅ 进度: {completed}/{len(issues_with_desc)}")
    
    log(f"   ✅ AI Summary 生成完成: {completed} 个 (失败: {failed} 个)")
    return results

# ==================== 步骤 4: 生成 HTML 报告 ====================
def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
    except:
        return None

def format_date(date_str):
    """格式化日期"""
    dt = parse_date(date_str)
    if dt:
        return dt.strftime('%Y-%m-%d')
    return '-'

def get_status_color(status_name):
    """获取状态颜色"""
    status_colors = {
        'New': '#0052CC',
        'To Do': '#0052CC',
        'Discovery': '#6554C0',
        'In Progress': '#FF8B00',
        'Execution': '#FF8B00',
        'Done': '#36B37E',
        'Closed': '#36B37E',
        'Resolved': '#36B37E',
        'Strategy': '#00B8D9'
    }
    return status_colors.get(status_name, '#5E6C84')

def extract_description(fields):
    """提取描述文本"""
    desc = fields.get('description', {})
    if not desc:
        return '-'
    
    def extract_text(content):
        texts = []
        if isinstance(content, list):
            for item in content:
                texts.extend(extract_text(item))
        elif isinstance(content, dict):
            if content.get('type') == 'text':
                texts.append(content.get('text', ''))
            elif 'content' in content:
                texts.extend(extract_text(content['content']))
        return texts
    
    try:
        texts = extract_text(desc.get('content', []))
        result = ' '.join(texts).strip()
        return result if result else '-'
    except:
        return '-'

def check_sla_alert(fields):
    """检查是否需要 SLA Alert"""
    status = fields.get('status', {})
    status_name = status.get('name', '')
    
    if status_name in ['Done', 'Closed', 'Resolved']:
        return False
    
    updated_str = fields.get('updated')
    if updated_str:
        try:
            updated = parse_date(updated_str)
            if updated:
                days_since = (datetime.now(timezone.utc) - updated).days
                return days_since > 14
        except:
            pass
    return False

def generate_html_report(data, ai_summary_results):
    """生成 HTML 报告"""
    log("📄 步骤 4: 生成 HTML 报告...")
    
    issues = data.get('issues', [])
    now = datetime.now(timezone.utc)
    
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
    
    # HTML 头部
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNTIN-730 Initiative Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #F4F5F7;
            padding: 20px;
            color: #172B4D;
        }}
        .container {{ max-width: 1800px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #0052CC 0%, #0747A6 100%);
            color: white;
            padding: 24px 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 13px; opacity: 0.9; }}
        .filter-section {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .filter-row {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; }}
        .filter-row:last-child {{ margin-bottom: 0; }}
        .filter-row input {{
            padding: 8px 12px;
            border: 1px solid #DFE1E6;
            border-radius: 4px;
            font-size: 14px;
            flex: 1;
            min-width: 200px;
        }}
        .filter-label {{ font-size: 13px; color: #5E6C84; font-weight: 500; min-width: 60px; }}
        .filter-group {{ display: flex; gap: 8px; flex-wrap: wrap; align-items: center; flex: 1; }}
        .filter-btn {{
            padding: 6px 14px;
            border: 1px solid #DFE1E6;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 500;
            cursor: pointer;
            background: white;
            color: #5E6C84;
            transition: all 0.2s;
        }}
        .filter-btn:hover {{ border-color: #0052CC; color: #0052CC; }}
        .filter-btn.active {{ background: #0052CC; color: white; border-color: #0052CC; }}
        .filter-btn.alert {{ border-color: #FF8B00; color: #FF8B00; }}
        .filter-btn.alert:hover, .filter-btn.alert.active {{ background: #FF8B00; color: white; }}
        .count-badge {{
            background: #EBECF0;
            color: #172B4D;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 11px;
            margin-left: 4px;
        }}
        .filter-btn.active .count-badge {{ background: rgba(255,255,255,0.3); color: white; }}
        .legend {{
            background: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            font-size: 13px;
        }}
        .legend-item {{ display: flex; align-items: center; gap: 10px; }}
        .legend-color {{
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }}
        .issues-table {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        thead {{ background: #F4F5F7; position: sticky; top: 0; z-index: 10; }}
        th {{
            padding: 14px 16px;
            text-align: left;
            font-weight: 600;
            color: #5E6C84;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.3px;
            border-bottom: 2px solid #DFE1E6;
            white-space: nowrap;
        }}
        td {{ padding: 14px 16px; border-bottom: 1px solid #EBECF0; vertical-align: top; }}
        tr {{ cursor: pointer; transition: background 0.2s; }}
        tr:hover td {{ background: #F4F5F7; }}
        tr.expanded td {{ background: #F0F7FF; }}
        tr.expanded:hover td {{ background: #E5F1FF; }}
        tr:last-child td {{ border-bottom: none; }}
        tr.has-sla-alert td {{ background: #FFFAF5; }}
        tr.has-sla-alert:hover td {{ background: #FFF0E0; }}
        tr.has-sla-alert.expanded td {{ background: #FFF5EB; }}
        .col-key-summary {{ min-width: 280px; max-width: 350px; }}
        .col-status {{ width: 90px; }}
        .col-assignee {{ width: 110px; }}
        .col-priority, .col-due {{ width: 80px; }}
        .col-date {{ width: 90px; }}
        .col-desc {{ min-width: 400px; max-width: 500px; }}
        .col-ai-summary {{ min-width: 350px; max-width: 450px; }}
        .alert-icon {{ color: #FF8B00; font-size: 12px; margin-left: 4px; cursor: help; }}
        .issue-key {{ font-size: 12px; color: #0052CC; font-weight: 600; display: block; margin-bottom: 4px; }}
        .issue-summary {{
            font-size: 13px;
            color: #172B4D;
            font-weight: 500;
            display: block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 320px;
            transition: all 0.2s;
        }}
        .issue-summary.expanded {{ white-space: normal; max-width: none; overflow: visible; }}
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            color: white;
            white-space: nowrap;
        }}
        .field-text {{ font-size: 13px; color: #172B4D; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
        .description-cell {{
            font-size: 12px;
            color: #5E6C84;
            line-height: 1.5;
            max-height: 80px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 4;
            -webkit-box-orient: vertical;
            word-break: break-word;
            transition: all 0.2s;
        }}
        .description-cell.expanded {{ max-height: none; -webkit-line-clamp: unset; overflow: visible; white-space: pre-wrap; }}
        .ai-summary-cell {{
            font-size: 12px;
            color: #172B4D;
            line-height: 1.6;
            max-height: 100px;
            overflow: hidden;
            display: -webkit-box;
            -webkit-line-clamp: 5;
            -webkit-box-orient: vertical;
            word-break: break-word;
            transition: all 0.2s;
            background: #F6F8FA;
            padding: 10px;
            border-radius: 6px;
            border-left: 3px solid #0052CC;
        }}
        .ai-summary-cell.expanded {{ max-height: none; -webkit-line-clamp: unset; overflow: visible; white-space: pre-wrap; }}
        .ai-summary-cell b {{ color: #0052CC; font-weight: 600; }}
        .ai-summary-missing {{ color: #5E6C84; font-style: italic; }}
        .ai-summary-error {{ color: #DE350B; font-style: italic; }}
        tr.hidden {{ display: none; }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #5E6C84;
            font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🏢 CNTIN-730 Initiative Report</h1>
        <div class="subtitle">
            📊 共 {len(issues)} 个 Initiative | 
            🏷️ {len(label_counts)} 个 Labels | 
            ⏰ 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
    
    <div class="filter-section">
        <div class="filter-row">
            <span class="filter-label">搜索:</span>
            <input type="text" id="searchInput" placeholder="搜索 Key, Summary, Description..." onkeyup="filterIssues()">
        </div>
        
        <div class="filter-row">
            <span class="filter-label">状态:</span>
            <div class="filter-group" id="statusFilters">
                <button class="filter-btn active" data-status="all" onclick="filterByStatus('all')">
                    全部<span class="count-badge">{len(issues)}</span>
                </button>
'''
    
    # 添加状态按钮
    for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
        html_content += f'''
                <button class="filter-btn" data-status="{status}" onclick="filterByStatus('{status}')">
                    {status}<span class="count-badge">{count}</span>
                </button>
'''
    
    # Alert 筛选按钮
    html_content += f'''
                <button class="filter-btn alert" data-alert="sla" onclick="filterByAlert('sla')">
                    Missing SLA<span class="count-badge">{sla_alert_count}</span>
                </button>
            </div>
        </div>
        
        <div class="filter-row">
            <span class="filter-label">Label:</span>
            <div class="filter-group" id="labelFilters">
                <button class="filter-btn active" data-label="all" onclick="filterByLabel('all')">
                    全部
                </button>
'''
    
    # 添加 Label 按钮
    for label, count in sorted_labels:
        html_content += f'''
                <button class="filter-btn" data-label="{label}" onclick="filterByLabel('{label}')">
                    {label}<span class="count-badge">{count}</span>
                </button>
'''
    
    html_content += '''            </div>
        </div>
    </div>
    
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color" style="background: #FFFAF5; border: 1px solid #FF8B00;"></div>
            <span>Missing SLA: 状态 ≠ Done 且更新时间超过2周</span>
        </div>
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
                    <th class="col-ai-summary">🤖 AI Summary (What / Why)</th>
                </tr>
            </thead>
            <tbody id="issuesContainer">
'''
    
    # 生成数据行
    for issue in issues:
        fields = issue.get('fields', {})
        key = issue.get('key', '')
        summary = fields.get('summary', '')
        status_name = fields.get('status', {}).get('name', 'Unknown')
        status_color = get_status_color(status_name)
        
        assignee = fields.get('assignee', {})
        assignee_name = assignee.get('displayName', '-') if assignee else '-'
        
        priority = fields.get('priority', {})
        priority_name = priority.get('name', '-') if priority else '-'
        
        created = format_date(fields.get('created'))
        updated = format_date(fields.get('updated'))
        duedate = fields.get('duedate') or '-'
        
        description = extract_description(fields)
        description_for_search = description[:500].lower() if description != '-' else ''
        description_html = html.escape(description)
        
        has_sla_alert = check_sla_alert(fields)
        alert_class = 'has-sla-alert' if has_sla_alert else ''
        alert_icon = '<span class="alert-icon" title="Missing SLA: 状态 ≠ Done 且更新时间超过2周">⚠️</span>' if has_sla_alert else ''
        
        labels = fields.get('labels', [])
        labels_attr = ','.join(labels)
        
        # 获取 AI Summary
        ai_summary_raw = ai_summary_results.get(key, "<span class='ai-summary-missing'>暂无 AI Summary</span>")
        ai_summary = ai_summary_raw.replace('\n', '<br>')
        
        html_content += f'''
                <tr class="{alert_class}"
                    data-status="{html.escape(status_name)}"
                    data-key="{html.escape(key.lower())}"
                    data-summary="{html.escape(summary.lower())}"
                    data-description="{html.escape(description_for_search)}"
                    data-labels="{html.escape(labels_attr)}"
                    data-has-sla="{'true' if has_sla_alert else 'false'}"
                    onclick="toggleRow(this)">
                    <td class="col-key-summary">
                        <span class="issue-key">{html.escape(key)}{alert_icon}</span>
                        <span class="issue-summary" title="{html.escape(summary)}">{html.escape(summary)}</span>
                    </td>
                    <td class="col-status">
                        <span class="status-badge" style="background: {status_color}">{html.escape(status_name)}</span>
                    </td>
                    <td class="col-assignee">
                        <span class="field-text">{html.escape(assignee_name)}</span>
                    </td>
                    <td class="col-priority">
                        <span class="field-text">{html.escape(priority_name)}</span>
                    </td>
                    <td class="col-date">
                        <span class="field-text">{html.escape(created)}</span>
                    </td>
                    <td class="col-date">
                        <span class="field-text">{html.escape(updated)}</span>
                    </td>
                    <td class="col-due">
                        <span class="field-text">{html.escape(duedate)}</span>
                    </td>
                    <td class="col-desc">
                        <div class="description-cell">{description_html}</div>
                    </td>
                    <td class="col-ai-summary">
                        <div class="ai-summary-cell">{ai_summary}</div>
                    </td>
                </tr>
'''
    
    # HTML 尾部 + JavaScript
    html_content += '''            </tbody>
        </table>
    </div>
    
    <div class="footer">
        <p>报告由 OpenClaw 自动生成 | 数据来源: Jira API</p>
    </div>
    
    <script>
        let currentStatusFilter = 'all';
        let currentAlertFilter = null;
        let currentLabelFilter = 'all';
        
        function filterIssues() {
            const searchText = document.getElementById('searchInput').value.toLowerCase().trim();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const key = row.getAttribute('data-key') || '';
                const summary = row.getAttribute('data-summary') || '';
                const description = row.getAttribute('data-description') || '';
                const status = row.getAttribute('data-status') || '';
                const labels = row.getAttribute('data-labels') || '';
                const hasSla = row.getAttribute('data-has-sla') === 'true';
                
                const matchesSearch = !searchText || 
                    key.includes(searchText) || 
                    summary.includes(searchText) || 
                    description.includes(searchText);
                
                const matchesStatus = currentStatusFilter === 'all' || status === currentStatusFilter;
                
                let matchesLabel = currentLabelFilter === 'all';
                if (!matchesLabel && labels) {
                    const labelList = labels.split(',');
                    matchesLabel = labelList.some(l => l === currentLabelFilter);
                }
                
                let matchesAlert = true;
                if (currentAlertFilter === 'sla') {
                    matchesAlert = hasSla;
                }
                
                if (matchesSearch && matchesStatus && matchesLabel && matchesAlert) {
                    row.classList.remove('hidden');
                } else {
                    row.classList.add('hidden');
                }
            });
        }
        
        function filterByStatus(status) {
            currentStatusFilter = status;
            document.querySelectorAll('.filter-btn[data-status]').forEach(btn => {
                btn.classList.remove('active');
                if (btn.getAttribute('data-status') === status) {
                    btn.classList.add('active');
                }
            });
            filterIssues();
        }
        
        function filterByAlert(alertType) {
            if (currentAlertFilter === alertType) {
                currentAlertFilter = null;
                document.querySelectorAll('.filter-btn[data-alert]').forEach(btn => {
                    btn.classList.remove('active');
                });
            } else {
                currentAlertFilter = alertType;
                document.querySelectorAll('.filter-btn[data-alert]').forEach(btn => {
                    btn.classList.remove('active');
                    if (btn.getAttribute('data-alert') === alertType) {
                        btn.classList.add('active');
                    }
                });
            }
            filterIssues();
        }
        
        function filterByLabel(label) {
            currentLabelFilter = label;
            document.querySelectorAll('.filter-btn[data-label]').forEach(btn => {
                btn.classList.remove('active');
                if (btn.getAttribute('data-label') === label) {
                    btn.classList.add('active');
                }
            });
            filterIssues();
        }
        
        function toggleRow(row) {
            const summary = row.querySelector('.issue-summary');
            const description = row.querySelector('.description-cell');
            const aiSummary = row.querySelector('.ai-summary-cell');
            
            const isExpanded = row.classList.toggle('expanded');
            
            if (summary) summary.classList.toggle('expanded', isExpanded);
            if (description) description.classList.toggle('expanded', isExpanded);
            if (aiSummary) aiSummary.classList.toggle('expanded', isExpanded);
        }
    </script>
</div>
</body>
</html>'''
    
    # 保存 HTML 文件
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = REPORTS_DIR / f"cntin_730_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    log(f"   ✅ HTML 报告已保存: {output_file}")
    return output_file

# ==================== 步骤 5: 发送邮件 ====================
def send_email(html_file):
    """发送邮件到指定邮箱"""
    log("📧 步骤 5: 发送邮件...")
    
    if not SENDER_PASSWORD:
        log("   ⚠️ 警告: 未设置 QQ_MAIL_PASSWORD 环境变量，跳过邮件发送")
        return False
    
    try:
        # 读取 HTML 内容
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = ', '.join(RECIPIENTS)
        msg['Cc'] = ', '.join(CC_RECIPIENTS)
        msg['Subject'] = f"[CNTIN-730 Initiative Report] {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 添加 HTML 内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 添加附件
        with open(html_file, 'rb') as f:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(f.read())
        
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="{html_file.name}"'
        )
        msg.attach(attachment)
        
        # 发送邮件
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            
            all_recipients = RECIPIENTS + CC_RECIPIENTS
            server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())
        
        log(f"   ✅ 邮件已发送至: {', '.join(RECIPIENTS)}")
        log(f"   📋 抄送: {', '.join(CC_RECIPIENTS)}")
        return True
        
    except Exception as e:
        log(f"   ❌ 邮件发送失败: {e}")
        return False

# ==================== 主函数 ====================
def main():
    """主函数"""
    log("=" * 60)
    log("🚀 CNTIN-730 Initiative 周报生成工具")
    log("=" * 60)
    
    start_time = time.time()
    
    # 步骤 1: 清空历史缓存
    clear_cache()
    
    # 步骤 2: 全量从 Jira 获取数据
    data = fetch_jira_data()
    
    # 准备数据用于 AI Summary
    issues_data = []
    for issue in data.get('issues', []):
        fields = issue.get('fields', {})
        description = extract_description(fields)
        issues_data.append({
            'key': issue.get('key', ''),
            'summary': fields.get('summary', ''),
            'description': description
        })
    
    # 步骤 3: 批量生成 AI Summary
    ai_summary_results = batch_generate_ai_summaries(issues_data, max_workers=5)
    
    # 步骤 4: 生成 HTML 报告
    html_file = generate_html_report(data, ai_summary_results)
    
    # 步骤 5: 发送邮件
    send_email(html_file)
    
    # 完成
    elapsed = time.time() - start_time
    log("=" * 60)
    log(f"✅ 全部完成! 耗时: {elapsed:.1f} 秒")
    log(f"📄 报告文件: {html_file}")
    log("=" * 60)

if __name__ == "__main__":
    main()
