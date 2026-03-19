#!/bin/bash
# 生成完整的报告，包含所有 Initiatives（包括没有 Epic 的）

source /Users/admin/.openclaw/workspace/.jira-config

OUTPUT_DIR="/Users/admin/.openclaw/workspace/jira-reports"
DATE_STR=$(date +%Y%m%d_%H%M)

echo "🚀 生成完整报告（包含所有 Initiatives）..."
echo ""

python3 << 'PYTHON_REPORT'
import json
import re
from datetime import datetime
from collections import defaultdict

DATE_STR = "20260310_1337"
OUTPUT_DIR = "/Users/admin/.openclaw/workspace/jira-reports"

def extract_text_from_adf(doc):
    if not doc:
        return ""
    if isinstance(doc, str):
        return doc
    texts = []
    def traverse(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for content in node.get("content", []):
                traverse(content)
        elif isinstance(node, list):
            for item in node:
                traverse(item)
    traverse(doc)
    return " ".join(texts)

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

def format_date(date_str):
    if not date_str:
        return ""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d")
    except:
        return date_str[:10] if date_str else ""

# 加载数据
with open(f"{OUTPUT_DIR}/red_step1_init_{DATE_STR}.json", "r") as f:
    init_data = json.load(f)
with open(f"{OUTPUT_DIR}/red_step2_feat_{DATE_STR}.json", "r") as f:
    feat_data = json.load(f)
with open(f"{OUTPUT_DIR}/red_step4_epics_{DATE_STR}.json", "r") as f:
    epic_data = json.load(f)

initiatives = init_data.get("issues", [])
features = feat_data.get("issues", [])
epics = epic_data.get("issues", [])

# 建立索引
init_by_key = {i["key"]: i for i in initiatives}
feat_by_key = {f["key"]: f for f in features}
epic_by_key = {e["key"]: e for e in epics}

# 建立层级关系
init_to_feats = defaultdict(list)
feat_to_epics = defaultdict(list)

for f in features:
    f_key = f["key"]
    parent = f["fields"].get("parent")
    if parent and parent["key"] in init_by_key:
        init_to_feats[parent["key"]].append(f_key)
    
    links = f["fields"].get("issuelinks", [])
    for link in links:
        if "inwardIssue" in link:
            linked_key = link["inwardIssue"]["key"]
            if linked_key in epic_by_key:
                feat_to_epics[f_key].append(linked_key)
        if "outwardIssue" in link:
            linked_key = link["outwardIssue"]["key"]
            if linked_key in epic_by_key:
                feat_to_epics[f_key].append(linked_key)

# 为每个 Initiative 建立完整数据（包括没有 Epic 的）
all_initiatives_data = []

for init in initiatives:
    init_key = init["key"]
    init_fields = init["fields"]
    init_summary = init_fields.get("summary", "")
    init_status = init_fields.get("status", {}).get("name", "")
    init_assignee = init_fields.get("assignee", {}).get("displayName", "") if init_fields.get("assignee") else ""
    
    # 获取该 Initiative 下的 Features
    feat_keys = init_to_feats.get(init_key, [])
    
    # 检查是否有 Epic
    has_epics = False
    epic_count = 0
    
    for feat_key in feat_keys:
        if feat_key in feat_to_epics and feat_to_epics[feat_key]:
            has_epics = True
            epic_count += len(feat_to_epics[feat_key])
    
    # 如果没有 Features，也标记为 warning
    if not feat_keys:
        has_epics = False
    
    init_data_item = {
        "init_key": init_key,
        "init_summary": init_summary,
        "init_status": init_status,
        "init_assignee": init_assignee,
        "features": [],
        "has_epics": has_epics,
        "epic_count": epic_count,
        "feature_count": len(feat_keys)
    }
    
    # 添加 Features 和 Epics
    for feat_key in feat_keys:
        feat = feat_by_key.get(feat_key)
        if not feat:
            continue
        
        feat_fields = feat["fields"]
        feat_summary = feat_fields.get("summary", "")
        feat_status = feat_fields.get("status", {}).get("name", "")
        feat_assignee = feat_fields.get("assignee", {}).get("displayName", "") if feat_fields.get("assignee") else ""
        
        feat_item = {
            "feat_key": feat_key,
            "feat_summary": feat_summary,
            "feat_status": feat_status,
            "feat_assignee": feat_assignee,
            "epics": []
        }
        
        # 添加 Epics
        epic_keys = feat_to_epics.get(feat_key, [])
        for epic_key in epic_keys:
            epic = epic_by_key.get(epic_key)
            if not epic:
                continue
            
            epic_fields = epic["fields"]
            epic_project = epic_fields.get("project", {}).get("key", "")
            epic_assignee = epic_fields.get("assignee", {}).get("displayName", "未分配") if epic_fields.get("assignee") else "未分配"
            epic_created = format_date(epic_fields.get("created", ""))
            
            plan_start = format_date(epic_fields.get("customfield_13835", "")) or format_date(epic_fields.get("customfield_12501", "")) or "-"
            plan_end = format_date(epic_fields.get("customfield_13836", "")) or format_date(epic_fields.get("customfield_12502", "")) or "-"
            
            labels = epic_fields.get("labels", [])
            components = [c.get("name", "") for c in epic_fields.get("components", [])]
            scope = ", ".join(labels + components) if (labels or components) else "-"
            
            feat_item["epics"].append({
                "epic_key": epic_key,
                "epic_summary": epic_fields.get("summary", ""),
                "epic_status": epic_fields.get("status", {}).get("name", ""),
                "epic_desc": clean_text(extract_text_from_adf(epic_fields.get("description"))),
                "epic_project": epic_project,
                "epic_assignee": epic_assignee,
                "epic_created": epic_created,
                "plan_start": plan_start,
                "plan_end": plan_end,
                "epic_scope": scope
            })
        
        init_data_item["features"].append(feat_item)
    
    all_initiatives_data.append(init_data_item)

# 排序：有 Epic 的在前，没有的在后
all_initiatives_data.sort(key=lambda x: (not x["has_epics"], x["init_key"]))

print(f"总共 {len(all_initiatives_data)} 个 Initiatives")
print(f"有 Epic 的: {sum(1 for i in all_initiatives_data if i['has_epics'])}")
print(f"没有 Epic 的: {sum(1 for i in all_initiatives_data if not i['has_epics'])}")

# 生成 JSON 数据
import json as json_lib
initiatives_json = json_lib.dumps(all_initiatives_data, ensure_ascii=False)

# 生成 HTML 报告
html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26_INIT 完整层级报告（含 Warning）</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: #fafafa; color: #333; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #8B0000 0%, #A52A2A 100%); color: white; padding: 30px 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }}
        .header h1 {{ font-size: 2em; margin-bottom: 8px; font-weight: 300; }}
        .header .subtitle {{ opacity: 0.9; font-size: 1em; }}
        .header .date {{ opacity: 0.7; margin-top: 8px; font-size: 0.85em; }}
        
        .summary-bar {{ background: white; padding: 20px 40px; border-bottom: 1px solid #eee; display: flex; gap: 30px; font-size: 0.9em; color: #666; }}
        .summary-bar span {{ font-weight: 600; color: #8B0000; }}
        .warning-stat {{ color: #ff9800 !important; }}
        
        .filter-bar {{ background: #f5f5f5; padding: 15px 40px; display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }}
        .filter-btn {{ background: white; border: 1px solid #ddd; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em; }}
        .filter-btn:hover {{ background: #f0f0f0; }}
        .filter-btn.active {{ background: #8B0000; color: white; border-color: #8B0000; }}
        
        .container {{ max-width: 1600px; margin: 0 auto; padding: 20px 40px; }}
        
        /* Initiative - 深红色背景 */
        .initiative-section {{ background: #8B0000; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(139,0,0,0.3); overflow: hidden; }}
        .initiative-section.no-epics {{ opacity: 0.7; }}
        .initiative-header {{ background: #8B0000; color: white; padding: 18px 25px; display: flex; justify-content: space-between; align-items: center; }}
        .initiative-section.no-epics .initiative-header {{ background: #A0522D; }}
        .initiative-header .init-key {{ background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 4px; font-size: 0.85em; font-family: monospace; margin-right: 10px; }}
        .initiative-header .init-title {{ font-size: 1.15em; font-weight: 600; flex: 1; }}
        .initiative-header .init-meta {{ text-align: right; font-size: 0.85em; opacity: 0.9; }}
        
        /* Warning 标记 */
        .warning-badge {{ background: #ff9800; color: white; padding: 6px 14px; border-radius: 20px; font-size: 0.85em; font-weight: 600; margin-left: 15px; display: flex; align-items: center; gap: 6px; }}
        .warning-badge::before {{ content: "⚠️"; }}
        .epic-count {{ background: rgba(255,255,255,0.25); padding: 6px 14px; border-radius: 20px; font-size: 0.9em; font-weight: 600; margin-left: 10px; }}
        
        /* Feature - 浅红色背景 */
        .feature-section {{ background: #CD5C5C; margin: 2px 0; }}
        .feature-header {{ background: #CD5C5C; color: white; padding: 14px 25px; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #8B0000; }}
        .feature-header .feat-key {{ background: rgba(255,255,255,0.2); padding: 3px 10px; border-radius: 4px; font-size: 0.8em; font-family: monospace; margin-right: 10px; }}
        .feature-header .feat-title {{ font-weight: 600; flex: 1; font-size: 0.95em; }}
        .feature-header .feat-meta {{ text-align: right; font-size: 0.8em; opacity: 0.9; }}
        
        /* Epic - 淡红色/粉红色背景 */
        .epics-container {{ background: #FFE4E1; padding: 15px 25px; }}
        .no-epics-message {{ background: #fff3e0; padding: 20px; text-align: center; color: #e65100; font-style: italic; border-left: 4px solid #ff9800; }}
        .no-features-message {{ background: #ffebee; padding: 20px; text-align: center; color: #c62828; font-style: italic; border-left: 4px solid #f44336; }}
        
        .epic-card {{ background: white; border-radius: 8px; padding: 15px; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); border-left: 4px solid #CD5C5C; }}
        .epic-card:last-child {{ margin-bottom: 0; }}
        
        .epic-header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }}
        .epic-key-project {{ display: flex; align-items: center; gap: 10px; }}
        .epic-key {{ font-family: monospace; font-size: 0.9em; color: #8B0000; background: #FFE4E1; padding: 3px 10px; border-radius: 4px; font-weight: 600; }}
        .epic-project {{ font-size: 0.75em; color: white; background: #8B0000; padding: 3px 10px; border-radius: 4px; font-weight: 500; }}
        .epic-title {{ font-size: 1.05em; font-weight: 600; color: #333; margin-bottom: 8px; }}
        .epic-desc {{ font-size: 0.9em; color: #666; line-height: 1.5; margin-bottom: 12px; }}
        
        .epic-details {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 10px; background: #f9f9f9; padding: 12px; border-radius: 6px; font-size: 0.85em; }}
        .detail-item {{ display: flex; flex-direction: column; }}
        .detail-label {{ color: #999; font-size: 0.8em; margin-bottom: 2px; }}
        .detail-value {{ color: #333; font-weight: 500; }}
        
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
        
        @media (max-width: 768px) {{
            .header {{ padding: 20px; }}
            .header h1 {{ font-size: 1.5em; }}
            .summary-bar {{ padding: 15px 20px; flex-direction: column; gap: 5px; }}
            .filter-bar {{ padding: 10px 20px; }}
            .container {{ padding: 15px 20px; }}
            .epic-details {{ grid-template-columns: 1fr; }}
            .initiative-header {{ flex-wrap: wrap; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>FY26_INIT 完整层级报告</h1>
        <div class="subtitle">所有 Initiatives（含 Warning 标记）</div>
        <div class="date">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>
    
    <div class="summary-bar">
        <div>总 Initiatives: <span>{len(all_initiatives_data)}</span></div>
        <div>有 Epic 的: <span>{sum(1 for i in all_initiatives_data if i['has_epics'])}</span></div>
        <div>⚠️ 无 Epic 的: <span class="warning-stat">{sum(1 for i in all_initiatives_data if not i['has_epics'])}</span></div>
        <div>总 Features: <span>{sum(i['feature_count'] for i in all_initiatives_data)}</span></div>
        <div>总 Epics: <span>{sum(i['epic_count'] for i in all_initiatives_data)}</span></div>
    </div>
    
    <div class="filter-bar">
        <button class="filter-btn active" onclick="showAll()">显示全部</button>
        <button class="filter-btn" onclick="showWithEpics()">✅ 有 Epic</button>
        <button class="filter-btn" onclick="showWithoutEpics()">⚠️ 无 Epic</button>
    </div>
    
    <div class="container" id="contentContainer"></div>
    
    <div class="footer">报告由 OpenClaw 自动生成 | lululemon Jira 数据</div>
    
    <script>
        const allData = {initiatives_json};
        let currentFilter = 'all';
        
        document.addEventListener('DOMContentLoaded', function() {{ renderContent(); }});
        
        function showAll() {{
            currentFilter = 'all';
            updateFilterButtons();
            renderContent();
        }}
        
        function showWithEpics() {{
            currentFilter = 'withEpics';
            updateFilterButtons();
            renderContent();
        }}
        
        function showWithoutEpics() {{
            currentFilter = 'withoutEpics';
            updateFilterButtons();
            renderContent();
        }}
        
        function updateFilterButtons() {{
            const buttons = document.querySelectorAll('.filter-btn');
            buttons.forEach(btn => btn.classList.remove('active'));
            if (currentFilter === 'all') buttons[0].classList.add('active');
            if (currentFilter === 'withEpics') buttons[1].classList.add('active');
            if (currentFilter === 'withoutEpics') buttons[2].classList.add('active');
        }}
        
        function escapeHtml(text) {{
            if (!text) return '';
            return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }}
        
        function renderContent() {{
            const container = document.getElementById('contentContainer');
            
            let filteredData = allData;
            if (currentFilter === 'withEpics') {{
                filteredData = allData.filter(i => i.has_epics);
            }} else if (currentFilter === 'withoutEpics') {{
                filteredData = allData.filter(i => !i.has_epics);
            }}
            
            if (filteredData.length === 0) {{
                container.innerHTML = '<div style="text-align: center; padding: 60px; color: #999;"><h3>没有找到匹配的结果</h3></div>';
                return;
            }}
            
            let html = '';
            
            filteredData.forEach(init => {{
                const hasEpicsClass = init.has_epics ? '' : 'no-epics';
                const warningBadge = init.has_epics 
                    ? `<span class="epic-count">${{init.epic_count}} Epics</span>`
                    : `<span class="warning-badge">无 Epic</span><span class="epic-count">${{init.feature_count}} Features</span>`;
                
                html += `<div class="initiative-section ${{hasEpicsClass}}">
                    <div class="initiative-header">
                        <div style="display: flex; align-items: center; flex: 1;">
                            <span class="init-key">${{init.init_key}}</span>
                            <span class="init-title">${{escapeHtml(init.init_summary)}}</span>
                        </div>
                        <div class="init-meta">
                            <div>${{init.init_status}} | ${{init.init_assignee || '未分配'}}</div>
                        </div>
                        ${{warningBadge}}
                    </div>`;
                
                if (init.features.length === 0) {{
                    html += `<div class="no-features-message">⚠️ 该 Initiative 下没有 Features</div>`;
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
    </script>
</body>
</html>'''

# 保存 HTML
html_path = f"{OUTPUT_DIR}/fy26_complete_with_warning_{DATE_STR}.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"✅ HTML 报告已生成: {html_path}")

# 生成 CSV（包含所有 Initiatives）
csv_path = f"{OUTPUT_DIR}/fy26_complete_with_warning_{DATE_STR}.csv"
with open(csv_path, "w", encoding="utf-8-sig") as f:
    f.write("Initiative Key,Initiative Summary,Initiative Status,Initiative Assignee,Has Epics,Feature Count,Epic Count,Feature Key,Feature Summary,Feature Status,Feature Assignee,Epic Key,Epic Summary,Epic Project,Epic Status,Epic Assignee,Epic Created,Plan Start,Plan End,Epic Scope,Epic Description\n")
    
    for init in all_initiatives_data:
        if init["features"]:
            for feat in init["features"]:
                if feat["epics"]:
                    for epic in feat["epics"]:
                        desc = epic['epic_desc'].replace('"', '""')
                        scope = epic['epic_scope'].replace('"', '""')
                        f.write(f'"{init["init_key"]}","{init["init_summary"]}","{init["init_status"]}","{init["init_assignee"]}","{\"是\" if init["has_epics"] else \"否\"}",{init["feature_count"]},{init["epic_count"]},"{feat["feat_key"]}","{feat["feat_summary"]}","{feat["feat_status"]}","{feat["feat_assignee"]}","{epic["epic_key"]}","{epic["epic_summary"]}","{epic["epic_project"]}","{epic["epic_status"]}","{epic["epic_assignee"]}","{epic["epic_created"]}","{epic["plan_start"]}","{epic["plan_end"]}","{scope}","{desc}"\n')
                else:
                    # Feature 没有 Epics
                    f.write(f'"{init["init_key"]}","{init["init_summary"]}","{init["init_status"]}","{init["init_assignee"]}","{\"是\" if init["has_epics"] else \"否\"}",{init["feature_count"]},{init["epic_count"]},"{feat["feat_key"]}","{feat["feat_summary"]}","{feat["feat_status"]}","{feat["feat_assignee"]}","","","","","","","","","","",""\n')
        else:
            # Initiative 没有 Features
            f.write(f'"{init["init_key"]}","{init["init_summary"]}","{init["init_status"]}","{init["init_assignee"]}","{\"是\" if init["has_epics"] else \"否\"}",{init["feature_count"]},{init["epic_count"]},"","","","","","","","","","","","","",""\n')

print(f"✅ CSV 报告已生成: {csv_path}")

PYTHON_REPORT

echo ""
echo "📁 生成的文件:"
ls -lh "$OUTPUT_DIR"/fy26_complete_with_warning_*