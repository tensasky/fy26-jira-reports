#!/bin/bash
# OpenClaw 紧急重启脚本
# 一键重启OpenClaw gateway

LOG_FILE="/Users/admin/.openclaw/logs/emergency-restart.log"

echo "========================================" | tee -a "$LOG_FILE"
echo "OpenClaw Emergency Restart - $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"

# 1. 检查当前状态
echo "[1/4] 检查当前状态..." | tee -a "$LOG_FILE"
if pgrep -f "openclaw gateway" > /dev/null 2>&1; then
    echo "  OpenClaw正在运行，准备重启..." | tee -a "$LOG_FILE"
else
    echo "  OpenClaw未运行，准备启动..." | tee -a "$LOG_FILE"
fi

# 2. 优雅停止
echo "[2/4] 停止OpenClaw..." | tee -a "$LOG_FILE"
pkill -f "openclaw gateway" 2>/dev/null
sleep 2
pkill -9 -f "openclaw gateway" 2>/dev/null
echo "  已停止" | tee -a "$LOG_FILE"

# 3. 清理临时文件
echo "[3/4] 清理临时文件..." | tee -a "$LOG_FILE"
rm -f /Users/admin/.openclaw/workspace/.openclaw.lock 2>/dev/null
echo "  完成" | tee -a "$LOG_FILE"

# 4. 重新启动
echo "[4/4] 启动OpenClaw..." | tee -a "$LOG_FILE"
if command -v openclaw &> /dev/null; then
    nohup openclaw gateway start > /dev/null 2>&1 &
    sleep 3
    
    # 验证启动
    if pgrep -f "openclaw gateway" > /dev/null 2>&1; then
        echo "✅ OpenClaw启动成功！PID: $(pgrep -f 'openclaw gateway')" | tee -a "$LOG_FILE"
        echo "" | tee -a "$LOG_FILE"
        echo "💡 提示：Agent可能需要1-2分钟才能完全恢复响应" | tee -a "$LOG_FILE"
        echo "   请稍后再发送测试消息" | tee -a "$LOG_FILE"
    else
        echo "❌ OpenClaw启动失败！" | tee -a "$LOG_FILE"
        exit 1
    fi
else
    echo "❌ 找不到openclaw命令" | tee -a "$LOG_FILE"
    exit 1
fi

echo "" | tee -a "$LOG_FILE"
echo "重启完成时间: $(date)" | tee -a "$LOG_FILE"
echo "========================================" | tee -a "$LOG_FILE"
