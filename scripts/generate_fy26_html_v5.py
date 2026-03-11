#!/usr/bin/env python3
import json
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("/Users/admin/.openclaw/workspace/jira-reports")

json_files = sorted(OUTPUT_DIR.glob("fy26_report_v5_*.json"), reverse=True)
if not json_files:
    print("❌ 未找到 JSON 报告文件")
    exit(1)

with open(json_files[0], "r") as f:
    report_data = json.load(f)

normal_initiatives = report_data["normal_initiatives"]
orphan_epics = report_data["orphan_epics"]
orphan_features = report_data["orphan_features"]
orphan_initiatives = report_data["orphan_initiatives"]
stats = report_data["stats"]

report_date = datetime.now().strftime("%Y-%m-%d")
report_time = datetime.now().strftime("%Y-%m-%d %H:%M")
DATE_STR = datetime.now().strftime("%Y%m%d_%H%M")

initiatives_json = json.dumps(normal_initiatives, ensure_ascii=False)
orphan_epics_json = json.dumps(orphan_epics, ensure_ascii=False)
orphan_features_json = json.dumps(orphan_features, ensure_ascii=False)
orphan_initiatives_json = json.dumps(orphan_initiatives, ensure_ascii=False)

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26_INIT Epic 日报 - {report_date}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: #fafafa; color: #333; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #8B0000 0%, #A52A2A 100%); color: white; padding: 30px 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }}
        .header h1 {{ font-size: 2em; margin-bottom: 8px; font-weight: 300; }}
        .header .subtitle {{ opacity: 0.9; font-size: 1em; }}
        .header .date {{ opacity: 0.7; margin-top: 8px; font-size: 0.85em; }}
        .summary-bar {{ background: white; padding: 20px 40px; border-bottom: 1px solid #eee; display: flex; gap: 30px; font-size: 0.9em; color: #666; flex-wrap: wrap; }}
        .summary-bar span {{ font-weight: 600; color: #8B0000; }}
        .warning-stat {{ color: #ff5722 !important; }}
        .section-header {{ background: #f5f5f5; padding: 20px 40px; border-bottom: 2px solid #ddd; display: flex; align-items: center; gap: 15px; }}
        .section-header h2 {{ font-size: 1.3em; color: #333; }}
        .section-badge {{ background: #8B0000; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 600; }}
        .section-badge.warning {{ background: #ff5722; }}
        .filter-bar {{ background: #f5f5f5; padding: 15px 40px; display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }}
        .filter-btn {{ background: white; border: 1px solid #ddd; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em; }}
        .filter-btn:hover {{ background: #f0f0f0; }}
        .filter-btn.active {{ background: #8B0000; color: white; border-color: #8B0000; }}
        .container {{ max-width: 1600px; margin: 0 auto; padding: 20px 40px; }}
        .initiative-section {{ background: #8B0000; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(139,0,0,0.3); overflow: hidden; }}
        .initiative-section.no-epics {{ opacity: 0.85; }}
        .initiative-header {{ background: #8B0000; color: white; padding: 18px 25px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }}
        .initiative-section.no-epics .initiative-header {{ background: #A0522D; }}
        .initiative-header .init-key {{ background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 4px; font-size: 0.85em; font-family: monospace; margin-right: 10px; }}
        .initiative-header .init-title {{ font-size: 1.15em; font-weight: 600; flex: 1; min-width: 200px; }}
        .initiative-header .init-meta {{ text-align: right; font-size: 0.85em; opacity: 0.9; }}
        .warning-badge {{ background: #ff9800; color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.85em; font-weight: 600; display: flex; align-items: center; gap: 6px; }}
        .epic-count {{ background: rgba(255,255,255,0.25); padding: 6px 14px; border-radius: 20px; font-size: 0.9em; font-weight: 600; }}
        .feature-section {{ background: #CD5C5C; margin: 2px 0; }}
        .feature-header {{ background: #CD5C5C; color: white; padding: 14px 25px; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #8B0000; flex-wrap: wrap; gap: 10px; }}
        .feature-header .feat-key {{ background: rgba(255,255,255,0.2); padding: 3px 10px; border-radius: 4px; font-size: 0.8em; font-family: monospace; margin-right: 10px; }}
        .feature-header .feat-title {{ font-weight: 600; flex: 1; min-width: 200px; font-size: 0.95em; }}
        .feature-header .feat-meta {{ text-align: right; font-size: 0.8em; opacity: 0.9; }}
        .epics-container {{ background: #FFE4E1; padding: 15px 25px; }}
        .no-epics-message {{ background: #fff3e0; padding: 20px; text-align: center; color: #e65100; font-style: italic; border-left: 4px solid #ff9800; margin: 10px 0; }}
        .no-features-message {{ background: #ffebee; padding: 20px; text-align: center; color: #c62828; font-style: italic; border-left: 4px solid #f44336; margin: 10px 0; }}
        .epic-card {{ background: white; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #CD5C5C; }}
        .epic-card:last-child {{ margin-bottom: 0; }}
        .epic-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; flex-wrap: wrap; gap: 10px; }}
        .epic-key-project {{ display: flex; align-items: center; gap: 10px; }}
        .epic-key {{ font-family: monospace; font-size: 0.9em; color: #8B0000; background: #FFE4E1; padding: 3px 10px; border-radius: 4px; font-weight: 600; }}
        .epic-project {{ font-size: 0.75em; color: white; background: #8B0000; padding: 3px 10px; border-radius: 4px; font-weight: 500; }}
        .epic-title {{ font-size: 1.05em; font-weight: 600; color: #333; margin-bottom: 8px; }}
        .epic-desc {{ font-size: 0.9em; color: #666; line-height: 1.5; margin-bottom: 12px; }}
        .epic-details {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; background: #f9f9f9; padding: 12px; border-radius: 6px; font-size: 0.85em; }}
        .detail-item {{ display: flex; flex-direction: column; }}
        .detail-label {{ color: #999; font-size: 0.8em; margin-bottom: 2px; }}
        .detail-value {{ color: #333; font-weight: 500; }}
        .orphan-section {{ background: #ffebee; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(255,87,34,0.2); overflow: hidden; border: 2px solid #ff5722; }}
        .orphan-header {{ background: #ff5722; color: white; padding: 18px 25px; }}
        .orphan-header h3 {{ font-size: 1.1em; margin-bottom: 5px; }}
        .orphan-header p {{ opacity: 0.9; font-size: 0.9em; }}
        .orphan-card {{ background: white; border-radius: 8px; padding: 15px; margin: 15px 25px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #ff5722; }}
        .orphan-card:last-child {{ margin-bottom: 25px; }}
        .status {{ display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 0.8em; font-weight: 500; }}
        .status-new {{ background: #e3f2fd; color: #1976d2; }}
        .status-in-progress {{ background: #fff3e0; color: #f57c00; }}
        .status-done {{ background: #e8f5e9; color: #388e3c; }}
        .status-closed {{ background: #e8f5e9; color: #388e3c; }}
        .status-execution {{ background: #fff3e0; color: #f57c00; }}
        .status-deferred {{ background: #fce4ec; color: #c2185b; }}
        .status-cancelled {{ background: #f5f5f5; color: #757575; }}
        .status-backlog {{ background: #f3e5f5; color: #7b1fa2; }}
        .status-discovery {{ background: #f3e5f5; color: #7b1fa2; }}
        .footer {{ text-align: center; padding: 30px; color: #999; font-size: 0.9em; }}
        .empty-state {{ text-align: center; padding: 40px; color: #999; }}
        .empty-state h4 {{ color: #666; margin-bottom: 10px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>FY26_INIT Epic 日报</h1>
        <div class="subtitle">CNTIN Initiative → CNTIN Feature → 其他项目 Epic (通过 parent 关联)</div>
        <div class="date">生成时间: {report_time}</div>
    </div>
    <div class="summary-bar">
        <div>总 Initiatives: <span>{stats['total_initiatives']}</span></div>
        <div>有 Epic 的: <span>{stats['initiatives_with_epics']}</span></div>
        <div>总 Epics (非 CNTIN): <span>{stats['total_epics_all']}</span></div>
        <div>已关联的 Epics: <span>{stats['total_epics_linked']}</span></div>
        <div>⚠️ 孤儿 Epic: <span class="warning-stat">{stats['orphan_epics_count']}</span></div>
        <div>⚠️ 孤儿 Feature: <span class="warning-stat">{stats['orphan_features_count']}</span></div>
        <div>⚠️ 孤儿 Initiative: <span class="warning-stat">{stats['orphan_initiatives_count']}</span></div>
    </div>
    <div class="section-header">
        <h2>📋 第一部分：正常的 Initiative/Feature/Epic</h2>
        <span class="section-badge">{stats['total_initiatives']} 个</span>
    </div>
    <div class="filter-bar">
        <button class="filter-btn active" onclick="showAll()">显示全部</button>
        <button class="filter-btn" onclick="showWithEpics()">✅ 有 Epic</button>
        <button class="filter-btn" onclick="showWithoutEpics()">⚠️ 无 Epic</button>
    </div>
    <div class="container" id="normalSection"></div>
    <div class="section-header">
        <h2>⚠️ 第二部分：有问题的数据</h2>
        <span class="section-badge warning">{stats['orphan_epics_count'] + stats['orphan_features_count'] + stats['orphan_initiatives_count']} 个</span>
    </div>
    <div class="container" id="orphanSection"></div>
    <div class="footer">报告由 OpenClaw 自动生成 | lululemon Jira 数据</div>
    <script>
        const normalData = {initiatives_json};
        const orphanEpicsData = {orphan_epics_json};
        const orphanFeaturesData = {orphan_features_json};
        const orphanInitiativesData = {orphan_initiatives_json};
        let currentFilter = 'all';
        document.addEventListener('DOMContentLoaded', function() {{ renderNormal(); renderOrphans(); }});
        function showAll() {{ currentFilter = 'all'; updateButtons(); renderNormal(); }}
        function showWithEpics() {{ currentFilter = 'withEpics'; updateButtons(); renderNormal(); }}
        function showWithoutEpics() {{ currentFilter = 'withoutEpics'; updateButtons(); renderNormal(); }}
        function updateButtons() {{
            document.querySelectorAll('.filter-btn').forEach((btn, i) => {{
                btn.classList.toggle('active', 
                    (currentFilter === 'all' && i === 0) ||
                    (currentFilter === 'withEpics' && i === 1) ||
                    (currentFilter === 'withoutEpics' && i === 2)
                );
            }});
        }}
        function escapeHtml(text) {{
            if (!text) return '';
            return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }}
        function renderNormal() {{
            const container = document.getElementById('normalSection');
            let filteredData = normalData;
            if (currentFilter === 'withEpics') filteredData = normalData.filter(i => i.has_epics);
            if (currentFilter === 'withoutEpics') filteredData = normalData.filter(i => !i.has_epics);
            if (filteredData.length === 0) {{
                container.innerHTML = '<div class="empty-state"><h4>没有找到匹配的结果</h4></div>';
                return;
            }}
            let html = '';
            filteredData.forEach(init => {{
                const warningBadge = init.has_epics 
                    ? `<span class="epic-count">${{init.epic_count}} Epics</span>`
                    : `<span class="warning-badge">⚠️ 无 Epic</span><span class="epic-count">${{init.feature_count}} Features</span>`;
                html += `<div class="initiative-section ${{init.has_epics ? '' : 'no-epics'}}">
                    <div class="initiative-header">
                        <div style="display: flex; align-items: center; flex: 1;">
                            <span class="init-key">${{init.init_key}}</span>
                            <span class="init-title">${{escapeHtml(init.init_summary)}}</span>
                        </div>
                        <div class="init-meta">${{init.init_status}} | ${{init.init_assignee || '未分配'}}</div>
                        ${{warningBadge}}
                    </div>`;
                if (init.features.length === 0) {{
                    html += `<div class="no-features-message">⚠️ �� Initiative 下没有 Features</div>`;
                }} else {{
                    init.features.forEach(feat => {{
                        html += `<div class="feature-section">
                            <div class="feature-header">
                                <div style="display: flex; align-items: center; flex: 1;">
                                    <span class="feat-key">${{feat.feat_key}}</span>
                                    <span class="feat-title">${{escapeHtml(feat.feat_summary)}}</span>
                                </div>
                                <div class="feat-meta">${{feat.feat_status}} | ${{feat.feat_assignee || '未分配'}}</div>
                            </div>
                            <div class="epics-container">`;
                        if (feat.epics.length === 0) {{
                            html += `<div class="no-epics-message">⚠️ 该 Feature 下没有关联的 Epics</div>`;
                        }} else {{
                            feat.epics.forEach(epic => {{
                                const statusClass = 'status-' + epic.epic_status.toLowerCase().replace(/\\s+/g, '-');
                                const descHtml = epic.epic_desc ? `<div class="epic-desc">${{escapeHtml(epic.epic_desc.substring(0, 200))}}${{epic.epic_desc.length > 200 ? '...' : ''}}</div>` : '';
                                const startHtml = epic.plan_start !== '-' ? `<div class="detail-item"><span class="detail-label">Plan Start</span><span class="detail-value">${{epic.plan_start}}</span></div>` : '';
                                const endHtml = epic.plan_end !== '-' ? `<div class="detail-item"><span class="detail-label">Plan End</span><span class="detail-value">${{epic.plan_end}}</span></div>` : '';
                                const scopeHtml = epic.epic_scope !== '-' ? `<div class="detail-item"><span class="detail-label">Scope</span><span class="detail-value">${{escapeHtml(epic.epic_scope)}}</span></div>` : '';
                                html += `<div class="epic-card">
                                    <div class="epic-header">
                                        <div class="epic-key-project">
                                            <span class="epic-key">${{epic.epic_key}}</span>
                                            <span class="epic-project">${{epic.epic_project}}</span>
                                        </div>
                                        <span class="status ${{statusClass}}">${{epic.epic_status}}</span>
                                    </div>
                                    <div class="epic-title">${{escapeHtml(epic.epic_summary)}}</div>
                                    ${{descHtml}}
                                    <div class="epic-details">
                                        <div class="detail-item"><span class="detail-label">负责人</span><span class="detail-value">${{epic.epic_assignee}}</span></div>
                                        ${{startHtml}}${{endHtml}}
                                        <div class="detail-item"><span class="detail-label">创建时间</span><span class="detail-value">${{epic.epic_created}}</span></div>
                                        ${{scopeHtml}}
                                    </div>
                                </div>`;
                            }});
                        }}
                        html += `</div></div>`;
                    }});
                }}
                html += `</div>`;
            }});
            container.innerHTML = html;
        }}
        function renderOrphans() {{
            const container = document.getElementById('orphanSection');
            let html = '';
            if (orphanEpicsData.length > 0) {{
                html += `<div class="orphan-section">
                    <div class="orphan-header">
                        <h3>⚠️ 孤儿 Epic（创建时间 > 2026-02-01，无 parent）</h3>
                        <p>${{orphanEpicsData.length}} 个 Epic 没有关联到 CNTIN Feature</p>
                    </div>`;
                orphanEpicsData.forEach(epic => {{
                    html += `<div class="orphan-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span class="epic-key">${{epic.epic_key}}</span>
                                <span class="epic-project">${{epic.epic_project}}</span>
                            </div>
                            <span class="status">${{epic.epic_status}}</span>
                        </div>
                        <div style="font-weight: 600; margin-bottom: 8px;">${{escapeHtml(epic.epic_summary)}}</div>
                        <div style="font-size: 0.85em; color: #666;">
                            负责人: ${{epic.epic_assignee}} | 创建时间: ${{epic.epic_created}}
                        </div>
                    </div>`;
                }});
                html += `</div>`;
            }}
            if (orphanFeaturesData.length > 0) {{
                html += `<div class="orphan-section" style="background: #fff3e0; border-color: #ff9800;">
                    <div class="orphan-header" style="background: #ff9800;">
                        <h3>⚠️ 孤儿 Feature（有 FY26_INIT 标签但无 Epic）</h3>
                        <p>${{orphanFeaturesData.length}} 个 Feature 没有关联 Epic</p>
                    </div>`;
                orphanFeaturesData.forEach(feat => {{
                    html += `<div class="orphan-card" style="border-left-color: #ff9800;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span class="epic-key">${{feat.feat_key}}</span>
                            <span class="status">${{feat.feat_status}}</span>
                        </div>
                        <div style="font-weight: 600; margin-bottom: 8px;">${{escapeHtml(feat.feat_summary)}}</div>
                        <div style="font-size: 0.85em; color: #666;">
                            Initiative: ${{feat.init_key}} | 负责人: ${{feat.feat_assignee}}
                        </div>
                    </div>`;
                }});
                html += `</div>`;
            }}
            if (orphanInitiativesData.length > 0) {{
                html += `<div class="orphan-section" style="background: #fce4ec; border-color: #e91e63;">
                    <div class="orphan-header" style="background: #e91e63;">
                        <h3>⚠️ 孤儿 Initiative（有 FY26_INIT 标签但无 Feature）</h3>
                        <p>${{orphanInitiativesData.length}} 个 Initiative 没有 Feature</p>
                    </div>`;
                orphanInitiativesData.forEach(init => {{
                    html += `<div class="orphan-card" style="border-left-color: #e91e63;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <span class="epic-key">${{init.init_key}}</span>
                            <span class="status">${{init.init_status}}</span>
                        </div>
                        <div style="font-weight: 600; margin-bottom: 8px;">${{escapeHtml(init.init_summary)}}</div>
                        <div style="font-size: 0.85em; color: #666;">
                            负责人: ${{init.init_assignee}}
                        </div>
                    </div>`;
                }});
                html += `</div>`;
            }}
            if (html === '') {{
                html = '<div class="empty-state"><h4>✅ 没有发现问题数据</h4></div>';
            }}
            container.innerHTML = html;
        }}
    </script>
</body>
</html>'''

html_path = OUTPUT_DIR / f"fy26_daily_report_v4_{DATE_STR}.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✅ HTML 报告已保存: {html_path}")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
