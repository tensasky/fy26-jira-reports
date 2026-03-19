#!/bin/bash
# 生成分页+搜索功能的 HTML 报告

source /Users/admin/.openclaw/workspace/.jira-config

OUTPUT_DIR="/Users/admin/.openclaw/workspace/jira-reports"
DATE_STR=$(date +%Y%m%d_%H%M)

echo "🚀 生成分页+搜索功能的 HTML 报告..."
echo ""

# 使用之前抓取的数据生成报告
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

# 为每个 Epic 建立完整层级路径
epic_hierarchy = []
for feat_key, epic_keys in feat_to_epics.items():
    feat = feat_by_key.get(feat_key)
    if not feat:
        continue
    
    feat_fields = feat["fields"]
    feat_summary = feat_fields.get("summary", "")
    feat_status = feat_fields.get("status", {}).get("name", "")
    feat_assignee = feat_fields.get("assignee", {}).get("displayName", "") if feat_fields.get("assignee") else ""
    
    # 找到所属的 Initiative
    init_key = None
    init_summary = ""
    init_status = ""
    init_assignee = ""
    for ik, feats_list in init_to_feats.items():
        if feat_key in feats_list:
            init_key = ik
            init_data = init_by_key.get(ik, {})
            init_fields = init_data.get("fields", {})
            init_summary = init_fields.get("summary", "")
            init_status = init_fields.get("status", {}).get("name", "")
            init_assignee = init_fields.get("assignee", {}).get("displayName", "") if init_fields.get("assignee") else ""
            break
    
    if not init_key:
        continue
    
    for epic_key in epic_keys:
        epic = epic_by_key.get(epic_key)
        if not epic:
            continue
        
        epic_fields = epic["fields"]
        epic_project = epic_fields.get("project", {}).get("key", "")
        
        # 提取 Epic 的详细信息
        epic_assignee = epic_fields.get("assignee", {}).get("displayName", "未分配") if epic_fields.get("assignee") else "未分配"
        epic_created = format_date(epic_fields.get("created", ""))
        epic_updated = format_date(epic_fields.get("updated", ""))
        
        # Plan Start/End Date (从自定义字段获取)
        plan_start = format_date(epic_fields.get("customfield_13835", "")) or format_date(epic_fields.get("customfield_12501", "")) or "-"
        plan_end = format_date(epic_fields.get("customfield_13836", "")) or format_date(epic_fields.get("customfield_12502", "")) or "-"
        
        # 获取 Scope
        labels = epic_fields.get("labels", [])
        components = [c.get("name", "") for c in epic_fields.get("components", [])]
        scope = ", ".join(labels + components) if (labels or components) else "-"
        
        epic_hierarchy.append({
            "epic_key": epic_key,
            "epic_summary": epic_fields.get("summary", ""),
            "epic_status": epic_fields.get("status", {}).get("name", ""),
            "epic_desc": clean_text(extract_text_from_adf(epic_fields.get("description"))),
            "epic_project": epic_project,
            "epic_assignee": epic_assignee,
            "epic_created": epic_created,
            "epic_updated": epic_updated,
            "plan_start": plan_start,
            "plan_end": plan_end,
            "epic_scope": scope,
            "feature_key": feat_key,
            "feature_summary": feat_summary,
            "feature_status": feat_status,
            "feature_assignee": feat_assignee,
            "initiative_key": init_key,
            "initiative_summary": init_summary,
            "initiative_status": init_status,
            "initiative_assignee": init_assignee
        })

# 按 Initiative -> Feature -> Epic 排序
epic_hierarchy.sort(key=lambda x: (x["initiative_key"], x["feature_key"], x["epic_key"]))

print(f"最终报告包含 {len(epic_hierarchy)} 个 Epic 条目")

# 统计
init_epic_count = defaultdict(int)
initiatives_list = sorted(set(item["initiative_key"] for item in epic_hierarchy))
statuses_list = sorted(set(item["epic_status"] for item in epic_hierarchy))

for item in epic_hierarchy:
    init_epic_count[item["initiative_key"]] += 1

# 生成 JSON 数据
import json as json_lib
epic_json = json_lib.dumps(epic_hierarchy, ensure_ascii=False)

# 生成 HTML 报告
html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26_INIT Epic 详细汇总报告（分页版）</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; background: #fafafa; color: #333; line-height: 1.6; }}
        .header {{ background: linear-gradient(135deg, #8B0000 0%, #A52A2A 100%); color: white; padding: 30px 40px; box-shadow: 0 2px 10px rgba(0,0,0,0.2); }}
        .header h1 {{ font-size: 2em; margin-bottom: 8px; font-weight: 300; }}
        .header .subtitle {{ opacity: 0.9; font-size: 1em; }}
        .header .date {{ opacity: 0.7; margin-top: 8px; font-size: 0.85em; }}
        
        .search-bar {{ background: white; padding: 20px 40px; border-bottom: 1px solid #eee; display: flex; gap: 15px; flex-wrap: wrap; align-items: center; }}
        .search-group {{ display: flex; align-items: center; gap: 8px; }}
        .search-group label {{ font-size: 0.9em; color: #666; font-weight: 500; }}
        .search-group input, .search-group select {{ padding: 8px 12px; border: 1px solid #ddd; border-radius: 6px; font-size: 0.9em; min-width: 150px; }}
        .search-group input:focus, .search-group select:focus {{ outline: none; border-color: #8B0000; }}
        .search-btn {{ background: #8B0000; color: white; border: none; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-size: 0.9em; }}
        .search-btn:hover {{ background: #A52A2A; }}
        .clear-btn {{ background: #f5f5f5; color: #666; border: 1px solid #ddd; padding: 8px 20px; border-radius: 6px; cursor: pointer; font-size: 0.9em; }}
        .clear-btn:hover {{ background: #eee; }}
        
        .stats-bar {{ background: #f5f5f5; padding: 15px 40px; display: flex; gap: 30px; font-size: 0.9em; color: #666; }}
        .stats-bar span {{ font-weight: 600; color: #8B0000; }}
        
        .pagination {{ background: white; padding: 15px 40px; border-bottom: 1px solid #eee; display: flex; justify-content: space-between; align-items: center; }}
        .page-info {{ font-size: 0.9em; color: #666; }}
        .page-controls {{ display: flex; gap: 10px; align-items: center; }}
        .page-btn {{ background: white; border: 1px solid #ddd; padding: 6px 12px; border-radius: 4px; cursor: pointer; font-size: 0.85em; }}
        .page-btn:hover:not(:disabled) {{ background: #f5f5f5; }}
        .page-btn:disabled {{ opacity: 0.5; cursor: not-allowed; }}
        .page-btn.active {{ background: #8B0000; color: white; border-color: #8B0000; }}
        .page-size {{ padding: 6px 10px; border: 1px solid #ddd; border-radius: 4px; font-size: 0.85em; }}
        
        .container {{ max-width: 1600px; margin: 0 auto; padding: 20px 40px; }}
        
        .initiative-section {{ background: #8B0000; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(139,0,0,0.3); overflow: hidden; }}
        .initiative-header {{ background: #8B0000; color: white; padding: 18px 25px; display: flex; justify-content: space-between; align-items: center; }}
        .initiative-header .init-key {{ background: rgba(255,255,255,0.2); padding: 4px 12px; border-radius: 4px; font-size: 0.85em; font-family: monospace; margin-right: 10px; }}
        .initiative-header .init-title {{ font-size: 1.15em; font-weight: 600; flex: 1; }}
        .initiative-header .init-meta {{ text-align: right; font-size: 0.85em; opacity: 0.9; }}
        .initiative-header .epic-count {{ background: rgba(255,255,255,0.25); padding: 6px 14px; border-radius: 20px; font-size: 0.9em; font-weight: 600; margin-left: 15px; }}
        
        .feature-section {{ background: #CD5C5C; margin: 2px 0; }}
        .feature-header {{ background: #CD5C5C; color: white; padding: 14px 25px; display: flex; justify-content: space-between; align-items: center; border-left: 5px solid #8B0000; }}
        .feature-header .feat-key {{ background: rgba(255,255,255,0.2); padding: 3px 10px; border-radius: 4px; font-size: 0.8em; font-family: monospace; margin-right: 10px; }}
        .feature-header .feat-title {{ font-weight: 600; flex: 1; font-size: 0.95em; }}
        .feature-header .feat-meta {{ text-align: right; font-size: 0.8em; opacity: 0.9; }}
        
        .epics-container {{ background: #FFE4E1; padding: 15px 25px; }}
        
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
        
        .no-results {{ text-align: center; padding: 60px; color: #999; }}
        
        .footer {{ text-align: center; padding: 30px; color: #999; font-size: 0.9em; }}
        
        @media (max-width: 768px) {{
            .header {{ padding: 20px; }}
            .header h1 {{ font-size: 1.5em; }}
            .search-bar {{ padding: 15px 20px; flex-direction: column; align-items: stretch; }}
            .search-group {{ width: 100%; }}
            .search-group input, .search-group select {{ width: 100%; }}
            .stats-bar {{ padding: 10px 20px; flex-direction: column; gap: 5px; }}
            .pagination {{ padding: 10px 20px; flex-direction: column; gap: 10px; }}
            .container {{ padding: 15px 20px; }}
            .epic-details {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>FY26_INIT Epic 详细汇总报告</h1>
        <div class="subtitle">CNTIN Initiative → CNTIN Feature → 其他项目 Epic</div>
        <div class="date">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")} | 共 {len(epic_hierarchy)} 个 Epic 条目</div>
    </div>
    
    <div class="search-bar">
        <div class="search-group">
            <label>Initiative:</label>
            <select id="initiativeFilter">
                <option value="">全部</option>
                {''.join([f'<option value="{init}">{init}</option>' for init in initiatives_list])}
            </select>
        </div>
        <div class="search-group">
            <label>Epic 状态:</label>
            <select id="statusFilter">
                <option value="">全部</option>
                {''.join([f'<option value="{status}">{status}</option>' for status in statuses_list])}
            </select>
        </div>
        <div class="search-group">
            <label>搜索:</label>
            <input type="text" id="searchInput" placeholder="搜索 Epic 标题、Key、负责人...">
        </div>
        <button class="search-btn" onclick="applyFilters()">筛选</button>
        <button class="clear-btn" onclick="clearFilters()">清除</button>
    </div>
    
    <div class="stats-bar">
        <div>显示: <span id="showingCount">0</span> / <span id="totalCount">{len(epic_hierarchy)}</span> 个 Epic</div>
        <div>Initiatives: <span>{len(initiatives_list)}</span></div>
        <div>涉及项目: <span>{len(set(item["epic_project"] for item in epic_hierarchy))}</span></div>
    </div>
    
    <div class="pagination">
        <div class="page-info">
            每页显示: 
            <select class="page-size" id="pageSize" onchange="changePageSize()">
                <option value="10">10</option>
                <option value="20" selected>20</option>
                <option value="50">50</option>
                <option value="100">100</option>
            </select>
            条
        </div>
        <div class="page-controls" id="pageControls"></div>
    </div>
    
    <div class="container" id="contentContainer"></div>
    
    <div class="footer">报告由 OpenClaw 自动生成 | lululemon Jira 数据</div>
    
    <script>
        const allData = {epic_json};
        let filteredData = [...allData];
        let currentPage = 1;
        let pageSize = 20;
        
        document.addEventListener('DOMContentLoaded', function() {{ applyFilters(); }});
        
        function applyFilters() {{
            const initiativeFilter = document.getElementById('initiativeFilter').value;
            const statusFilter = document.getElementById('statusFilter').value;
            const searchInput = document.getElementById('searchInput').value.toLowerCase();
            
            filteredData = allData.filter(item => {{
                if (initiativeFilter && item.initiative_key !== initiativeFilter) return false;
                if (statusFilter && item.epic_status !== statusFilter) return false;
                if (searchInput) {{
                    const searchText = `${{item.epic_key}} ${{item.epic_summary}} ${{item.epic_assignee}} ${{item.feature_key}} ${{item.initiative_key}}`.toLowerCase();
                    if (!searchText.includes(searchInput)) return false;
                }}
                return true;
            }});
            
            currentPage = 1;
            renderContent();
        }}
        
        function clearFilters() {{
            document.getElementById('initiativeFilter').value = '';
            document.getElementById('statusFilter').value = '';
            document.getElementById('searchInput').value = '';
            applyFilters();
        }}
        
        function changePageSize() {{
            pageSize = parseInt(document.getElementById('pageSize').value);
            currentPage = 1;
            renderContent();
        }}
        
        function escapeHtml(text) {{
            if (!text) return '';
            return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
        }}
        
        function renderContent() {{
            const container = document.getElementById('contentContainer');
            const showingCount = document.getElementById('showingCount');
            
            if (filteredData.length === 0) {{
                container.innerHTML = '<div class="no-results"><h3>📭 没有找到匹配的结果</h3><p>请调整筛选条件</p></div>';
                showingCount.textContent = 0;
                renderPagination(0);
                return;
            }}
            
            const totalPages = Math.ceil(filteredData.length / pageSize);
            const start = (currentPage - 1) * pageSize;
            const end = Math.min(start + pageSize, filteredData.length);
            const pageData = filteredData.slice(start, end);
            
            showingCount.textContent = filteredData.length;
            
            let html = '';
            let currentInit = null;
            let currentFeat = null;
            
            const initEpicCount = {{}};
            pageData.forEach(item => {{ initEpicCount[item.initiative_key] = (initEpicCount[item.initiative_key] || 0) + 1; }});
            
            pageData.forEach(item => {{
                if (item.initiative_key !== currentInit) {{
                    if (currentInit) html += '</div></div></div>';
                    currentInit = item.initiative_key;
                    currentFeat = null;
                    html += `<div class="initiative-section"><div class="initiative-header"><div style="display: flex; align-items: center; flex: 1;"><span class="init-key">${{item.initiative_key}}</span><span class="init-title">${{escapeHtml(item.initiative_summary)}}</span></div><div class="init-meta"><div>${{item.initiative_status}} | ${{item.initiative_assignee || '未分配'}}</div></div><span class="epic-count">${{initEpicCount[item.initiative_key]}} Epics</span></div>`;
                }}
                
                if (item.feature_key !== currentFeat) {{
                    if (currentFeat) html += '</div></div>';
                    currentFeat = item.feature_key;
                    html += `<div class="feature-section"><div class="feature-header"><div style="display: flex; align-items: center; flex: 1;"><span class="feat-key">${{item.feature_key}}</span><span class="feat-title">${{escapeHtml(item.feature_summary)}}</span></div><div class="feat-meta">${{item.feature_status}} | ${{item.feature_assignee || '未分配'}}</div></div><div class="epics-container">`;
                }}
                
                const statusClass = 'status-' + item.epic_status.toLowerCase().replace(/\\s+/g, '-');
                const descHtml = item.epic_desc ? `<div class="epic-desc">${{escapeHtml(item.epic_desc.substring(0, 200))}}${{item.epic_desc.length > 200 ? '...' : ''}}</div>` : '';
                const startHtml = item.plan_start !== '-' ? `<div class="detail-item"><span class="detail-label">Plan Start</span><span class="detail-value">${{item.plan_start}}</span></div>` : '';
                const endHtml = item.plan_end !== '-' ? `<div class="detail-item"><span class="detail-label">Plan End</span><span class="detail-value">${{item.plan_end}}</span></div>` : '';
                const scopeHtml = item.epic_scope !== '-' ? `<div class="detail-item"><span class="detail-label">Scope</span><span class="detail-value">${{escapeHtml(item.epic_scope)}}</span></div>` : '';
                
                html += `<div class="epic-card"><div class="epic-header"><div class="epic-key-project"><span class="epic-key">${{item.epic_key}}</span><span class="epic-project">${{item.epic_project}}</span></div><span class="status ${{statusClass}}">${{item.epic_status}}</span></div><div class="epic-title">${{escapeHtml(item.epic_summary)}}</div>${{descHtml}}<div class="epic-details"><div class="detail-item"><span class="detail-label">负责人</span><span class="detail-value">${{item.epic_assignee}}</span></div>${{startHtml}}${{endHtml}}<div class="detail-item"><span class="detail-label">创建时间</span><span class="detail-value">${{item.epic_created}}</span></div>${{scopeHtml}}</div></div>`;
            }});
            
            if (currentFeat) html += '</div></div>';
            if (currentInit) html += '</div>';
            
            container.innerHTML = html;
            renderPagination(totalPages);
        }}
        
        function renderPagination(totalPages) {{
            const controls = document.getElementById('pageControls');
            if (totalPages <= 1) {{ controls.innerHTML = ''; return; }}
            
            let html = `<button class="page-btn" onclick="goToPage(${{currentPage - 1}})" ${{currentPage === 1 ? 'disabled' : ''}}>上一页</button>`;
            
            const maxButtons = 5;
            let startPage = Math.max(1, currentPage - Math.floor(maxButtons / 2));
            let endPage = Math.min(totalPages, startPage + maxButtons - 1);
            if (endPage - startPage < maxButtons - 1) startPage = Math.max(1, endPage - maxButtons + 1);
            
            if (startPage > 1) {{
                html += `<button class="page-btn" onclick="goToPage(1)">1</button>`;
                if (startPage > 2) html += `<span style="padding: 0 5px;">...</span>`;
            }}
            
            for (let i = startPage; i <= endPage; i++) {{
                html += `<button class="page-btn ${{i === currentPage ? 'active' : ''}}" onclick="goToPage(${{i}})">${{i}}</button>`;
            }}
            
            if (endPage < totalPages) {{
                if (endPage < totalPages - 1) html += `<span style="padding: 0 5px;">...</span>`;
                html += `<button class="page-btn" onclick="goToPage(${{totalPages}})">${{totalPages}}</button>`;
            }}
            
            html += `<button class="page-btn" onclick="goToPage(${{currentPage + 1}})" ${{currentPage === totalPages ? 'disabled' : ''}}>下一页</button>`;
            controls.innerHTML = html;
        }}
        
        function goToPage(page) {{
            const totalPages = Math.ceil(filteredData.length / pageSize);
            if (page < 1 || page > totalPages) return;
            currentPage = page;
            renderContent();
            window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}
    </script>
</body>
</html>'''

# 保存 HTML
html_path = f"{OUTPUT_DIR}/fy26_paged_epic_report_{DATE_STR}.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_template)

print(f"✅ HTML 报告已生成: {html_path}")

# 生成 CSV
csv_path = f"{OUTPUT_DIR}/fy26_paged_epic_report_{DATE_STR}.csv"
with open(csv_path, "w", encoding="utf-8-sig") as f:
    f.write("Initiative Key,Initiative Summary,Initiative Status,Initiative Assignee,Feature Key,Feature Summary,Feature Status,Feature Assignee,Epic Key,Epic Summary,Epic Project,Epic Status,Epic Assignee,Epic Created,Epic Updated,Plan Start,Plan End,Epic Scope,Epic Description\n")
    for item in epic_hierarchy:
        desc = item['epic_desc'].replace('"', '""')
        scope = item['epic_scope'].replace('"', '""')
        f.write(f'"{item["initiative_key"]}","{item["initiative_summary"]}","{item["initiative_status"]}","{item["initiative_assignee"]}","{item["feature_key"]}","{item["feature_summary"]}","{item["feature_status"]}","{item["feature_assignee"]}","{item["epic_key"]}","{item["epic_summary"]}","{item["epic_project"]}","{item["epic_status"]}","{item["epic_assignee"]}","{item["epic_created"]}","{item["epic_updated"]}","{item["plan_start"]}","{item["plan_end"]}","{scope}","{desc}"\n')

print(f"✅ CSV 报告已生成: {csv_path}")

PYTHON_REPORT

echo ""
echo "📁 生成的文件:"
ls -lh "$OUTPUT_DIR"/fy26_paged_*"${DATE_STR}".*