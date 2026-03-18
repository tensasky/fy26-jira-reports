#!/bin/bash
# 抓取 CNTIN FY26_INIT Initiatives -> Features -> 关联项目的 Epics

source /Users/admin/.openclaw/workspace/.jira-config

OUTPUT_DIR="/Users/admin/.openclaw/workspace/jira-reports"
mkdir -p "$OUTPUT_DIR"
DATE_STR=$(date +%Y%m%d_%H%M)

echo "🚀 开始抓取 CNTIN FY26_INIT 层级（跨项目）..."
echo ""

# Step 1: 抓取 CNTIN 的 FY26_INIT Initiatives
echo "📋 Step 1: 抓取 CNTIN FY26_INIT Initiatives..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "project = CNTIN AND issuetype = Initiative AND labels = FY26_INIT ORDER BY key ASC",
    "maxResults": 100,
    "fields": ["key", "summary", "description", "status", "labels"]
  }' > "$OUTPUT_DIR/cntin_fy26_init_cross_${DATE_STR}.json"

INIT_COUNT=$(cat "$OUTPUT_DIR/cntin_fy26_init_cross_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $INIT_COUNT 个 Initiatives"

# 获取 Initiative keys
INIT_KEYS=$(cat "$OUTPUT_DIR/cntin_fy26_init_cross_${DATE_STR}.json" | python3 -c "
import json,sys
data=json.load(sys.stdin)
issues=data.get('issues',[])
keys=[i['key'] for i in issues]
print(','.join(keys))
")

# Step 2: 抓取 CNTIN 的 Features
echo ""
echo "📋 Step 2: 抓取 CNTIN Features..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d "{
    \"jql\": \"project = CNTIN AND issuetype = Feature AND parent in ($INIT_KEYS) ORDER BY key ASC\",
    \"maxResults\": 500,
    \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"parent\"]
  }" > "$OUTPUT_DIR/cntin_fy26_feat_cross_${DATE_STR}.json"

FEAT_COUNT=$(cat "$OUTPUT_DIR/cntin_fy26_feat_cross_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $FEAT_COUNT 个 Features"

# 获取 Feature keys
FEAT_KEYS=$(cat "$OUTPUT_DIR/cntin_fy26_feat_cross_${DATE_STR}.json" | python3 -c "
import json,sys
data=json.load(sys.stdin)
issues=data.get('issues',[])
keys=[i['key'] for i in issues]
print(','.join(keys)) if keys else print('NONE')
")

if [ "$FEAT_KEYS" = "NONE" ]; then
    echo "❌ 没有找到 Features"
    exit 1
fi

# Step 3: 抓取所有项目的 Epics（通过 Epic Link 关联到 Features）
echo ""
echo "📋 Step 3: 抓取跨项目的 Epics..."

# 先尝试用 Epic Link 字段
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d "{
    \"jql\": \"issuetype = Epic AND \"Epic Link\" in ($FEAT_KEYS) ORDER BY project ASC, key ASC\",
    \"maxResults\": 1000,
    \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"project\", \"customfield_10014\", \"issuelinks\"]
  }" > "$OUTPUT_DIR/cntin_fy26_epics_cross_${DATE_STR}.json"

EPIC_COUNT=$(cat "$OUTPUT_DIR/cntin_fy26_epics_cross_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $EPIC_COUNT 个 Epics（通过 Epic Link）"

# 如果没有找到，尝试通过 issuelinks 查找
if [ "$EPIC_COUNT" -eq "0" ]; then
    echo ""
    echo "📋 尝试通过 Issue Links 查找 Epics..."
    
    # 获取所有项目
    PROJECTS="CNTD,CNTEST,CNENG,CNINFA,CNCA,CPR,EPCH,CNCRM,CNDIN,SWMP,CDM,CMDM,CNSCM,CNRTPRJ,CSCPVT,CNPMO,CYBERPJT"
    
    curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
      -H "Accept: application/json" \
      -X POST \
      "${JIRA_BASE_URL}/rest/api/3/search/jql" \
      -H "Content-Type: application/json" \
      -d "{
        \"jql\": \"project in ($PROJECTS) AND issuetype = Epic ORDER BY key ASC\",
        \"maxResults\": 1000,
        \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"project\", \"issuelinks\"]
      }" > "$OUTPUT_DIR/all_epics_cross_${DATE_STR}.json"
    
    ALL_EPIC_COUNT=$(cat "$OUTPUT_DIR/all_epics_cross_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
    echo "  ✓ 找到 $ALL_EPIC_COUNT 个 Epics（所有项目）"
fi

echo ""
echo "📊 生成跨项目 Epic 汇总 HTML 报告..."

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
with open(f"{OUTPUT_DIR}/cntin_fy26_init_cross_{DATE_STR}.json", "r") as f:
    init_data = json.load(f)
with open(f"{OUTPUT_DIR}/cntin_fy26_feat_cross_{DATE_STR}.json", "r") as f:
    feat_data = json.load(f)

# 尝试加载 Epics
epics = []
try:
    with open(f"{OUTPUT_DIR}/cntin_fy26_epics_cross_{DATE_STR}.json", "r") as f:
        epic_data = json.load(f)
    epics = epic_data.get("issues", [])
except:
    pass

# 如果没有通过 Epic Link 找到，尝试从所有 Epics 中筛选
try:
    with open(f"{OUTPUT_DIR}/all_epics_cross_{DATE_STR}.json", "r") as f:
        all_epic_data = json.load(f)
    all_epics = all_epic_data.get("issues", [])
    
    # 建立 Feature keys 集合
    feat_keys_set = {f["key"] for f in feat_data.get("issues", [])}
    
    # 筛选出与 Features 有关联的 Epics
    linked_epics = []
    for epic in all_epics:
        fields = epic.get("fields", {})
        links = fields.get("issuelinks", [])
        for link in links:
            if "inwardIssue" in link:
                linked_key = link["inwardIssue"]["key"]
                if linked_key in feat_keys_set:
                    linked_epics.append(epic)
                    break
            if "outwardIssue" in link:
                linked_key = link["outwardIssue"]["key"]
                if linked_key in feat_keys_set:
                    linked_epics.append(epic)
                    break
    
    if linked_epics:
        epics = linked_epics
        print(f"通过 Issue Links 找到 {len(epics)} 个关联 Epics")
except Exception as e:
    print(f"筛选 Epics 时出错: {e}")

initiatives = init_data.get("issues", [])
features = feat_data.get("issues", [])

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

# Feature -> Epic（通过 Epic Link）
for e in epics:
    e_key = e["key"]
    fields = e["fields"]
    epic_link = fields.get("customfield_10014")
    if epic_link and epic_link in feat_by_key:
        feat_to_epics[epic_link].append(e_key)

# Feature -> Epic（通过 Issue Links）
for e in epics:
    e_key = e["key"]
    fields = e["fields"]
    links = fields.get("issuelinks", [])
    for link in links:
        if "inwardIssue" in link:
            linked_key = link["inwardIssue"]["key"]
            if linked_key in feat_by_key:
                feat_to_epics[linked_key].append(e_key)
                break
        if "outwardIssue" in link:
            linked_key = link["outwardIssue"]["key"]
            if linked_key in feat_by_key:
                feat_to_epics[linked_key].append(e_key)
                break

print(f"建立了 {len(feat_to_epics)} 个 Feature -> Epic 关系")

# 为每个 Epic 建立完整层级路径
epic_hierarchy = []
for epic_key, epic in epic_by_key.items():
    epic_fields = epic["fields"]
    epic_project = epic_fields.get("project", {}).get("key", "")
    
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
    
    if feat_key:  # 只保留有关联的 Epics
        epic_hierarchy.append({
            "epic_key": epic_key,
            "epic_summary": epic_fields.get("summary", ""),
            "epic_status": epic_fields.get("status", {}).get("name", ""),
            "epic_desc": clean_text(extract_text_from_adf(epic_fields.get("description"))),
            "epic_project": epic_project,
            "feature_key": feat_key,
            "feature_summary": feat_summary,
            "initiative_key": init_key,
            "initiative_summary": init_summary
        })

# 按 Initiative -> Feature -> Epic 排序
epic_hierarchy.sort(key=lambda x: (x["initiative_key"] or "ZZZ", x["feature_key"] or "ZZZ", x["epic_key"]))

print(f"最终报告包含 {len(epic_hierarchy)} 个关联 Epics")

# 生成 HTML 报告
html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26_INIT 跨项目 Epic 汇总报告</title>
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
        .epic-project {{
            font-size: 0.8em;
            color: #999;
            margin-left: 8px;
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
        
        .no-epics {{
            padding: 20px;
            text-align: center;
            color: #999;
            font-style: italic;
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
        <h1>FY26_INIT 跨项目 Epic 汇总报告</h1>
        <div class="subtitle">CNTIN Initiative → Feature → 跨项目 Epic</div>
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
            <div class="number">{len(epic_hierarchy)}</div>
            <div class="label">关联 Epics</div>
        </div>
    </div>
    
    <div class="container">
'''

if not epic_hierarchy:
    html_content += '''
        <div style="text-align: center; padding: 60px; color: #999;">
            <h3>📭 没有找到关联的 Epics</h3>
            <p>Features 与其他项目的 Epics 之间没有建立链接关系</p>
        </div>
'''
else:
    # 按 Initiative 分组显示
    current_init = None
    current_feat = None
    
    for item in epic_hierarchy:
        # 新的 Initiative
        if item["initiative_key"] != current_init:
            if current_init:
                html_content += '</tbody></table></div>'  # 关闭上一个 table 和 feature-section
                html_content += '</div>'  # 关闭 hierarchy-section
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
                html_content += '</tbody></table></div>'  # 关闭上一个 table 和 feature-section
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
                            <th style="width: 140px;">Epic Key</th>
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
                            <td>
                                <span class="epic-key">{item["epic_key"]}</span>
                                <span class="epic-project">{item["epic_project"]}</span>
                            </td>
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
html_path = f"{OUTPUT_DIR}/fy26_cross_project_epic_report_{DATE_STR}.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ 跨项目 Epic 汇总报告已生成: {html_path}")

# 同时生成 CSV 报告
csv_path = f"{OUTPUT_DIR}/fy26_cross_project_epic_report_{DATE_STR}.csv"
with open(csv_path, "w", encoding="utf-8-sig") as f:
    f.write("Initiative Key,Initiative Summary,Feature Key,Feature Summary,Epic Key,Epic Summary,Epic Project,Epic Status,Epic Description\\n")
    for item in epic_hierarchy:
        desc = item['epic_desc'].replace('"', '""')
        f.write(f'"{item["initiative_key"]}","{item["initiative_summary"]}","{item["feature_key"]}","{item["feature_summary"]}","{item["epic_key"]}","{item["epic_summary"]}","{item["epic_project"]}","{item["epic_status"]}","{desc}"\\n')

print(f"✅ CSV 报告已生成: {csv_path}")

PYTHON_SCRIPT

echo ""
echo "📁 生成的文件:"
ls -lh "$OUTPUT_DIR"/fy26_cross_*"${DATE_STR}".* 2>/dev/null || ls -lh "$OUTPUT_DIR"/*"${DATE_STR}"*.html