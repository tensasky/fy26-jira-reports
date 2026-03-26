#!/usr/bin/env python3
"""
FY26_Intake_Cost 报表数据抓取
- 抓取 CNTIN-730 Initiatives (FY26_INIT 标签)
- 新增字段：affects version, fix version, InitiativeChildCount, components, linked issues
"""

import json
import requests
import base64
import sqlite3
import os
import re
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def parse_adf_to_text(adf_content):
    """将 Atlassian Document Format (ADF) 解析为纯文本"""
    if not adf_content or not isinstance(adf_content, dict):
        return ""
    
    texts = []
    
    def extract_text(node):
        if isinstance(node, dict):
            # 提取文本节点
            if node.get('type') == 'text':
                text = node.get('text', '')
                # 处理 marks (加粗、下划线等)
                marks = node.get('marks', [])
                for mark in marks:
                    if mark.get('type') == 'strong':
                        text = f"**{text}**"
                    elif mark.get('type') == 'underline':
                        text = f"_{text}_"
                texts.append(text)
            # 处理 mention
            elif node.get('type') == 'mention':
                attrs = node.get('attrs', {})
                texts.append(attrs.get('text', ''))
            # 处理 emoji
            elif node.get('type') == 'emoji':
                attrs = node.get('attrs', {})
                texts.append(attrs.get('text', ''))
            # 处理换行
            elif node.get('type') == 'hardBreak':
                texts.append('\n')
            # 递归处理 content
            if 'content' in node:
                for child in node['content']:
                    extract_text(child)
        elif isinstance(node, list):
            for item in node:
                extract_text(item)
    
    extract_text(adf_content)
    
    # 合并文本并清理
    result = ''.join(texts)
    # 去除多余空白
    result = re.sub(r'\n+', '\n', result)
    result = re.sub(r' +', ' ', result)
    return result.strip()

# 配置
DB_PATH = "/Users/admin/.openclaw/workspace/projects/fy26-intake-cost/intake_cost.db"
JIRA_URL = "https://lululemon.atlassian.net"
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "rcheng2@lululemon.com")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN", "")

if not JIRA_TOKEN:
    print("❌ 请设置 JIRA_API_TOKEN 环境变量")
    exit(1)

auth_str = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
auth_b64 = base64.b64encode(auth_str.encode()).decode()
headers = {
    'Authorization': f'Basic {auth_b64}',
    'Content-Type': 'application/json'
}

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intakes (
            key TEXT PRIMARY KEY,
            summary TEXT,
            description TEXT,
            status TEXT,
            status_category TEXT,
            assignee TEXT,
            reporter TEXT,
            created TEXT,
            updated TEXT,
            labels TEXT,
            components TEXT,
            affects_versions TEXT,
            fix_versions TEXT,
            initiative_child_count INTEGER,
            linked_issues TEXT,
            issue_links TEXT,
            intake_type TEXT,
            cost_rmb REAL,
            approver TEXT,
            scope TEXT,
            follow_up TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fetch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            count INTEGER,
            status TEXT,
            message TEXT
        )
    ''')
    
    conn.commit()
    return conn, cursor

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

def parse_components(fields):
    """解析 components 字段"""
    components = fields.get('components', [])
    return ', '.join([c.get('name', '') for c in components]) if components else ''

def parse_versions(fields, version_type):
    """解析 affectsVersions 或 fixVersions"""
    versions = fields.get(version_type, [])
    return ', '.join([v.get('name', '') for v in versions]) if versions else ''

def parse_linked_issues(fields):
    """解析 issue links，提取 linked work items"""
    issue_links = fields.get('issuelinks', [])
    linked = []
    
    for link in issue_links:
        # 只提取 outwardIssue（当前 ticket 链接到的其他 ticket）
        outward = link.get('outwardIssue')
        if outward:
            linked.append({
                'key': outward['key'],
                'type': link.get('type', {}).get('outward', 'links to')
            })
        # 也包含 inwardIssue（被其他 ticket 链接的）
        inward = link.get('inwardIssue')
        if inward:
            linked.append({
                'key': inward['key'],
                'type': link.get('type', {}).get('inward', 'is linked by')
            })
    
    return linked

def fetch_intake_cost_data(cursor):
    """抓取 CNTIN-730 Intake 数据"""
    print("\n📋 抓取 CNTIN-730 Intakes...")
    
    # 需要的字段 - 包含自定义字段
    fields = [
        "key", "summary", "description", "status", "assignee", "reporter",
        "created", "updated", "labels", "components",
        "versions", "fixVersions",
        "customfield_16143",  # InitiativeChildCount
        "customfield_16201",  # Cost/Estimated Cost (假设)
        "customfield_16144",  # Type/Intake Type (假设)
        "customfield_16145",  # Approver (假设)
        "customfield_16146",  # Scope (假设)
        "customfield_16147",  # Follow up (假设)
        "issuelinks"
    ]
    
    issues = fetch_issues_jql(
        "project = CNTIN AND issuetype = Initiative AND parent = CNTIN-730 ORDER BY key ASC",
        fields
    )
    
    print(f"  ✓ 抓到 {len(issues)} 个 Intakes")
    
    # 清空旧数据
    cursor.execute("DELETE FROM intakes")
    
    for issue in issues:
        fields = issue['fields']
        
        # 解析 linked issues
        linked = parse_linked_issues(fields)
        
        # 解析 ADF description
        adf_desc = fields.get('description')
        plain_desc = parse_adf_to_text(adf_desc) if adf_desc else ''
        
        # 获取自定义字段值
        intake_type = fields.get('customfield_16144') or 'TBD'
        cost_value = fields.get('customfield_16201') or 0
        approver = fields.get('customfield_16145') or ''
        scope = fields.get('customfield_16146') or ''
        follow_up = fields.get('customfield_16147') or ''
        
        cursor.execute('''
            INSERT OR REPLACE INTO intakes (
                key, summary, description, status, status_category, assignee, reporter,
                created, updated, labels, components, affects_versions, fix_versions,
                initiative_child_count, linked_issues, issue_links,
                intake_type, cost_rmb, approver, scope, follow_up
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            issue['key'],
            fields.get('summary', ''),
            plain_desc,
            fields.get('status', {}).get('name', ''),
            fields.get('status', {}).get('statusCategory', {}).get('name', ''),
            fields.get('assignee', {}).get('displayName', 'Unassigned') if fields.get('assignee') else 'Unassigned',
            fields.get('reporter', {}).get('displayName', 'Unknown') if fields.get('reporter') else 'Unknown',
            fields.get('created', ''),
            fields.get('updated', ''),
            json.dumps(fields.get('labels', [])),
            parse_components(fields),
            parse_versions(fields, 'versions'),
            parse_versions(fields, 'fixVersions'),
            fields.get('customfield_16143') or 0,
            json.dumps(linked),
            json.dumps(fields.get('issuelinks', [])),
            intake_type if intake_type else 'TBD',
            float(cost_value) if cost_value else 0,
            approver,
            scope,
            follow_up
        ))
    
    # 记录日志
    cursor.execute(
        "INSERT INTO fetch_log (count, status, message) VALUES (?, ?, ?)",
        (len(issues), "success", f"Fetched {len(issues)} intakes")
    )
    
    return issues

def generate_stats(cursor):
    """生成统计信息"""
    print("\n📊 数据统计:")
    
    cursor.execute("SELECT COUNT(*) FROM intakes")
    total = cursor.fetchone()[0]
    
    # 按状态分类统计
    cursor.execute('''
        SELECT status_category, COUNT(*) 
        FROM intakes 
        GROUP BY status_category 
        ORDER BY COUNT(*) DESC
    ''')
    status_counts = cursor.fetchall()
    
    print(f"  - 总数: {total}")
    for status, count in status_counts:
        print(f"  - {status}: {count}")
    
    # 统计有 linked issues 的数量
    cursor.execute("SELECT COUNT(*) FROM intakes WHERE linked_issues != '[]'")
    with_links = cursor.fetchone()[0]
    print(f"  - 有关联项: {with_links}")

def main():
    print("🚀 FY26_Intake_Cost 数据抓取开始...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    conn, cursor = init_db()
    
    try:
        fetch_intake_cost_data(cursor)
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
