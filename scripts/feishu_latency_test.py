#!/usr/bin/env python3
"""
飞书消息延迟测试工具
测量从发送到接收的时间延迟
"""

import time
import json
from datetime import datetime
from pathlib import Path

LOG_FILE = Path("/Users/admin/.openclaw/workspace/logs/feishu_latency_test.jsonl")
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

def log_test(direction, timestamp, latency_ms=None, note=""):
    """记录测试数据"""
    data = {
        "timestamp": timestamp,
        "direction": direction,  # "sent" or "received"
        "latency_ms": latency_ms,
        "note": note,
        "datetime": datetime.now().isoformat()
    }
    
    with open(LOG_FILE, 'a') as f:
        f.write(json.dumps(data) + '\n')
    
    return data

def run_latency_test():
    """执行延迟测试"""
    print("="*50)
    print("飞书消息延迟测试")
    print("="*50)
    
    # 发送测试消息
    send_time = time.time()
    send_timestamp = int(send_time * 1000)
    
    log_test("sent", send_timestamp, note="Test message initiated")
    
    print(f"\n[发送时间] {datetime.now().strftime('%H:%M:%S.%f')[:-3]}")
    print(f"[时间戳] {send_timestamp}")
    print("\n请立即回复此消息，我将计算往返延迟...")
    
    return send_timestamp

def calculate_latency(sent_timestamp, received_timestamp):
    """计算延迟"""
    latency_ms = received_timestamp - sent_timestamp
    return latency_ms

def analyze_results():
    """分析历史测试结果"""
    if not LOG_FILE.exists():
        print("尚无测试记录")
        return
    
    print("\n" + "="*50)
    print("历史测试结果分析")
    print("="*50)
    
    results = []
    with open(LOG_FILE, 'r') as f:
        for line in f:
            try:
                data = json.loads(line.strip())
                if data.get('latency_ms'):
                    results.append(data['latency_ms'])
            except:
                pass
    
    if results:
        avg_latency = sum(results) / len(results)
        min_latency = min(results)
        max_latency = max(results)
        
        print(f"\n测试次数: {len(results)}")
        print(f"平均延迟: {avg_latency:.0f} ms ({avg_latency/1000:.1f} 秒)")
        print(f"最小延迟: {min_latency:.0f} ms")
        print(f"最大延迟: {max_latency:.0f} ms")
        
        # 评级
        if avg_latency < 1000:
            rating = "🟢 优秀"
        elif avg_latency < 3000:
            rating = "🟡 良好"
        elif avg_latency < 5000:
            rating = "🟠 一般"
        else:
            rating = "🔴 较差"
        
        print(f"\n评级: {rating}")
    else:
        print("暂无完整测试数据")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "analyze":
        analyze_results()
    else:
        run_latency_test()
