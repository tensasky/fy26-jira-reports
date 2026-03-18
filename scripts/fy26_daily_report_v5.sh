#!/bin/bash
# FY26_INIT Epic 日报主脚本 v5.0
# 每天执行：全量抓取数据 → 生成报告 → 发送邮件

set -e  # 遇到错误立即退出

WORKSPACE="$HOME/.openclaw/workspace"
LOG_DIR="$WORKSPACE/logs"
LOG_FILE="$LOG_DIR/fy26_daily_report.log"

# 确保日志目录存在
mkdir -p "$LOG_DIR"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=========================================="
log "开始执行 FY26_INIT Epic 日报 (v5.0)"
log "=========================================="

# Step 1: 全量抓取数据
log "Step 1: 全量抓取 Jira 数据..."
if python3 "$WORKSPACE/scripts/fetch_fy26_v5.py" >> "$LOG_FILE" 2>&1; then
    log "✅ 数据抓取成功"
else
    log "❌ 数据抓取失败"
    exit 1
fi

# Step 2: 生成 JSON 报告
log "Step 2: 生成 JSON 报告..."
if python3 "$WORKSPACE/scripts/generate_fy26_report_v5.py" >> "$LOG_FILE" 2>&1; then
    log "✅ JSON 报告生成成功"
else
    log "❌ JSON 报告生成失败"
    exit 1
fi

# Step 3: 生成 HTML 报告
log "Step 3: 生成 HTML 报告..."
if python3 "$WORKSPACE/scripts/generate_fy26_html_v5.py" >> "$LOG_FILE" 2>&1; then
    log "✅ HTML 报告生成成功"
else
    log "❌ HTML 报告生成失败"
    exit 1
fi

# Step 4: 发送邮件
log "Step 4: 发送邮件..."
if python3 "$WORKSPACE/scripts/send_fy26_report_v5.py" >> "$LOG_FILE" 2>&1; then
    log "✅ 邮件发送成功"
else
    log "❌ 邮件发送失败"
    exit 1
fi

log "=========================================="
log "✅ FY26_INIT Epic 日报执行完成"
log "=========================================="
