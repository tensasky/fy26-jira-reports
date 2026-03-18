#!/bin/bash

# Moonshot Token 用量查询并发送到飞书
# 这个脚本由 cron 每6小时调用一次

WORKSPACE="/Users/admin/.openclaw/workspace"
SCRIPT_DIR="$WORKSPACE/scripts"

# 加载 API Key（从环境变量或 .env 文件）
if [ -f "$WORKSPACE/.env" ]; then
    export $(grep -v '^#' "$WORKSPACE/.env" | xargs)
fi

API_KEY="${MOONSHOT_API_KEY:-}"

if [ -z "$API_KEY" ]; then
    echo "错误: 未设置 MOONSHOT_API_KEY"
    exit 1
fi

# 查询余额
echo "查询 Moonshot 余额..."
RESPONSE=$(curl -s -X GET "https://api.moonshot.cn/v1/users/me/balance" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json")

# 使用 Python 解析 JSON
if command -v python3 &> /dev/null; then
    AVAILABLE=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('available_balance',0))")
    TOTAL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('total_balance',0))")
    GRANTED=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('granted_balance',0))")
    TOPPED_UP=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('topped_up_balance',0))")
else
    echo "错误: 需要 Python3 来解析 JSON"
    exit 1
fi

AVAILABLE=${AVAILABLE:-0}
TOTAL=${TOTAL:-0}
GRANTED=${GRANTED:-0}
TOPPED_UP=${TOPPED_UP:-0}

# 计算使用率
if [ "$TOTAL" -gt 0 ]; then
    USED=$((TOTAL - AVAILABLE))
    USAGE_RATE=$(python3 -c "print(f'{($USED/$TOTAL)*100:.1f}')")
else
    USED=0
    USAGE_RATE=0
fi

# 格式化数字
format_number() {
    python3 -c "print(f'{int('$1'):,}')"
}

CURRENT_TIME=$(date '+%Y-%m-%d %H:%M')

# 确定状态图标和消息
if (( $(echo "$USAGE_RATE > 90" | bc -l 2>/dev/null || python3 -c "print(1 if float('$USAGE_RATE') > 90 else 0)") )); then
    STATUS_ICON="🚨"
    STATUS_MSG="余额严重不足！请及时充值"
elif (( $(echo "$USAGE_RATE > 70" | bc -l 2>/dev/null || python3 -c "print(1 if float('$USAGE_RATE') > 70 else 0)") )); then
    STATUS_ICON="⚠️"
    STATUS_MSG="余额尚可，请注意使用"
else
    STATUS_ICON="✅"
    STATUS_MSG="余额充足"
fi

# 构建飞书消息内容
MESSAGE="🌙 **Moonshot Token 用量报告**

📅 查询时间: $CURRENT_TIME

💰 **余额情况**
• 可用余额: $(format_number $AVAILABLE) tokens
• 总余额: $(format_number $TOTAL) tokens  
• 已使用: $(format_number $USED) tokens ($USAGE_RATE%)

📊 **余额构成**
• 赠送余额: $(format_number $GRANTED) tokens
• 充值余额: $(format_number $TOPPED_UP) tokens

$STATUS_ICON **状态**: $STATUS_MSG

---
⏰ 每6小时自动更新"

# 通过 openclaw 的 message 工具发送（这里使用 echo，实际需要通过 openclaw 发送）
echo "$MESSAGE"

# 保存历史记录
HISTORY_FILE="$WORKSPACE/moonshot-balance-history.csv"
echo "$CURRENT_TIME,$AVAILABLE,$TOTAL,$USED,$USAGE_RATE,$GRANTED,$TOPPED_UP" >> "$HISTORY_FILE"

# 保留最近200条记录
tail -n 200 "$HISTORY_FILE" > "$HISTORY_FILE.tmp" && mv "$HISTORY_FILE.tmp" "$HISTORY_FILE"

echo ""
echo "报告已生成，准备发送到飞书..."
