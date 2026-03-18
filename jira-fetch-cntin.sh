#!/bin/bash
# Jira Initiative-Feature-Epic 层级数据抓取脚本 (CNTIN 项目)
# 使用新的 Jira API v3

source /Users/admin/.openclaw/workspace/.jira-config

# 输出目录
OUTPUT_DIR="/Users/admin/.openclaw/workspace/jira-reports"
mkdir -p "$OUTPUT_DIR"

# 获取当前日期
DATE_STR=$(date +%Y%m%d_%H%M)

echo "🚀 开始抓取 CNTIN 项目的 Initiative-Feature-Epic 层级数据..."
echo ""

# Step 1: 抓取所有 Initiatives
echo "📋 Step 1: 抓取 Initiatives..."

curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "project = CNTIN AND issuetype = Initiative ORDER BY key ASC",
    "maxResults": 100,
    "fields": ["key", "summary", "description", "status", "assignee", "created", "updated", "issuelinks", "customfield_10014"]
  }' > "$OUTPUT_DIR/cntin_initiatives_${DATE_STR}.json"

INITIATIVE_COUNT=$(cat "$OUTPUT_DIR/cntin_initiatives_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $INITIATIVE_COUNT 个 Initiatives"

# Step 2: 抓取所有 Features
echo ""
echo "📋 Step 2: 抓取 Features..."

curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "project = CNTIN AND issuetype = Feature ORDER BY key ASC",
    "maxResults": 200,
    "fields": ["key", "summary", "description", "status", "assignee", "created", "updated", "issuelinks", "parent"]
  }' > "$OUTPUT_DIR/cntin_features_${DATE_STR}.json"

FEATURE_COUNT=$(cat "$OUTPUT_DIR/cntin_features_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $FEATURE_COUNT 个 Features"

# Step 3: 抓取所有 Epics
echo ""
echo "📋 Step 3: 抓取 Epics..."

curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "project = CNTIN AND issuetype = Epic ORDER BY key ASC",
    "maxResults": 300,
    "fields": ["key", "summary", "description", "status", "assignee", "created", "updated", "issuelinks", "parent", "customfield_10014"]
  }' > "$OUTPUT_DIR/cntin_epics_${DATE_STR}.json"

EPIC_COUNT=$(cat "$OUTPUT_DIR/cntin_epics_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $EPIC_COUNT 个 Epics"

# Step 4: 解析层级关系并生成 CSV
echo ""
echo "📊 Step 4: 解析层级关系并生成 CSV..."

python3 << PYTHON_SCRIPT
import json
import csv
import re
from datetime import datetime
from collections import defaultdict

OUTPUT_DIR = "/Users/admin/.openclaw/workspace/jira-reports"
DATE_STR = "$DATE_STR"

def extract_text_from_adf(doc):
    """从 Atlassian Document Format 中提取纯文本"""
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
    """清理文本，移除多余空白"""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

# 加载数据
with open(f"{OUTPUT_DIR}/cntin_initiatives_{DATE_STR}.json", "r") as f:
    initiatives_data = json.load(f)

with open(f"{OUTPUT_DIR}/cntin_features_{DATE_STR}.json", "r") as f:
    features_data = json.load(f)

with open(f"{OUTPUT_DIR}/cntin_epics_{DATE_STR}.json", "r") as f:
    epics_data = json.load(f)

# 建立索引
initiatives = {i["key"]: i for i in initiatives_data.get("issues", [])}
features = {f["key"]: f for f in features_data.get("issues", [])}
epics = {e["key"]: e for e in epics_data.get("issues", [])}

# 建立层级关系
# Initiative -> Features
initiative_to_features = defaultdict(list)
# Feature -> Epics
feature_to_epics = defaultdict(list)

# 解析 Features 的 parent 关系
for f_key, f_data in features.items():
    fields = f_data["fields"]
    # 检查 parent 字段
    parent = fields.get("parent")
    if parent:
        parent_key = parent.get("key")
        if parent_key and parent_key in initiatives:
            initiative_to_features[parent_key].append(f_key)
    
    # 检查 issuelinks
    for link in fields.get("issuelinks", []):
        link_type = link.get("type", {}).get("name", "")
        if "parent" in link_type.lower() or "child" in link_type.lower():
            if "inwardIssue" in link:
                linked_key = link["inwardIssue"]["key"]
                if linked_key in initiatives:
                    initiative_to_features[linked_key].append(f_key)

# 解析 Epics 的 parent 关系
for e_key, e_data in epics.items():
    fields = e_data["fields"]
    # 检查 parent 字段
    parent = fields.get("parent")
    if parent:
        parent_key = parent.get("key")
        if parent_key and parent_key in features:
            feature_to_epics[parent_key].append(e_key)
    
    # 检查 Epic Link 字段 (customfield_10014)
    epic_link = fields.get("customfield_10014")
    if epic_link and epic_link in features:
        feature_to_epics[epic_link].append(e_key)

print(f"  建立了 {len(initiative_to_features)} 个 Initiative -> Features 关系")
print(f"  建立了 {len(feature_to_epics)} 个 Feature -> Epics 关系")

# 生成 CSV
csv_rows = []
csv_rows.append([
    "Initiative Key",
    "Initiative Summary",
    "Initiative Status",
    "Initiative Description",
    "Feature Keys",
    "Feature Summaries",
    "Feature Count",
    "Epic Keys",
    "Epic Count",
    "Last Updated"
])

for init_key in sorted(initiatives.keys()):
    init_data = initiatives[init_key]
    init_fields = init_data["fields"]
    
    init_summary = init_fields.get("summary", "")
    init_status = init_fields.get("status", {}).get("name", "")
    init_updated = init_fields.get("updated", "")
    
    # 提取 description
    description = extract_text_from_adf(init_fields.get("description"))
    description = clean_text(description)
    
    # 获取关联的 Features
    related_features = initiative_to_features.get(init_key, [])
    feature_keys_str = ", ".join(related_features) if related_features else ""
    
    # 获取 Feature 的 summaries
    feature_summaries = []
    for fk in related_features:
        if fk in features:
            feature_summaries.append(features[fk]["fields"].get("summary", ""))
    feature_summaries_str = " | ".join(feature_summaries) if feature_summaries else ""
    
    # 获取所有相关的 Epics
    all_epics = []
    for fk in related_features:
        all_epics.extend(feature_to_epics.get(fk, []))
    epic_keys_str = ", ".join(all_epics) if all_epics else ""
    
    csv_rows.append([
        init_key,
        init_summary,
        init_status,
        description,
        feature_keys_str,
        feature_summaries_str,
        len(related_features),
        epic_keys_str,
        len(all_epics),
        init_updated
    ])

# 写入 CSV
csv_path = f"{OUTPUT_DIR}/cntin_initiative_summary_{DATE_STR}.csv"
with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
    writer = csv.writer(f)
    writer.writerows(csv_rows)

print(f"\\n  ✓ CSV 文件已生成: {csv_path}")
print(f"  ✓ 共 {len(initiatives)} 个 Initiatives")
print(f"  ✓ 共 {len(features)} 个 Features")
print(f"  ✓ 共 {len(epics)} 个 Epics")

# 同时生成详细的 JSON
json_path = f"{OUTPUT_DIR}/cntin_hierarchy_{DATE_STR}.json"
hierarchy = {
    "generated_at": datetime.now().isoformat(),
    "project": "CNTIN",
    "summary": {
        "initiatives_count": len(initiatives),
        "features_count": len(features),
        "epics_count": len(epics)
    },
    "initiatives": []
}

for init_key in sorted(initiatives.keys()):
    init_data = initiatives[init_key]
    init_fields = init_data["fields"]
    
    related_features = initiative_to_features.get(init_key, [])
    features_list = []
    
    for fk in related_features:
        if fk in features:
            f_data = features[fk]
            f_fields = f_data["fields"]
            related_epics = feature_to_epics.get(fk, [])
            
            epics_list = []
            for ek in related_epics:
                if ek in epics:
                    e_data = epics[ek]
                    e_fields = e_data["fields"]
                    epics_list.append({
                        "key": ek,
                        "summary": e_fields.get("summary", ""),
                        "status": e_fields.get("status", {}).get("name", "")
                    })
            
            features_list.append({
                "key": fk,
                "summary": f_fields.get("summary", ""),
                "status": f_fields.get("status", {}).get("name", ""),
                "epics": epics_list
            })
    
    hierarchy["initiatives"].append({
        "key": init_key,
        "summary": init_fields.get("summary", ""),
        "status": init_fields.get("status", {}).get("name", ""),
        "description": clean_text(extract_text_from_adf(init_fields.get("description"))),
        "features": features_list,
        "feature_count": len(features_list),
        "epic_count": sum(len(f["epics"]) for f in features_list)
    })

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(hierarchy, f, indent=2, ensure_ascii=False)

print(f"  ✓ JSON 层级文件已生成: {json_path}")

PYTHON_SCRIPT

echo ""
echo "✅ 数据抓取完成！"
echo ""
echo "📁 输出文件:"
ls -lh "$OUTPUT_DIR"/*"${DATE_STR}"*
