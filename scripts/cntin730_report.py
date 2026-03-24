#!/usr/bin/env python3
"""
CNTIN-730 Initiative 周报生成脚本 - v5.2 完整功能版
包含: 统计卡片、Assignee筛选、冻结列、行展开、Excel导出
"""

import json
import sqlite3
import requests
import base64
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
from collections import Counter

# 路径配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
REPORTS_DIR = WORKSPACE / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Jira 配置
JIRA_URL = "https://lululemon.atlassian.net"
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "rcheng2@lululemon.com")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")

def fetch_jira_data():
    """从 Jira 获取数据 - 使用新分页机制"""
    print("📥 从 Jira 获取数据...")
    
    jql = 'project = CNTIN AND issuetype = Initiative AND parent = CNTIN-730 AND status != Cancelled'
    
    auth_str = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    auth_b64 = base64.b64encode(auth_str.encode()).decode()
    headers = {
        'Authorization': f'Basic {auth_b64}',
        'Content-Type': 'application/json'
    }
    
    all_issues = []
    next_page_token = None
    page_count = 0
    
    while True:
        url = f"{JIRA_URL}/rest/api/3/search/jql"
        params = {
            'jql': jql,
            'maxResults': 100,
            'fields': 'summary,status,assignee,priority,created,updated,duedate,description,labels'
        }
        if next_page_token:
            params['nextPageToken'] = next_page_token
        
        response = requests.get(url, headers=headers, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        issues = data.get('issues', [])
        all_issues.extend(issues)
        page_count += 1
        print(f"   第 {page_count} 页: {len(issues)} 条, 累计 {len(all_issues)} 条")
        
        if data.get('isLast', True):
            break
        next_page_token = data.get('nextPageToken')
        if not next_page_token:
            break
    
    print(f"✅ 总共获取 {len(all_issues)} 个 Initiative")
    return all_issues

def generate_ai_summary(description):
    """根据 description 生成 What/Why 摘要"""
    if not description or len(description.strip()) < 20:
        return "<i>Description 内容不足，无法生成摘要</i>"
    
    desc_lower = description.lower()
    sentences = [s.strip() for s in description.replace('?', '.').replace('!', '.').split('.') if len(s.strip()) > 10]
    
    # 提取 What (目标/做什么)
    what_keywords = ['aim to', 'aims to', 'goal is', 'objective is', 'purpose is', 'intends to', 'plan to', 'planned to', 
                     'build', 'create', 'develop', 'implement', 'enable', 'support', 'integrate', 'launch', 'deploy',
                     '目标', '旨在', '用于', '实现', '构建', '开发', '创建', '部署', '上线', '整合', '支持']
    what = None
    for sentence in sentences[:5]:  # 只看前5句
        for kw in what_keywords:
            if kw in sentence.lower():
                what = sentence
                break
        if what:
            break
    
    # 如果没找到，用第一句（如果是描述性的）
    if not what and sentences:
        first = sentences[0]
        if len(first) > 20 and not first.lower().startswith('http'):
            what = first
    
    # 提取 Why (原因/价值/背景)
    why_keywords = ['because', 'due to', 'in order to', 'so that', 'to enable', 'to support', 'to improve',
                    'benefit', 'value', 'impact', 'driver', 'reason', 'background', 'context',
                    '因为', '由于', '为了', '以便', '从而', '背景', '原因', '价值', '收益', '影响']
    why = None
    for sentence in sentences:
        for kw in why_keywords:
            if kw in sentence.lower():
                why = sentence
                break
        if why:
            break
    
    # 如果没找到 Why，尝试找包含业务价值或数字的句子
    if not why:
        for sentence in sentences:
            if any(x in sentence.lower() for x in ['revenue', 'cost', 'efficiency', 'time', 'user', 'customer', 'experience']):
                why = sentence
                break
    
    # 构建摘要 HTML
    parts = []
    if what:
        parts.append(f"<b>What:</b> {what}")
    if why:
        parts.append(f"<b>Why:</b> {why}")
    
    if parts:
        return "<br>".join(parts)
    else:
        # 如果无法提取，返回前200字符作为 fallback
        return f"<b>Summary:</b> {description[:200]}{'...' if len(description) > 200 else ''}"

def process_data(issues):
    """处理数据，计算统计信息"""
    processed = []
    status_counts = Counter()
    label_counts = Counter()
    assignee_counts = Counter()
    
    now = datetime.now()
    two_weeks_ago = now - timedelta(days=14)
    
    for issue in issues:
        fields = issue['fields']
        key = issue['key']
        summary = fields.get('summary', '')
        status = fields['status']['name']
        assignee = fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned'
        priority = fields.get('priority', {}).get('name', '')
        created = fields.get('created', '')[:10]
        updated = fields.get('updated', '')[:10]
        duedate = fields.get('duedate', '') or ''
        labels = fields.get('labels', [])
        
        # 处理 description
        desc = fields.get('description', '')
        desc_text = ''
        if isinstance(desc, dict):
            # 简单提取文本
            desc_text = extract_text_from_adf(desc)
        elif desc:
            desc_text = str(desc)
        
        # 检查 Missing SLA (状态 ≠ Done 且更新时间超过2周)
        updated_str = fields.get('updated', '')
        has_sla = False
        if updated_str:
            try:
                # 处理 Jira 日期格式: 2026-03-18T23:17:40.004-0700
                updated_str = updated_str.replace('Z', '+00:00')
                if len(updated_str) > 19:
                    # 移除毫秒和时区，只保留日期时间部分
                    updated_str = updated_str[:19]
                updated_dt = datetime.fromisoformat(updated_str)
                has_sla = status != 'Done' and updated_dt < two_weeks_ago
            except:
                has_sla = False
        
        # AI Summary - 根据 description 生成
        ai_summary = generate_ai_summary(desc_text)
        
        processed.append({
            'key': key,
            'summary': summary,
            'status': status,
            'assignee': assignee,
            'priority': priority,
            'created': created,
            'updated': updated,
            'duedate': duedate,
            'description': desc_text,
            'labels': labels,
            'has_sla': has_sla,
            'ai_summary': ai_summary
        })
        
        status_counts[status] += 1
        for label in labels:
            label_counts[label] += 1
        assignee_counts[assignee] += 1
    
    return processed, status_counts, label_counts, assignee_counts

def extract_text_from_adf(adf):
    """从 Atlassian Document Format 提取完整文本"""
    texts = []
    
    def extract_content(content):
        if isinstance(content, list):
            for item in content:
                extract_content(item)
        elif isinstance(content, dict):
            if 'text' in content:
                texts.append(content['text'])
            if 'content' in content:
                extract_content(content['content'])
    
    if adf and 'content' in adf:
        extract_content(adf['content'])
    
    return ' '.join(texts)

def generate_html(issues, status_counts, label_counts, assignee_counts):
    """生成完整功能版 HTML"""
    
    total = len(issues)
    done_count = status_counts.get('Done', 0)
    discovery_count = status_counts.get('Discovery', 0)
    sla_count = sum(1 for i in issues if i['has_sla'])
    
    # 生成 Assignee 筛选按钮 (取前20)
    top_assignees = assignee_counts.most_common(20)
    assignee_buttons = ''.join([
        f'''<button class="filter-btn" data-assignee="{name}" onclick="filterByAssignee('{name}')">
            {name}<span class="count-badge">{count}</span>
        </button>''' for name, count in top_assignees
    ])
    
    # 生成 Status 筛选按钮
    status_buttons = ''.join([
        f'''<button class="filter-btn" data-status="{status}" onclick="filterByStatus('{status}')">
            {status}<span class="count-badge">{count}</span>
        </button>''' for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True)
    ])
    
    # 生成 Label 筛选按钮 (取前10)
    top_labels = label_counts.most_common(10)
    label_buttons = ''.join([
        f'''<button class="filter-btn" data-label="{label}" onclick="filterByLabel('{label}')">
            {label}<span class="count-badge">{count}</span>
        </button>''' for label, count in top_labels
    ])
    
    # 生成表格行
    rows = []
    for issue in issues:
        sla_class = 'has-sla-alert' if issue['has_sla'] else ''
        sla_icon = '<span class="alert-icon" title="Missing SLA: 状态 ≠ Done 且更新时间超过2周">⚠️</span>' if issue['has_sla'] else ''
        labels_attr = ','.join(issue['labels'])
        
        # 状态颜色
        status_colors = {
            'Done': '#36B37E',
            'Discovery': '#6554C0',
            'Execution': '#FF8B00',
            'New': '#0052CC',
            'Strategy': '#00B8D9'
        }
        status_color = status_colors.get(issue['status'], '#5E6C84')
        
        # 处理 HTML 转义
        import html
        full_desc_escaped = html.escape(issue['description'])
        summary_escaped = html.escape(issue['summary'])
        
        rows.append(f'''
        <tr class="{sla_class}" 
            data-status="{issue['status']}" 
            data-key="{issue['key'].lower()}" 
            data-summary="{issue['summary'].lower()}"
            data-description="{html.escape(issue['description'][:300]).lower()}"
            data-labels="{labels_attr}"
            data-assignee="{issue['assignee']}"
            data-has-sla="{'true' if issue['has_sla'] else 'false'}"
            onclick="toggleRow(this)">
            <td class="col-key-summary">
                <span class="issue-key"><a href="https://lululemon.atlassian.net/browse/{issue['key']}" target="_blank" onclick="event.stopPropagation();">{issue['key']}</a>{sla_icon}</span>
                <span class="issue-summary" title="{summary_escaped}">{summary_escaped[:80]}{'...' if len(issue['summary']) > 80 else ''}</span>
            </td>
            <td class="col-status">
                <span class="status-badge" style="background: {status_color}">{issue['status']}</span>
            </td>
            <td class="col-assignee">
                <span class="field-text">{issue['assignee']}</span>
            </td>
            <td class="col-priority">
                <span class="field-text">{issue['priority']}</span>
            </td>
            <td class="col-date">
                <span class="field-text">{issue['created']}</span>
            </td>
            <td class="col-date">
                <span class="field-text">{issue['updated']}</span>
            </td>
            <td class="col-due">
                <span class="field-text">{issue['duedate'] or '-'}</span>
            </td>
            <td class="col-desc">
                <div class="description-cell">{full_desc_escaped}</div>
            </td>
            <td class="col-ai-summary">
                <div class="ai-summary-cell">{issue['ai_summary']}</div>
            </td>
        </tr>''')
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNTIN-730 FY26 Intakes - Initiative 报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: #F4F5F7;
            color: #172B4D;
            line-height: 1.6;
            padding: 20px;
        }}
        
        .header {{
            background: linear-gradient(135deg, #0052CC 0%, #0747A6 100%);
            color: white;
            padding: 25px 30px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .header .subtitle {{ font-size: 13px; opacity: 0.9; }}
        
        /* 统计卡片 */
        .stats-container {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }}
        
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-value {{
            font-size: 32px;
            font-weight: bold;
            color: #0052CC;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #5E6C84;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .stat-card.sla .stat-value {{ color: #FF8B00; }}
        .stat-card.done .stat-value {{ color: #36B37E; }}
        .stat-card.discovery .stat-value {{ color: #6554C0; }}
        
        /* 筛选区域 */
        .filter-section {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .filter-row {{
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
            margin-bottom: 10px;
        }}
        
        .filter-row:last-child {{ margin-bottom: 0; }}
        
        .filter-row input {{
            padding: 8px 12px;
            border: 1px solid #DFE1E6;
            border-radius: 4px;
            font-size: 14px;
            flex: 1;
            min-width: 200px;
        }}
        
        .filter-label {{
            font-size: 13px;
            color: #5E6C84;
            font-weight: 500;
            min-width: 60px;
        }}
        
        .filter-group {{
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
            align-items: center;
            flex: 1;
        }}
        
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
        
        /* Export 按钮 */
        .export-btn {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #36B37E;
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            border: none;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(54,179,126,0.4);
            transition: all 0.2s;
            z-index: 100;
        }}
        
        .export-btn:hover {{ background: #2EA36A; transform: translateY(-2px); }}
        
        /* 表格 */
        .issues-table {{
            background: white;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            overflow-x: auto;
        }}
        
        table {{
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            min-width: 1600px;
        }}
        
        th {{
            padding: 12px 16px;
            background: #FAFBFC;
            border-bottom: 1px solid #EBECF0;
            font-size: 11px;
            font-weight: 600;
            color: #5E6C84;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            text-align: left;
            white-space: nowrap;
            position: sticky;
            top: 0;
            z-index: 20;
        }}
        
        td {{
            padding: 14px 16px;
            border-bottom: 1px solid #EBECF0;
            vertical-align: top;
            background: white;
        }}
        
        /* 冻结列 */
        .col-key-summary {{
            min-width: 280px;
            max-width: 500px;
            position: sticky;
            left: 0;
            z-index: 10;
            background: white;
        }}
        
        .col-status {{
            width: 90px;
            position: sticky;
            left: 280px;
            z-index: 10;
            background: white;
            border-left: 1px solid #EBECF0;
        }}
        
        .col-assignee {{
            width: 110px;
            position: sticky;
            left: 370px;
            z-index: 10;
            background: white;
            border-left: 1px solid #EBECF0;
        }}
        
        /* 表头冻结列 */
        th.col-key-summary, th.col-status, th.col-assignee {{
            z-index: 30;
            background: #FAFBFC;
        }}
        
        tr {{ cursor: pointer; transition: background 0.2s; }}
        tr:hover td {{ background: #F4F5F7; }}
        tr:hover td.col-key-summary, tr:hover td.col-status, tr:hover td.col-assignee {{ background: #F4F5F7; }}
        
        tr.expanded td {{ background: #F0F7FF; }}
        tr.expanded td.col-key-summary, tr.expanded td.col-status, tr.expanded td.col-assignee {{ background: #F0F7FF; }}
        
        tr.has-sla-alert td {{ background: #FFFAF5; }}
        tr.has-sla-alert td.col-key-summary, tr.has-sla-alert td.col-status, tr.has-sla-alert td.col-assignee {{ background: #FFFAF5; }}
        tr.has-sla-alert:hover td, tr.has-sla-alert:hover td.col-key-summary, tr.has-sla-alert:hover td.col-status, tr.has-sla-alert:hover td.col-assignee {{ background: #FFF0E0; }}
        
        .issue-key {{
            font-size: 12px;
            font-weight: 600;
            display: block;
            margin-bottom: 4px;
        }}
        
        .issue-key a {{
            color: #0052CC;
            text-decoration: none;
        }}
        
        .issue-key a:hover {{
            text-decoration: underline;
            color: #0747A6;
        }}
        
        .issue-summary {{
            font-size: 13px;
            color: #172B4D;
            font-weight: 500;
            display: block;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 450px;
            transition: all 0.2s;
        }}
        
        .issue-summary.expanded {{
            white-space: normal;
            max-width: 500px;
            overflow: visible;
        }}
        
        .status-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: 600;
            color: white;
            white-space: nowrap;
        }}
        
        .field-text {{
            font-size: 13px;
            color: #172B4D;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        
        .col-priority, .col-due {{ width: 80px; }}
        .col-date {{ width: 90px; }}
        .col-desc {{ min-width: 400px; max-width: 600px; }}
        .col-ai-summary {{ min-width: 350px; max-width: 550px; }}
        
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
        
        .description-cell.expanded {{
            max-height: none;
            -webkit-line-clamp: unset;
            overflow: visible;
            white-space: pre-wrap;
        }}
        
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
        
        .ai-summary-cell.expanded {{
            max-height: none;
            -webkit-line-clamp: unset;
            overflow: visible;
            white-space: pre-wrap;
        }}
        
        .alert-icon {{
            color: #FF8B00;
            font-size: 12px;
            margin-left: 4px;
            cursor: help;
        }}
        
        .legend {{
            background: white;
            padding: 12px 20px;
            border-radius: 8px;
            margin-bottom: 15px;
            font-size: 12px;
            color: #5E6C84;
        }}
        
        .hidden {{ display: none !important; }}
        
        .footer {{
            text-align: center;
            padding: 20px;
            color: #5E6C84;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 CNTIN-730 FY26 Intakes</h1>
        <div class="subtitle">Parent = CNTIN-730 | Status ≠ Cancelled | Type = Initiative</div>
        <div class="subtitle">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stats-container">
        <div class="stat-card">
            <div class="stat-value">{total}</div>
            <div class="stat-label">Total Initiatives</div>
        </div>
        <div class="stat-card done">
            <div class="stat-value">{done_count}</div>
            <div class="stat-label">Done</div>
        </div>
        <div class="stat-card discovery">
            <div class="stat-value">{discovery_count}</div>
            <div class="stat-label">Discovery</div>
        </div>
        <div class="stat-card sla">
            <div class="stat-value">{sla_count}</div>
            <div class="stat-label">Missing SLA</div>
        </div>
    </div>
    
    <div class="filter-section">
        <div class="filter-row">
            <input type="text" id="searchInput" placeholder="🔍 搜索 Key、Summary、Description..." onkeyup="filterIssues()">
        </div>
        
        <div class="filter-row">
            <span class="filter-label">状态:</span>
            <div class="filter-group">
                <button class="filter-btn active" data-status="all" onclick="filterByStatus('all')">
                    全部<span class="count-badge">{total}</span>
                </button>
                {status_buttons}
                <button class="filter-btn alert" data-alert="sla" onclick="filterByAlert('sla')">
                    Missing SLA<span class="count-badge">{sla_count}</span>
                </button>
            </div>
        </div>
        
        <div class="filter-row">
            <span class="filter-label">负责人:</span>
            <div class="filter-group">
                <button class="filter-btn active" data-assignee="all" onclick="filterByAssignee('all')">
                    全部<span class="count-badge">{total}</span>
                </button>
                {assignee_buttons}
            </div>
        </div>
        
        <div class="filter-row">
            <span class="filter-label">Label:</span>
            <div class="filter-group">
                <button class="filter-btn active" data-label="all" onclick="filterByLabel('all')">全部</button>
                {label_buttons}
            </div>
        </div>
    </div>
    
    <div class="legend">
        ⚠️ Missing SLA: 状态 ≠ Done 且更新时间超过2周 | 单击行展开/收起详情
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
                {''.join(rows)}
            </tbody>
        </table>
    </div>
    
    <button class="export-btn" onclick="exportToExcel()">📊 Export to Excel</button>
    
    <div class="footer">
        <p>报告由 OpenClaw 自动生成 | 数据来源: Jira API | 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    
    <script>
        let currentStatusFilter = 'all';
        let currentAssigneeFilter = 'all';
        let currentLabelFilter = 'all';
        let currentAlertFilter = null;
        
        function filterIssues() {{
            const searchText = document.getElementById('searchInput').value.toLowerCase().trim();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {{
                const key = row.getAttribute('data-key') || '';
                const summary = row.getAttribute('data-summary') || '';
                const description = row.getAttribute('data-description') || '';
                const status = row.getAttribute('data-status') || '';
                const assignee = row.getAttribute('data-assignee') || '';
                const labels = row.getAttribute('data-labels') || '';
                const hasSla = row.getAttribute('data-has-sla') === 'true';
                
                const matchesSearch = !searchText || 
                    key.includes(searchText) || 
                    summary.includes(searchText) || 
                    description.includes(searchText);
                
                const matchesStatus = currentStatusFilter === 'all' || status === currentStatusFilter;
                const matchesAssignee = currentAssigneeFilter === 'all' || assignee === currentAssigneeFilter;
                
                let matchesLabel = currentLabelFilter === 'all';
                if (!matchesLabel && labels) {{
                    matchesLabel = labels.split(',').includes(currentLabelFilter);
                }}
                
                let matchesAlert = true;
                if (currentAlertFilter === 'sla') {{
                    matchesAlert = hasSla;
                }}
                
                if (matchesSearch && matchesStatus && matchesAssignee && matchesLabel && matchesAlert) {{
                    row.classList.remove('hidden');
                }} else {{
                    row.classList.add('hidden');
                }}
            }});
        }}
        
        function filterByStatus(status) {{
            currentStatusFilter = status;
            currentAlertFilter = null;
            document.querySelectorAll('.filter-btn[data-status], .filter-btn[data-alert]').forEach(btn => {{
                btn.classList.remove('active');
                if (btn.getAttribute('data-status') === status || 
                    (status === 'all' && btn.getAttribute('data-status') === 'all')) {{
                    btn.classList.add('active');
                }}
            }});
            filterIssues();
        }}
        
        function filterByAssignee(assignee) {{
            currentAssigneeFilter = assignee;
            document.querySelectorAll('.filter-btn[data-assignee]').forEach(btn => {{
                btn.classList.remove('active');
                if (btn.getAttribute('data-assignee') === assignee) {{
                    btn.classList.add('active');
                }}
            }});
            filterIssues();
        }}
        
        function filterByLabel(label) {{
            currentLabelFilter = label;
            document.querySelectorAll('.filter-btn[data-label]').forEach(btn => {{
                btn.classList.remove('active');
                if (btn.getAttribute('data-label') === label) {{
                    btn.classList.add('active');
                }}
            }});
            filterIssues();
        }}
        
        function filterByAlert(alertType) {{
            if (currentAlertFilter === alertType) {{
                currentAlertFilter = null;
                document.querySelectorAll('.filter-btn[data-alert]').forEach(btn => btn.classList.remove('active'));
                document.querySelector('.filter-btn[data-status="all"]').classList.add('active');
            }} else {{
                currentAlertFilter = alertType;
                currentStatusFilter = 'all';
                document.querySelectorAll('.filter-btn[data-status], .filter-btn[data-alert]').forEach(btn => {{
                    btn.classList.remove('active');
                    if (btn.getAttribute('data-alert') === alertType) {{
                        btn.classList.add('active');
                    }}
                }});
            }}
            filterIssues();
        }}
        
        function toggleRow(row) {{
            const summary = row.querySelector('.issue-summary');
            const description = row.querySelector('.description-cell');
            const aiSummary = row.querySelector('.ai-summary-cell');
            
            const isExpanded = row.classList.toggle('expanded');
            
            if (summary) summary.classList.toggle('expanded', isExpanded);
            if (description) description.classList.toggle('expanded', isExpanded);
            if (aiSummary) aiSummary.classList.toggle('expanded', isExpanded);
        }}
        
        function exportToExcel() {{
            const visibleRows = document.querySelectorAll('tbody tr:not(.hidden)');
            let csv = 'Key,Summary,Status,Assignee,Priority,Created,Updated,Due Date,Labels\\n';
            
            visibleRows.forEach(row => {{
                const key = row.querySelector('.issue-key')?.textContent?.replace('⚠️', '').trim() || '';
                const summary = row.querySelector('.issue-summary')?.textContent?.trim() || '';
                const status = row.getAttribute('data-status') || '';
                const assignee = row.getAttribute('data-assignee') || '';
                const priority = row.querySelector('.col-priority .field-text')?.textContent?.trim() || '';
                const created = row.querySelector('.col-date .field-text')?.textContent?.trim() || '';
                const updated = row.querySelectorAll('.col-date .field-text')[1]?.textContent?.trim() || '';
                const due = row.querySelector('.col-due .field-text')?.textContent?.trim() || '';
                const labels = row.getAttribute('data-labels') || '';
                
                csv += `"${{key}}","${{summary}}","${{status}}","${{assignee}}","${{priority}}","${{created}}","${{updated}}","${{due}}","${{labels}}"\\n`;
            }});
            
            const blob = new Blob([csv], {{ type: 'text/csv;charset=utf-8;' }});
            const link = document.createElement('a');
            link.href = URL.createObjectURL(blob);
            link.download = 'CNTIN-730_Initiatives_{datetime.now().strftime('%Y%m%d')}.csv';
            link.click();
        }}
    </script>
</body>
</html>'''
    
    return html

def main():
    print("="*60)
    print("🚀 CNTIN-730 Initiative 周报生成工具 v5.2")
    print("="*60)
    
    # 获取数据
    issues = fetch_jira_data()
    
    # 处理数据
    processed, status_counts, label_counts, assignee_counts = process_data(issues)
    
    print(f"\n📊 数据统计:")
    print(f"   总数: {len(processed)}")
    print(f"   Status: {dict(status_counts)}")
    print(f"   Missing SLA: {sum(1 for i in processed if i['has_sla'])}")
    
    # 生成 HTML
    html = generate_html(processed, status_counts, label_counts, assignee_counts)
    
    # 保存
    output_path = REPORTS_DIR / f"cntin_730_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\n✅ 报告已保存: {output_path}")
    
    # 同时保存为最新版本
    latest_path = REPORTS_DIR / "CNTIN-730_FY26_Intakes_Report_Latest.html"
    with open(latest_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ 最新版本: {latest_path}")

if __name__ == '__main__':
    main()
