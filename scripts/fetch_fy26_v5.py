#!/usr/bin/env python3
"""
FY26_INIT 数据抓取脚本 v5.2
完整逻辑：
1. 抓取所有带 FY26_INIT 标签的 CNTIN Initiative
2. 抓取这些 Initiative 下的所有 Feature
3. 抓取这些 Feature 下的所有 Epic
4. 额外抓取所有项目的所有 Epic（确保数据完整）
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
JIRA_URL = config.get('JIRA_URL') or config.get('JIRA_BASE_URL')
JIRA_USER = config.get('JIRA_USER') or config.get('JIRA_USER_EMAIL')
JIRA_TOKEN = config.get('JIRA_TOKEN') or config.get('JIRA_API_TOKEN')

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

# 抓取所有 FY26_INIT Initiative
def fetch_fy26_initiatives(conn):
    print(f"\n📊 Step 1: 抓取所有带 FY26_INIT 标签的 CNTIN Initiative...")
    
    jql = "project = CNTIN AND issuetype = Initiative AND labels = FY26_INIT ORDER BY created DESC"
    url = f"{JIRA_URL}/rest/api/3/search/jql"
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
        return [issue['key'] for issue in issues]
        
    except Exception as e:
        print(f"❌ 失败: {e}")
        return []

# 抓取 Initiative 下的所有 Feature
def fetch_features_by_initiative(conn, init_keys):
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

# 批量抓取 Epic（使用 parent in 语法）
def fetch_epics_by_features_batch(conn, feature_keys):
    if not feature_keys:
        return 0
    
    print(f"\n📊 Step 3: 批量抓取 {len(feature_keys)} 个 Feature 下的所有 Epic...")
    
    total_count = 0
    batch_size = 50  # 每批处理 50 个 Feature
    
    for i in range(0, len(feature_keys), batch_size):
        batch = feature_keys[i:i+batch_size]
        batch_str = ','.join(batch)
        
        jql = f"parent in ({batch_str}) AND issuetype = Epic ORDER BY created DESC"
        url = f"{JIRA_URL}/rest/api/3/search/jql"
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

# 抓取所有项目的所有 Epic
def fetch_all_epics(conn):
    print(f"\n📊 Step 4: 抓取所有项目的所有 Epic...")
    
    total_count = 0
    
    for project in PROJECTS:
        print(f"  - 抓取 {project} 项目的 Epic...")
        
        jql = f"project = {project} AND issuetype = Epic ORDER BY created DESC"
        url = f"{JIRA_URL}/rest/api/3/search/jql"
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
            
            total_count += len(issues)
            print(f"    ✅ {project}: {len(issues)} 个 Epic")
            
        except Exception as e:
            print(f"    ❌ {project} 失败: {e}")
    
    conn.commit()
    print(f"✅ 共抓取了 {total_count} 个 Epic")
    return total_count

# 主函数
def main():
    print("🚀 开始抓取 FY26_INIT 数据 (v5.2 - 完整抓取逻辑)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {DB_PATH}")
    print("")
    
    # 初始化数据库
    conn = init_db()
    
    # Step 1: 抓取所有 FY26_INIT Initiative
    init_keys = fetch_fy26_initiatives(conn)
    
    # Step 2: 抓取这些 Initiative 下的所有 Feature
    fetch_features_by_initiative(conn, init_keys)
    
    # Step 3: 获取所有 Feature 的 key，批量抓取它们下面的 Epic
    cursor = conn.execute('SELECT DISTINCT key FROM features')
    feature_keys = [row[0] for row in cursor.fetchall()]
    fetch_epics_by_features_batch(conn, feature_keys)
    
    # Step 4: 抓取所有项目的所有 Epic（确保数据完整）
    fetch_all_epics(conn)
    
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
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn.close()

if __name__ == '__main__':
    main()
