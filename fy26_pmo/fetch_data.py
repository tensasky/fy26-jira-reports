#!/usr/bin/env python3
"""
FY26_PMO 数据抓取脚本 - 修复版
正确的抓取逻辑：
1. 抓取所有Epics (22个项目)
2. 抓取所有FY26_INIT Initiatives (直接查询)
3. 从Initiatives抓取子Features (正向查询)
4. 从Epics提取parent Features (反向查询)
5. 合并Features并去重
"""

import json
import requests
import base64
import sqlite3
import os
from datetime import datetime
from collections import Counter
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# 配置
DB_PATH = "/Users/admin/.openclaw/workspace/fy26_pmo/jira_report.db"
OUTPUT_DIR = "/Users/admin/.openclaw/workspace/fy26_pmo"
JIRA_URL = "https://lululemon.atlassian.net"
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "rcheng2@lululemon.com")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN", "")

if not JIRA_TOKEN:
    print("❌ 请设置 JIRA_API_TOKEN 环境变量")
    exit(1)

# 22个Epic项目（分批处理）
# OF是JQL保留字，需要单独处理
PROJECT_BATCHES = [
    ["CNTEC","CNTOM","CNTDM","CNTMM","CNTD"],
    ["CNTEST","CNENG","CNINFA","CNCA","CPR"],
    ["EPCH","CNCRM","CNDIN","SWMP","CDM"],
    ["CMDM","CNSCM","CNRTPRJ","CSCPVT"],  # 去掉OF，单独处理
    ["CNPMO","CYBERPJT"]
]

auth_str = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
auth_b64 = base64.b64encode(auth_str.encode()).decode()
headers = {
    'Authorization': f'Basic {auth_b64}',
    'Content-Type': 'application/json'
}

def log_fetch(cursor, step, project, count, status, message=""):
    cursor.execute('''
        INSERT INTO fetch_log (step, project, count, status, message)
        VALUES (?, ?, ?, ?, ?)
    ''', (step, project, count, status, message))

def fetch_issues_jql(jql, fields, page_size=100):
    """抓取所有issues，支持分页"""
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    all_issues = []
    next_page_token = None
    page = 1

    while True:
        payload = {"jql": jql, "maxResults": page_size, "fields": fields}
        if next_page_token:
            payload["nextPageToken"] = next_page_token

        try:
            response = requests.post(url, headers=headers, json=payload, verify=False, timeout=120)
            response.raise_for_status()
            data = response.json()

            issues = data.get('issues', [])
            all_issues.extend(issues)

            # 检查是否有下一页
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break

            page += 1
            if page % 5 == 0:
                print(f"      分页进度: {len(all_issues)} 个...")

        except Exception as e:
            print(f"    ⚠️ 请求失败: {e}")
            break

    return all_issues

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    return conn, cursor

def step1_fetch_epics(cursor):
    """Step 1: 从22个项目抓取所有Epics"""
    print("\n📋 Step 1: 从22个项目抓取所有Epics...")
    
    all_epics = []
    
    # 先处理常规项目
    for i, batch in enumerate(PROJECT_BATCHES, 1):
        print(f"  批次 {i}/{len(PROJECT_BATCHES)}: {','.join(batch)}")
        projects_str = ','.join(batch)
        epics = fetch_issues_jql(
            f"project in ({projects_str}) AND issuetype = Epic AND created >= '2025-11-01' ORDER BY project ASC, key ASC",
            ["key", "summary", "description", "status", "assignee", "created", "updated", "project", "parent", "labels"]
        )
        print(f"    ✓ 找到 {len(epics)} 个Epics")
        all_epics.extend(epics)
        log_fetch(cursor, "Step1", f"batch_{i}", len(epics), "success")
        
        # 显示每个项目的分布
        from collections import Counter
        project_counts = Counter([e['fields'].get('project', {}).get('key', 'UNKNOWN') for e in epics])
        for proj, cnt in sorted(project_counts.items()):
            print(f"      - {proj}: {cnt}")
    
    # 单独处理OF项目（JQL保留字）
    print("  单独抓取OF项目...")
    of_epics = fetch_issues_jql(
        "project = 'OF' AND issuetype = Epic AND created >= '2025-11-01' ORDER BY key ASC",
        ["key", "summary", "description", "status", "assignee", "created", "updated", "project", "parent", "labels"]
    )
    print(f"    ✓ 找到 {len(of_epics)} 个Epics")
    all_epics.extend(of_epics)
    log_fetch(cursor, "Step1", "OF", len(of_epics), "success")
    
    print(f"  ✓ 总共找到 {len(all_epics)} 个Epics")
    
    # 存入数据库
    epics_with_parent = 0
    epics_no_parent = 0
    
    for epic in all_epics:
        epic_key = epic['key']
        fields = epic['fields']
        parent = fields.get('parent')
        parent_key = parent['key'] if parent else None
        has_parent = 1 if parent_key else 0
        
        if has_parent:
            epics_with_parent += 1
        else:
            epics_no_parent += 1
        
        cursor.execute('''
            INSERT OR REPLACE INTO epics 
            (key, project, summary, status, assignee, parent_key, labels, created, updated, has_parent)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            epic_key,
            fields.get('project', {}).get('key', ''),
            fields.get('summary', ''),
            fields.get('status', {}).get('name', ''),
            fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
            parent_key,
            json.dumps(fields.get('labels', [])),
            fields.get('created', ''),
            fields.get('updated', ''),
            has_parent
        ))
    
    print(f"    - 有parent的Epics: {epics_with_parent}")
    print(f"    - 无parent的Epics: {epics_no_parent}")
    log_fetch(cursor, "Step1", "total", len(all_epics), "success", 
              f"with_parent:{epics_with_parent},no_parent:{epics_no_parent}")
    
    return all_epics

def step2_fetch_fy26_init_initiatives(cursor):
    """Step 2: 抓取所有带FY26_INIT标签的CNTIN Initiatives (2025-11-01后创建)"""
    print("\n📋 Step 2: 抓取所有带FY26_INIT标签的CNTIN Initiatives...")
    
    initiatives = fetch_issues_jql(
        "project = CNTIN AND issuetype = Initiative AND labels = 'FY26_INIT' AND created >= '2025-11-01' ORDER BY key ASC",
        ["key", "summary", "description", "status", "assignee", "created", "updated", "labels"]
    )
    
    print(f"  ✓ 抓到 {len(initiatives)} 个Initiatives")
    
    # 存入数据库
    for init in initiatives:
        fields = init['fields']
        cursor.execute('''
            INSERT OR REPLACE INTO initiatives 
            (key, summary, status, assignee, labels, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            init['key'],
            fields.get('summary', ''),
            fields.get('status', {}).get('name', ''),
            fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
            json.dumps(fields.get('labels', [])),
            fields.get('created', ''),
            fields.get('updated', '')
        ))
    
    log_fetch(cursor, "Step2", "CNTIN_FY26_INIT", len(initiatives), "success")
    return initiatives

def step3_fetch_all_features(cursor):
    """Step 3: 抓取所有Features (两个来源合并)"""
    print("\n📋 Step 3: 抓取所有CNTIN Features...")
    
    all_features = []
    
    # 来源1: 从Epics反向提取的Feature keys
    print("  来源1: 从Epics提取Feature keys...")
    cursor.execute("SELECT DISTINCT parent_key FROM epics WHERE parent_key LIKE 'CNTIN-%'")
    feature_keys_from_epics = [row[0] for row in cursor.fetchall()]
    print(f"    从Epics提取到 {len(feature_keys_from_epics)} 个Feature keys")
    
    if feature_keys_from_epics:
        batch_size = 50
        for i in range(0, len(feature_keys_from_epics), batch_size):
            batch = feature_keys_from_epics[i:i+batch_size]
            features = fetch_issues_jql(
                f"key in ({','.join(batch)}) ORDER BY key ASC",
                ["key", "summary", "description", "status", "assignee", "created", "updated", "parent", "labels"]
            )
            all_features.extend(features)
        print(f"    ✓ 从Epics来源抓到 {len(all_features)} 个Features")
    
    # 来源2: 从Initiatives正向抓取子Features
    print("  来源2: 从Initiatives抓取子Features...")
    cursor.execute("SELECT key FROM initiatives")
    initiative_keys = [row[0] for row in cursor.fetchall()]
    print(f"    从 {len(initiative_keys)} 个Initiatives抓取...")
    
    features_from_initiatives = []
    for i, init_key in enumerate(initiative_keys):
        if i > 0 and i % 10 == 0:
            print(f"    进度: {i}/{len(initiative_keys)}")
        
        features = fetch_issues_jql(
            f"project = CNTIN AND issuetype = Feature AND parent = {init_key} AND created >= '2025-11-01' ORDER BY key ASC",
            ["key", "summary", "description", "status", "assignee", "created", "updated", "parent", "labels"]
        )
        if features:
            features_from_initiatives.extend(features)
    
    print(f"    ✓ 从Initiatives来源抓到 {len(features_from_initiatives)} 个Features")
    
    # 合并并去重
    feature_keys_set = set()
    merged_features = []
    
    for feat in all_features + features_from_initiatives:
        key = feat['key']
        if key not in feature_keys_set:
            feature_keys_set.add(key)
            merged_features.append(feat)
    
    print(f"\n  ✓ 合并去重后: {len(merged_features)} 个唯一Features")
    
    # 清空并重新存入数据库
    cursor.execute("DELETE FROM features")
    
    for feat in merged_features:
        fields = feat['fields']
        parent = fields.get('parent')
        parent_key = parent['key'] if parent else None
        
        cursor.execute('''
            INSERT OR REPLACE INTO features 
            (key, summary, status, assignee, parent_key, labels, created, updated)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            feat['key'],
            fields.get('summary', ''),
            fields.get('status', {}).get('name', ''),
            fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
            parent_key,
            json.dumps(fields.get('labels', [])),
            fields.get('created', ''),
            fields.get('updated', '')
        ))
    
    log_fetch(cursor, "Step3", "CNTIN", len(merged_features), "success", 
              f"from_epics:{len(all_features)},from_init:{len(features_from_initiatives)}")
    return merged_features

def generate_stats(cursor):
    print("\n📊 数据统计:")
    
    cursor.execute("SELECT COUNT(*) FROM initiatives")
    init_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM features")
    feat_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM epics")
    epic_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM epics WHERE has_parent = 1")
    epic_with_parent = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM epics WHERE has_parent = 0")
    epic_no_parent = cursor.fetchone()[0]
    
    print(f"  - Initiatives (FY26_INIT): {init_count}")
    print(f"  - Features: {feat_count}")
    print(f"  - Epics: {epic_count}")
    print(f"    - 有parent: {epic_with_parent}")
    print(f"    - 无parent: {epic_no_parent}")
    
    # Features按Initiative分布
    print(f"\n  Features按Initiative分布(前10):")
    cursor.execute('''
        SELECT parent_key, COUNT(*) as cnt 
        FROM features 
        WHERE parent_key LIKE 'CNTIN-%' 
        GROUP BY parent_key 
        ORDER BY cnt DESC 
        LIMIT 10
    ''')
    for row in cursor.fetchall():
        print(f"    {row[0]}: {row[1]} Features")

def main():
    print("🚀 FY26_PMO 数据抓取开始...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn, cursor = init_db()
    
    try:
        # 清空旧数据
        print("\n🧹 清空旧数据...")
        cursor.execute("DELETE FROM initiatives")
        cursor.execute("DELETE FROM features")
        cursor.execute("DELETE FROM epics")
        cursor.execute("DELETE FROM fetch_log")
        
        # 执行步骤
        step1_fetch_epics(cursor)
        step2_fetch_fy26_init_initiatives(cursor)
        step3_fetch_all_features(cursor)
        
        generate_stats(cursor)
        
        conn.commit()
        print("\n✅ 数据抓取完成!")
        print(f"数据库: {DB_PATH}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    main()
