#!/bin/bash
# 抓取 CNTIN 项目中 FY26_INIT 的 Initiatives 及其层级，生成 Epic 汇总报告

source /Users/admin/.openclaw/workspace/.jira-config

OUTPUT_DIR="/Users/admin/.openclaw/workspace/jira-reports"
mkdir -p "$OUTPUT_DIR"
DATE_STR=$(date +%Y%m%d_%H%M)

echo "🚀 开始抓取 CNTIN 项目 FY26_INIT Initiatives 及其层级..."
echo ""

# Step 1: 抓取 FY26_INIT 的 Initiatives
echo "📋 Step 1: 抓取 FY26_INIT Initiatives..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "project = CNTIN AND issuetype = Initiative AND labels = FY26_INIT ORDER BY key ASC",
    "maxResults": 100,
    "fields": ["key", "summary", "description", "status", "assignee", "created", "updated", "labels"]
  }' > "$OUTPUT_DIR/cntin_fy26_initiatives_${DATE_STR}.json"

INIT_COUNT=$(cat "$OUTPUT_DIR/cntin_fy26_initiatives_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $INIT_COUNT 个 FY26_INIT Initiatives"

if [ "$INIT_COUNT" -eq "0" ]; then
    echo "❌ 没有找到 FY26_INIT Initiatives"
    exit 1
fi

# 获取 Initiative keys
INIT_KEYS=$(cat "$OUTPUT_DIR/cntin_fy26_initiatives_${DATE_STR}.json" | python3 -c "
import json,sys
data=json.load(sys.stdin)
issues=data.get('issues',[])
keys=[i['key'] for i in issues]
print(','.join(f'\"{k}\"' for k in keys))
")

# Step 2: 抓取关联的 Features (通过 parent 或 Epic Link)
echo ""
echo "📋 Step 2: 抓取关联的 Features..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d "{
    \"jql\": \"project = CNTIN AND issuetype = Feature AND parent in ($INIT_KEYS) ORDER BY key ASC\",
    \"maxResults\": 200,
    \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"parent\"]
  }" > "$OUTPUT_DIR/cntin_fy26_features_${DATE_STR}.json"

FEAT_COUNT=$(cat "$OUTPUT_DIR/cntin_fy26_features_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $FEAT_COUNT 个 Features"

# 获取 Feature keys
FEAT_KEYS=$(cat "$OUTPUT_DIR/cntin_fy26_features_${DATE_STR}.json" | python3 -c "
import json,sys
data=json.load(sys.stdin)
issues=data.get('issues',[])
keys=[i['key'] for i in issues]
print(','.join(f'\"{k}\"' for k in keys)) if keys else print('\"NONE\"')
")

# Step 3: 抓取关联的 Epics (通过 parent 或 Epic Link)
echo ""
echo "📋 Step 3: 抓取关联的 Epics..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d "{
    \"jql\": \"project = CNTIN AND issuetype = Epic AND (parent in ($FEAT_KEYS) OR \"Epic Link\" in ($FEAT_KEYS)) ORDER BY key ASC\",
    \"maxResults\": 500,
    \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"parent\", \"customfield_10014\", \"issuelinks\"]
  }" > "$OUTPUT_DIR/cntin_fy26_epics_${DATE_STR}.json"

EPIC_COUNT=$(cat "$OUTPUT_DIR/cntin_fy26_epics_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $EPIC_COUNT 个 Epics"

echo ""
echo "📊 生成 Epic 汇总 HTML 报告..."

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
with open(f"{OUTPUT_DIR}/cntin_fy26_initiatives_{DATE_STR}.json", "r") as f:
    init_data = json.load(f)
with open(f"{OUTPUT_DIR}/cntin_fy26_features_{DATE_STR}.json", "r") as f:
    feat_data = json.load(f)
with open(f"{OUTPUT_DIR}/cntin_fy26_epics_{DATE_STR}.json", "r") as f:
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

# Initiative -> Feature
for f in features:
    f_key = f["key"]
    parent = f["fields"].get("parent")
    if parent and parent["key"] in init_by_key:
        init_to_feats[parent["key"]].append(f_key)

# Feature -> Epic
for e in epics:
    e_key = e["key"]
    fields = e["fields"]
    parent = fields.get("parent")
    if parent and parent["key"] in feat_by_key:
        feat_to_epics[parent["key"]].append(e_key)
    # 检查 Epic Link
    epic_link = fields.get("customfield_10014")
    if epic_link and epic_link in feat_by_key:
        feat_to_epics[epic_link].append(e_key)

# 为每个 Epic 建立完整层级路径
epic_hierarchy = []
for epic_key, epic in epic_by_key.items():
    epic_fields = epic["fields"]
    
    # 找到所属的 Feature
    feat_key = None
    feat_summary = ""
    for fk, epics_list in feat_to_epics.items():
        if epic_key in epics_list:
            feat_key = fk
            feat_summary = feat_by_key.get(fk, {}).get("fields", {}).get("summary", "")
            break
    
    # 找到所属的 Initiative
    init_key = None
    init_summary = ""
    if feat_key:
        for ik, feats_list in init_to_feats.items():
            if feat_key in feats_list:
                init_key = ik
                init_summary = init_by_key.get(ik, {}).get("fields", {}).get("summary", "")
                break
    
    epic_hierarchy.append({
        "epic_key": epic_key,
        "epic_summary": epic_fields.get("summary", ""),
        "epic_status": epic_fields.get("status", {}).get("name", ""),
        "epic_desc": clean_text(extract_text_from_adf(epic_fields.get("description"))),
        "feature_key": feat_key or "",
        "feature_summary": feat_summary,
        "initiative_key": init_key or "",
        "initiative_summary": init_summary
    })

# 按 Initiative -> Feature -> Epic 排序
epic_hierarchy.sort(key=lambda x: (x["initiative_key"] or "ZZZ", x["feature_key"] or "ZZZ", x["epic_key"]))

# 生成 HTML 报告
html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26_INIT Epic 汇总报告</title>
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
        
        .hierarchy-section {{
            background: white;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
        }}
        
        .initiative-header {{
            background: #E31937;
            color: white;
            padding: 20px 25px;
            font-size: 1.2em;
            font-weight: 600;
        }}
        .initiative-header .init-key {{
            opacity: 0.8;
            font-size: 0.85em;
            font-weight: 400;
            font-family: monospace;
            margin-right: 10px;
        }}
        
        .feature-section {{
            border-bottom: 1px solid #eee;
        }}
        .feature-section:last-child {{ border-bottom: none; }}
        
        .feature-header {{
            background: #fafafa;
            padding: 15px 25px;
            font-weight: 600;
            color: #444;
            border-left: 4px solid #ff6b7a;
        }}
        .feature-header .feat-key {{
            color: #999;
            font-size: 0.85em;
            font-family: monospace;
            margin-right: 10px;
        }}
        
        .epics-table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .epics-table th {{
            background: #f5f5f5;
            padding: 12px 15px;
            text-align: left;
            font-weight: 600;
            color: #666;
            font-size: 0.9em;
            border-bottom: 2px solid #eee;
        }}
        .epics-table td {{
            padding: 15px;
            border-bottom: 1px solid #f0f0f0;
            vertical-align: top;
        }}
        .epics-table tr:hover {{ background: #fafafa; }}
        
        .epic-key {{
            font-family: monospace;
            font-size: 0.9em;
            color: #666;
            background: #f5f5f5;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .epic-title {{
            font-weight: 500;
            color: #333;
            margin-bottom: 5px;
        }}
        .epic-desc {{
            font-size: 0.9em;
            color: #666;
            line-height: 1.5;
        }}
        
        .status {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 500;
        }}
        .status-new {{ background: #e3f2fd; color: #1976d2; }}
        .status-in-progress {{ background: #fff3e0; color: #f57c00; }}
        .status-done {{ background: #e8f5e9; color: #388e3c; }}
        .status-closed {{ background: #e8f5e9; color: #388e3c; }}
        .status-execution {{ background: #fff3e0; color: #f57c00; }}
        .status-deferred {{ background: #fce4ec; color: #c2185b; }}
        .status-cancelled {{ background: #f5f5f5; color: #757575; }}
        .status-backlog {{ background: #f3e5f5; color: #7b1fa2; }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #999;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .header {{ padding: 25px; }}
            .header h1 {{ font-size: 1.8em; }}
            .summary {{ padding: 20px; }}
            .container {{ padding: 0 20px 20px; }}
            .epics-table {{ font-size: 0.9em; }}
            .epics-table th, .epics-table td {{ padding: 10px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>FY26_INIT Epic 汇总报告</h1>
        <div class="subtitle">CNTIN 项目 | Initiative → Feature → Epic 层级</div>
        <div class="date">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>
    
    <div class="summary">
        <div class="stat-card">
            <div class="number">{len(initiatives)}</div>
            <div class="label">FY26_INIT Initiatives</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(features)}</div>
            <div class="label">Features</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(epics)}</div>
            <div class="label">Epics</div>
        </div>
    </div>
    
    <div class="container">
'''

# 按 Initiative 分组显示
current_init = None
current_feat = None

for item in epic_hierarchy:
    # 新的 Initiative
    if item["initiative_key"] != current_init:
        if current_init:
            html_content += '</div></div>'  # 关闭上一个 feature-section 和 hierarchy-section
        current_init = item["initiative_key"]
        current_feat = None
        
        html_content += f'''
        <div class="hierarchy-section">
            <div class="initiative-header">
                <span class="init-key">{item["initiative_key"]}</span>
                {item["initiative_summary"]}
            </div>
'''
    
    # 新的 Feature
    if item["feature_key"] != current_feat:
        if current_feat:
            html_content += '</table></div>'  # 关闭上一个 table 和 feature-section
        current_feat = item["feature_key"]
        
        html_content += f'''
            <div class="feature-section">
                <div class="feature-header">
                    <span class="feat-key">{item["feature_key"]}</span>
                    {item["feature_summary"]}
                </div>
                <table class="epics-table">
                    <thead>
                        <tr>
                            <th style="width: 120px;">Epic Key</th>
                            <th>Epic 标题 & 描述</th>
                            <th style="width: 100px;">状态</th>
                        </tr>
                    </thead>
                    <tbody>
'''
    
    # Epic 行
    status_class = f"status-{item['epic_status'].lower().replace(' ', '-')}"
    html_content += f'''
                        <tr>
                            <td><span class="epic-key">{item["epic_key"]}</span></td>
                            <td>
                                <div class="epic-title">{item["epic_summary"]}</div>
                                {f'<div class="epic-desc">{item["epic_desc"][:150]}{"..." if len(item["epic_desc"]) > 150 else ""}</div>' if item["epic_desc"] else ''}
                            </td>
                            <td><span class="status {status_class}">{item["epic_status"]}</span></td>
                        </tr>
'''

# 关闭最后一个表格和 div
if current_feat:
    html_content += '</tbody></table></div>'
if current_init:
    html_content += '</div>'

html_content += '''
    </div>
    
    <div class="footer">
        报告由 OpenClaw 自动生成 | lululemon Jira 数据
    </div>
</body>
</html>
'''

# 保存 HTML
html_path = f"{OUTPUT_DIR}/cntin_fy26_epic_summary_{DATE_STR}.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ Epic 汇总报告已生成: {html_path}")
print(f"   包含 {len(initiatives)} Initiatives, {len(features)} Features, {len(epics)} Epics")

PYTHON_SCRIPT

echo ""
echo "📁 生成的文件:"
ls -lh "$OUTPUT_DIR"/cntin_fy26_*"${DATE_STR}"*.html