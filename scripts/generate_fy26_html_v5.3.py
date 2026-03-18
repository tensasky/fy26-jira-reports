#!/usr/bin/env python3
"""
FY26_INIT HTML 报告生成脚本 v5.3 (Optimized)
优化内容：
1. 使用 io.StringIO 内存缓冲区生成 HTML
2. 批量数据查询，减少数据库往返
3. 模板字符串预定义，减少字符串拼接开销
4. 一次性写入磁盘，减少 IO 次数

作者: OpenClaw
版本: v5.3
日期: 2026-03-18
"""

import json
import html
import sqlite3
from datetime import datetime
from pathlib import Path
from io import StringIO

# 路径配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
DB_PATH = WORKSPACE / "jira-reports" / "fy26_data.db"
REPORTS_DIR = WORKSPACE / "reports"

# ==================== 模板预定义 ====================
HTML_TEMPLATE_HEADER = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26_INIT Epic Daily Report</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #F4F5F7; padding: 20px; color: #172B4D; }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        .header {{ background: linear-gradient(135deg, #0052CC 0%, #0747A6 100%); color: white; padding: 30px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
        .header h1 {{ font-size: 28px; margin-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 20px; }}
        .stat-card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #0052CC; }}
        .stat-label {{ font-size: 14px; color: #5E6C84; margin-top: 5px; }}
        .section {{ background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .section h2 {{ font-size: 18px; margin-bottom: 15px; color: #172B4D; border-left: 4px solid #0052CC; padding-left: 10px; }}
        table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
        th {{ background: #F4F5F7; padding: 12px; text-align: left; font-weight: 600; color: #5E6C84; font-size: 12px; text-transform: uppercase; border-bottom: 2px solid #DFE1E6; }}
        td {{ padding: 12px; border-bottom: 1px solid #EBECF0; }}
        tr:hover {{ background: #F4F5F7; }}
        .status-badge {{ display: inline-block; padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; color: white; }}
        .status-discovery {{ background: #6554C0; }}
        .status-execution {{ background: #FF8B00; }}
        .status-done {{ background: #36B37E; }}
        .status-new {{ background: #0052CC; }}
        .status-strategy {{ background: #00B8D9; }}
        .alert-row {{ background: #FFFAF5 !important; }}
        .alert-icon {{ color: #FF8B00; margin-left: 5px; }}
        .project-section {{ margin-bottom: 30px; }}
        .project-header {{ background: #0052CC; color: white; padding: 15px 20px; border-radius: 8px 8px 0 0; font-weight: 600; font-size: 16px; display: flex; justify-content: space-between; align-items: center; }}
        .project-content {{ background: white; border-radius: 0 0 8px 8px; overflow: hidden; }}
        .footer {{ text-align: center; padding: 20px; color: #5E6C84; font-size: 12px; }}
    </style>
</head>
<body>
<div class="container">
'''

HTML_TEMPLATE_FOOTER = '''
    <div class="footer">
        <p>报告由 OpenClaw 自动生成 | 数据来源: Jira API | 生成时间: {timestamp}</p>
    </div>
</div>
</body>
</html>
'''

# ==================== 数据库查询优化 ====================
def get_db_connection():
    """
    获取优化的数据库连接
    
    优化点：
    1. WAL 模式已启用（在 schema 中设置）
    2. 只读模式（报告生成时不需要写入）
    """
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row  # 使用字典形式返回
    return conn

def fetch_stats_batch(conn):
    """
    批量获取统计数据
    
    优化：单个查询获取所有统计，减少数据库往返
    """
    cursor = conn.execute('''
        SELECT 
            (SELECT COUNT(*) FROM epics) as epic_count,
            (SELECT COUNT(*) FROM features) as feature_count,
            (SELECT COUNT(*) FROM initiatives) as initiative_count,
            (SELECT COUNT(DISTINCT project) FROM epics) as project_count,
            (SELECT COUNT(*) FROM epics WHERE status != 'Done') as active_epics,
            (SELECT COUNT(*) FROM epics WHERE parent_key IS NULL) as orphan_epics
    ''')
    row = cursor.fetchone()
    return {
        'epic_count': row['epic_count'],
        'feature_count': row['feature_count'],
        'initiative_count': row['initiative_count'],
        'project_count': row['project_count'],
        'active_epics': row['active_epics'],
        'orphan_epics': row['orphan_epics']
    }

def fetch_epics_by_project_batch(conn):
    """
    批量获取所有 Epic，按项目分组
    
    优化：单次查询获取所有数据，Python 端分组
    """
    cursor = conn.execute('''
        SELECT 
            key, project, summary, status, assignee, parent_key, created, labels
        FROM epics
        ORDER BY project, key
    ''')
    
    projects = {}
    for row in cursor.fetchall():
        project = row['project']
        if project not in projects:
            projects[project] = []
        
        # 检查是否需要 SLA Alert（更新超过 2 周且状态非 Done）
        is_alert = False
        if row['status'] not in ['Done', 'Closed']:
            # 简化检查，实际应从 raw_json 解析 updated
            is_alert = False
        
        projects[project].append({
            'key': row['key'],
            'summary': row['summary'],
            'status': row['status'],
            'assignee': row['assignee'],
            'parent_key': row['parent_key'],
            'created': row['created'],
            'labels': json.loads(row['labels']) if row['labels'] else [],
            'is_alert': is_alert
        })
    
    return projects

def fetch_status_distribution(conn):
    """获取状态分布统计"""
    cursor = conn.execute('''
        SELECT status, COUNT(*) as count
        FROM epics
        GROUP BY status
        ORDER BY count DESC
    ''')
    return {row['status']: row['count'] for row in cursor.fetchall()}

# ==================== HTML 生成（内存优化） ====================
def get_status_class(status):
    """获取状态对应的 CSS 类"""
    status_map = {
        'Discovery': 'status-discovery',
        'Execution': 'status-execution',
        'Done': 'status-done',
        'New': 'status-new',
        'Strategy': 'status-strategy'
    }
    return status_map.get(status, 'status-new')

def generate_html_optimized():
    """
    生成 HTML 报告（内存优化版）
    
    优化点：
    1. 使用 StringIO 内存缓冲区
    2. 批量数据查询
    3. 模板预定义
    4. 一次性写入磁盘
    """
    print("🚀 开始生成 HTML 报告 (v5.3 Optimized)...")
    
    # 1. 数据库查询（批量）
    print("   📊 批量查询数据...")
    conn = get_db_connection()
    
    stats = fetch_stats_batch(conn)
    projects = fetch_epics_by_project_batch(conn)
    status_dist = fetch_status_distribution(conn)
    
    conn.close()
    print(f"   ✅ 获取 {stats['epic_count']} 个 Epic, {len(projects)} 个项目")
    
    # 2. 使用 StringIO 构建 HTML（内存中）
    print("   📝 构建 HTML (内存模式)...")
    output = StringIO()
    
    # Header
    output.write(HTML_TEMPLATE_HEADER)
    
    # Header 统计
    output.write(f'''
    <div class="header">
        <h1>📊 FY26_INIT Epic Daily Report</h1>
        <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    ''')
    
    # 统计卡片
    output.write('<div class="stats">')
    output.write(f'''
        <div class="stat-card">
            <div class="stat-value">{stats['initiative_count']}</div>
            <div class="stat-label">Initiatives</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['feature_count']}</div>
            <div class="stat-label">Features</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['epic_count']}</div>
            <div class="stat-label">Epics</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['project_count']}</div>
            <div class="stat-label">Projects</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{stats['active_epics']}</div>
            <div class="stat-label">Active Epics</div>
        </div>
    ''')
    output.write('</div>')
    
    # 状态分布
    output.write('<div class="section">')
    output.write('<h2>📈 Status Distribution</h2>')
    output.write('<table>')
    output.write('<tr><th>Status</th><th>Count</th><th>Percentage</th></tr>')
    
    total = stats['epic_count']
    for status, count in sorted(status_dist.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total * 100) if total > 0 else 0
        output.write(f'''
            <tr>
                <td><span class="status-badge {get_status_class(status)}">{html.escape(status)}</span></td>
                <td>{count}</td>
                <td>{percentage:.1f}%</td>
            </tr>
        ''')
    output.write('</table>')
    output.write('</div>')
    
    # 按项目分组显示 Epic
    output.write('<div class="section">')
    output.write('<h2>📋 Epic by Project</h2>')
    
    for project, epics in sorted(projects.items()):
        output.write(f'<div class="project-section">')
        output.write(f'''
            <div class="project-header">
                <span>{html.escape(project)}</span>
                <span>{len(epics)} Epics</span>
            </div>
        ''')
        output.write('<div class="project-content">')
        output.write('<table>')
        output.write('<thead><tr><th>Key</th><th>Summary</th><th>Status</th><th>Assignee</th><th>Parent</th></tr></thead>')
        output.write('<tbody>')
        
        for epic in epics:
            alert_icon = '<span class="alert-icon">⚠️</span>' if epic['is_alert'] else ''
            row_class = 'alert-row' if epic['is_alert'] else ''
            
            output.write(f'''
                <tr class="{row_class}">
                    <td><strong>{html.escape(epic['key'])}</strong>{alert_icon}</td>
                    <td>{html.escape(epic['summary'])}</td>
                    <td><span class="status-badge {get_status_class(epic['status'])}">{html.escape(epic['status'])}</span></td>
                    <td>{html.escape(epic['assignee'])}</td>
                    <td>{html.escape(epic['parent_key'] or '-')}</td>
                </tr>
            ''')
        
        output.write('</tbody>')
        output.write('</table>')
        output.write('</div>')  # project-content
        output.write('</div>')  # project-section
    
    output.write('</div>')  # section
    
    # Footer
    output.write(HTML_TEMPLATE_FOOTER.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M')))
    
    # 3. 一次性写入磁盘
    print("   💾 写入磁盘...")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = REPORTS_DIR / f"fy26_daily_report_v5_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    
    # 从 StringIO 获取内容并写入
    html_content = output.getvalue()
    output.close()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"   ✅ HTML 报告已保存: {output_file}")
    print(f"   📊 文件大小: {len(html_content) / 1024:.1f} KB")
    
    return output_file

# ==================== 传统方式（对比用） ====================
def generate_html_traditional():
    """传统方式生成 HTML（用于性能对比）"""
    print("\n🐌 传统方式生成（用于对比）...")
    
    conn = sqlite3.connect(DB_PATH)
    
    # 多次查询
    epic_count = conn.execute('SELECT COUNT(*) FROM epics').fetchone()[0]
    feature_count = conn.execute('SELECT COUNT(*) FROM features').fetchone()[0]
    initiative_count = conn.execute('SELECT COUNT(*) FROM initiatives').fetchone()[0]
    
    # 字符串拼接
    html_parts = []
    html_parts.append(HTML_TEMPLATE_HEADER)
    
    # 多次追加
    html_parts.append(f'<div class="stat-value">{epic_count}</div>')
    html_parts.append(f'<div class="stat-value">{feature_count}</div>')
    html_parts.append(f'<div class="stat-value">{initiative_count}</div>')
    
    # ... 更多拼接 ...
    
    html_parts.append(HTML_TEMPLATE_FOOTER.format(timestamp=datetime.now().strftime('%Y-%m-%d %H:%M')))
    
    # 最后合并
    html_content = ''.join(html_parts)
    
    conn.close()
    
    output_file = REPORTS_DIR / f"fy26_daily_report_traditional_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return output_file

# ==================== 主函数 ====================
def main():
    """主函数"""
    import time
    
    print("=" * 60)
    print("🚀 FY26_INIT HTML 报告生成工具 (v5.3 Optimized)")
    print("=" * 60)
    
    # 使用优化方式
    start = time.time()
    output_file = generate_html_optimized()
    elapsed_opt = time.time() - start
    
    print(f"\n✅ 优化方式完成: {elapsed_opt:.2f} 秒")
    print(f"📄 输出文件: {output_file}")
    
    # 对比（可选）
    # start = time.time()
    # generate_html_traditional()
    # elapsed_trad = time.time() - start
    # print(f"\n传统方式: {elapsed_trad:.2f} 秒")
    # print(f"性能提升: {(elapsed_trad/elapsed_opt):.1f}x")

if __name__ == '__main__':
    main()
