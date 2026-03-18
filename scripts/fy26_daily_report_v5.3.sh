#!/usr/bin/env python3
"""
FY26_INIT Epic 日报主控脚本 v5.3 (Optimized)
整合所有优化：
1. 并行化项目抓取 (5 workers)
2. 增量更新策略 (Delta Updates)
3. SQLite WAL 模式
4. 内存模式 HTML 生成
5. 批量数据查询

作者: OpenClaw
版本: v5.3
日期: 2026-03-18
"""

import os
import sys
import time
from pathlib import Path

WORKSPACE = Path.home() / ".openclaw" / "workspace"

def log(message):
    """打印带时间戳的日志"""
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def main():
    """主控流程"""
    log("=" * 60)
    log("🚀 FY26_INIT Epic 日报生成系统 v5.3 (Optimized)")
    log("=" * 60)
    
    start_time = time.time()
    
    # 步骤 1: 数据抓取（并行 + 增量）
    log("\n📥 Step 1: 数据抓取 (并行 + 增量)")
    import subprocess
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "fetch_fy26_v5.3.py")],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        log("❌ 数据抓取失败")
        print(result.stderr)
        return 1
    
    # 步骤 2: 生成报告（JSON）
    log("\n📊 Step 2: 生成 JSON 报告")
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "generate_fy26_report_v5.py")],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        log("⚠️ JSON 报告生成失败，继续生成 HTML")
    
    # 步骤 3: 生成 HTML 报告（内存优化版）
    log("\n🌐 Step 3: 生成 HTML 报告 (内存优化)")
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "generate_fy26_html_v5.3.py")],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        log("❌ HTML 报告生成失败")
        print(result.stderr)
        return 1
    
    # 步骤 4: 发送邮件
    log("\n📧 Step 4: 发送邮件")
    result = subprocess.run(
        [sys.executable, str(WORKSPACE / "scripts" / "send_fy26_report_v5.py")],
        capture_output=True,
        text=True
    )
    print(result.stdout)
    if result.returncode != 0:
        log("⚠️ 邮件发送失败")
        print(result.stderr)
    
    elapsed = time.time() - start_time
    log("\n" + "=" * 60)
    log(f"✅ 全部完成! 总耗时: {elapsed:.1f} 秒")
    log("=" * 60)
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
