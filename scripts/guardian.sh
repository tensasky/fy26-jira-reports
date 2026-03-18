#!/bin/bash
# OpenClaw Guardian - 看门狗脚本
# 每2分钟检查一次主agent状态

LOG_FILE="/Users/admin/.openclaw/logs/guardian.log"
OPENCLAW_BIN="/opt/homebrew/bin/openclaw"
NOTIFY_SCRIPT="/Users/admin/.openclaw/scripts/notify-feishu.sh"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

# 检查openclaw进程是否在运行
check_openclaw() {
    if pgrep -f "openclaw gateway" > /dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# 检查agent是否响应（通过检查最近的心跳时间）
check_agent_responsive() {
    # 检查主session文件的最后更新时间
    SESSION_FILE="/Users/admin/.openclaw/agents/main/sessions/c692e3d4-44d2-4df6-91a8-054373d21488.jsonl"
    
    if [ -f "$SESSION_FILE" ]; then
        # 获取文件最后修改时间（秒）
        LAST_MODIFIED=$(stat -f %m "$SESSION_FILE" 2>/dev/null || echo "0")
        CURRENT_TIME=$(date +%s)
        TIME_DIFF=$((CURRENT_TIME - LAST_MODIFIED))
        
        # 如果超过5分钟没有更新，认为无响应
        if [ $TIME_DIFF -gt 300 ]; then
            log "WARNING: Agent not responsive for ${TIME_DIFF}s"
            return 1
        fi
    fi
    return 0
}

# 发送飞书通知
notify_user() {
    local message="$1"
    log "NOTIFY: $message"
    
    # 如果有通知脚本，调用它
    if [ -x "$NOTIFY_SCRIPT" ]; then
        "$NOTIFY_SCRIPT" "$message" &
    fi
}

# 重启openclaw
restart_openclaw() {
    log "RESTART: Attempting to restart OpenClaw..."
    
    # 先尝试优雅停止
    pkill -f "openclaw gateway" 2>/dev/null
    sleep 2
    
    # 强制停止如果还在运行
    pkill -9 -f "openclaw gateway" 2>/dev/null
    sleep 1
    
    # 重新启动
    if [ -x "$OPENCLAW_BIN" ]; then
        nohup "$OPENCLAW_BIN" gateway start > /dev/null 2>&1 &
        log "RESTART: OpenClaw restarted with PID $!"
        notify_user "🔄 OpenClaw已自动重启（检测到无响应）"
        return 0
    else
        log "ERROR: OpenClaw binary not found at $OPENCLAW_BIN"
        return 1
    fi
}

# 主逻辑
main() {
    log "--- Guardian check started ---"
    
    # 1. 检查进程是否存在
    if ! check_openclaw; then
        log "ALERT: OpenClaw process not running!"
        notify_user "🚨 OpenClaw进程不存在，正在自动重启..."
        restart_openclaw
        exit 0
    fi
    
    # 2. 检查是否响应
    if ! check_agent_responsive; then
        log "ALERT: Agent not responsive!"
        notify_user "⚠️ Agent无响应超过5分钟，正在自动重启..."
        restart_openclaw
        exit 0
    fi
    
    log "OK: Agent is healthy"
}

# 运行主逻辑
main
