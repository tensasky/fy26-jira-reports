#!/usr/bin/env python3
"""
FY26_PMO 报告生成脚本 - V5.7
添加折叠/展开功能
"""

import sqlite3
import json
import re
from datetime import datetime

DB_PATH = "/Users/admin/.openclaw/workspace/fy26_pmo/jira_report.db"
OUTPUT_DIR = "/Users/admin/.openclaw/workspace/fy26_pmo"
JIRA_BASE_URL = "https://lululemon.atlassian.net/browse"

# Status Trend 颜色映射
STATUS_TREND_COLORS = {
    'On track': '#2e7d32',
    'On Track': '#2e7d32',
    'At risk': '#ef6c00',
    'At Risk': '#ef6c00',
    'Off track': '#c62828',
    'Off Track': '#c62828',
    'Not started': '#212121',
    'Not Started': '#212121',
    'Complete': '#1565c0',
    'On hold': '#5d4037',
    'On Hold': '#5d4037',
    '': '#757575',
    None: '#757575',
}

STATUS_COLORS = {
    'New': '#1976d2',
    'Discovery': '#0277bd',
    'Strategy': '#7b1fa2',
    'Execution': '#f57c00',
    'Done': '#388e3c',
    'Closed': '#388e3c',
    'In Progress': '#f57c00',
}

def normalize_status_trend(status_trend):
    if not status_trend:
        return ''
    cleaned = re.sub(r'[🟢🔴🟠⚪🔵🟤\u200e\u200f\u202a-\u202e]', '', status_trend)
    return cleaned.strip()

def get_status_trend_color(status_trend):
    normalized = normalize_status_trend(status_trend)
    return STATUS_TREND_COLORS.get(normalized, 'transparent')

def get_status_color(status):
    return STATUS_COLORS.get(status, '#666')

def build_data():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT key, summary, status, assignee, status_trend FROM initiatives ORDER BY key")
    initiatives = {}
    for row in cursor.fetchall():
        initiatives[row['key']] = {
            'key': row['key'], 'summary': row['summary'], 'status': row['status'] or 'Unknown',
            'assignee': row['assignee'] or 'Unassigned', 'status_trend': row['status_trend'] or '',
            'features': {}
        }
    
    cursor.execute("SELECT key, summary, status, assignee, parent_key, status_trend FROM features")
    features_list = []
    for row in cursor.fetchall():
        feat = {
            'key': row['key'], 'summary': row['summary'], 'status': row['status'] or 'Unknown',
            'assignee': row['assignee'] or 'Unassigned', 'status_trend': row['status_trend'] or '',
            'parent_key': row['parent_key'], 'epics': []
        }
        features_list.append(feat)
        if row['parent_key'] in initiatives:
            initiatives[row['parent_key']]['features'][row['key']] = feat
    
    cursor.execute("SELECT key, summary, status, assignee, parent_key FROM epics WHERE has_parent = 1")
    linked_epics = []
    for row in cursor.fetchall():
        epic = {
            'key': row['key'], 'summary': row['summary'], 'status': row['status'] or 'Unknown',
            'assignee': row['assignee'] or 'Unassigned', 'parent_key': row['parent_key']
        }
        linked_epics.append(epic)
        for init in initiatives.values():
            if row['parent_key'] in init['features']:
                init['features'][row['parent_key']]['epics'].append(epic)
                break
    
    cursor.execute("""
        SELECT key, project, summary, status, assignee, parent_key 
        FROM epics 
        WHERE has_parent = 0 OR parent_key NOT IN (SELECT key FROM features)
        ORDER BY project, key
    """)
    orphan_epics = []
    for row in cursor.fetchall():
        orphan_epics.append({
            'key': row['key'], 'project': row['project'], 'summary': row['summary'],
            'status': row['status'] or 'Unknown', 'assignee': row['assignee'] or 'Unassigned',
            'parent_key': row['parent_key']
        })
    
    for init in initiatives.values():
        init['has_alert'] = not init['features']
        for feat in init['features'].values():
            feat['has_alert'] = not feat['epics']
            if feat['has_alert']:
                init['has_alert'] = True
    
    conn.close()
    return initiatives, features_list, linked_epics, orphan_epics

def generate_html(initiatives, features_list, linked_epics, orphan_epics):
    date_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    total_init = len(initiatives)
    total_feat = len(features_list)
    total_epic = len(linked_epics)
    alert_count = sum(1 for i in initiatives.values() if i['has_alert'])
    orphan_count = len(orphan_epics)
    
    all_statuses = set()
    for init in initiatives.values():
        all_statuses.add(init['status'])
        for feat in init['features'].values():
            all_statuses.add(feat['status'])
            for epic in feat['epics']:
                all_statuses.add(epic['status'])
    for epic in orphan_epics:
        all_statuses.add(epic['status'])
    all_statuses = sorted(all_statuses)
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26_PMO 报表 V5.7</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f0f2f5; color: #333; line-height: 1.6; padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #E31937 0%, #c41230 100%);
            color: white; padding: 30px; text-align: center; border-radius: 16px; margin-bottom: 24px;
            box-shadow: 0 4px 12px rgba(227, 25, 55, 0.3);
        }}
        .header h1 {{ font-size: 2.2em; margin-bottom: 8px; font-weight: 300; }}
        .header .date {{ opacity: 0.8; font-size: 0.95em; }}
        
        .stats {{
            display: flex; gap: 16px; justify-content: center; margin-bottom: 24px; flex-wrap: wrap;
        }}
        .stat-item {{
            background: white; padding: 20px 28px; border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); cursor: pointer; transition: all 0.3s;
            text-align: center; min-width: 110px; border: 2px solid transparent;
        }}
        .stat-item:hover {{
            transform: translateY(-3px); box-shadow: 0 6px 16px rgba(0,0,0,0.12);
            border-color: #E31937;
        }}
        .stat-item.active {{
            border-color: #E31937; background: #fff5f5;
        }}
        .stat-item .num {{ font-size: 1.8em; font-weight: bold; color: #E31937; }}
        .stat-item.alert .num {{ color: #ff9800; }}
        .stat-item.orphan .num {{ color: #666; }}
        .stat-item .label {{ font-size: 0.85em; color: #666; margin-top: 6px; }}
        
        .view-title {{
            background: white; padding: 16px 24px; border-radius: 10px;
            margin-bottom: 16px; font-size: 1.1em; font-weight: 600;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06); display: none;
        }}
        .view-title.active {{ display: block; }}
        
        /* 折叠控制栏 */
        .collapse-controls {{
            background: white; padding: 12px 20px; border-radius: 10px; margin-bottom: 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06); display: flex; gap: 12px; align-items: center;
        }}
        .collapse-btn {{
            padding: 8px 16px; background: #f5f5f5; color: #333; border: 1px solid #e0e0e0;
            border-radius: 6px; cursor: pointer; font-size: 0.85em; font-weight: 500;
            transition: all 0.2s;
        }}
        .collapse-btn:hover {{ background: #E31937; color: white; border-color: #E31937; }}
        
        .filters {{
            background: white; padding: 16px 20px; border-radius: 10px; margin-bottom: 16px;
            box-shadow: 0 2px 6px rgba(0,0,0,0.06); display: flex; gap: 12px; flex-wrap: wrap; align-items: center;
        }}
        .filters input {{
            padding: 10px 14px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 0.9em; min-width: 220px;
            transition: border-color 0.2s;
        }}
        .filters input:focus {{ border-color: #E31937; outline: none; }}
        .filters select {{
            padding: 10px 14px; border: 1px solid #e0e0e0; border-radius: 8px; font-size: 0.9em; min-width: 160px;
            background: white; cursor: pointer;
        }}
        .filters button {{
            padding: 10px 18px; background: #E31937; color: white; border: none; border-radius: 8px; cursor: pointer;
            font-weight: 500; transition: background 0.2s;
        }}
        .filters button:hover {{ background: #c41230; }}
        
        .content {{ background: transparent; border-radius: 0; box-shadow: none; overflow: visible; }}
        
        /* 折叠按钮 */
        .toggle-btn {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 28px; height: 28px; background: #f5f5f5; border: 1px solid #e0e0e0;
            border-radius: 6px; cursor: pointer; font-size: 0.8em; margin-right: 8px;
            transition: all 0.2s;
        }}
        .toggle-btn:hover {{ background: #E31937; color: white; border-color: #E31937; }}
        .toggle-btn.collapsed {{ transform: rotate(-90deg); }}
        
        /* 树状视图样式 */
        .tree-view {{ padding: 8px 0; }}
        
        /* Initiative 卡片 */
        .initiative-card {{
            background: white; border-radius: 12px; margin-bottom: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08); overflow: hidden;
            border-left: 4px solid #E31937;
        }}
        .initiative-header {{
            padding: 16px 20px; background: linear-gradient(135deg, #fff5f5 0%, #ffffff 100%);
            border-bottom: 1px solid #f0f0f0; cursor: pointer;
            display: flex; align-items: center; justify-content: space-between;
        }}
        .initiative-header:hover {{ background: linear-gradient(135deg, #ffebee 0%, #fff5f5 100%); }}
        .initiative-main {{ flex: 1; }}
        .initiative-title {{
            display: flex; align-items: center; gap: 12px; margin-bottom: 10px;
        }}
        .initiative-key {{
            font-family: monospace; font-size: 0.95em; font-weight: 600;
            color: #E31937; background: white; padding: 4px 10px;
            border-radius: 6px; border: 1px solid #ffebee;
        }}
        .initiative-key:hover {{ background: #ffebee; }}
        .initiative-summary {{
            font-size: 1.15em; font-weight: 600; color: #1a1a1a; flex: 1;
        }}
        .initiative-meta {{
            display: flex; align-items: center; gap: 12px; flex-wrap: wrap;
        }}
        .initiative-toggle {{ display: flex; align-items: center; }}
        .feature-count {{
            font-size: 0.8em; color: #999; margin-left: 8px;
        }}
        
        /* Feature 卡片 */
        .feature-list {{ 
            padding: 0 20px 16px 40px; background: #fafbfc;
            transition: all 0.3s ease;
        }}
        .feature-list.collapsed {{ display: none; }}
        .feature-card {{
            background: white; border-radius: 10px; margin-top: 12px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.06); overflow: hidden;
            border-left: 3px solid #ff6b7a;
        }}
        .feature-header {{
            padding: 14px 18px; background: linear-gradient(135deg, #fafafa 0%, #ffffff 100%);
            border-bottom: 1px solid #f5f5f5; cursor: pointer;
            display: flex; align-items: center; justify-content: space-between;
        }}
        .feature-header:hover {{ background: linear-gradient(135deg, #f5f5f5 0%, #fafafa 100%); }}
        .feature-main {{ flex: 1; }}
        .feature-title {{
            display: flex; align-items: center; gap: 10px; margin-bottom: 8px;
        }}
        .feature-key {{
            font-family: monospace; font-size: 0.9em; font-weight: 600;
            color: #E31937; background: white; padding: 3px 8px;
            border-radius: 5px; border: 1px solid #ffebee;
        }}
        .feature-key:hover {{ background: #ffebee; }}
        .feature-summary {{
            font-size: 1.05em; font-weight: 500; color: #333; flex: 1;
        }}
        .feature-meta {{
            display: flex; align-items: center; gap: 10px; flex-wrap: wrap;
        }}
        .feature-toggle {{ display: flex; align-items: center; }}
        .epic-count {{
            font-size: 0.75em; color: #999; margin-left: 6px;
        }}
        
        /* Epic 列表 */
        .epic-list {{ 
            padding: 0 16px 12px 32px; background: white;
            transition: all 0.3s ease;
        }}
        .epic-list.collapsed {{ display: none; }}
        .epic-item {{
            display: flex; align-items: center; gap: 10px;
            padding: 10px 14px; margin-top: 8px;
            background: #f8f9fa; border-radius: 8px;
            border: 1px solid #e8e8e8;
        }}
        .epic-key {{
            font-family: monospace; font-size: 0.85em; font-weight: 500;
            color: #666; background: white; padding: 2px 8px;
            border-radius: 4px; border: 1px solid #e0e0e0;
        }}
        .epic-key:hover {{ background: #f5f5f5; color: #E31937; border-color: #E31937; }}
        .epic-summary {{
            font-size: 0.95em; color: #555; flex: 1;
        }}
        
        /* 状态标签 */
        .status-dot {{
            display: inline-block; width: 10px; height: 10px;
            border-radius: 50%; margin-right: 6px;
        }}
        .status-badge {{
            display: inline-flex; align-items: center;
            padding: 4px 10px; border-radius: 20px;
            font-size: 0.8em; font-weight: 500;
            background: #f5f5f5; color: #666;
        }}
        
        /* Status Trend 标签 */
        .trend-tag {{
            display: inline-flex; align-items: center;
            padding: 4px 10px; border-radius: 6px;
            font-size: 0.8em; font-weight: 500;
        }}
        .trend-none {{
            background-color: #ffebee; color: #c62828;
            border: 1px solid #ffcdd2;
        }}
        
        /* 负责人 */
        .assignee {{
            display: inline-flex; align-items: center;
            font-size: 0.85em; color: #666;
            background: #f5f5f5; padding: 4px 10px;
            border-radius: 20px;
        }}
        .assignee::before {{
            content: "👤"; margin-right: 4px; font-size: 0.9em;
        }}
        
        /* 警告标记 */
        .alert-icon {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 24px; height: 24px; background: #ff9800;
            color: white; border-radius: 50%; font-size: 0.8em;
            margin-left: 8px;
        }}
        
        .view-section {{ display: none; }}
        .view-section.active {{ display: block; }}
        
        .hidden {{ display: none !important; }}
        .footer {{ text-align: center; padding: 24px; color: #999; font-size: 0.85em; margin-top: 24px; }}
        
        /* 数据表格 */
        .data-table {{
            width: 100%; border-collapse: collapse; font-size: 0.9em;
            background: white; border-radius: 10px; overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        }}
        .data-table th {{
            background: #E31937; color: white; padding: 14px; text-align: left; font-weight: 600;
            position: sticky; top: 0;
        }}
        .data-table td {{ padding: 12px 14px; border-bottom: 1px solid #f0f0f0; }}
        .data-table tr:hover {{ background: #fafafa; }}
        .data-table a {{
            color: #E31937; text-decoration: none; font-family: monospace; background: #f5f5f5;
            padding: 3px 8px; border-radius: 4px;
        }}
        .data-table a:hover {{ background: #ffebee; }}
        
        .summary-cell {{
            max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
        }}
        .summary-cell:hover {{ white-space: normal; overflow: visible; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>FY26_PMO 报表 V5.7</h1>
        <div class="date">生成时间: {date_str}</div>
    </div>
    
    <div class="stats">
        <div class="stat-item" onclick="showView('all')" data-view="all">
            <div class="num">{total_init}</div>
            <div class="label">全部视图</div>
        </div>
        <div class="stat-item" onclick="showView('initiatives')" data-view="initiatives">
            <div class="num">{total_init}</div>
            <div class="label">Initiatives</div>
        </div>
        <div class="stat-item" onclick="showView('features')" data-view="features">
            <div class="num">{total_feat}</div>
            <div class="label">Features</div>
        </div>
        <div class="stat-item" onclick="showView('epics')" data-view="epics">
            <div class="num">{total_epic}</div>
            <div class="label">Epics</div>
        </div>
        <div class="stat-item alert" onclick="showView('alerts')" data-view="alerts">
            <div class="num">{alert_count}</div>
            <div class="label">需要关注</div>
        </div>
        <div class="stat-item orphan" onclick="showView('orphans')" data-view="orphans">
            <div class="num">{orphan_count}</div>
            <div class="label">孤儿 Epics</div>
        </div>
    </div>
    
    <div class="view-title" id="viewTitle">全部数据</div>
    
    <!-- 折叠控制栏 -->
    <div class="collapse-controls" id="collapseControls" style="display: none;">
        <span style="font-weight: 600; color: #666;">折叠控制：</span>
        <button class="collapse-btn" onclick="toggleAllInitiatives(true)">📁 折叠所有 Initiative</button>
        <button class="collapse-btn" onclick="toggleAllInitiatives(false)">📂 展开所有 Initiative</button>
        <button class="collapse-btn" onclick="toggleAllFeatures(true)">📁 折叠所有 Feature</button>
        <button class="collapse-btn" onclick="toggleAllFeatures(false)">📂 展开所有 Feature</button>
    </div>
    
    <div class="filters">
        <input type="text" id="searchInput" placeholder="🔍 搜索 Key / Summary / Assignee...">
        <select id="statusFilter">
            <option value="">📋 所有状态</option>
'''
    
    for status in all_statuses:
        html += f'            <option value="{status}">{status}</option>\n'
    
    html += '''        </select>
        <button onclick="clearFilters()">清除筛选</button>
    </div>
'''
    
    # View: All (Tree) - 卡片式布局 + 折叠功能
    html += '''
    <div class="content view-section active" id="view-all">
        <div class="tree-view" id="treeAll">
'''
    for init_key, init in sorted(initiatives.items()):
        init_status_color = get_status_color(init['status'])
        init_trend_color = get_status_trend_color(init['status_trend'])
        init_trend_text = normalize_status_trend(init['status_trend']) or 'None Trend'
        init_alert = '<span class="alert-icon">⚠️</span>' if init['has_alert'] else ''
        feat_count = len(init['features'])
        feat_count_html = f'<span class="feature-count">({feat_count} Features)</span>' if feat_count > 0 else ''
        
        html += f'''
            <div class="initiative-card" data-search="{init_key} {init['summary']} {init['assignee']}" data-status="{init['status']}">
                <div class="initiative-header" onclick="toggleInitiative(this)">
                    <div class="initiative-main">
                        <div class="initiative-title">
                            <a class="initiative-key" href="{JIRA_BASE_URL}/{init_key}" target="_blank" onclick="event.stopPropagation()">{init_key}</a>
                            <span class="initiative-summary">{init['summary']}</span>
                            {init_alert}
                        </div>
                        <div class="initiative-meta">
                            <span class="status-badge">
                                <span class="status-dot" style="background:{init_status_color}"></span>
                                {init['status']}
                            </span>
                            <span class="trend-tag" style="background-color: {init_trend_color if init['status_trend'] else '#ffebee'}; color: {'black' if init['status_trend'] else '#c62828'}; border: {'none' if init['status_trend'] else '1px solid #ffcdd2'}">
                                {init_trend_text}
                            </span>
                            <span class="assignee">{init['assignee']}</span>
                            {feat_count_html}
                        </div>
                    </div>
                    <div class="initiative-toggle">
                        <button class="toggle-btn" data-action="toggle">▼</button>
                    </div>
                </div>
'''
        if init['features']:
            html += '<div class="feature-list">'
            for feat_key, feat in sorted(init['features'].items()):
                feat_status_color = get_status_color(feat['status'])
                feat_trend_color = get_status_trend_color(feat['status_trend'])
                feat_trend_text = normalize_status_trend(feat['status_trend']) or 'None Trend'
                feat_alert = '<span class="alert-icon">⚠️</span>' if feat['has_alert'] else ''
                epic_count = len(feat['epics'])
                epic_count_html = f'<span class="epic-count">({epic_count} Epics)</span>' if epic_count > 0 else ''
                
                html += f'''
                <div class="feature-card" data-search="{feat_key} {feat['summary']} {feat['assignee']}" data-status="{feat['status']}">
                    <div class="feature-header" onclick="toggleFeature(this)">
                        <div class="feature-main">
                            <div class="feature-title">
                                <a class="feature-key" href="{JIRA_BASE_URL}/{feat_key}" target="_blank" onclick="event.stopPropagation()">{feat_key}</a>
                                <span class="feature-summary">{feat['summary']}</span>
                                {feat_alert}
                            </div>
                            <div class="feature-meta">
                                <span class="status-badge">
                                    <span class="status-dot" style="background:{feat_status_color}"></span>
                                    {feat['status']}
                                </span>
                                <span class="trend-tag" style="background-color: {feat_trend_color if feat['status_trend'] else '#ffebee'}; color: {'black' if feat['status_trend'] else '#c62828'}; border: {'none' if feat['status_trend'] else '1px solid #ffcdd2'}">
                                    {feat_trend_text}
                                </span>
                                <span class="assignee">{feat['assignee']}</span>
                                {epic_count_html}
                            </div>
                        </div>
                        <div class="feature-toggle">
                            <button class="toggle-btn" data-action="toggle">▼</button>
                        </div>
                    </div>
'''
                if feat['epics']:
                    html += '<div class="epic-list">'
                    for epic in feat['epics']:
                        epic_status_color = get_status_color(epic['status'])
                        html += f'''
                        <div class="epic-item" data-search="{epic['key']} {epic['summary']} {epic['assignee']}" data-status="{epic['status']}">
                            <a class="epic-key" href="{JIRA_BASE_URL}/{epic['key']}" target="_blank">{epic['key']}</a>
                            <span class="epic-summary">{epic['summary']}</span>
                            <span class="status-badge">
                                <span class="status-dot" style="background:{epic_status_color}"></span>
                                {epic['status']}
                            </span>
                            <span class="assignee">{epic['assignee']}</span>
                        </div>
'''
                    html += '</div>'
                html += '</div>'
            html += '</div>'
        html += '</div>'
    html += '''
        </div>
    </div>
'''
    
    # 其他视图
    html += '''
    <div class="content view-section" id="view-initiatives">
        <table class="data-table">
            <thead><tr>
                <th>Key</th><th>Summary</th><th>Status</th><th>Assignee</th><th>Features</th>
            </tr></thead>
            <tbody>
'''
    for init_key, init in sorted(initiatives.items()):
        feat_count = len(init['features'])
        alert_mark = ' ⚠️' if init['has_alert'] else ''
        html += f'''
                <tr data-search="{init_key} {init['summary']} {init['assignee']}" data-status="{init['status']}">
                    <td><a href="{JIRA_BASE_URL}/{init_key}" target="_blank">{init_key}</a>{alert_mark}</td>
                    <td class="summary-cell">{init['summary']}</td>
                    <td>{init['status']}</td>
                    <td>{init['assignee']}</td>
                    <td>{feat_count}</td>
                </tr>
'''
    html += '</tbody></table></div>'
    
    html += '''
    <div class="content view-section" id="view-features">
        <table class="data-table">
            <thead><tr>
                <th>Key</th><th>Summary</th><th>Status</th><th>Assignee</th><th>Parent</th><th>Epics</th>
            </tr></thead>
            <tbody>
'''
    for feat in sorted(features_list, key=lambda x: x['key']):
        epic_count = len(feat['epics'])
        alert_mark = ' ⚠️' if feat.get('has_alert', False) else ''
        html += f'''
                <tr data-search="{feat['key']} {feat['summary']} {feat['assignee']}" data-status="{feat['status']}">
                    <td><a href="{JIRA_BASE_URL}/{feat['key']}" target="_blank">{feat['key']}</a>{alert_mark}</td>
                    <td class="summary-cell">{feat['summary']}</td>
                    <td>{feat['status']}</td>
                    <td>{feat['assignee']}</td>
                    <td><a href="{JIRA_BASE_URL}/{feat['parent_key']}" target="_blank">{feat['parent_key']}</a></td>
                    <td>{epic_count}</td>
                </tr>
'''
    html += '</tbody></table></div>'
    
    html += '''
    <div class="content view-section" id="view-epics">
        <table class="data-table">
            <thead><tr>
                <th>Key</th><th>Summary</th><th>Status</th><th>Assignee</th><th>Parent Feature</th>
            </tr></thead>
            <tbody>
'''
    for epic in sorted(linked_epics, key=lambda x: x['key']):
        html += f'''
                <tr data-search="{epic['key']} {epic['summary']} {epic['assignee']}" data-status="{epic['status']}">
                    <td><a href="{JIRA_BASE_URL}/{epic['key']}" target="_blank">{epic['key']}</a></td>
                    <td class="summary-cell">{epic['summary']}</td>
                    <td>{epic['status']}</td>
                    <td>{epic['assignee']}</td>
                    <td><a href="{JIRA_BASE_URL}/{epic['parent_key']}" target="_blank">{epic['parent_key']}</a></td>
                </tr>
'''
    html += '</tbody></table></div>'
    
    html += '''
    <div class="content view-section" id="view-alerts">
        <table class="data-table">
            <thead><tr>
                <th>Type</th><th>Key</th><th>Summary</th><th>Status</th><th>Alert</th>
            </tr></thead>
            <tbody>
'''
    for init_key, init in sorted(initiatives.items()):
        if init['has_alert']:
            html += f'''
                <tr data-status="{init['status']}">
                    <td>Initiative</td>
                    <td><a href="{JIRA_BASE_URL}/{init_key}" target="_blank">{init_key}</a></td>
                    <td>{init['summary']}</td>
                    <td>{init['status']}</td>
                    <td><span class="alert-icon">⚠️</span> 无 Features</td>
                </tr>
'''
        for feat_key, feat in sorted(init['features'].items()):
            if feat['has_alert']:
                html += f'''
                <tr data-status="{feat['status']}">
                    <td>Feature</td>
                    <td><a href="{JIRA_BASE_URL}/{feat_key}" target="_blank">{feat_key}</a></td>
                    <td>{feat['summary']}</td>
                    <td>{feat['status']}</td>
                    <td><span class="alert-icon">⚠️</span> 无 Epics</td>
                </tr>
'''
    html += '</tbody></table></div>'
    
    html += '''
    <div class="content view-section" id="view-orphans">
        <table class="data-table">
            <thead><tr>
                <th>Key</th><th>Project</th><th>Summary</th><th>Status</th><th>Assignee</th><th>Parent</th>
            </tr></thead>
            <tbody>
'''
    for epic in orphan_epics:
        parent_info = epic['parent_key'] if epic['parent_key'] else '(无)'
        html += f'''
                <tr data-search="{epic['key']} {epic['summary']} {epic['assignee']}" data-status="{epic['status']}">
                    <td><a href="{JIRA_BASE_URL}/{epic['key']}" target="_blank">{epic['key']}</a></td>
                    <td>{epic['project']}</td>
                    <td class="summary-cell">{epic['summary']}</td>
                    <td>{epic['status']}</td>
                    <td>{epic['assignee']}</td>
                    <td>{parent_info}</td>
                </tr>
'''
    html += '</tbody></table></div>'
    
    # JavaScript - 添加折叠功能
    html += '''
    <div class="footer">报告由 OpenClaw 自动生成 | 数据来源: lululemon Jira</div>
    
    <script>
        const titles = {
            'all': '全部数据（树状视图）',
            'initiatives': 'Initiatives 列表',
            'features': 'Features 列表',
            'epics': 'Epics 列表',
            'alerts': '需要关注的项（无子项）',
            'orphans': '孤儿 Epics（无 CNTIN Feature parent）'
        };
        
        function showView(viewName) {
            document.querySelectorAll('.stat-item').forEach(item => {
                item.classList.toggle('active', item.dataset.view === viewName);
            });
            
            const titleEl = document.getElementById('viewTitle');
            titleEl.textContent = titles[viewName];
            titleEl.classList.add('active');
            
            document.querySelectorAll('.view-section').forEach(section => {
                section.classList.remove('active');
            });
            document.getElementById('view-' + viewName).classList.add('active');
            
            // 显示/隐藏折叠控制栏
            const collapseControls = document.getElementById('collapseControls');
            collapseControls.style.display = viewName === 'all' ? 'flex' : 'none';
            
            applyFilters();
        }
        
        // 折叠/展开 Initiative
        function toggleInitiative(header) {
            const card = header.closest('.initiative-card');
            const featureList = card.querySelector('.feature-list');
            const toggleBtn = header.querySelector('.toggle-btn');
            
            if (featureList) {
                featureList.classList.toggle('collapsed');
                toggleBtn.classList.toggle('collapsed');
                toggleBtn.textContent = featureList.classList.contains('collapsed') ? '▶' : '▼';
            }
        }
        
        // 折叠/展开 Feature
        function toggleFeature(header) {
            const card = header.closest('.feature-card');
            const epicList = card.querySelector('.epic-list');
            const toggleBtn = header.querySelector('.toggle-btn');
            
            if (epicList) {
                epicList.classList.toggle('collapsed');
                toggleBtn.classList.toggle('collapsed');
                toggleBtn.textContent = epicList.classList.contains('collapsed') ? '▶' : '▼';
            }
        }
        
        // 一键折叠/展开所有 Initiative
        function toggleAllInitiatives(collapse) {
            document.querySelectorAll('.initiative-card').forEach(card => {
                const featureList = card.querySelector('.feature-list');
                const toggleBtn = card.querySelector('.initiative-toggle .toggle-btn');
                
                if (featureList) {
                    if (collapse) {
                        featureList.classList.add('collapsed');
                        toggleBtn.classList.add('collapsed');
                        toggleBtn.textContent = '▶';
                    } else {
                        featureList.classList.remove('collapsed');
                        toggleBtn.classList.remove('collapsed');
                        toggleBtn.textContent = '▼';
                    }
                }
            });
        }
        
        // 一键折叠/展开所有 Feature
        function toggleAllFeatures(collapse) {
            document.querySelectorAll('.feature-card').forEach(card => {
                const epicList = card.querySelector('.epic-list');
                const toggleBtn = card.querySelector('.feature-toggle .toggle-btn');
                
                if (epicList) {
                    if (collapse) {
                        epicList.classList.add('collapsed');
                        toggleBtn.classList.add('collapsed');
                        toggleBtn.textContent = '▶';
                    } else {
                        epicList.classList.remove('collapsed');
                        toggleBtn.classList.remove('collapsed');
                        toggleBtn.textContent = '▼';
                    }
                }
            });
        }
        
        function applyFilters() {
            const searchTerm = document.getElementById('searchInput').value.toLowerCase();
            const statusFilter = document.getElementById('statusFilter').value;
            const activeView = document.querySelector('.view-section.active');
            
            if (!activeView) return;
            
            const items = activeView.querySelectorAll('[data-search]');
            items.forEach(item => {
                const searchText = item.dataset.search.toLowerCase();
                const status = item.dataset.status;
                
                const matchesSearch = !searchTerm || searchText.includes(searchTerm);
                const matchesStatus = !statusFilter || status === statusFilter;
                
                item.classList.toggle('hidden', !(matchesSearch && matchesStatus));
            });
        }
        
        document.getElementById('searchInput').addEventListener('input', applyFilters);
        document.getElementById('statusFilter').addEventListener('change', applyFilters);
        
        function clearFilters() {
            document.getElementById('searchInput').value = '';
            document.getElementById('statusFilter').value = '';
            applyFilters();
        }
        
        showView('all');
    </script>
</body>
</html>
'''
    
    return html

def main():
    print("📊 生成 FY26_PMO 报告 V5.7 (添加折叠/展开功能)...")
    initiatives, features_list, linked_epics, orphan_epics = build_data()
    
    html = generate_html(initiatives, features_list, linked_epics, orphan_epics)
    html_path = f"{OUTPUT_DIR}/fy26_pmo_report_v5_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    latest_path = f"{OUTPUT_DIR}/fy26_pmo_report_v5_latest.html"
    with open(latest_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML报告: {html_path}")
    print(f"✅ Latest版本: {latest_path}")

if __name__ == "__main__":
    main()
