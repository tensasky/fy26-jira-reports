#!/bin/bash
# 抓取带有 FY26 标签的 Initiatives 及其层级数据

source /Users/admin/.openclaw/workspace/.jira-config

OUTPUT_DIR="/Users/admin/.openclaw/workspace/jira-reports"
mkdir -p "$OUTPUT_DIR"
DATE_STR=$(date +%Y%m%d_%H%M)

PROJECTS="CNTD,CNTEST,CNENG,CNINFA,CNCA,CPR,EPCH,CNCRM,CNDIN,SWMP,CDM,CMDM,CNSCM,CNRTPRJ,CSCPVT,CNPMO,CYBERPJT"

echo "🚀 开始抓取 FY26 Initiatives 及其层级数据..."
echo ""

# 抓取带有 FY26 标签的 Initiatives
echo "📋 抓取 FY26 Initiatives..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d "{
    \"jql\": \"project in ($PROJECTS) AND issuetype = Initiative AND labels = FY26 ORDER BY project ASC, key ASC\",
    \"maxResults\": 500,
    \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"issuelinks\", \"project\", \"labels\"]
  }" > "$OUTPUT_DIR/fy26_initiatives_${DATE_STR}.json"

INIT_COUNT=$(cat "$OUTPUT_DIR/fy26_initiatives_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $INIT_COUNT 个 FY26 Initiatives"

if [ "$INIT_COUNT" -eq "0" ]; then
    echo ""
    echo "⚠️ 没有找到 FY26 标签的 Initiatives"
    echo "尝试搜索其他可能的标签格式..."
    
    # 尝试搜索包含 FY26 的标签
    curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
      -H "Accept: application/json" \
      -X POST \
      "${JIRA_BASE_URL}/rest/api/3/search/jql" \
      -H "Content-Type: application/json" \
      -d "{
        \"jql\": \"project in ($PROJECTS) AND issuetype = Initiative AND labels in (FY26, fy26, Fy26, FY-26, FY_26) ORDER BY key ASC\",
        \"maxResults\": 100,
        \"fields\": [\"key\", \"summary\", \"labels\"]
      }" > "$OUTPUT_DIR/fy26_initiatives_alt_${DATE_STR}.json"
    
    ALT_COUNT=$(cat "$OUTPUT_DIR/fy26_initiatives_alt_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
    echo "  找到 $ALT_COUNT 个（使用备选标签格式）"
fi

# 获取 Initiative keys 用于后续查询
INIT_KEYS=$(cat "$OUTPUT_DIR/fy26_initiatives_${DATE_STR}.json" | python3 -c "
import json,sys
data=json.load(sys.stdin)
issues=data.get('issues',[])
keys=[i['key'] for i in issues]
print(','.join(keys)) if keys else print('')
")

if [ -n "$INIT_KEYS" ]; then
    echo ""
    echo "📋 抓取关联的 Features..."
    curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
      -H "Accept: application/json" \
      -X POST \
      "${JIRA_BASE_URL}/rest/api/3/search/jql" \
      -H "Content-Type: application/json" \
      -d "{
        \"jql\": \"project in ($PROJECTS) AND issuetype = Feature AND (parent in ($INIT_KEYS) OR \"Epic Link\" in ($INIT_KEYS)) ORDER BY key ASC\",
        \"maxResults\": 500,
        \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"issuelinks\", \"parent\", \"project\", \"customfield_10014\"]
      }" > "$OUTPUT_DIR/fy26_features_${DATE_STR}.json"
    
    FEAT_COUNT=$(cat "$OUTPUT_DIR/fy26_features_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
    echo "  ✓ 找到 $FEAT_COUNT 个 Features"
    
    echo ""
    echo "📋 抓取关联的 Epics..."
    curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
      -H "Accept: application/json" \
      -X POST \
      "${JIRA_BASE_URL}/rest/api/3/search/jql" \
      -H "Content-Type: application/json" \
      -d "{
        \"jql\": \"project in ($PROJECTS) AND issuetype = Epic ORDER BY key ASC\",
        \"maxResults\": 1000,
        \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"issuelinks\", \"parent\", \"project\", \"customfield_10014\"]
      }" > "$OUTPUT_DIR/fy26_epics_${DATE_STR}.json"
    
    EPIC_COUNT=$(cat "$OUTPUT_DIR/fy26_epics_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
    echo "  ✓ 找到 $EPIC_COUNT 个 Epics"
fi

echo ""
echo "📊 生成 HTML 报告..."

python3 << PYTHON_SCRIPT
import json
import re
from datetime import datetime
from collections import defaultdict

OUTPUT_DIR = "/Users/admin/.openclaw/workspace/jira-reports"
DATE_STR = "$DATE_STR"

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

# 加载数据
with open(f"{OUTPUT_DIR}/fy26_initiatives_{DATE_STR}.json", "r") as f:
    init_data = json.load(f)

initiatives = init_data.get("issues", [])

if not initiatives:
    # 尝试备选文件
    try:
        with open(f"{OUTPUT_DIR}/fy26_initiatives_alt_{DATE_STR}.json", "r") as f:
            init_data = json.load(f)
        initiatives = init_data.get("issues", [])
    except:
        pass

features = []
epics = []

if initiatives:
    try:
        with open(f"{OUTPUT_DIR}/fy26_features_{DATE_STR}.json", "r") as f:
            feat_data = json.load(f)
        features = feat_data.get("issues", [])
    except:
        pass
    
    try:
        with open(f"{OUTPUT_DIR}/fy26_epics_{DATE_STR}.json", "r") as f:
            epic_data = json.load(f)
        epics = epic_data.get("issues", [])
    except:
        pass

# 建立索引
init_by_key = {i["key"]: i for i in initiatives}
feat_by_key = {f["key"]: f for f in features}
epic_by_key = {e["key"]: e for e in epics}

# 按项目分组
init_by_project = defaultdict(list)
for i in initiatives:
    proj = i["fields"]["project"]["key"]
    init_by_project[proj].append(i)

# 建立层级关系
init_to_feats = defaultdict(list)
feat_to_epics = defaultdict(list)

# 解析 Feature 关系
for f in features:
    f_key = f["key"]
    fields = f["fields"]
    parent = fields.get("parent")
    if parent and parent["key"] in init_by_key:
        init_to_feats[parent["key"]].append(f_key)
    # 检查 Epic Link
    epic_link = fields.get("customfield_10014")
    if epic_link and epic_link in init_by_key:
        init_to_feats[epic_link].append(f_key)

# 解析 Epic 关系
for e in epics:
    e_key = e["key"]
    fields = e["fields"]
    parent = fields.get("parent")
    if parent and parent["key"] in feat_by_key:
        feat_to_epics[parent["key"]].append(e_key)
    epic_link = fields.get("customfield_10014")
    if epic_link and epic_link in feat_by_key:
        feat_to_epics[epic_link].append(e_key)

# 生成 HTML
html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26 Initiative 层级报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #E31937 0%, #c41230 100%);
            color: white;
            padding: 40px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; font-weight: 300; }}
        .header .subtitle {{ opacity: 0.9; font-size: 1.1em; }}
        .header .date {{ opacity: 0.7; margin-top: 10px; font-size: 0.9em; }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #E31937;
        }}
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: 700;
            color: #E31937;
            margin-bottom: 5px;
        }}
        .stat-card .label {{ color: #666; font-size: 0.95em; }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 40px 40px;
        }}
        
        .project-section {{
            background: white;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
        }}
        .project-header {{
            background: #fafafa;
            padding: 20px 25px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .project-header h2 {{
            font-size: 1.3em;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .project-header .badge {{
            background: #E31937;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        
        .initiative {{
            border-bottom: 1px solid #f0f0f0;
            padding: 20px 25px;
        }}
        .initiative:last-child {{ border-bottom: none; }}
        
        .init-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}
        .init-title {{
            font-size: 1.1em;
            font-weight: 600;
            color: #1a1a1a;
            display: flex;
            align-items: center;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .init-key {{
            background: #f0f0f0;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            color: #666;
            font-family: monospace;
        }}
        .fy26-badge {{
            background: #E31937;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.75em;
            font-weight: 600;
        }}
        .status {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 500;
        }}
        .status-new {{ background: #e3f2fd; color: #1976d2; }}
        .status-in-progress {{ background: #fff3e0; color: #f57c00; }}
        .status-done {{ background: #e8f5e9; color: #388e3c; }}
        .status-closed {{ background: #e8f5e9; color: #388e3c; }}
        .status-deferred {{ background: #fce4ec; color: #c2185b; }}
        .status-cancelled {{ background: #f5f5f5; color: #757575; }}
        .status-to-do {{ background: #f5f5f5; color: #757575; }}
        .status-backlog {{ background: #f3e5f5; color: #7b1fa2; }}
        .status-execution {{ background: #fff3e0; color: #f57c00; }}
        .status-discovery {{ background: #f3e5f5; color: #7b1fa2; }}
        
        .init-desc {{
            color: #555;
            margin-bottom: 15px;
            line-height: 1.7;
        }}
        
        .features {{
            margin-left: 20px;
            padding-left: 20px;
            border-left: 3px solid #e0e0e0;
        }}
        .feature {{
            background: #fafafa;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }}
        .feature-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }}
        .feature-title {{
            font-weight: 500;
            color: #444;
        }}
        .feature-key {{
            font-size: 0.8em;
            color: #999;
            font-family: monospace;
        }}
        
        .epics {{
            margin-top: 8px;
            margin-left: 15px;
        }}
        .epic {{
            font-size: 0.9em;
            color: #666;
            padding: 4px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .epic::before {{
            content: "└─";
            color: #ccc;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #999;
            font-size: 0.9em;
        }}
        
        .no-data {{
            text-align: center;
            padding: 60px 40px;
            color: #999;
        }}
        .no-data h3 {{
            font-size: 1.5em;
            margin-bottom: 10px;
            color: #666;
        }}
        
        @media (max-width: 768px) {{
            .header {{ padding: 25px; }}
            .header h1 {{ font-size: 1.8em; }}
            .summary {{ padding: 20px; }}
            .container {{ padding: 0 20px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>FY26 Initiative 层级报告</h1>
        <div class="subtitle">17个项目 | FY26 标签筛选</div>
        <div class="date">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>
'''

if not initiatives:
    html_content += '''
    <div class="no-data">
        <h3>📭 没有找到 FY26 标签的 Initiatives</h3>
        <p>请检查标签名称是否正确，或联系项目管理员确认 FY26 标签的使用情况。</p>
    </div>
'''
else:
    html_content += f'''
    <div class="summary">
        <div class="stat-card">
            <div class="number">{len(initiatives)}</div>
            <div class="label">FY26 Initiatives</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(features)}</div>
            <div class="label">Features</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(epics)}</div>
            <div class="label">Epics</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(init_by_project)}</div>
            <div class="label">项目数</div>
        </div>
    </div>
    
    <div class="container">
'''
    
    # 按项目生成内容
    for proj in sorted(init_by_project.keys()):
        proj_inits = init_by_project[proj]
        
        html_content += f'''
        <div class="project-section">
            <div class="project-header">
                <h2>📁 {proj}</h2>
                <span class="badge">{len(proj_inits)} Initiatives</span>
            </div>
'''
        
        for init in proj_inits:
            init_key = init["key"]
            fields = init["fields"]
            summary = fields.get("summary", "")
            status = fields.get("status", {}).get("name", "New")
            desc = clean_text(extract_text_from_adf(fields.get("description")))
            labels = fields.get("labels", [])
            
            status_class = f"status-{status.lower().replace(' ', '-')}"
            
            html_content += f'''
            <div class="initiative">
                <div class="init-header">
                    <div class="init-title">
                        <span class="init-key">{init_key}</span>
                        {summary}
                        <span class="fy26-badge">FY26</span>
                    </div>
                    <span class="status {status_class}">{status}</span>
                </div>
'''
            
            if desc:
                html_content += f'<div class="init-desc">{desc[:250]}{"..." if len(desc) > 250 else ""}</div>'
            
            # 添加 Features
            related_feats = init_to_feats.get(init_key, [])
            if related_feats:
                html_content += '<div class="features">'
                for feat_key in related_feats[:15]:  # 最多显示15个
                    if feat_key in feat_by_key:
                        feat = feat_by_key[feat_key]
                        feat_fields = feat["fields"]
                        feat_summary = feat_fields.get("summary", "")
                        
                        html_content += f'''
                <div class="feature">
                    <div class="feature-header">
                        <span class="feature-title">{feat_summary}</span>
                        <span class="feature-key">{feat_key}</span>
                    </div>
'''
                        # 添加 Epics
                        related_epics = feat_to_epics.get(feat_key, [])
                        if related_epics:
                            html_content += '<div class="epics">'
                            for epic_key in related_epics[:8]:
                                if epic_key in epic_by_key:
                                    epic = epic_by_key[epic_key]
                                    epic_summary = epic["fields"].get("summary", "")
                                    html_content += f'<div class="epic">{epic_key}: {epic_summary[:50]}{"..." if len(epic_summary) > 50 else ""}</div>'
                            if len(related_epics) > 8:
                                html_content += f'<div class="epic">... 还有 {len(related_epics)-8} 个 Epics</div>'
                            html_content += '</div>'
                        
                        html_content += '</div>'
                
                if len(related_feats) > 15:
                    html_content += f'<div style="text-align:center;color:#999;padding:10px;">... 还有 {len(related_feats)-15} 个 Features</div>'
                
                html_content += '</div>'
            
            html_content += '</div>'
        
        html_content += '</div>'
    
    html_content += '</div>'

html_content += '''
    <div class="footer">
        报告由 OpenClaw 自动生成 | lululemon Jira 数据
    </div>
</body>
</html>
'''

# 保存 HTML
html_path = f"{OUTPUT_DIR}/fy26_initiative_report_{DATE_STR}.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ HTML 报告已生成: {html_path}")
if initiatives:
    print(f"   包含 {len(initiatives)} FY26 Initiatives, {len(features)} Features, {len(epics)} Epics")
    print(f"   覆盖 {len(init_by_project)} 个项目")
else:
    print("   没有找到 FY26 标签的 Initiatives")

PYTHON_SCRIPT

echo ""
echo "📁 生成的文件:"
ls -lh "$OUTPUT_DIR"/fy26_*"${DATE_STR}"*.html 2>/dev/null || echo "   (无 HTML 文件)"