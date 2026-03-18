#!/bin/bash
# 抓取 FY26_INIT 层级并生成带详细信息的报告（红色系背景）

source /Users/admin/.openclaw/workspace/.jira-config

OUTPUT_DIR="/Users/admin/.openclaw/workspace/jira-reports"
mkdir -p "$OUTPUT_DIR"
DATE_STR=$(date +%Y%m%d_%H%M)

PROJECTS="CNTD,CNTEST,CNENG,CNINFA,CNCA,CPR,EPCH,CNCRM,CNDIN,SWMP,CDM,CMDM,CNSCM,CNRTPRJ,CSCPVT,CNPMO,CYBERPJT"

echo "🚀 开始抓取 FY26_INIT 层级（带详细信息）..."
echo ""

# Step 1: 抓取 CNTIN FY26_INIT Initiatives
echo "📋 Step 1: 抓取 CNTIN FY26_INIT Initiatives..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "project = CNTIN AND issuetype = Initiative AND labels = FY26_INIT ORDER BY key ASC",
    "maxResults": 100,
    "fields": ["key", "summary", "description", "status", "assignee", "created", "updated", "labels", "customfield_10014"]
  }' > "$OUTPUT_DIR/red_step1_init_${DATE_STR}.json"

INIT_COUNT=$(cat "$OUTPUT_DIR/red_step1_init_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $INIT_COUNT 个 Initiatives"

INIT_KEYS=$(cat "$OUTPUT_DIR/red_step1_init_${DATE_STR}.json" | python3 -c "
import json,sys
data=json.load(sys.stdin)
issues=data.get('issues',[])
keys=[i['key'] for i in issues]
print(','.join(keys))
")

# Step 2: 抓取 CNTIN Features
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
    \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"parent\", \"issuelinks\", \"customfield_10014\"]
  }" > "$OUTPUT_DIR/red_step2_feat_${DATE_STR}.json"

FEAT_COUNT=$(cat "$OUTPUT_DIR/red_step2_feat_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $FEAT_COUNT 个 Features"

# Step 3: 提取 Epic keys
echo ""
echo "📋 Step 3: 提取 Epic keys..."

python3 << PYTHON_SCRIPT
import json
from collections import defaultdict

OUTPUT_DIR = "/Users/admin/.openclaw/workspace/jira-reports"
DATE_STR = "$DATE_STR"

with open(f"{OUTPUT_DIR}/red_step2_feat_{DATE_STR}.json", "r") as f:
    feat_data = json.load(f)

features = feat_data.get("issues", [])
feat_by_key = {f["key"]: f for f in features}

# 提取 Epic keys
epic_keys_set = set()
feat_to_epic_keys = defaultdict(list)

for f in features:
    f_key = f["key"]
    links = f["fields"].get("issuelinks", [])
    
    for link in links:
        if "inwardIssue" in link:
            linked = link["inwardIssue"]
            linked_key = linked["key"]
            linked_type = linked.get("fields", {}).get("issuetype", {}).get("name", "")
            if linked_type == "Epic":
                epic_keys_set.add(linked_key)
                feat_to_epic_keys[f_key].append(linked_key)
        
        if "outwardIssue" in link:
            linked = link["outwardIssue"]
            linked_key = linked["key"]
            linked_type = linked.get("fields", {}).get("issuetype", {}).get("name", "")
            if linked_type == "Epic":
                epic_keys_set.add(linked_key)
                feat_to_epic_keys[f_key].append(linked_key)

print(f"提取到 {len(epic_keys_set)} 个 Epic keys")
print(f"建立了 {len(feat_to_epic_keys)} 个 Feature -> Epic 关系")

with open(f"{OUTPUT_DIR}/red_epic_keys_{DATE_STR}.txt", "w") as f:
    f.write(','.join(sorted(epic_keys_set)))

PYTHON_SCRIPT

EPIC_KEYS=$(cat "$OUTPUT_DIR/red_epic_keys_${DATE_STR}.txt")

if [ -z "$EPIC_KEYS" ]; then
    echo "❌ 没有找到 Epic keys"
    exit 1
fi

EPIC_COUNT=$(echo "$EPIC_KEYS" | tr ',' '\n' | wc -l)
echo "  提取到 $EPIC_COUNT 个 Epic keys"

# Step 4: 抓取 Epics 详细信息（包含时间、scope、负责人等）
echo ""
echo "📋 Step 4: 抓取 Epics 详细信息..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d "{
    \"jql\": \"key in ($EPIC_KEYS) ORDER BY project ASC, key ASC\",
    \"maxResults\": 1000,
    \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"project\", \"customfield_10014\", \"customfield_10015\", \"customfield_10020\", \"customfield_10030\", \"labels\", \"components\", \"fixVersions\"]
  }" > "$OUTPUT_DIR/red_step4_epics_${DATE_STR}.json"

FETCHED_EPIC_COUNT=$(cat "$OUTPUT_DIR/red_step4_epics_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 抓到 $FETCHED_EPIC_COUNT 个 Epics 详细信息"

echo ""
echo "📊 生成带详细信息的 HTML 报告（红色系背景）..."

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
    feat_assignee = feat_fields.get("assignee", {}).get("displayName", "")
    
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
            init_assignee = init_fields.get("assignee", {}).get("displayName", "")
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
        epic_assignee = epic_fields.get("assignee", {}).get("displayName", "未分配")
        epic_created = format_date(epic_fields.get("created", ""))
        epic_updated = format_date(epic_fields.get("updated", ""))
        
        # 尝试获取开始/结束日期（自定义字段）
        epic_start = format_date(epic_fields.get("customfield_10014", ""))
        epic_end = format_date(epic_fields.get("customfield_10015", ""))
        
        # 获取 Scope（从 labels、components 或描述中提取）
        labels = epic_fields.get("labels", [])
        components = [c.get("name", "") for c in epic_fields.get("components", [])]
        scope = ", ".join(labels + components) if (labels or components) else ""
        
        epic_hierarchy.append({
            "epic_key": epic_key,
            "epic_summary": epic_fields.get("summary", ""),
            "epic_status": epic_fields.get("status", {}).get("name", ""),
            "epic_desc": clean_text(extract_text_from_adf(epic_fields.get("description"))),
            "epic_project": epic_project,
            "epic_assignee": epic_assignee,
            "epic_created": epic_created,
            "epic_updated": epic_updated,
            "epic_start": epic_start,
            "epic_end": epic_end,
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
for item in epic_hierarchy:
    init_epic_count[item["initiative_key"]] += 1

# 生成 HTML 报告（红色系背景）
html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FY26_INIT Epic 详细汇总报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #fafafa;
            color: #333;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #8B0000 0%, #A52A2A 100%);
            color: white;
            padding: 40px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; font-weight: 300; }}
        .header .subtitle {{ opacity: 0.9; font-size: 1.1em; }}
        .header .date {{ opacity: 0.7; margin-top: 10px; font-size: 0.9em; }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            max-width: 1600px;
            margin: 0 auto;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #8B0000;
        }}
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: 700;
            color: #8B0000;
            margin-bottom: 5px;
        }}
        .stat-card .label {{ color: #666; font-size: 0.95em; }}
        
        .container {{
            max-width: 1600px;
            margin: 0 auto;
            padding: 0 40px 40px;
        }}
        
        /* Initiative - 深红色背景 */
        .initiative-section {{
            background: #8B0000;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 4px 12px rgba(139,0,0,0.3);
            overflow: hidden;
        }}
        .initiative-header {{
            background: #8B0000;
            color: white;
            padding: 20px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .initiative-header .init-key {{
            background: rgba(255,255,255,0.2);
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 0.85em;
            font-family: monospace;
            margin-right: 10px;
        }}
        .initiative-header .init-title {{
            font-size: 1.2em;
            font-weight: 600;
            flex: 1;
        }}
        .initiative-header .init-meta {{
            text-align: right;
            font-size: 0.85em;
            opacity: 0.9;
        }}
        .initiative-header .epic-count {{
            background: rgba(255,255,255,0.25);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: 600;
            margin-left: 15px;
        }}
        
        /* Feature - 浅红色背景 */
        .feature-section {{
            background: #CD5C5C;
            margin: 2px 0;
        }}
        .feature-header {{
            background: #CD5C5C;
            color: white;
            padding: 15px 25px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-left: 5px solid #8B0000;
        }}
        .feature-header .feat-key {{
            background: rgba(255,255,255,0.2);
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.8em;
            font-family: monospace;
            margin-right: 10px;
        }}
        .feature-header .feat-title {{
            font-weight: 600;
            flex: 1;
        }}
        .feature-header .feat-meta {{
            text-align: right;
            font-size: 0.8em;
            opacity: 0.9;
        }}
        
        /* Epic - 淡红色/粉红色背景 */
        .epics-container {{
            background: #FFE4E1;
            padding: 15px 25px;
        }}
        
        .epic-card {{
            background: white;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 12px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-left: 4px solid #CD5C5C;
        }}
        .epic-card:last-child {{ margin-bottom: 0; }}
        
        .epic-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 10px;
        }}
        .epic-key-project {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .epic-key {{
            font-family: monospace;
            font-size: 0.9em;
            color: #8B0000;
            background: #FFE4E1;
            padding: 3px 10px;
            border-radius: 4px;
            font-weight: 600;
        }}
        .epic-project {{
            font-size: 0.75em;
            color: white;
            background: #8B0000;
            padding: 3px 10px;
            border-radius: 4px;
            font-weight: 500;
        }}
        .epic-title {{
            font-size: 1.1em;
            font-weight: 600;
            color: #333;
            margin-bottom: 8px;
        }}
        .epic-desc {{
            font-size: 0.9em;
            color: #666;
            line-height: 1.5;
            margin-bottom: 12px;
        }}
        
        .epic-details {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            background: #f9f9f9;
            padding: 12px;
            border-radius: 6px;
            font-size: 0.85em;
        }}
        .detail-item {{
            display: flex;
            flex-direction: column;
        }}
        .detail-label {{
            color: #999;
            font-size: 0.8em;
            margin-bottom: 2px;
        }}
        .detail-value {{
            color: #333;
            font-weight: 500;
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
        .status-discovery {{ background: #f3e5f5; color: #7b1fa2; }}
        
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
            .epic-details {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>FY26_INIT Epic 详细汇总报告</h1>
        <div class="subtitle">CNTIN Initiative → CNTIN Feature → 其他项目 Epic</div>
        <div class="date">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>
    
    <div class="summary">
        <div class="stat-card">
            <div class="number">{len(initiatives)}</div>
            <div class="label">FY26_INIT Initiatives</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(features)}</div>
            <div class="label">CNTIN Features</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(epic_hierarchy)}</div>
            <div class="label">关联 Epics</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(set(item['epic_project'] for item in epic_hierarchy))}</div>
            <div class="label">涉及项目</div>
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
            html_content += '</div></div></div>'  # 关闭 epics-container, feature-section, initiative-section
        current_init = item["initiative_key"]
        current_feat = None
        
        epic_count = init_epic_count.get(current_init, 0)
        
        html_content += f'''
        <div class="initiative-section">
            <div class="initiative-header">
                <div style="display: flex; align-items: center; flex: 1;">
                    <span class="init-key">{item["initiative_key"]}</span>
                    <span class="init-title">{item["initiative_summary"]}</span>
                </div>
                <div class="init-meta">
                    <div>{item["initiative_status"]} | {item["initiative_assignee"] or "未分配"}</div>
                </div>
                <span class="epic-count">{epic_count} Epics</span>
            </div>
'''
    
    # 新的 Feature
    if item["feature_key"] != current_feat:
        if current_feat:
            html_content += '</div></div>'  # 关闭 epics-container, feature-section
        current_feat = item["feature_key"]
        
        html_content += f'''
            <div class="feature-section">
                <div class="feature-header">
                    <div style="display: flex; align-items: center; flex: 1;">
                        <span class="feat-key">{item["feature_key"]}</span>
                        <span class="feat-title">{item["feature_summary"]}</span>
                    </div>
                    <div class="feat-meta">
                        {item["feature_status"]} | {item["feature_assignee"] or "未分配"}
                    </div>
                </div>
                <div class="epics-container">
'''
    
    # Epic 卡片
    status_class = f"status-{item['epic_status'].lower().replace(' ', '-')}"
    
    html_content += f'''
                    <div class="epic-card">
                        <div class="epic-header">
                            <div class="epic-key-project">
                                <span class="epic-key">{item["epic_key"]}</span>
                                <span class="epic-project">{item["epic_project"]}</span>
                            </div>
                            <span class="status {status_class}">{item["epic_status"]}</span>
                        </div>
                        <div class="epic-title">{item["epic_summary"]}</div>
                        {f'<div class="epic-desc">{item["epic_desc"][:200]}{"..." if len(item["epic_desc"]) > 200 else ""}</div>' if item["epic_desc"] else ''}
                        <div class="epic-details">
                            <div class="detail-item">
                                <span class="detail-label">负责人</span>
                                <span class="detail-value">{item["epic_assignee"]}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">创建时间</span>
                                <span class="detail-value">{item["epic_created"]}</span>
                            </div>
                            <div class="detail-item">
                                <span class="detail-label">更新时间</span>
                                <span class="detail-value">{item["epic_updated"]}</span>
                            </div>
                            {f'<div class="detail-item"><span class="detail-label">开始日期</span><span class="detail-value">{item["epic_start"]}</span></div>' if item["epic_start"] else ''}
                            {f'<div class="detail-item"><span class="detail-label">结束日期</span><span class="detail-value">{item["epic_end"]}</span></div>' if item["epic_end"] else ''}
                            {f'<div class="detail-item"><span class="detail-label">Scope</span><span class="detail-value">{item["epic_scope"]}</span></div>' if item["epic_scope"] else ''}
                        </div>
                    </div>
'''

# 关闭最后一个 div
if current_feat:
    html_content += '</div></div>'
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
html_path = f"{OUTPUT_DIR}/fy26_detailed_epic_report_{DATE_STR}.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\\n✅ HTML 报告已生成: {html_path}")

# 生成 CSV
csv_path = f"{OUTPUT_DIR}/fy26_detailed_epic_report_{DATE_STR}.csv"
with open(csv_path, "w", encoding="utf-8-sig") as f:
    f.write("Initiative Key,Initiative Summary,Initiative Status,Initiative Assignee,Feature Key,Feature Summary,Feature Status,Feature Assignee,Epic Key,Epic Summary,Epic Project,Epic Status,Epic Assignee,Epic Created,Epic Updated,Epic Start,Epic End,Epic Scope,Epic Description\\n")
    for item in epic_hierarchy:
        desc = item['epic_desc'].replace('"', '""')
        scope = item['epic_scope'].replace('"', '""')
        f.write(f'"{item["initiative_key"]}","{item["initiative_summary"]}","{item["initiative_status"]}","{item["initiative_assignee"]}","{item["feature_key"]}","{item["feature_summary"]}","{item["feature_status"]}","{item["feature_assignee"]}","{item["epic_key"]}","{item["epic_summary"]}","{item["epic_project"]}","{item["epic_status"]}","{item["epic_assignee"]}","{item["epic_created"]}","{item["epic_updated"]}","{item["epic_start"]}","{item["epic_end"]}","{scope}","{desc}"\\n')

print(f"✅ CSV 报告已生成: {csv_path}")

PYTHON_SCRIPT

echo ""
echo "📁 生成的文件:"
ls -lh "$OUTPUT_DIR"/fy26_detailed_*"${DATE_STR}".*