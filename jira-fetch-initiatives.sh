#!/bin/bash
# Jira Initiative-Feature-Epic 层级数据抓取脚本
# 针对项目: CNTD, CNTEST, CNENG, CNINFA, CNCA, CPR, EPCH, CNCRM, CNDIN, SWMP, CDM, CMDM, CNSCM, OF, CNRTPRJ, CSCPVT, CNPMO, CYBERPJT

source /Users/admin/.openclaw/workspace/.jira-config
source /Users/admin/.openclaw/workspace/.jira-projects

# 输出目录
OUTPUT_DIR="/Users/admin/.openclaw/workspace/jira-reports"
mkdir -p "$OUTPUT_DIR"

# 获取当前日期
DATE_STR=$(date +%Y%m%d)

echo "🚀 开始抓取 Initiative-Feature-Epic 层级数据..."
echo "目标项目: ${#PROJECT_KEYS[@]} 个"
echo ""

# Step 1: 抓取所有 Initiatives (Issue Type = Initiative)
echo "📋 Step 1: 抓取 Initiatives..."

# 构建 JQL 查询
JQL_INITIATIVES="project in ($PROJECT_KEYS_JQL) AND issuetype = Initiative ORDER BY updated DESC"

curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -G "${JIRA_BASE_URL}/rest/api/3/search" \
  --data-urlencode "jql=$JQL_INITIATIVES" \
  --data-urlencode "maxResults=100" \
  --data-urlencode "fields=key,summary,description,status,assignee,created,updated,issuelinks" \
  > "$OUTPUT_DIR/initiatives_raw_${DATE_STR}.json"

INITIATIVE_COUNT=$(cat "$OUTPUT_DIR/initiatives_raw_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('total', 0))")
echo "  ✓ 找到 $INITIATIVE_COUNT 个 Initiatives"

# Step 2: 解析并构建层级关系
echo ""
echo "📊 Step 2: 解析层级关系并生成 CSV..."

python3 << 'PYTHON_SCRIPT'
import json
import csv
import sys
import re
from datetime import datetime

OUTPUT_DIR = "/Users/admin/.openclaw/workspace/jira-reports"
DATE_STR = datetime.now().strftime("%Y%m%d")

# 读取 initiatives 数据
with open(f"{OUTPUT_DIR}/initiatives_raw_{DATE_STR}.json", "r") as f:
    data = json.load(f)

initiatives = data.get("issues", [])

# 准备 CSV 数据
csv_rows = []
csv_rows.append([
    "Initiative Key",
    "Initiative Summary", 
    "Initiative Status",
    "Initiative Description",
    "Feature Keys",
    "Feature Count",
    "Epic Keys",
    "Epic Count",
    "Last Updated"
])

for initiative in initiatives:
    init_key = initiative["key"]
    init_fields = initiative["fields"]
    init_summary = init_fields.get("summary", "")
    init_status = init_fields.get("status", {}).get("name", "")
    init_updated = init_fields.get("updated", "")
    
    # 提取 description (处理 Atlassian Document Format)
    description = ""
    desc_field = init_fields.get("description")
    if desc_field:
        if isinstance(desc_field, dict):
            # ADF 格式，提取文本
            def extract_text_adf(node):
                texts = []
                if isinstance(node, dict):
                    if node.get("type") == "text":
                        texts.append(node.get("text", ""))
                    for child in node.get("content", []):
                        texts.extend(extract_text_adf(child))
                elif isinstance(node, list):
                    for item in node:
                        texts.extend(extract_text_adf(item))
                return texts
            description = " ".join(extract_text_adf(desc_field))
        else:
            description = str(desc_field)
    
    # 清理 description (移除多余空白)
    description = re.sub(r'\s+', ' ', description).strip()
    
    # 获取关联的 Features (通过 issuelinks)
    feature_keys = []
    epic_keys = []
    
    links = init_fields.get("issuelinks", [])
    for link in links:
        link_type = link.get("type", {}).get("name", "")
        # 检查是否是 "is parent of" 或类似关系
        if "outwardIssue" in link:
            linked_issue = link["outwardIssue"]
            linked_key = linked_issue["key"]
            linked_type = linked_issue.get("fields", {}).get("issuetype", {}).get("name", "")
            if linked_type == "Feature":
                feature_keys.append(linked_key)
        elif "inwardIssue" in link:
            linked_issue = link["inwardIssue"]
            linked_key = linked_issue["key"]
            linked_type = linked_issue.get("fields", {}).get("issuetype", {}).get("name", "")
            if linked_type == "Feature":
                feature_keys.append(linked_key)
    
    # 去重
    feature_keys = list(set(feature_keys))
    
    csv_rows.append([
        init_key,
        init_summary,
        init_status,
        description,
        ", ".join(feature_keys) if feature_keys else "",
        len(feature_keys),
        "",  # Epic keys (需要额外查询)
        "",  # Epic count
        init_updated
    ])

# 写入 CSV
csv_path = f"{OUTPUT_DIR}/initiatives_summary_{DATE_STR}.csv"
with open(csv_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerows(csv_rows)

print(f"  ✓ CSV 文件已生成: {csv_path}")
print(f"  ✓ 共 {len(initiatives)} 个 Initiatives")

# 同时生成 JSON 方便后续处理
json_path = f"{OUTPUT_DIR}/initiatives_summary_{DATE_STR}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump({
        "generated_at": datetime.now().isoformat(),
        "total_initiatives": len(initiatives),
        "initiatives": [
            {
                "key": row[0],
                "summary": row[1],
                "status": row[2],
                "description": row[3],
                "features": row[4],
                "feature_count": row[5],
                "last_updated": row[8]
            }
            for row in csv_rows[1:]  # 跳过表头
        ]
    }, f, indent=2, ensure_ascii=False)

print(f"  ✓ JSON 文件已生成: {json_path}")
PYTHON_SCRIPT

echo ""
echo "✅ 数据抓取完成！"
echo ""
echo "📁 输出文件:"
ls -lh "$OUTPUT_DIR"/*"${DATE_STR}"*
