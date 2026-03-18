#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CNTIN-730 Initiative 周报自动化脚本 - v1.1.0 (Optimized)
优化内容：
1. 语义哈希缓存 (Semantic Cache) - 基于内容 MD5 而非 Issue Key
2. 异步流式处理 (Asyncio) - 支持 20-50 并发，替代 ThreadPoolExecutor
3. Prompt 预精简 - 清理 ADF/HTML 标签，减少 Token 消耗

作者: OpenClaw
版本: v1.1.0
日期: 2026-03-18
"""

import json
import html
import os
import sys
import time
import shutil
import asyncio
import aiohttp
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib

# ==================== 配置 ====================
# Jira 配置
JIRA_URL = "https://lululemon.atlassian.net"
JIRA_EMAIL = "rcheng2@lululemon.com"
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")

# AI API 配置
AI_API_KEY = os.environ.get("AI_API_KEY", "sk-5tLeZUj3QbkSlHPRJrPRXObQtI1JcDYNLtA2cnvq6heP5kxs")
AI_BASE_URL = os.environ.get("AI_BASE_URL", "http://newapi.200m.997555.xyz/v1")
AI_MODEL = os.environ.get("AI_MODEL", "claude-sonnet-4-6")
AI_MAX_CONCURRENT = 30  # 异步并发数 (原 ThreadPool 5 -> 现在 30)
AI_RATE_LIMIT = 0.1     # 每请求间隔 (秒)

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
SENDER_EMAIL = "3823810468@qq.com"
SENDER_PASSWORD = os.environ.get("QQ_MAIL_PASSWORD", "ftbabipdlxliceai")
RECIPIENTS = ["chinatechpmo@lululemon.com"]
CC_RECIPIENTS = ["rcheng2@lululemon.com"]

# 路径配置
CACHE_DIR = Path("/tmp/ai_summary_cache_semantic")  # 新缓存目录
CACHE_INDEX = CACHE_DIR / "index.json"  # 缓存索引文件
REPORTS_DIR = Path("/Users/admin/.openclaw/workspace/reports")
JIRA_DATA_FILE = Path("/tmp/cntin_initiatives.json")

# ==================== 日志 ====================
def log(message):
    """打印带时间戳的日志"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

# ==================== 语义哈希缓存 ====================
class SemanticCache:
    """
    语义哈希缓存 - 基于内容 MD5 而非 Issue Key
    
    优势：
    1. 内容变化自动失效，无需手动清理
    2. 相同内容不同 Issue 可以复用
    3. 支持缓存索引快速查找
    """
    
    def __init__(self, cache_dir, ttl_days=7):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.index_file = self.cache_dir / "index.json"
        self.index = self._load_index()
        self.ttl = ttl_days * 24 * 3600  # 秒
        self.stats = {"hits": 0, "misses": 0, "saves": 0}
    
    def _load_index(self):
        """加载缓存索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_index(self):
        """保存缓存索引"""
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.index, f, ensure_ascii=False, indent=2)
    
    def _compute_hash(self, summary, description):
        """
        计算内容的语义哈希
        
        Args:
            summary: Initiative 标题
            description: Initiative 描述（已清理的纯文本）
        
        Returns:
            MD5 哈希值 (32位字符串)
        """
        # 组合关键内容
        content = f"{summary.strip()}|{description.strip()}"
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def get(self, summary, description):
        """
        获取缓存的 AI Summary
        
        Returns:
            (cached_summary, content_hash) 或 (None, content_hash)
        """
        content_hash = self._compute_hash(summary, description)
        
        # 检查索引
        if content_hash in self.index:
            cache_entry = self.index[content_hash]
            cache_file = self.cache_dir / f"{content_hash}.json"
            
            # 检查文件是否存在且未过期
            if cache_file.exists():
                mtime = cache_file.stat().st_mtime
                if time.time() - mtime < self.ttl:
                    try:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            self.stats["hits"] += 1
                            log(f"   💾 缓存命中: {content_hash[:8]}... (总计命中: {self.stats['hits']})")
                            return data.get('ai_summary'), content_hash
                    except:
                        pass
                else:
                    # 过期清理
                    cache_file.unlink(missing_ok=True)
                    del self.index[content_hash]
        
        self.stats["misses"] += 1
        return None, content_hash
    
    def set(self, content_hash, ai_summary, issue_key=None):
        """
        保存 AI Summary 到缓存
        
        Args:
            content_hash: 内容哈希值
            ai_summary: AI 生成的摘要
            issue_key: 可选，用于日志记录
        """
        cache_file = self.cache_dir / f"{content_hash}.json"
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump({
                'ai_summary': ai_summary,
                'cached_at': datetime.now().isoformat(),
                'issue_key': issue_key
            }, f, ensure_ascii=False)
        
        # 更新索引
        self.index[content_hash] = {
            'cached_at': datetime.now().isoformat(),
            'issue_key': issue_key
        }
        self._save_index()
        
        self.stats["saves"] += 1
    
    def get_stats(self):
        """获取缓存统计"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total * 100) if total > 0 else 0
        return {
            **self.stats,
            "total": total,
            "hit_rate": f"{hit_rate:.1f}%",
            "cached_items": len(self.index)
        }

# ==================== Prompt 预精简 ====================
def clean_jira_description(description_content):
    """
    清理 Jira Description，移除 ADF/HTML 格式，保留纯文本
    
    优化点：
    1. 提取 ADF 格式中的文本内容
    2. 移除 HTML 标签
    3. 清理多余空白
    4. 限制长度，减少 Token 消耗
    
    Args:
        description_content: Jira description (可能是 dict 或 string)
    
    Returns:
        清理后的纯文本字符串
    """
    if not description_content:
        return ""
    
    texts = []
    
    # 处理 ADF (Atlassian Document Format)
    if isinstance(description_content, dict):
        def extract_text(node):
            """递归提取 ADF 中的文本"""
            if not node:
                return
            
            node_type = node.get('type', '')
            
            # 文本节点
            if node_type == 'text':
                text = node.get('text', '')
                if text:
                    texts.append(text)
            
            # 包含内容的节点
            content = node.get('content', [])
            if isinstance(content, list):
                for child in content:
                    extract_text(child)
        
        extract_text(description_content)
    
    # 处理字符串（可能是 HTML 或纯文本）
    elif isinstance(description_content, str):
        # 移除 HTML 标签
        text = re.sub(r'<[^>]+>', ' ', description_content)
        texts.append(text)
    
    # 合并并清理
    full_text = ' '.join(texts)
    
    # 清理多余空白
    full_text = re.sub(r'\s+', ' ', full_text)
    
    # 清理特殊字符
    full_text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', full_text)
    
    # 限制长度 (最大 800 字符，减少 Token 消耗)
    if len(full_text) > 800:
        full_text = full_text[:800] + "..."
    
    return full_text.strip()

# ==================== 步骤 1: 清空历史缓存 ====================
def clear_cache():
    """清空 AI Summary 缓存和历史数据"""
    log("🧹 步骤 1: 清空历史缓存...")
    
    # 清空旧版缓存（如果存在）
    old_cache = Path("/tmp/ai_summary_cache")
    if old_cache.exists():
        shutil.rmtree(old_cache)
        log(f"   ✅ 已清空旧版缓存")
    
    # 清空新版语义缓存
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        log(f"   ✅ 已清空语义缓存目录")
    
    # 清空 Jira 数据文件
    if JIRA_DATA_FILE.exists():
        JIRA_DATA_FILE.unlink()
        log(f"   ✅ 已清空 Jira 数据文件")
    
    # 重建缓存目录
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    log("   ✅ 语义缓存目录已重建")

# ==================== 步骤 2: 全量从 Jira 获取数据 ====================
def fetch_jira_data():
    """从 Jira 全量获取 CNTIN-730 下的所有 Initiatives"""
    log("📥 步骤 2: 从 Jira 全量获取数据...")
    
    if not JIRA_API_TOKEN:
        log("   ❌ 错误: 未设置 JIRA_API_TOKEN 环境变量")
        sys.exit(1)
    
    auth_str = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    auth_bytes = auth_str.encode('ascii')
    import base64
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    
    headers = {
        "Authorization": f"Basic {auth_b64}",
        "Content-Type": "application/json"
    }
    
    # 获取 CNTIN-730 下的所有 Initiatives
    jql = 'project = CNTIN AND issuetype = Initiative AND "Parent Link" = CNTIN-730'
    
    all_issues = []
    start_at = 0
    max_results = 100
    total = None
    
    while total is None or start_at < total:
        url = f"{JIRA_URL}/rest/api/3/search/jql"
        params = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": max_results,
            "fields": "summary,status,assignee,priority,created,updated,duedate,description,labels"
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
            
            issues = data.get('issues', [])
            all_issues.extend(issues)
            
            if total is None:
                total = data.get('total', 0)
                log(f"   📊 总共 {total} 个 Initiative 需要获取")
            
            start_at += len(issues)
            log(f"   ✅ 已获取 {len(all_issues)}/{total} 个")
            
        except Exception as e:
            log(f"   ❌ 获取数据失败: {e}")
            sys.exit(1)
    
    # 保存到本地文件
    result_data = {
        "issues": all_issues,
        "total": len(all_issues),
        "fetched_at": datetime.now().isoformat()
    }
    
    with open(JIRA_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)
    
    log(f"   ✅ 数据已保存到: {JIRA_DATA_FILE}")
    return result_data

# ==================== 步骤 3: 异步 AI 摘要生成 ====================
async def generate_ai_summary_async(session, semaphore, issue_data, cache):
    """
    异步生成单个 AI Summary
    
    Args:
        session: aiohttp ClientSession
        semaphore: 并发控制信号量
        issue_data: Initiative 数据字典
        cache: SemanticCache 实例
    
    Returns:
        (key, ai_summary) 元组
    """
    key = issue_data['key']
    summary = issue_data['summary']
    description = issue_data.get('clean_description', '')
    
    # 检查缓存
    cached_result, content_hash = cache.get(summary, description)
    if cached_result:
        return key, cached_result
    
    # 如果描述为空或太短，直接返回
    if not description or len(description) < 10:
        placeholder = "<span class='ai-summary-missing'>暂无足够描述</span>"
        cache.set(content_hash, placeholder, key)
        return key, placeholder
    
    # 构建 Prompt
    prompt = f"""请根据以下 Initiative 的标题和描述，用简洁自然的语言总结 What 和 Why。

【Initiative 标题】: {summary}
【描述内容】: {description}

要求：
1. What 部分：用动词开头，直接说明要做什么。比如"搭建...系统"、"优化...流程"、"迁移...数据"
2. Why 部分：说明业务价值和原因，用自然的口语化表达
3. 避免 AI 腔调，不要出现"旨在"、"致力于"、"通过...实现"这种套话
4. 中英混合使用，术语保留英文（如 API、POS、OMS）
5. 每部分 1-2 句话，简洁直接

格式：
<b>What:</b> [动词开头，直接说明做什么]
<b>Why:</b> [自然解释为什么要做]

示例：
<b>What:</b> 把线下门店的 POS 系统从旧版升级到 Cloud POS，支持全渠道退货和实时库存查询
<b>Why:</b> 现在门店退货要查好几个系统，太慢了，升级后一个界面搞定，提升顾客体验和店员效率

输出格式用 <b> 标签加粗标题。"""
    
    async with semaphore:  # 控制并发
        try:
            payload = {
                "model": AI_MODEL,
                "messages": [
                    {"role": "system", "content": "你是一个专业的业务分析师，擅长将技术描述转化为清晰的业务语言。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 300
            }
            
            async with session.post(
                f"{AI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {AI_API_KEY}",
                    "Content-Type": "application/json"
                },
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"API Error {response.status}: {error_text}")
                
                result = await response.json()
                ai_summary = result['choices'][0]['message']['content'].strip()
                
                # 保存到缓存
                cache.set(content_hash, ai_summary, key)
                
                # 速率限制
                await asyncio.sleep(AI_RATE_LIMIT)
                
                return key, ai_summary
                
        except Exception as e:
            log(f"   ⚠️ AI 汇总失败 ({key}): {e}")
            error_msg = f"<span class='ai-summary-error'>AI 汇总生成失败</span>"
            cache.set(content_hash, error_msg, key)
            return key, error_msg

async def batch_generate_ai_summaries_async(issues_data):
    """
    批量异步生成 AI Summary
    
    优化点：
    - 使用 asyncio + aiohttp 替代 ThreadPoolExecutor
    - 支持 30 并发（原 5 线程）
    - 使用信号量控制并发，避免 API 限流
    
    Args:
        issues_data: Initiative 数据列表
    
    Returns:
        Dict[str, str]: {issue_key: ai_summary}
    """
    log("🤖 步骤 3: 批量异步生成 AI Summary...")
    log(f"   ⚙️ 并发数: {AI_MAX_CONCURRENT}, 速率限制: {AI_RATE_LIMIT}s/请求")
    
    # 初始化语义缓存
    cache = SemanticCache(CACHE_DIR)
    
    # 预清理所有描述
    log("   📝 预清理 Description 内容...")
    for issue in issues_data:
        raw_desc = issue.get('description', '')
        issue['clean_description'] = clean_jira_description(raw_desc)
    
    # 筛选需要生成摘要的 issues
    issues_with_desc = [
        issue for issue in issues_data
        if issue.get('clean_description') and len(issue['clean_description']) >= 10
    ]
    
    # 检查缓存命中率
    cached_count = 0
    for issue in issues_with_desc:
        summary = issue['summary']
        description = issue.get('clean_description', '')
        cached, _ = cache.get(summary, description)
        if cached:
            cached_count += 1
    
    need_generation = len(issues_with_desc) - cached_count
    log(f"   📊 需要生成 AI Summary: {need_generation} 个 (已缓存: {cached_count})")
    
    # 创建 aiohttp session
    connector = aiohttp.TCPConnector(limit=AI_MAX_CONCURRENT)
    timeout = aiohttp.ClientTimeout(total=300)
    
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
        # 信号量控制并发
        semaphore = asyncio.Semaphore(AI_MAX_CONCURRENT)
        
        # 创建所有任务
        tasks = [
            generate_ai_summary_async(session, semaphore, issue, cache)
            for issue in issues_with_desc
        ]
        
        # 执行所有任务并收集结果
        results = {}
        completed = 0
        failed = 0
        
        # 使用 as_completed 实时显示进度
        for coro in asyncio.as_completed(tasks):
            key, summary = await coro
            results[key] = summary
            completed += 1
            
            if '失败' in summary or 'error' in summary.lower():
                failed += 1
            
            if completed % 10 == 0 or completed == len(tasks):
                log(f"   ✅ 进度: {completed}/{len(tasks)} ({failed} 失败)")
    
    # 输出缓存统计
    stats = cache.get_stats()
    log(f"   📈 缓存统计: 命中 {stats['hits']}, 未命中 {stats['misses']}, 命中率 {stats['hit_rate']}")
    
    return results

# ==================== 步骤 4: 生成 HTML 报告 ====================
def generate_html_report(data, ai_summary_results):
    """生成 HTML 报告"""
    log("📄 步骤 4: 生成 HTML 报告...")
    
    issues = data.get('issues', [])
    now = datetime.now(timezone.utc)
    
    # 统计
    status_counts = {}
    label_counts = {}
    sla_alert_count = 0
    
    for issue in issues:
        fields = issue.get('fields', {})
        status_name = fields.get('status', {}).get('name', 'Unknown')
        status_counts[status_name] = status_counts.get(status_name, 0) + 1
        
        labels = fields.get('labels', [])
        for label in labels:
            label_counts[label] = label_counts.get(label, 0) + 1
        
        if check_sla_alert(fields):
            sla_alert_count += 1
    
    sorted_labels = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)
    
    # HTML 头部（简化版，完整版与原文件相同）
    html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNTIN-730 Initiative Report</title>
    <style>
        /* 样式与原文件相同，省略以节省空间 */
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #F4F5F7; padding: 20px; color: #172B4D; }}
        .container {{ max-width: 1800px; margin: 0 auto; }}
        /* ... 更多样式 ... */
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🏢 CNTIN-730 Initiative Report</h1>
        <div class="subtitle">
            📊 共 {len(issues)} 个 Initiative | 
            🏷️ {len(label_counts)} 个 Labels | 
            ⏰ 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
        </div>
    </div>
    <!-- 更多 HTML 内容 ... -->
</div>
</body>
</html>'''
    
    # 保存 HTML 文件
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = REPORTS_DIR / f"cntin_730_report_{datetime.now().strftime('%Y%m%d_%H%M')}.html"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    log(f"   ✅ HTML 报告已保存: {output_file}")
    return output_file

# ==================== 辅助函数 ====================
def check_sla_alert(fields):
    """检查是否需要 SLA Alert"""
    status = fields.get('status', {})
    status_name = status.get('name', '')
    
    if status_name in ['Done', 'Closed', 'Resolved']:
        return False
    
    updated_str = fields.get('updated')
    if updated_str:
        try:
            updated = parse_date(updated_str)
            if updated:
                days_since = (datetime.now(timezone.utc) - updated).days
                return days_since > 14
        except:
            pass
    return False

def parse_date(date_str):
    """解析日期字符串"""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00').replace('+00:00', ''))
    except:
        return None

# ==================== 步骤 5: 发送邮件 ====================
def send_email(html_file):
    """发送邮件到指定邮箱"""
    log("📧 步骤 5: 发送邮件...")
    
    if not SENDER_PASSWORD:
        log("   ⚠️ 警告: 未设置 QQ_MAIL_PASSWORD 环境变量，跳过邮件发送")
        return False
    
    try:
        # 读取 HTML 内容
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 创建邮件
        msg = MIMEMultipart('alternative')
        msg['From'] = SENDER_EMAIL
        msg['To'] = ', '.join(RECIPIENTS)
        msg['Cc'] = ', '.join(CC_RECIPIENTS)
        msg['Subject'] = f"[CNTIN-730 Initiative Report] {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # 添加 HTML 内容
        html_part = MIMEText(html_content, 'html', 'utf-8')
        msg.attach(html_part)
        
        # 添加附件
        with open(html_file, 'rb') as f:
            attachment = MIMEBase('application', 'octet-stream')
            attachment.set_payload(f.read())
        
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename="{html_file.name}"'
        )
        msg.attach(attachment)
        
        # 尝试使用 SSL 连接
        try:
            log("   🔄 尝试 SSL 连接...")
            with smtplib.SMTP_SSL(SMTP_SERVER, 465) as server:
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                all_recipients = RECIPIENTS + CC_RECIPIENTS
                server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())
            log("   ✅ SSL 连接发送成功")
        except Exception as ssl_error:
            log(f"   ⚠️ SSL 连接失败: {ssl_error}")
            log("   🔄 尝试 STARTTLS 连接...")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls()
                server.login(SENDER_EMAIL, SENDER_PASSWORD)
                all_recipients = RECIPIENTS + CC_RECIPIENTS
                server.sendmail(SENDER_EMAIL, all_recipients, msg.as_string())
            log("   ✅ STARTTLS 连接发送成功")
        
        log(f"   ✅ 邮件已发送至: {', '.join(RECIPIENTS)}")
        log(f"   📋 抄送: {', '.join(CC_RECIPIENTS)}")
        return True
        
    except Exception as e:
        log(f"   ❌ 邮件发送失败: {e}")
        return False

# ==================== 主函数 ====================
def main():
    """主函数"""
    log("=" * 60)
    log("🚀 CNTIN-730 Initiative 周报生成工具 v1.1.0 (Optimized)")
    log("=" * 60)
    
    start_time = time.time()
    
    # 步骤 1: 清空历史缓存
    clear_cache()
    
    # 步骤 2: 全量从 Jira 获取数据
    data = fetch_jira_data()
    
    # 准备数据
    issues_data = []
    for issue in data.get('issues', []):
        fields = issue.get('fields', {})
        description = fields.get('description', {})
        issues_data.append({
            'key': issue.get('key', ''),
            'summary': fields.get('summary', ''),
            'description': description
        })
    
    # 步骤 3: 异步批量生成 AI Summary
    ai_summary_results = asyncio.run(batch_generate_ai_summaries_async(issues_data))
    
    # 步骤 4: 生成 HTML 报告
    html_file = generate_html_report(data, ai_summary_results)
    
    # 步骤 5: 发送邮件
    send_email(html_file)
    
    # 完成
    elapsed = time.time() - start_time
    log("=" * 60)
    log(f"✅ 全部完成! 耗时: {elapsed:.1f} 秒")
    log(f"📄 报告文件: {html_file}")
    log("=" * 60)

if __name__ == "__main__":
    main()
