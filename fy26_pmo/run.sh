#!/bin/bash
# FY26_PMO 定时报告脚本 - 修复版
# 每天 15:00 运行

cd /Users/admin/.openclaw/workspace/fy26_pmo

# 加载 Jira 和邮箱配置
if [ -f "$HOME/.openclaw/workspace/.jira-config" ]; then
    source "$HOME/.openclaw/workspace/.jira-config"
fi
export JIRA_API_TOKEN="${JIRA_API_TOKEN:-}"
export JIRA_EMAIL="${JIRA_USER_EMAIL:-rcheng2@lululemon.com}"
export QQ_MAIL_PASSWORD="${QQ_EMAIL_PASSWORD:-${QQ_MAIL_PASSWORD:-}}"

# 记录日志
LOG_FILE="/Users/admin/.openclaw/workspace/fy26_pmo/logs/cron_$(date +%Y%m%d_%H%M).log"
mkdir -p logs

echo "========== FY26_PMO 定时报告 ==========" > "$LOG_FILE"
echo "开始时间: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 1. 抓取 Epics (修复版，带延迟)
echo "[1/4] 抓取 Epics (修复版)..." >> "$LOG_FILE"
python3 fetch_data.py >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Epics 抓取失败" >> "$LOG_FILE"
    exit 1
fi
echo "✅ Epics 抓取完成" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 2. 抓取 Initiatives 和 Features
echo "[2/4] 抓取 Initiatives 和 Features..." >> "$LOG_FILE"
bash fetch_features_initiatives.sh >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Initiatives/Features 抓取失败" >> "$LOG_FILE"
    exit 1
fi
echo "✅ Initiatives/Features 抓取完成" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 3. 导入数据库
echo "[3/4] 导入数据库..." >> "$LOG_FILE"
python3 import_curl_data.py >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 数据库导入失败" >> "$LOG_FILE"
    exit 1
fi
echo "✅ 数据库导入完成" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 4. 生成报告
echo "[4/4] 生成报告..." >> "$LOG_FILE"
python3 generate_html.py >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 报告生成失败" >> "$LOG_FILE"
    exit 1
fi
echo "✅ 报告生成完成" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 5. 发送邮件（加密 ZIP）
echo "[5/5] 发送邮件..." >> "$LOG_FILE"

# 加载 QQ 邮箱密码
if [ -f "$HOME/.openclaw/workspace/.jira-config" ]; then
    source "$HOME/.openclaw/workspace/.jira-config"
fi
export QQ_MAIL_PASSWORD="${QQ_EMAIL_PASSWORD:-}"

# 找到最新生成的报告
LATEST_REPORT=$(ls -t fy26_pmo_report_*.html 2>/dev/null | head -1)
if [ -n "$LATEST_REPORT" ]; then
    python3 send_email.py --type fy26 --path "$LATEST_REPORT" >> "$LOG_FILE" 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ 邮件发送完成" >> "$LOG_FILE"
    else
        echo "❌ 邮件发送失败" >> "$LOG_FILE"
    fi
else
    echo "❌ 未找到报告文件" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"

echo "完成时间: $(date)" >> "$LOG_FILE"
echo "======================================" >> "$LOG_FILE"
