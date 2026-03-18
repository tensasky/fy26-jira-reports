#!/bin/bash
# 飞书通知脚本（简化版）
# 实际使用时需要配置飞书机器人webhook

MESSAGE="$1"
USER_ID="ou_40ced1776aaa261aed192a6246ffd252"
LOG_FILE="/Users/admin/.openclaw/logs/notify.log"

# 记录到日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] To $USER_ID: $MESSAGE" >> "$LOG_FILE"

# TODO: 配置飞书机器人后取消下面的注释
# WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/xxxx"
# curl -s -X POST "$WEBHOOK_URL" \
#     -H "Content-Type: application/json" \
#     -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$MESSAGE\"}}" \
#     >> "$LOG_FILE" 2>&1

echo "Notification logged: $MESSAGE"
