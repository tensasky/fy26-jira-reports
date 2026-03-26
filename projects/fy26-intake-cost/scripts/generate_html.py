#!/usr/bin/env python3
"""
FY26_Intake_Cost HTML 报告生成 - V4 (完整交互版)
- 实时汇率更新
- SLA 智能计算（Done 用状态变更日期）
- 可折叠行
- 中英文切换
- 搜索和筛选
- Pillar 列（来自 labels）
- 交互式图表
"""

import sqlite3
import json
import math
import re
from datetime import datetime, timedelta
import os

DB_PATH = "/Users/admin/.openclaw/workspace/projects/fy26-intake-cost/intake_cost.db"
OUTPUT_DIR = "/Users/admin/.openclaw/workspace/projects/fy26-intake-cost/reports"

DEFAULT_EXCHANGE_RATE = 0.135

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_jira_date(date_str):
    """解析 Jira 日期格式"""
    if not date_str:
        return None
    try:
        # 处理 2026-03-24T21:00:14.127-0700 格式
        if date_str.endswith(('-0700', '-0800', '-0600', '-0500', '+0000')):
            date_str = date_str[:-2] + ':' + date_str[-2:]
        
        if '.' in date_str:
            if '+' in date_str or date_str.count('-') > 2:
                dt = datetime.fromisoformat(date_str)
            else:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt
    except:
        return None

def calculate_sla_days(created_str, status, history=None):
    """计算 SLA 天数
    - 如果 status 是 Done/Closed/Resolved，用状态变更时间 - 创建时间
    - 否则用当前时间 - 创建时间
    """
    created_dt = parse_jira_date(created_str)
    if not created_dt:
        return 0, None
    
    # 如果是完成状态，尝试从历史记录中找到完成时间
    if status in ['Done', 'Closed', 'Resolved'] and history:
        # 从后往前找状态变更记录
        for item in reversed(history):
            if item.get('field') == 'status':
                to_status = item.get('toString', '')
                if to_status in ['Done', 'Closed', 'Resolved']:
                    change_date = item.get('created', '')
                    change_dt = parse_jira_date(change_date)
                    if change_dt:
                        days = (change_dt - created_dt).days
                        return days, change_date[:10]
    
    # 否则用当前时间
    now = datetime.now(created_dt.tzinfo)
    days = (now - created_dt).days
    return days, None

def get_sla_class(days):
    if days > 14:
        return "sla-danger"
    elif days > 7:
        return "sla-warning"
    return ""

def format_cost(child_count, exchange_rate):
    """格式化成本"""
    if not child_count or child_count == 0:
        return (0, 0, "¥0", "$0")
    
    try:
        cost_rmb = float(child_count)
        cost_usd = cost_rmb * exchange_rate
        return (
            cost_rmb,
            cost_usd,
            f"¥{cost_rmb:,.0f}",
            f"${cost_usd:,.2f}"
        )
    except:
        return (0, 0, "¥0", "$0")

def generate_html():
    print("📊 生成 FY26_Intake_Cost 报告 V4 (完整交互版)...")
    
    conn = init_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM intakes ORDER BY created DESC')
    rows = cursor.fetchall()
    conn.close()
    
    # 收集所有唯一的 pillar (labels)
    all_pillars = set()
    processed_rows = []
    
    for row in rows:
        # 解析 labels 作为 pillars
        labels = json.loads(row['labels'] or '[]')
        pillars = [l for l in labels if l and not l.startswith('FY26')]
        all_pillars.update(pillars)
        
        status = row['status'] or 'Unknown'
        status_cat = row['status_category'] or 'Unknown'
        
        # 计算 SLA
        history = json.loads(row['issue_links'] or '[]')  # 临时用 issue_links 存历史
        sla_days, done_date = calculate_sla_days(row['created'], status, history)
        
        # Type = Components
        intake_type = row['components'] or 'TBD'
        if intake_type.strip() == '' or intake_type == '-':
            intake_type = 'TBD'
        
        # Cost raw values for JS calculation
        child_count = row['initiative_child_count'] or 0
        cost_rmb_raw, cost_usd_raw, rmb_str, usd_str = format_cost(child_count, DEFAULT_EXCHANGE_RATE)
        
        # Approver = AffectsVersions
        approver = row['affects_versions'] or '-'
        
        # Scope = Description
        scope = row['description'] or '-'
        scope_short = scope[:80] + '...' if len(scope) > 80 else scope
        scope = scope.replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
        
        # Follow up = LinkedIssues
        linked_issues = json.loads(row['linked_issues'] or '[]')
        
        processed_rows.append({
            'key': row['key'],
            'summary': row['summary'] or '',
            'created': row['created'][:10] if row['created'] else '',
            'pillars': pillars,
            'pillar_str': ','.join(pillars) if pillars else '-',
            'intake_type': intake_type,
            'sla_days': sla_days,
            'sla_class': get_sla_class(sla_days),
            'done_date': done_date or '',
            'status': status,
            'status_cat': status_cat,
            'assignee': row['assignee'] or '-',
            'cost_rmb_raw': cost_rmb_raw,
            'cost_usd_raw': cost_usd_raw,
            'rmb_str': rmb_str,
            'usd_str': usd_str,
            'approver': approver,
            'scope': scope,
            'scope_short': scope_short,
            'linked_issues': linked_issues
        })
    
    # 统计数据
    stats = {
        'total': len(processed_rows),
        'not_started': sum(1 for r in processed_rows if r['status_cat'] == 'To Do' or r['status'] in ['To Do', 'Open', 'New']),
        'in_progress': sum(1 for r in processed_rows if r['status_cat'] == 'In Progress' or r['status'] in ['In Progress']),
        'closed': sum(1 for r in processed_rows if r['status_cat'] == 'Done' or r['status'] in ['Done', 'Closed', 'Resolved']),
        'cancelled': sum(1 for r in processed_rows if 'Cancel' in r['status'])
    }
    
    # Pillar 分布统计
    pillar_dist = {}
    for row in processed_rows:
        for p in row['pillars']:
            pillar_dist[p] = pillar_dist.get(p, 0) + 1
    
    # 生成数据 JSON 供 JS 使用
    rows_json = json.dumps(processed_rows, ensure_ascii=False)
    pillars_list = sorted(list(all_pillars))
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FY26 Intake Cost Report</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif; background: #f5f7fa; color: #333; padding: 20px; }}
.container {{ max-width: 1700px; margin: 0 auto; }}

/* Header */
.header {{ background: #fff; padding: 24px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; justify-content: space-between; align-items: center; }}
.header h1 {{ font-size: 24px; color: #1a1a1a; margin: 0; }}
.header .subtitle {{ color: #666; font-size: 14px; margin-top: 4px; }}
.header-left {{ flex: 1; }}
.header-right {{ display: flex; gap: 12px; align-items: center; }}

/* Language Toggle */
.lang-toggle {{ display: flex; gap: 8px; background: #f0f0f0; padding: 4px; border-radius: 4px; }}
.lang-btn {{ padding: 6px 12px; border: none; background: transparent; cursor: pointer; border-radius: 4px; font-size: 13px; }}
.lang-btn.active {{ background: #fff; color: #1890ff; font-weight: 500; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}

/* Rate Setting */
.rate-setting {{ background: #f0f7ff; border: 1px solid #91d5ff; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px; display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }}
.rate-setting label {{ font-weight: 500; color: #333; }}
.rate-setting input {{ width: 100px; padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 14px; }}
.rate-setting .rate-info {{ color: #666; font-size: 13px; }}

/* Search & Filter */
.filter-bar {{ background: #fff; padding: 16px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: flex; gap: 16px; flex-wrap: wrap; align-items: center; }}
.filter-group {{ display: flex; align-items: center; gap: 8px; }}
.filter-group label {{ font-size: 13px; color: #666; font-weight: 500; }}
.filter-group input, .filter-group select {{ padding: 8px 12px; border: 1px solid #d9d9d9; border-radius: 4px; font-size: 13px; min-width: 150px; }}
.filter-group input:focus, .filter-group select:focus {{ outline: none; border-color: #1890ff; }}
.pillar-filter {{ display: flex; gap: 8px; flex-wrap: wrap; }}
.pillar-tag {{ padding: 4px 12px; background: #f0f0f0; border-radius: 4px; font-size: 12px; cursor: pointer; user-select: none; border: 2px solid transparent; }}
.pillar-tag:hover {{ background: #e0e0e0; }}
.pillar-tag.active {{ background: #1890ff; color: #fff; border-color: #1890ff; }}
.clear-filters {{ padding: 8px 16px; background: #ff4d4f; color: #fff; border: none; border-radius: 4px; cursor: pointer; font-size: 13px; }}
.clear-filters:hover {{ background: #ff7875; }}

/* Stats Cards - Clickable */
.stats-cards {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; margin-bottom: 20px; }}
.stat-card {{ background: #fff; padding: 20px; border-radius: 8px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); cursor: pointer; transition: all 0.2s; border: 2px solid transparent; }}
.stat-card:hover {{ transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }}
.stat-card.active {{ border-color: #1890ff; background: #f0f7ff; }}
.stat-card.total.active {{ border-color: #1890ff; }}
.stat-card.total {{ background: #e6f7ff; border: 1px solid #91d5ff; }}
.stat-label {{ font-size: 14px; color: #666; margin-bottom: 8px; }}
.stat-value {{ font-size: 32px; font-weight: 600; color: #1a1a1a; }}
.stat-value.blue {{ color: #1890ff; }}
.stat-value.orange {{ color: #fa8c16; }}
.stat-value.green {{ color: #52c41a; }}
.stat-value.red {{ color: #ff4d4f; }}

/* Charts */
.charts-section {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 20px; }}
.chart-card {{ background: #fff; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
.chart-title {{ font-size: 16px; color: #1a1a1a; margin-bottom: 16px; }}
.donut-chart {{ width: 200px; height: 200px; margin: 0 auto; position: relative; cursor: pointer; }}
.donut-chart svg {{ transform: rotate(-90deg); }}
.donut-chart path {{ transition: opacity 0.2s; }}
.donut-chart path:hover {{ opacity: 0.8; }}
.donut-center {{ position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); text-align: center; }}
.donut-center .number {{ font-size: 32px; font-weight: 600; }}
.donut-center .label {{ font-size: 12px; color: #666; }}
.chart-legend {{ display: flex; justify-content: center; gap: 16px; margin-top: 16px; flex-wrap: wrap; }}
.legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 12px; cursor: pointer; padding: 4px 8px; border-radius: 4px; transition: background 0.2s; }}
.legend-item:hover {{ background: #f0f0f0; }}
.legend-item.disabled {{ opacity: 0.4; }}
.legend-dot {{ width: 8px; height: 8px; border-radius: 50%; }}
.bar-chart {{ display: flex; flex-direction: column; gap: 10px; }}
.bar-item {{ display: flex; align-items: center; gap: 12px; cursor: pointer; padding: 4px; border-radius: 4px; transition: background 0.2s; }}
.bar-item:hover {{ background: #f5f7fa; }}
.bar-item.disabled {{ opacity: 0.4; }}
.bar-label {{ width: 120px; font-size: 12px; color: #666; text-align: right; }}
.bar-track {{ flex: 1; height: 24px; background: #f0f0f0; border-radius: 4px; overflow: hidden; position: relative; }}
.bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
.bar-value {{ position: absolute; right: 8px; top: 50%; transform: translateY(-50%); font-size: 12px; color: #333; font-weight: 500; }}

/* Table */
.table-section {{ background: #fff; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; width: 100%; }}
.table-header {{ display: grid; grid-template-columns: 40px minmax(140px,1.3fr) minmax(70px,0.7fr) minmax(50px,0.5fr) minmax(80px,0.7fr) minmax(80px,0.7fr) minmax(90px,0.8fr) minmax(80px,0.7fr) minmax(120px,1fr) minmax(100px,0.9fr); background: #fafafa; padding: 12px 16px; font-weight: 600; font-size: 13px; color: #333; border-bottom: 2px solid #e8e8e8; gap: 10px; align-items: center; }}
.table-row {{ display: grid; grid-template-columns: 40px minmax(140px,1.3fr) minmax(70px,0.7fr) minmax(50px,0.5fr) minmax(80px,0.7fr) minmax(80px,0.7fr) minmax(90px,0.8fr) minmax(80px,0.7fr) minmax(120px,1fr) minmax(100px,0.9fr); padding: 12px 16px; border-bottom: 1px solid #f0f0f0; align-items: start; font-size: 13px; gap: 10px; cursor: pointer; transition: background 0.2s; }}
.table-row:hover {{ background: #f5f7fa; }}
.table-row.expanded {{ background: #f0f7ff; }}

.col-expand {{ text-align: center; color: #999; font-size: 12px; }}
.col-expand::before {{ content: '▶'; display: inline-block; transition: transform 0.2s; }}
.table-row.expanded .col-expand::before {{ transform: rotate(90deg); }}

.col-intake {{ display: flex; flex-direction: column; gap: 3px; }}
.ticket-key {{ font-weight: 600; color: #1890ff; text-decoration: none; font-size: 13px; }}
.ticket-key:hover {{ text-decoration: underline; }}
.ticket-summary {{ font-size: 11px; color: #666; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.ticket-date {{ font-size: 11px; color: #999; }}

.col-pillar {{ font-size: 12px; color: #666; }}
.col-type {{ color: #333; font-weight: 500; font-size: 12px; }}
.col-type.tbd {{ color: #999; font-style: italic; }}

.col-sla {{ font-weight: 600; text-align: center; font-size: 12px; }}
.sla-warning {{ color: #fa8c16; background: #fff7e6; padding: 4px 8px; border-radius: 4px; }}
.sla-danger {{ color: #ff4d4f; background: #fff1f0; padding: 4px 8px; border-radius: 4px; }}
.sla-done {{ color: #52c41a; background: #f6ffed; padding: 4px 8px; border-radius: 4px; }}

.col-status {{ display: flex; justify-content: center; }}
.status-badge {{ display: inline-block; padding: 4px 10px; border-radius: 4px; font-size: 11px; font-weight: 500; }}
.status-todo {{ background: #e6f7ff; color: #1890ff; }}
.status-progress {{ background: #fff7e6; color: #fa8c16; }}
.status-done {{ background: #f6ffed; color: #52c41a; }}
.status-cancel {{ background: #f5f5f5; color: #999; }}

.col-assignee {{ color: #666; font-size: 12px; text-align: center; }}
.col-cost {{ font-family: 'SF Mono', Monaco, monospace; font-size: 11px; line-height: 1.5; color: #333; text-align: center; }}
.col-approver {{ color: #666; font-size: 12px; text-align: center; }}
.col-scope {{ color: #666; font-size: 12px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: pointer; }}
.col-scope:hover {{ color: #1890ff; }}
.col-followup {{ font-size: 11px; }}
.followup-link {{ display: block; color: #1890ff; text-decoration: none; margin-bottom: 2px; }}
.followup-link:hover {{ text-decoration: underline; }}

/* Expanded Row Content */
.row-details {{ grid-column: 1 / -1; padding: 16px; background: #fafafa; border-top: 1px dashed #e8e8e8; display: none; }}
.row-details.show {{ display: block; }}
.detail-section {{ margin-bottom: 12px; }}
.detail-label {{ font-weight: 600; color: #333; font-size: 12px; margin-bottom: 4px; }}
.detail-content {{ color: #666; font-size: 12px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }}

/* No Results */
.no-results {{ text-align: center; padding: 60px; color: #999; }}
.no-results-icon {{ font-size: 48px; margin-bottom: 16px; }}

/* Hidden */
.hidden {{ display: none !important; }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div class="header-left">
      <h1 data-i18n="title">FY26 Intake Cost Report</h1>
      <div class="subtitle" data-i18n="subtitle">Project Progress, Cost & SLA Monitoring</div>
    </div>
    <div class="header-right">
      <div class="lang-toggle">
        <button class="lang-btn active" onclick="setLang('zh')">中文</button>
        <button class="lang-btn" onclick="setLang('en')">EN</button>
      </div>
      <button class="btn btn-primary" onclick="window.print()" data-i18n="print">🖨️ Print</button>
    </div>
  </div>

  <div class="rate-setting">
    <label data-i18n="exchangeRate">💱 Exchange Rate (RMB → USD):</label>
    <input type="number" id="exchangeRate" value="{DEFAULT_EXCHANGE_RATE}" step="0.001" min="0" max="1" onchange="updateExchangeRate()">
    <span class="rate-info" data-i18n="rateInfo">Formula: Cost = InitiativeChildCount × Exchange Rate</span>
  </div>

  <div class="filter-bar">
    <div class="filter-group">
      <label data-i18n="searchTicket">🔍 Ticket:</label>
      <input type="text" id="searchTicket" placeholder="CNTIN-XXX" oninput="applyFilters()">
    </div>
    <div class="filter-group">
      <label data-i18n="searchStatus">Status:</label>
      <select id="filterStatus" onchange="applyFilters()">
        <option value="" data-i18n="allStatuses">All Statuses</option>
        <option value="To Do,Open,New" data-i18n="notStarted">Not Started</option>
        <option value="In Progress" data-i18n="inProgress">In Progress</option>
        <option value="Done,Closed,Resolved" data-i18n="closed">Closed</option>
      </select>
    </div>
    <div class="filter-group">
      <label data-i18n="filterPillar">Pillar:</label>
      <div class="pillar-filter" id="pillarFilter"></div>
    </div>
    <button class="clear-filters" onclick="clearFilters()" data-i18n="clearFilters">Clear Filters</button>
  </div>

  <div class="stats-cards">
    <div class="stat-card total" onclick="filterByStatus('all')">
      <div class="stat-label" data-i18n="total">Total</div>
      <div class="stat-value" id="statTotal">{stats['total']}</div>
    </div>
    <div class="stat-card" onclick="filterByStatus('not_started')">
      <div class="stat-label" data-i18n="notStarted">Not Started</div>
      <div class="stat-value blue" id="statNotStarted">{stats['not_started']}</div>
    </div>
    <div class="stat-card" onclick="filterByStatus('in_progress')">
      <div class="stat-label" data-i18n="inProgress">In Progress</div>
      <div class="stat-value orange" id="statInProgress">{stats['in_progress']}</div>
    </div>
    <div class="stat-card" onclick="filterByStatus('closed')">
      <div class="stat-label" data-i18n="closed">Closed</div>
      <div class="stat-value green" id="statClosed">{stats['closed']}</div>
    </div>
    <div class="stat-card" onclick="filterByStatus('cancelled')">
      <div class="stat-label" data-i18n="cancelled">Cancelled</div>
      <div class="stat-value red" id="statCancelled">{stats['cancelled']}</div>
    </div>
  </div>

  <div class="charts-section">
    <div class="chart-card">
      <div class="chart-title" data-i18n="statusChart">Status Distribution</div>
      <div class="donut-chart" id="statusChart"></div>
      <div class="chart-legend" id="statusLegend"></div>
    </div>
    <div class="chart-card">
      <div class="chart-title" data-i18n="pillarChart">Pillar Distribution</div>
      <div class="bar-chart" id="pillarChart"></div>
    </div>
  </div>

  <div class="table-section">
    <div class="table-header">
      <div></div>
      <div data-i18n="colIntake">Intake</div>
      <div data-i18n="colPillar">Pillar</div>
      <div data-i18n="colType">Type</div>
      <div data-i18n="colSLA">SLA</div>
      <div data-i18n="colStatus">Status</div>
      <div data-i18n="colAssignee">Assignee</div>
      <div data-i18n="colCost">Cost</div>
      <div data-i18n="colApprover">Approver</div>
      <div data-i18n="colScope">Scope</div>
    </div>
    <div id="tableBody"></div>
  </div>
</div>

<script>
// Data
const rowsData = {rows_json};
const allPillars = {json.dumps(pillars_list)};
let currentLang = 'zh';
let exchangeRate = {DEFAULT_EXCHANGE_RATE};
let activeFilters = {{
  status: 'all',
  pillars: [],
  search: ''
}};

// i18n
const i18n = {{
  zh: {{
    title: 'FY26 Intake Cost 报表',
    subtitle: '项目进度、费用及 SLA 监控',
    print: '🖨️ 打印',
    exchangeRate: '💱 汇率设置 (RMB → USD):',
    rateInfo: '公式: Cost = InitiativeChildCount × 汇率',
    searchTicket: '🔍 搜索 Ticket:',
    searchStatus: '状态筛选:',
    allStatuses: '全部状态',
    notStarted: '未开始',
    inProgress: '进行中',
    closed: '已关闭',
    clearFilters: '清除筛选',
    total: '总数',
    cancelled: '已取消',
    statusChart: '状态分布',
    pillarChart: 'Pillar 分布',
    colIntake: 'Intake',
    colPillar: 'Pillar',
    colType: 'Type',
    colSLA: 'SLA',
    colStatus: 'Status',
    colAssignee: 'Assignee',
    colCost: 'Cost',
    colApprover: 'Approver',
    colScope: 'Scope',
    colFollowUp: 'Follow up',
    noResults: '没有找到匹配的数据'
  }},
  en: {{
    title: 'FY26 Intake Cost Report',
    subtitle: 'Project Progress, Cost & SLA Monitoring',
    print: '🖨️ Print',
    exchangeRate: '💱 Exchange Rate (RMB → USD):',
    rateInfo: 'Formula: Cost = InitiativeChildCount × Exchange Rate',
    searchTicket: '🔍 Search Ticket:',
    searchStatus: 'Status Filter:',
    allStatuses: 'All Statuses',
    notStarted: 'Not Started',
    inProgress: 'In Progress',
    closed: 'Closed',
    clearFilters: 'Clear Filters',
    total: 'Total',
    cancelled: 'Cancelled',
    statusChart: 'Status Distribution',
    pillarChart: 'Pillar Distribution',
    colIntake: 'Intake',
    colPillar: 'Pillar',
    colType: 'Type',
    colSLA: 'SLA',
    colStatus: 'Status',
    colAssignee: 'Assignee',
    colCost: 'Cost',
    colApprover: 'Approver',
    colScope: 'Scope',
    colFollowUp: 'Follow up',
    noResults: 'No matching results found'
  }}
}};

function setLang(lang) {{
  currentLang = lang;
  document.querySelectorAll('.lang-btn').forEach(btn => btn.classList.remove('active'));
  event.target.classList.add('active');
  
  document.querySelectorAll('[data-i18n]').forEach(el => {{
    const key = el.getAttribute('data-i18n');
    if (i18n[lang][key]) {{
      el.textContent = i18n[lang][key];
    }}
  }});
}}

function formatCost(rmb, rate) {{
  const usd = rmb * rate;
  const rmbStr = '¥' + rmb.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
  const usdStr = '$' + usd.toLocaleString('en-US', {{minimumFractionDigits: 2, maximumFractionDigits: 2}});
  return rmbStr + '<br>' + usdStr;
}}

function updateExchangeRate() {{
  exchangeRate = parseFloat(document.getElementById('exchangeRate').value) || 0.135;
  renderTable();
}}

function getStatusClass(status) {{
  if (['To Do', 'Open', 'New'].includes(status)) return 'status-todo';
  if (['In Progress'].includes(status)) return 'status-progress';
  if (['Done', 'Closed', 'Resolved'].includes(status)) return 'status-done';
  return 'status-cancel';
}}

function getSLAClass(days, status) {{
  if (['Done', 'Closed', 'Resolved'].includes(status)) return 'sla-done';
  if (days > 14) return 'sla-danger';
  if (days > 7) return 'sla-warning';
  return '';
}}

function toggleRow(key) {{
  const row = document.querySelector(`[data-key="${{key}}"]`);
  row.classList.toggle('expanded');
  const details = document.getElementById(`details-${{key}}`);
  if (details) details.classList.toggle('show');
}}

function togglePillar(pillar) {{
  const idx = activeFilters.pillars.indexOf(pillar);
  if (idx > -1) {{
    activeFilters.pillars.splice(idx, 1);
  }} else {{
    activeFilters.pillars.push(pillar);
  }}
  renderPillarFilter();
  applyFilters();
}}

function filterByStatus(status) {{
  activeFilters.status = status;
  document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active'));
  event.currentTarget.classList.add('active');
  applyFilters();
}}

function applyFilters() {{
  activeFilters.search = document.getElementById('searchTicket').value.toLowerCase();
  const statusFilter = document.getElementById('filterStatus').value;
  if (statusFilter) activeFilters.status = statusFilter;
  
  renderTable();
  updateCharts();
}}

function clearFilters() {{
  activeFilters = {{ status: 'all', pillars: [], search: '' }};
  document.getElementById('searchTicket').value = '';
  document.getElementById('filterStatus').value = '';
  document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active'));
  renderPillarFilter();
  renderTable();
  updateCharts();
}}

function renderPillarFilter() {{
  const container = document.getElementById('pillarFilter');
  container.innerHTML = allPillars.map(p => `
    <span class="pillar-tag ${{activeFilters.pillars.includes(p) ? 'active' : ''}}" onclick="togglePillar('${{p}}')">${{p}}</span>
  `).join('');
}}

function renderTable() {{
  const container = document.getElementById('tableBody');
  
  let filtered = rowsData.filter(row => {{
    // Search filter
    if (activeFilters.search && !row.key.toLowerCase().includes(activeFilters.search) && 
        !row.summary.toLowerCase().includes(activeFilters.search)) return false;
    
    // Status filter
    if (activeFilters.status && activeFilters.status !== 'all') {{
      const statusMapping = {{
        'not_started': ['To Do', 'Open', 'New'],
        'in_progress': ['In Progress', 'In Review'],
        'closed': ['Done', 'Closed', 'Resolved'],
        'cancelled': ['Cancelled', 'Canceled']
      }};
      
      let statusList;
      if (statusMapping[activeFilters.status]) {{
        statusList = statusMapping[activeFilters.status];
      }} else {{
        statusList = activeFilters.status.split(',');
      }}
      
      if (!statusList.includes(row.status)) return false;
    }}
    
    // Pillar filter
    if (activeFilters.pillars.length > 0) {{
      const hasPillar = row.pillars.some(p => activeFilters.pillars.includes(p));
      if (!hasPillar) return false;
    }}
    
    return true;
  }});
  
  if (filtered.length === 0) {{
    container.innerHTML = `
      <div class="no-results">
        <div class="no-results-icon">🔍</div>
        <div>${{i18n[currentLang].noResults}}</div>
      </div>
    `;
    return;
  }}
  
  container.innerHTML = filtered.map(row => {{
    const costDisplay = formatCost(row.cost_rmb_raw, exchangeRate);
    const statusClass = getStatusClass(row.status);
    const slaClass = getSLAClass(row.sla_days, row.status);
    const slaText = row.sla_days + 'd';
    
    const followUpLinks = row.linked_issues.map(li => 
      `<a href="https://lululemon.atlassian.net/browse/${{li.key}}" class="followup-link" target="_blank">${{li.key}}</a>`
    ).join('') || '-';
    
    return `
      <div class="table-row" data-key="${{row.key}}" onclick="toggleRow('${{row.key}}')">
        <div class="col-expand"></div>
        <div class="col-intake">
          <a href="https://lululemon.atlassian.net/browse/${{row.key}}" class="ticket-key" target="_blank" onclick="event.stopPropagation()">${{row.key}}</a>
          <span class="ticket-summary">${{row.summary}}</span>
          <span class="ticket-date">${{row.created}}</span>
        </div>
        <div class="col-pillar">${{row.pillar_str}}</div>
        <div class="col-type ${{row.intake_type === 'TBD' ? 'tbd' : ''}}">${{row.intake_type}}</div>
        <div class="col-sla ${{slaClass}}">${{slaText}}</div>
        <div class="col-status"><span class="status-badge ${{statusClass}}">${{row.status}}</span></div>
        <div class="col-assignee">${{row.assignee}}</div>
        <div class="col-cost" data-rmb="${{row.cost_rmb_raw}}">${{costDisplay}}</div>
        <div class="col-approver">${{row.approver}}</div>
        <div class="col-scope" title="Click to expand">${{row.scope_short}}</div>
      </div>
      <div class="row-details" id="details-${{row.key}}">
        <div class="detail-section">
          <div class="detail-label">Scope (Full):</div>
          <div class="detail-content">${{row.scope}}</div>
        </div>
        <div class="detail-section">
          <div class="detail-label">Follow up:</div>
          <div class="detail-content">${{followUpLinks}}</div>
        </div>
      </div>
    `;
  }}).join('');
}}

function updateCharts() {{
  // Status donut chart
  const statusCounts = {{}};
  rowsData.forEach(row => {{
    if (!statusCounts[row.status]) statusCounts[row.status] = 0;
    statusCounts[row.status]++;
  }});
  
  // Pillar bar chart
  const pillarCounts = {{}};
  rowsData.forEach(row => {{
    row.pillars.forEach(p => {{
      pillarCounts[p] = (pillarCounts[p] || 0) + 1;
    }});
  }});
  
  // Render charts (simplified)
  const colors = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452'];
  
  // Status legend
  const statusLegend = document.getElementById('statusLegend');
  statusLegend.innerHTML = Object.entries(statusCounts).map(([status, count], i) => `
    <span class="legend-item"><span class="legend-dot" style="background:${{colors[i % 7]}}"></span>${{status}} ${{count}}</span>
  `).join('');
  
  // Pillar bar chart
  const pillarChart = document.getElementById('pillarChart');
  const maxCount = Math.max(...Object.values(pillarCounts));
  pillarChart.innerHTML = Object.entries(pillarCounts).map(([pillar, count], i) => `
    <div class="bar-item" onclick="togglePillar('${{pillar}}')">
      <div class="bar-label">${{pillar}}</div>
      <div class="bar-track">
        <div class="bar-fill" style="width:${{(count/maxCount*100)}}%;background:${{colors[i % 7]}}"></div>
        <span class="bar-value">${{count}}</span>
      </div>
    </div>
  `).join('');
}}

// Init
renderPillarFilter();
renderTable();
updateCharts();
</script>
</body>
</html>'''
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    report_path = os.path.join(OUTPUT_DIR, f'fy26_intake_cost_report_{timestamp}.html')
    latest_path = os.path.join(OUTPUT_DIR, 'fy26_intake_cost_report_latest.html')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    with open(latest_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ HTML报告: {report_path}")
    print(f"✅ Latest版本: {latest_path}")
    return latest_path

def main():
    report_path = generate_html()
    print(f"\n报告已生成: {report_path}")

if __name__ == "__main__":
    main()
