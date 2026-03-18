#!/bin/bash

# Moonshot Token 余额查询脚本
# 每6小时查询一次并通过飞书发送报告

# 从环境变量获取 API Key
API_KEY="${MOONSHOT_API_KEY:-}"

if [ -z "$API_KEY" ]; then
    echo "错误: 未设置 MOONSHOT_API_KEY 环境变量"
    exit 1
fi

# 查询余额
echo "正在查询 Moonshot 余额..."
RESPONSE=$(curl -s -X GET "https://api.moonshot.cn/v1/users/me/balance" \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" 2>/dev/null)

# 检查 curl 是否成功
if [ $? -ne 0 ]; then
    echo "错误: 无法连接到 Moonshot API"
    exit 1
fi

# 解析 JSON 响应
AVAILABLE=$(echo "$RESPONSE" | grep -o '"available_balance":[0-9]*' | cut -d':' -f2)
TOTAL=$(echo "$RESPONSE" | grep -o '"total_balance":[0-9]*' | cut -d':' -f2)
GRANTED=$(echo "$RESPONSE" | grep -o '"granted_balance":[0-9]*' | cut -d':' -f2)
TOPPED_UP=$(echo "$RESPONSE" | grep -o '"topped_up_balance":[0-9]*' | cut -d':' -f2)

# 如果没有获取到数据，尝试使用 Python 解析
if [ -z "$AVAILABLE" ] && command -v python3 &> /dev/null; then
    AVAILABLE=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('available_balance',0))" 2>/dev/null)
    TOTAL=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('total_balance',0))" 2>/dev/null)
    GRANTED=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('granted_balance',0))" 2>/dev/null)
    TOPPED_UP=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('topped_up_balance',0))" 2>/dev/null)
fi

# 默认值
AVAILABLE=${AVAILABLE:-0}
TOTAL=${TOTAL:-0}
GRANTED=${GRANTED:-0}
TOPPED_UP=${TOPPED_UP:-0}

# 计算使用率
if [ "$TOTAL" -gt 0 ]; then
    USED=$((TOTAL - AVAILABLE))
    USAGE_RATE=$(awk "BEGIN {printf \"%.1f\", ($USED/$TOTAL)*100}")
else
    USAGE_RATE=0
fi

# 格式化数字
format_number() {
    echo "$1" | awk '{printf "%'\''d\n", $1}'
}

# 当前时间
CURRENT_TIME=$(date '+%Y-%m-%d %H:%M:%S')

# 输出报告
echo ""
echo "=================================="
echo "🌙 Moonshot Token 用量报告"
echo "=================================="
echo "查询时间: $CURRENT_TIME"
echo ""
echo "💰 余额情况:"
echo "  • 可用余额: $(format_number $AVAILABLE) tokens"
echo "  • 总余额: $(format_number $TOTAL) tokens"
echo "  • 已使用: $(format_number $USED) tokens ($USAGE_RATE%)"
echo ""
echo "📊 余额构成:"
echo "  • 赠送余额: $(format_number $GRANTED) tokens"
echo "  • 充值余额: $(format_number $TOPPED_UP) tokens"
echo ""

# 状态判断
if (( $(echo "$USAGE_RATE > 90" | bc -l 2>/dev/null || echo "0") )); then
    echo "⚠️ 状态: 余额不足！请及时充值"
elif (( $(echo "$USAGE_RATE > 70" | bc -l 2>/dev/null || echo "0") )); then
    echo "⚡ 状态: 余额尚可，请注意使用"
else
    echo "✅ 状态: 余额充足"
fi

echo "=================================="

# 保存到历史记录文件
HISTORY_FILE="$HOME/.moonshot_balance_history"
echo "$CURRENT_TIME,$AVAILABLE,$TOTAL,$USED,$USAGE_RATE" >> "$HISTORY_FILE"

# 保留最近100条记录
if [ -f "$HISTORY_FILE" ]; then
    tail -n 100 "$HISTORY_FILE" > "$HISTORY_FILE.tmp" && mv "$HISTORY_FILE.tmp" "$HISTORY_FILE"
fi
