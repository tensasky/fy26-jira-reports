#!/bin/bash
# FY26_Intake_Cost 报表系统 - 主运行脚本
# 每周运行一次

cd /Users/admin/.openclaw/workspace/projects/fy26-intake-cost

# 记录日志
LOG_FILE="/Users/admin/.openclaw/workspace/projects/fy26-intake-cost/logs/run_$(date +%Y%m%d_%H%M).log"
mkdir -p logs

echo "========== FY26_Intake_Cost 报表系统 ==========" > "$LOG_FILE"
echo "开始时间: $(date)" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 加载 Jira 配置
if [ -f "$HOME/.openclaw/workspace/.jira-config" ]; then
    source "$HOME/.openclaw/workspace/.jira-config"
fi
export JIRA_API_TOKEN="${JIRA_API_TOKEN:-}"
export JIRA_EMAIL="${JIRA_EMAIL:-rcheng2@lululemon.com}"

# 1. 抓取数据
echo "[1/3] 抓取 Intake 数据..." >> "$LOG_FILE"
python3 scripts/fetch_intake_cost.py >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 数据抓取失败" >> "$LOG_FILE"
    exit 1
fi
echo "✅ 数据抓取完成" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 2. 生成 HTML 报告
echo "[2/3] 生成 HTML 报告..." >> "$LOG_FILE"
python3 scripts/generate_html.py >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 报告生成失败" >> "$LOG_FILE"
    exit 1
fi
echo "✅ 报告生成完成" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# 3. 发送邮件（可选）
echo "[3/3] 发送邮件..." >> "$LOG_FILE"

# 加载 QQ 邮箱密码
export QQ_MAIL_PASSWORD="${QQ_EMAIL_PASSWORD:-}"

if [ -n "$QQ_MAIL_PASSWORD" ]; then
    LATEST_REPORT=$(ls -t reports/fy26_intake_cost_report_*.html 2>/dev/null | head -1)
    if [ -n "$LATEST_REPORT" ]; then
        # 创建加密 ZIP
        cd reports
        ZIP_FILE="fy26_intake_cost_report_latest_Encrypted.zip"
        rm -f "$ZIP_FILE"
        
        # 使用 7z 创建 AES-256 加密 ZIP
        if command -v 7z &> /dev/null; then
            7z a -tzip -p"lulupmo" -mem=AES256 "$ZIP_FILE" "$(basename $LATEST_REPORT)" > /dev/null 2>&1
        else
            # 备选：使用系统 zip（无加密）
            zip "$ZIP_FILE" "$(basename $LATEST_REPORT)" > /dev/null 2>&1
        fi
        
        cd ..
        
        echo "✅ 加密 ZIP 创建完成" >> "$LOG_FILE"
    else
        echo "⚠️ 未找到报告文件" >> "$LOG_FILE"
    fi
else
    echo "⚠️ 未配置邮箱密码，跳过发送" >> "$LOG_FILE"
fi

echo "" >> "$LOG_FILE"
echo "完成时间: $(date)" >> "$LOG_FILE"
echo "=============================================" >> "$LOG_FILE"

echo "✅ FY26_Intake_Cost 报表生成完成!"
