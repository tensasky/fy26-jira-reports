#!/usr/bin/env python3
"""
Moonshot 余额查询并发送到飞书
每6小时自动查询并发送报告
余额单位：元（人民币）
"""

import os
import sys
import json
import csv
from datetime import datetime
from pathlib import Path
import urllib.request
import urllib.error

# 配置
WORKSPACE = Path("/Users/admin/.openclaw/workspace")
HISTORY_FILE = WORKSPACE / "moonshot-balance-history.csv"
ENV_FILE = WORKSPACE / ".env"

# Moonshot定价：大约 1元 = 12,500 tokens (基于 0.00008元/1K tokens)
TOKENS_PER_YUAN = 12500

def load_env():
    """从 .env 文件加载环境变量"""
    if ENV_FILE.exists():
        with open(ENV_FILE) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

def query_moonshot_balance(api_key):
    """查询 Moonshot 余额"""
    url = "https://api.moonshot.cn/v1/users/me/balance"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data.get('data', {})
    except Exception as e:
        print(f"查询失败: {e}")
        return None

def format_number(num):
    """格式化数字，添加千分位"""
    return f"{num:,.2f}"

def format_money(num):
    """格式化金额"""
    return f"¥{num:,.2f}"

def calculate_usage_rate(available, total):
    """计算使用率"""
    if total > 0:
        used = total - available
        return (used / total) * 100
    return 0

def get_status(available):
    """根据余额返回状态"""
    if available < 10:
        return "🚨", "余额严重不足！请立即充值"
    elif available < 50:
        return "⚠️", "余额较低，建议充值"
    else:
        return "✅", "余额充足"

def estimate_tokens(yuan_amount):
    """估算可使用的token数量"""
    return int(yuan_amount * TOKENS_PER_YUAN)

def save_history(data, usage_rate):
    """保存历史记录"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 确保目录存在
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 写入 CSV
    file_exists = HISTORY_FILE.exists()
    with open(HISTORY_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['time', 'available_yuan', 'total_yuan', 'used_yuan', 'usage_rate', 'granted_yuan', 'topped_up_yuan'])
        writer.writerow([
            now,
            data.get('available_balance', 0),
            data.get('total_balance', 0),
            data.get('total_balance', 0) - data.get('available_balance', 0),
            f"{usage_rate:.1f}",
            data.get('granted_balance', 0),
            data.get('topped_up_balance', 0)
        ])
    
    # 只保留最近200条
    if HISTORY_FILE.exists():
        with open(HISTORY_FILE, 'r') as f:
            lines = f.readlines()
        if len(lines) > 201:  # 1 header + 200 data
            with open(HISTORY_FILE, 'w') as f:
                f.writelines([lines[0]] + lines[-200:])

def generate_report(data):
    """生成报告文本"""
    available = data.get('available_balance', 0)
    total = data.get('total_balance', 0)
    granted = data.get('granted_balance', 0)
    topped_up = data.get('topped_up_balance', 0)
    used = total - available if total > 0 else 0
    usage_rate = calculate_usage_rate(available, total)
    
    status_icon, status_msg = get_status(available)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 估算可用tokens
    estimated_tokens = estimate_tokens(available)
    
    report = f"""🌙 **Moonshot 余额报告**

📅 查询时间: {now}

💰 **账户余额（人民币）**
• 可用余额: {format_money(available)}
• 总余额: {format_money(total)}
• 已使用: {format_money(used)} ({usage_rate:.1f}%)

💎 **余额构成**
• 赠送余额: {format_money(granted)}
• 充值余额: {format_money(topped_up)}

📊 **Token 估算**
• 约可调用: {estimated_tokens:,} tokens
• 按当前用量约可用: {estimated_tokens // 50000} 天

{status_icon} **状态**: {status_msg}

💡 **充值建议**
• 1元 ≈ 12,500 tokens (基于当前定价)
• 建议充值 ¥50-100 可长期使用

---
⏰ 每6小时自动更新"""
    
    return report

def main():
    # 加载环境变量
    load_env()
    
    # 获取 API Key
    api_key = os.environ.get('MOONSHOT_API_KEY')
    if not api_key:
        print("错误: 未设置 MOONSHOT_API_KEY 环境变量")
        print(f"请在 {ENV_FILE} 文件中添加: MOONSHOT_API_KEY=your_api_key")
        sys.exit(1)
    
    # 查询余额
    print("正在查询 Moonshot 余额...")
    data = query_moonshot_balance(api_key)
    
    if not data:
        print("查询失败")
        sys.exit(1)
    
    # 计算使用率
    available = data.get('available_balance', 0)
    total = data.get('total_balance', 0)
    usage_rate = calculate_usage_rate(available, total)
    
    # 保存历史
    save_history(data, usage_rate)
    
    # 生成报告
    report = generate_report(data)
    
    # 输出报告（stdout）
    print("\n" + "="*50)
    print(report)
    print("="*50)
    
    # 将报告写入文件，供其他工具读取
    report_file = WORKSPACE / "moonshot-latest-report.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n报告已保存到: {report_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
