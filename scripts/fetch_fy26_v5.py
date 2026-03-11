#!/usr/bin/env python3
"""
FY26_INIT 数据抓取脚本 v5.0
使用 SQLite 数据库存储数据，避免 JSON 合并问题
"""

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime
from base64 import b64encode
from pathlib import Path

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
DB_PATH = WORKSPACE / "jira-reports" / "fy26_data.db"
CONFIG_FILE = WORKSPACE / ".jira-config"

# 读取 Jira 配置
def load_config():
    config = {}
    with open(CONFIG_FILE) as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                config[key] = value.strip('"').strip("'")
    return config

config = load_config()
JIRA_URL = config['JIRA_URL']
JIRA_USER = config['JIRA_USER']
JIRA_TOKEN = config['JIRA_TOKEN']

# 认证
auth_string = f"{JIRA_USER}:{JIRA_TOKEN}"
auth_bytes = auth_string.encode('ascii')
auth_b64 = b64encode(auth_bytes).decode('ascii')
HEADERS = {
    'Authorization': f'Basic {auth_b64}',
    'Content-Type': 'application/json'
}

# 项目列表
PROJECTS = [
    "CNTEC", "CNTOM", "CNTDM", "CNTMM", "CNTD", "CNTEST", "CNENG", "CNINFA",
    "CNCA", "CPR", "EPCH", "CNCRM", "CNDIN", "SWMP", "CDM", "CMDM",
    "CNSCM", "OF", "CNRTPRJ", "CSCPVT", "CNPMO", "CYBERPJT"
]

# 初始化数据库
def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    # 读取并执行 schema
    schema_file = WORKSPACE / "scripts" / "fy26_db_schema.sql"
    with open(schema_file) as f:
        conn.executescript(f.read())
    
    conn.commit()
    return conn

# 抓取 Epic
def fetch_epics(conn, project):
    print(f"  - 抓取 {project} 项目的 Epic...")
    
    jql = f"project = {project} AND issuetype = Epic ORDER BY created DESC"
    url = f"{JIRA_URL}/rest/api/3/search"
    params = {
        'jql': jql,
        'maxResults': 1000,
        'fields': 'summary,status,assignee,created,labels,parent,project'
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        issues = data.get('issues', [])
        count = len(issues)
        
        # 插入数据库
        for issue in issues:
            key = issue['key']
            fields = issue['fields']
            
            conn.execute('''
                INSERT OR REPLACE INTO epics 
                (key, project, summary, status, assignee, parent_key, created, labels, raw_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                key,
                project,
                fields.get('summary', ''),
                fields.get('status', {}).get('name', ''),
                fields.get('assignee', {}).get('displayName', '未分配') if fields.get('assignee') else '未分配',
                fields.get('parent', {}).get('key') if fields.get('parent') else None,
                fields.get('created', '')[:10],
                json.dumps(fields.get('labels', [])),
                json.dumps(issue)
            ))
        
        conn.commit()
        
        # 记录日志
        conn.execute('''
            INSERT INTO fetch_log (project, issue_type, count, status)
            VALUES (?, ?, ?, ?)
        ''', (project, 'Epic', count, 'success'))
        conn.commit()
        
        print(f"    ✅ 找到 {count} 个 Epic")
        return count
        
    except Exception as e:
        print(f"    ❌ 失败: {e}")
        conn.execute('''
            INSERT INTO fetch_log (project, issue_type, count, status, error_message)
            VALUES (?, ?, ?, ?, ?)
        ''', (project, 'Epic', 0, 'failed', str(e)))
        conn.commit()
        return 0

# 抓取 Feature（通过 parent key）
def fetch_features_by_keys(conn, feature_keys):
    if not feature_keys:
        return 0
    
    print(f"\n📊 Step 2: 抓取 {len(feature_keys)} 个 CNTIN Feature...")
    
    # 分批抓取（每次最多 100 个）
    batch_size = 100
    total_count = 0
    
    for i in range(0, len(feature_keys), batch_size):
        batch = feature_keys[i:i+batch_size]
        jql = f"key in ({','.join(batch)})"
        url = f"{JIRA_URL}/rest/api/3/search"
        params = {
            'jql': jql,
            'maxResults': batch_size,
            'fields': 'summary,status,assignee,parent,labels,project'
        }
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=60)
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
                    fields.get('project', {}).get('key', 'CNTIN'),
                    fields.get('summary', ''),
                    fields.get('status', {}).get('name', ''),
                    fields.get('assignee', {}).get('displayName', '未分配') if fields.get('assignee') else '未分配',
                    fields.get('parent', {}).get('key') if fields.get('parent') else None,
                    json.dumps(fields.get('labels', [])),
                    json.dumps(issue)
                ))
            
            total_count += len(issues)
            
        except Exception as e:
            print(f"  ❌ 批次 {i//batch_size + 1} 失败: {e}")
    
    conn.commit()
    print(f"✅ 抓取了 {total_count} 个 Feature")
    return total_count

# 抓取 Initiative（通过 parent key）
def fetch_initiatives_by_keys(conn, init_keys):
    if not init_keys:
        return 0
    
    print(f"\n📊 Step 3: 抓取 {len(init_keys)} 个 CNTIN Initiative...")
    
    batch_size = 100
    total_count = 0
    
    for i in range(0, len(init_keys), batch_size):
        batch = init_keys[i:i+batch_size]
        jql = f"key in ({','.join(batch)})"
        url = f"{JIRA_URL}/rest/api/3/search"
        params = {
            'jql': jql,
            'maxResults': batch_size,
            'fields': 'summary,status,assignee,labels,project'
        }
        
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=60)
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
                    fields.get('project', {}).get('key', 'CNTIN'),
                    fields.get('summary', ''),
                    fields.get('status', {}).get('name', ''),
                    fields.get('assignee', {}).get('displayName', '未分配') if fields.get('assignee') else '未分配',
                    json.dumps(fields.get('labels', [])),
                    json.dumps(issue)
                ))
            
            total_count += len(issues)
            
        except Exception as e:
            print(f"  ❌ 批次 {i//batch_size + 1} 失败: {e}")
    
    conn.commit()
    print(f"✅ 抓取了 {total_count} 个 Initiative")
    return total_count

# 抓取所有 FY26_INIT Feature
def fetch_all_fy26_features(conn):
    print(f"\n📊 Step 4: 抓取所有带 FY26_INIT 标签的 CNTIN Feature...")
    
    jql = "project = CNTIN AND issuetype = Feature AND labels = FY26_INIT ORDER BY created DESC"
    url = f"{JIRA_URL}/rest/api/3/search"
    params = {
        'jql': jql,
        'maxResults': 1000,
        'fields': 'summary,status,assignee,parent,labels,project'
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        issues = data.get('issues', [])
        count = len(issues)
        
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
        
        conn.commit()
        print(f"✅ 找到 {count} 个带 FY26_INIT 标签的 Feature")
        return count
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return 0

# 抓取所有 FY26_INIT Initiative
def fetch_all_fy26_initiatives(conn):
    print(f"\n📊 Step 5: 抓取所有带 FY26_INIT 标签的 CNTIN Initiative...")
    
    jql = "project = CNTIN AND issuetype = Initiative AND labels = FY26_INIT ORDER BY created DESC"
    url = f"{JIRA_URL}/rest/api/3/search"
    params = {
        'jql': jql,
        'maxResults': 1000,
        'fields': 'summary,status,assignee,labels,project'
    }
    
    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        issues = data.get('issues', [])
        count = len(issues)
        
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
        print(f"✅ 找到 {count} 个带 FY26_INIT 标签的 Initiative")
        return count
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return 0

# 主函数
def main():
    print("🚀 开始抓取 FY26_INIT 数据 (v5.0 - SQLite 架构)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {DB_PATH}")
    print("")
    
    # 初始化数据库
    conn = init_db()
    
    # Step 1: 抓取所有项目的 Epic
    print("📊 Step 1: 抓取其他项目的所有 Epic...")
    total_epics = 0
    for project in PROJECTS:
        count = fetch_epics(conn, project)
        total_epics += count
    
    print(f"\n✅ Step 1 完成: 共抓取 {total_epics} 个 Epic")
    
    # Step 2: 获取所有有 parent 的 Epic 的 Feature Key
    cursor = conn.execute('SELECT DISTINCT parent_key FROM epics WHERE parent_key IS NOT NULL')
    feature_keys = [row[0] for row in cursor.fetchall()]
    
    if feature_keys:
        fetch_features_by_keys(conn, feature_keys)
    
    # Step 3: 获取所有 Feature 的 Initiative Key
    cursor = conn.execute('SELECT DISTINCT parent_key FROM features WHERE parent_key IS NOT NULL')
    init_keys = [row[0] for row in cursor.fetchall()]
    
    if init_keys:
        fetch_initiatives_by_keys(conn, init_keys)
    
    # Step 4 & 5: 抓取所有 FY26_INIT 标签的数据
    fetch_all_fy26_features(conn)
    fetch_all_fy26_initiatives(conn)
    
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
    print(f"   - Epics: {epic_count}")
    print(f"   - Features: {feature_count}")
    print(f"   - Initiatives: {init_count}")
    print(f"\n📁 数据库: {DB_PATH}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn.close()

if __name__ == '__main__':
    main()
