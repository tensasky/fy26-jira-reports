#!/bin/bash
# CNTIN-730 周报定时任务脚本
# 每个工作日中午 12:00 执行

set -e

# 加载 Jira 配置
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$SCRIPT_DIR")"

if [ -f "$WORKSPACE_DIR/.jira-config" ]; then
    source "$WORKSPACE_DIR/.jira-config"
fi

# 设置环境变量
export JIRA_EMAIL="${JIRA_USER_EMAIL:-rcheng2@lululemon.com}"
export JIRA_API_TOKEN="${JIRA_API_TOKEN:-}"

# 日志
LOG_FILE="$WORKSPACE_DIR/logs/cntin730_cron.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 开始执行 CNTIN-730 周报任务" >> "$LOG_FILE"

# 执行报告生成
python3 "$SCRIPT_DIR/cntin730_report.py" >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 报告生成成功" >> "$LOG_FILE"
    
    # 发送邮件（如果配置了邮件发送脚本）
    if [ -f "$SCRIPT_DIR/send_report.py" ]; then
        python3 "$SCRIPT_DIR/send_report.py" >> "$LOG_FILE" 2>&1
    fi
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 报告生成失败" >> "$LOG_FILE"
    exit 1
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] 任务完成" >> "$LOG_FILE"
