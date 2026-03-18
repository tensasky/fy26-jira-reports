#!/usr/bin/env python3
"""
FY26_INIT 数据抓取脚本 v5.3 (Optimized)
优化内容：
1. 并行化项目抓取 - 4-5 个 Worker 线程并发抓取 22 个项目
2. 增量更新策略 - 基于 updated_at 时间戳，只抓取 24h 内变动的 Issue

作者: OpenClaw
版本: v5.3
日期: 2026-03-18
"""

import os
import sys
import json
import sqlite3
import requests
import concurrent.futures
from datetime import datetime, timedelta
from base64 import b64encode
from pathlib import Path
from functools import wraps
import time

# ==================== 配置 ====================
WORKSPACE = Path.home() / ".openclaw" / "workspace"
DB_PATH = WORKSPACE / "jira-reports" / "fy26_data.db"
CONFIG_FILE = WORKSPACE / ".jira-config"
STATE_FILE = WORKSPACE / "jira-reports" / ".fetch_state.json"

# 并发配置
MAX_WORKERS = 5  # 并发抓取线程数
REQUEST_TIMEOUT = 60

# 项目列表
PROJECTS = [
    "CNTEC", "CNTOM", "CNTDM", "CNTMM", "CNTD", "CNTEST", "CNENG", "CNINFA",
    "CNCA", "CPR", "EPCH", "CNCRM", "CNDIN", "SWMP", "CDM", "CMDM",
    "CNSCM", "OF", "CNRTPRJ", "CSCPVT", "CNPMO", "CYBERPJT"
]

# ==================== 辅助函数 ====================
def retry_on_error(max_retries=3, delay=2):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt < max_retries - 1:
                        print(f"    ⚠️ 重试 {attempt+1}/{max_retries}: {e}")
                        time.sleep(delay * (attempt + 1))  # 指数退避
                    else:
                        raise
            return None
        return wrapper
    return decorator

def timing(func):
    """计时装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        elapsed = time.time() - start
        print(f"    ⏱️ 耗时: {elapsed:.2f}s")
        return result
    return wrapper

# ==================== Jira 配置 ====================
def load_config():
    """读取 Jira 配置"""
    config = {}
    with open(CONFIG_FILE) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value.strip('"').strip("'")
    return config

config = load_config()
JIRA_URL = config.get('JIRA_URL') or config.get('JIRA_BASE_URL')
JIRA_USER = config.get('JIRA_USER') or config.get('JIRA_USER_EMAIL')
JIRA_TOKEN = config.get('JIRA_TOKEN') or config.get('JIRA_API_TOKEN')

# 认证头
auth_string = f"{JIRA_USER}:{JIRA_TOKEN}"
auth_b64 = b64encode(auth_string.encode('ascii')).decode('ascii')
HEADERS = {
    'Authorization': f'Basic {auth_b64}',
    'Content-Type': 'application/json'
}

# ==================== 状态管理 ====================
class FetchState:
    """
    抓取状态管理器
    用于记录上次抓取的时间，实现增量更新
    """
    
    def __init__(self):
        self.state_file = STATE_FILE
        self.state = self._load()
    
    def _load(self):
        """加载状态文件"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {
            'last_run': None,
            'last_full_run': None,
            'project_states': {}
        }
    
    def save(self):
        """保存状态文件"""
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.state_file, 'w') as f:
            json.dump(self.state, f, indent=2)
    
    def get_last_update(self):
        """获取上次更新时间"""
        return self.state.get('last_run')
    
    def set_last_update(self, timestamp=None):
        """设置更新时间"""
        self.state['last_run'] = timestamp or datetime.now().isoformat()
        self.save()
    
    def get_project_last_update(self, project):
        """获取特定项目的上次更新时间"""
        return self.state.get('project_states', {}).get(project)
    
    def set_project_last_update(self, project, timestamp=None):
        """设置特定项目的更新时间"""
        if 'project_states' not in self.state:
            self.state['project_states'] = {}
        self.state['project_states'][project] = timestamp or datetime.now().isoformat()
        self.save()
    
    def should_run_full_fetch(self):
        """判断是否应该执行全量抓取"""
        last_full = self.state.get('last_full_run')
        if not last_full:
            return True
        
        last_full_dt = datetime.fromisoformat(last_full)
        # 每 7 天执行一次全量抓取
        return (datetime.now() - last_full_dt) > timedelta(days=7)
    
    def mark_full_run(self):
        """标记全量抓取完成"""
        self.state['last_full_run'] = datetime.now().isoformat()
        self.save()

# ==================== 数据库 ====================
def init_db():
    """初始化数据库"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    # 读取并执行 schema
    schema_file = WORKSPACE / "scripts" / "fy26_db_schema.sql"
    with open(schema_file) as f:
        conn.executescript(f.read())
    
    conn.commit()
    return conn

def save_epic_batch(conn, epics):
    """批量保存 Epic"""
    for epic in epics:
        conn.execute('''
            INSERT OR REPLACE INTO epics 
            (key, project, summary, status, assignee, parent_key, created, labels, raw_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            epic['key'],
            epic['project'],
            epic['summary'],
            epic['status'],
            epic['assignee'],
            epic.get('parent_key'),
            epic['created'],
            json.dumps(epic.get('labels', [])),
            json.dumps(epic.get('raw', {}))
        ))
    conn.commit()

# ==================== 并行化项目抓取 ====================
@retry_on_error(max_retries=3, delay=2)
def fetch_project_epics(project, incremental=False, since_timestamp=None):
    """
    抓取单个项目的所有 Epic
    
    Args:
        project: 项目代码 (如 'CPR')
        incremental: 是否增量抓取
        since_timestamp: 增量抓取的时间阈值
    
    Returns:
        list: Epic 列表
    """
    epics = []
    start_at = 0
    max_results = 100
    
    # 构建 JQL
    if incremental and since_timestamp:
        # 增量更新：只抓取指定时间后更新的 Epic
        # Jira 的 updated 字段格式: 2026-03-17T10:00:00.000+0800
        since_str = datetime.fromisoformat(since_timestamp).strftime('%Y-%m-%d %H:%M')
        jql = f"project = {project} AND issuetype = Epic AND updated >= \"{since_str}\" ORDER BY updated DESC"
    else:
        # 全量抓取
        jql = f"project = {project} AND issuetype = Epic ORDER BY created DESC"
    
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    
    while True:
        params = {
            'jql': jql,
            'startAt': start_at,
            'maxResults': max_results,
            'fields': 'summary,status,assignee,created,updated,labels,parent,project'
        }
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            issues = data.get('issues', [])
            
            for issue in issues:
                fields = issue['fields']
                epics.append({
                    'key': issue['key'],
                    'project': project,
                    'summary': fields.get('summary', ''),
                    'status': fields.get('status', {}).get('name', ''),
                    'assignee': fields.get('assignee', {}).get('displayName', '未分配') if fields.get('assignee') else '未分配',
                    'parent_key': fields.get('parent', {}).get('key') if fields.get('parent') else None,
                    'created': fields.get('created', '')[:10],
                    'updated': fields.get('updated', ''),
                    'labels': fields.get('labels', []),
                    'raw': issue
                })
            
            # 检查是否还有更多
            if len(issues) < max_results:
                break
            start_at += max_results
            
        except requests.exceptions.Timeout:
            print(f"    ⚠️ {project} 请求超时，重试...")
            raise
        except Exception as e:
            print(f"    ❌ {project} 抓取失败: {e}")
            raise
    
    return epics

def fetch_all_epics_parallel(conn, state, incremental=False):
    """
    并行抓取所有项目的 Epic
    
    Args:
        conn: 数据库连接
        state: FetchState 实例
        incremental: 是否增量抓取
    
    Returns:
        int: 抓取的 Epic 总数
    """
    print(f"\n📊 Step 4: 并行抓取所有项目的 Epic...")
    print(f"   模式: {'增量更新' if incremental else '全量抓取'}")
    print(f"   并发数: {MAX_WORKERS}")
    
    total_count = 0
    success_count = 0
    fail_count = 0
    
    def fetch_with_progress(project):
        """包装函数，带进度和错误处理"""
        try:
            since = state.get_project_last_update(project) if incremental else None
            epics = fetch_project_epics(project, incremental, since)
            
            if epics:
                save_epic_batch(conn, epics)
                state.set_project_last_update(project)
            
            return project, len(epics), None
        except Exception as e:
            return project, 0, str(e)
    
    # 使用 ThreadPoolExecutor 并发抓取
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # 提交所有任务
        future_to_project = {
            executor.submit(fetch_with_progress, project): project 
            for project in PROJECTS
        }
        
        # 收集结果（实时显示进度）
        for future in concurrent.futures.as_completed(future_to_project):
            project, count, error = future.result()
            
            if error:
                print(f"    ❌ {project}: 失败 ({error})")
                fail_count += 1
            else:
                print(f"    ✅ {project}: {count} 个 Epic")
                total_count += count
                success_count += 1
    
    print(f"\n✅ 项目抓取完成: {success_count} 成功, {fail_count} 失败")
    print(f"✅ 共抓取 {total_count} 个 Epic")
    
    return total_count

# ==================== 原有功能保持不变 ====================
def fetch_fy26_initiatives(conn):
    """抓取所有 FY26_INIT Initiative"""
    print(f"\n📊 Step 1: 抓取所有带 FY26_INIT 标签的 CNTIN Initiative...")
    
    jql = "project = CNTIN AND issuetype = Initiative AND labels = FY26_INIT ORDER BY created DESC"
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    params = {
        'jql': jql,
        'maxResults': 1000,
        'fields': 'summary,status,assignee,labels,project,updated'
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        issues = data.get('issues', [])
        
        for issue in issues:
            key = issue['key']
            fields = issue['fields']
            
            conn.execute('''
                INSERT OR REPLACE INTO initiatives
                (key, project, summary, status, assignee, labels, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                key,
                'CNTIN',
                fields.get('summary', ''),
                fields.get('status', {}).get('name', ''),
                fields.get('assignee', {}).get('displayName', '未分配') if fields.get('assignee') else '未分配',
                json.dumps(fields.get('labels', [])),
                json.dumps(issue)
            ))
        
        conn.commit()
        print(f"✅ 找到 {len(issues)} 个带 FY26_INIT 标签的 Initiative")
        return [issue['key'] for issue in issues]
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return []

def fetch_features_by_initiative(conn, init_keys):
    """抓取 Initiative 下的所有 Feature"""
    if not init_keys:
        return 0
    
    print(f"\n📊 Step 2: 抓取 {len(init_keys)} 个 Initiative 下的所有 Feature...")
    
    total_count = 0
    
    for init_key in init_keys:
        jql = f"parent = {init_key} AND issuetype = Feature ORDER BY created DESC"
        url = f"{JIRA_URL}/rest/api/3/search/jql"
        params = {
            'jql': jql,
            'maxResults': 1000,
            'fields': 'summary,status,assignee,parent,labels,project,updated'
        }
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            issues = data.get('issues', [])
            
            for issue in issues:
                key = issue['key']
                fields = issue['fields']
                
                conn.execute('''
                    INSERT OR REPLACE INTO features
                    (key, project, summary, status, assignee, parent_key, labels, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    key,
                    'CNTIN',
                    fields.get('summary', ''),
                    fields.get('status', {}).get('name', ''),
                    fields.get('assignee', {}).get('displayName', '未分配') if fields.get('assignee') else '未分配',
                    fields.get('parent', {}).get('key') if fields.get('parent') else None,
                    json.dumps(fields.get('labels', [])),
                    json.dumps(issue)
                ))
            
            total_count += len(issues)
            print(f"  - {init_key}: {len(issues)} 个 Feature")
            
        except Exception as e:
            print(f"  ❌ {init_key} 失败: {e}")
    
    conn.commit()
    print(f"✅ 共抓取了 {total_count} 个 Feature")
    return total_count

def fetch_epics_by_features_batch(conn, feature_keys):
    """批量抓取 Feature 下的 Epic"""
    if not feature_keys:
        return 0
    
    print(f"\n📊 Step 3: 批量抓取 {len(feature_keys)} 个 Feature 下的所有 Epic...")
    
    total_count = 0
    batch_size = 50
    
    for i in range(0, len(feature_keys), batch_size):
        batch = feature_keys[i:i+batch_size]
        batch_str = ','.join(batch)
        
        jql = f"parent in ({batch_str}) AND issuetype = Epic ORDER BY created DESC"
        url = f"{JIRA_URL}/rest/api/3/search/jql"
        params = {
            'jql': jql,
            'maxResults': 1000,
            'fields': 'summary,status,assignee,created,labels,parent,project,updated'
        }
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()
            
            issues = data.get('issues', [])
            
            for issue in issues:
                key = issue['key']
                fields = issue['fields']
                
                conn.execute('''
                    INSERT OR REPLACE INTO epics 
                    (key, project, summary, status, assignee, parent_key, created, labels, raw_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    key,
                    fields.get('project', {}).get('key', 'UNKNOWN'),
                    fields.get('summary', ''),
                    fields.get('status', {}).get('name', ''),
                    fields.get('assignee', {}).get('displayName', '未分配') if fields.get('assignee') else '未分配',
                    fields.get('parent', {}).get('key') if fields.get('parent') else None,
                    fields.get('created', '')[:10],
                    json.dumps(fields.get('labels', [])),
                    json.dumps(issue)
                ))
            
            total_count += len(issues)
            print(f"  批次 {i//batch_size + 1}/{(len(feature_keys)-1)//batch_size + 1}: {len(issues)} 个 Epic")
            
        except Exception as e:
            print(f"  ❌ 批次 {i//batch_size + 1} 失败: {e}")
    
    conn.commit()
    print(f"✅ 共抓取了 {total_count} 个 Epic")
    return total_count

# ==================== 主函数 ====================
def main():
    print("🚀 开始抓取 FY26_INIT 数据 (v5.3 - Optimized)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {DB_PATH}")
    
    # 初始化
    conn = init_db()
    state = FetchState()
    
    # 判断抓取模式
    incremental = not state.should_run_full_fetch()
    
    if incremental:
        last_update = state.get_last_update()
        print(f"\n📅 上次全量抓取: {state.state.get('last_full_run')}")
        print(f"📅 上次更新: {last_update}")
        print("🔄 执行增量更新 (只抓取 24h 内变动的数据)")
    else:
        print("\n🔄 执行全量抓取")
    
    # Step 1: 抓取所有 FY26_INIT Initiative
    init_keys = fetch_fy26_initiatives(conn)
    
    # Step 2: 抓取这些 Initiative 下的所有 Feature
    fetch_features_by_initiative(conn, init_keys)
    
    # Step 3: 获取所有 Feature 的 key，批量抓取它们下面的 Epic
    cursor = conn.execute('SELECT DISTINCT key FROM features')
    feature_keys = [row[0] for row in cursor.fetchall()]
    fetch_epics_by_features_batch(conn, feature_keys)
    
    # Step 4: 并行抓取所有项目的所有 Epic（优化后的核心功能）
    fetch_all_epics_parallel(conn, state, incremental)
    
    # 更新状态
    state.set_last_update()
    if not incremental:
        state.mark_full_run()
    
    # 统计
    print("\n" + "="*50)
    print("✅ 数据抓取完成！")
    print("="*50)
    
    cursor = conn.execute('SELECT COUNT(*) FROM epics')
    epic_count = cursor.fetchone()[0]
    
    cursor = conn.execute('SELECT COUNT(*) FROM features')
    feature_count = cursor.fetchone()[0]
    
    cursor = conn.execute('SELECT COUNT(*) FROM initiatives')
    init_count = cursor.fetchone()[0]
    
    print(f"📊 统计:")
    print(f"   - FY26_INIT Initiatives: {init_count}")
    print(f"   - Features: {feature_count}")
    print(f"   - Epics: {epic_count}")
    print(f"\n📁 数据库: {DB_PATH}")
    print(f"📁 状态文件: {STATE_FILE}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn.close()

if __name__ == '__main__':
    main()
