#!/bin/bash
# 抓取 Initiatives 和 Features

cd /Users/admin/.openclaw/workspace/fy26_pmo

source /Users/admin/.openclaw/workspace/.jira-config

curl_jira() {
    local jql="$1"
    local fields="$2"
    local output_file="$3"
    
    # 添加延迟避免限流
    sleep 1
    
    curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
        -H "Accept: application/json" \
        -H "Content-Type: application/json" \
        -X POST \
        "${JIRA_BASE_URL}/rest/api/3/search/jql" \
        -d "{
            \"jql\": \"$jql\",
            \"maxResults\": 1000,
            \"fields\": [$fields]
        }" > "$output_file"
}

echo "📋 抓取 FY26_INIT Initiatives..."
curl_jira "project = CNTIN AND issuetype = Initiative AND labels = 'FY26_INIT' ORDER BY key ASC" \
    '"key","summary","description","status","assignee","created","updated","labels","customfield_14024"' \
    "step2_initiatives.json"

init_count=$(python3 -c "import json; print(len(json.load(open('step2_initiatives.json')).get('issues', [])))")
echo "  ✓ $init_count Initiatives"

echo ""
echo "📋 从 Initiatives 抓取 Features..."

# 获取所有Initiative keys
init_keys=$(python3 -c "
import json
data = json.load(open('step2_initiatives.json'))
keys = [i['key'] for i in data.get('issues', [])]
print(' '.join(keys))
")

echo '{"issues":[]}' > step3_features_merged.json

for init_key in $init_keys; do
    echo "  抓取 $init_key 的子Features..."
    curl_jira "project = CNTIN AND issuetype = Feature AND parent = $init_key ORDER BY key ASC" \
        '"key","summary","description","status","assignee","created","updated","parent","labels","customfield_14024"' \
        "step3_${init_key}_features.json"
    
    python3 << PYEOF
import json
try:
    with open('step3_features_merged.json', 'r') as f:
        merged = json.load(f)
    with open("step3_${init_key}_features.json", 'r') as f:
        data = json.load(f)
    merged['issues'].extend(data.get('issues', []))
    with open('step3_features_merged.json', 'w') as f:
        json.dump(merged, f)
except:
    pass
PYEOF
done

# 去重
python3 << PYEOF
import json
with open('step3_features_merged.json', 'r') as f:
    data = json.load(f)
seen = set()
unique = []
for feat in data.get('issues', []):
    key = feat['key']
    if key not in seen:
        seen.add(key)
        unique.append(feat)
data['issues'] = unique
with open('step3_features_merged.json', 'w') as f:
    json.dump(data, f)
print(f"  ✓ 去重后 {len(unique)} 个唯一Features")
PYEOF

echo ""
echo "✅ 数据抓取完成!"
