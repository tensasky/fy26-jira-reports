#!/usr/bin/env python3
"""
FY26_Intake_Cost 报表数据抓取脚本
=====================================

功能：从 Jira 抓取 CNTIN-730 下的所有 Initiatives，存储到 SQLite 数据库
依赖：requests, urllib3 (see requirements below)
环境变量：JIRA_API_TOKEN (required), JIRA_EMAIL (optional, default: rcheng2@lululemon.com)

数据流：
--------
Jira REST API v3 (/rest/api/3/search/jql)
    → fetch_issues_jql() [分页处理]
    → parse_adf_to_text() [ADF解析]
    → SQLite (intake_cost.db)

JQL 查询逻辑：
--------------
parent = CNTIN-730 AND issuetype = Initiative ORDER BY key ASC

说明：
- CNTIN-730 是一个 Goal 类型（hierarchy level 4）
- 子项是 Initiative 类型
- 截至 2026-04-02，共有 167 个 Initiatives

字段映射：
----------
| 数据库字段            | Jira 字段                  | 说明                    |
|----------------------|---------------------------|------------------------|
| key                  | key                       | Ticket 编号             |
| summary              | fields.summary            | 标题                    |
| description          | fields.description (ADF)  | 描述（已解析为纯文本）    |
| status               | fields.status.name        | 状态名称                |
| status_category      | fields.status.statusCategory.name | 状态分类       |
| assignee             | fields.assignee.displayName | 负责人                |
| reporter             | fields.reporter.displayName | 创建者                |
| created              | fields.created            | 创建时间                |
| updated              | fields.updated            | 更新时间                |
| labels               | fields.labels             | 标签（JSON数组）         |
| components           | fields.components         | 组件名称（逗号分隔）      |
| affects_versions     | fields.versions           | 影响版本                |
| fix_versions         | fields.fixVersions        | 修复版本                |
| initiative_child_count | customfield_16143       | 子项数量（用于成本计算）  |
| linked_issues        | fields.issuelinks         | 关联的 tickets           |
| issue_links          | fields.issuelinks (raw)   | 原始 issue links         |

依赖安装：
----------
pip install requests urllib3

系统依赖（可选）：
- 7z (p7zip): 用于生成 AES-256 加密的 ZIP 文件
  brew install p7zip

运行方式：
----------
# 1. 设置环境变量
export JIRA_API_TOKEN="your_token_here"

# 2. 运行脚本
python3 scripts/fetch_intake_cost.py

# 3. 完整流程（包含生成 HTML 和发送邮件）
./run.sh

调试技巧：
----------
# 测试 Jira API 连接
curl -X POST \
  -H "Authorization: Basic $(echo -n 'rcheng2@lululemon.com:$JIRA_API_TOKEN' | base64)" \
  -H "Content-Type: application/json" \
  https://lululemon.atlassian.net/rest/api/3/search/jql \
  -d '{"jql": "parent = CNTIN-730", "maxResults": 5}'

# 查看数据库内容
sqlite3 intake_cost.db "SELECT key, summary, status FROM intakes LIMIT 10"

故障排除：
----------
问题："请设置 JIRA_API_TOKEN 环境变量"
解决：export JIRA_API_TOKEN="your_token"

问题：0 records returned
解决：
1. 检查 token 是否过期
2. 确认 token 有权限访问 CNTIN 项目
3. 检查网络连接

作者：Tensasky
最后更新：2026-04-02
"""

import json
import requests
import base64
import sqlite3
import os
import re
from datetime import datetime
from urllib3.exceptions import InsecureRequestWarning

# 禁用 SSL 证书验证警告（Jira 使用自签名证书时需要）
# 注意：生产环境建议使用 verify=True 并配置 CA 证书
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


def parse_adf_to_text(adf_content):
    """
    将 Atlassian Document Format (ADF) 解析为纯文本
    
    ADF 是 Jira 的富文本格式，结构为嵌套的 JSON。
    此函数递归遍历 ADF 树，提取所有文本节点。
    
    参数:
        adf_content (dict): Jira API 返回的 description 字段 (ADF 格式)
    
    返回:
        str: 纯文本内容，去除多余空白
    
    示例:
        >>> adf = {"type": "doc", "content": [{"type": "paragraph", 
        ...           "content": [{"type": "text", "text": "Hello"}]}]}
        >>> parse_adf_to_text(adf)
        'Hello'
    
    支持的 ADF 节点类型：
        - text: 普通文本（支持 marks 加粗/下划线）
        - mention: @用户提及
        - emoji: 表情符号
        - hardBreak: 硬换行
    """
    if not adf_content or not isinstance(adf_content, dict):
        return ""
    
    texts = []
    
    def extract_text(node):
        """递归提取文本的辅助函数"""
        if isinstance(node, dict):
            # 文本节点
            if node.get('type') == 'text':
                text = node.get('text', '')
                # 处理富文本标记（加粗、下划线等）
                marks = node.get('marks', [])
                for mark in marks:
                    if mark.get('type') == 'strong':
                        text = f"**{text}**"
                    elif mark.get('type') == 'underline':
                        text = f"_{text}_"
                texts.append(text)
            
            # 提及节点 (@username)
            elif node.get('type') == 'mention':
                attrs = node.get('attrs', {})
                texts.append(attrs.get('text', ''))
            
            # 表情符号节点
            elif node.get('type') == 'emoji':
                attrs = node.get('attrs', {})
                texts.append(attrs.get('text', ''))
            
            # 硬换行
            elif node.get('type') == 'hardBreak':
                texts.append('\n')
            
            # 递归处理子内容
            if 'content' in node:
                for child in node['content']:
                    extract_text(child)
        
        elif isinstance(node, list):
            for item in node:
                extract_text(item)
    
    extract_text(adf_content)
    
    # 合并并清理文本
    result = ''.join(texts)
    result = re.sub(r'\n+', '\n', result)  # 合并连续换行
    result = re.sub(r' +', ' ', result)    # 合并连续空格
    return result.strip()


# =============================================================================
# 配置区域
# =============================================================================

# 数据库路径
DB_PATH = "/Users/admin/.openclaw/workspace/projects/fy26-intake-cost/intake_cost.db"

# Jira API 配置
JIRA_URL = "https://lululemon.atlassian.net"
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "rcheng2@lululemon.com")
JIRA_TOKEN = os.getenv("JIRA_API_TOKEN", "")

# 验证必需的 JIRA_API_TOKEN
if not JIRA_TOKEN:
    print("❌ 请设置 JIRA_API_TOKEN 环境变量")
    print("   获取方式: https://id.atlassian.com/manage-profile/security/api-tokens")
    exit(1)

# 构建 Basic Auth Header
# 注意：必须动态计算 base64，不能使用预计算的环境变量
# 原因：$JIRA_AUTH 环境变量可能在某些 shell 中格式不正确
auth_str = f"{JIRA_EMAIL}:{JIRA_TOKEN}"
auth_b64 = base64.b64encode(auth_str.encode()).decode()
headers = {
    'Authorization': f'Basic {auth_b64}',
    'Content-Type': 'application/json'
}


def init_db():
    """
    初始化 SQLite 数据库
    
    创建两个表：
    1. intakes: 存储所有 initiative 数据
    2. fetch_log: 记录每次抓取的日志（用于审计和调试）
    
    返回:
        tuple: (connection, cursor)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 主数据表 - 存储 initiative 详细信息
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS intakes (
            key TEXT PRIMARY KEY,              -- CNTIN-XXX 格式的 ticket key
            summary TEXT,                      -- 标题
            description TEXT,                  -- 描述（ADF解析后的纯文本）
            status TEXT,                       -- 当前状态名称
            status_category TEXT,              -- 状态分类（To Do, In Progress, Done）
            assignee TEXT,                     -- 负责人
            reporter TEXT,                     -- 创建者
            created TEXT,                      -- 创建时间（ISO 8601）
            updated TEXT,                      -- 更新时间（ISO 8601）
            labels TEXT,                       -- 标签（JSON数组字符串）
            components TEXT,                   -- 组件（逗号分隔）
            affects_versions TEXT,             -- 影响版本（逗号分隔）
            fix_versions TEXT,                 -- 修复版本（逗号分隔）
            initiative_child_count INTEGER,    -- 子项数量（成本基数）
            linked_issues TEXT,                -- 关联issues（JSON数组）
            issue_links TEXT,                  -- 原始issue links（JSON）
            intake_type TEXT,                  -- 类型
            cost_rmb REAL,                     -- 成本（人民币）
            approver TEXT,                     -- 审批人
            scope TEXT,                        -- 范围
            follow_up TEXT                     -- 后续跟进
        )
    ''')
    
    # 抓取日志表 - 用于追踪每次运行的结果
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fetch_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,  -- 自动记录时间
            count INTEGER,                                   -- 抓取到的记录数
            status TEXT,                                     -- success / error
            message TEXT                                     -- 详细信息或错误消息
        )
    ''')
    
    conn.commit()
    return conn, cursor


def fetch_issues_jql(jql, fields, page_size=100):
    """
    从 Jira API 抓取 issues，支持分页
    
    使用 Jira REST API v3 的 /search/jql 端点（POST 方法）。
    分页使用 nextPageToken（Jira v3 推荐方式，替代传统的 startAt）。
    
    参数:
        jql (str): Jira Query Language 字符串
        fields (list): 需要返回的字段列表
        page_size (int): 每页记录数（默认 100，最大 100）
    
    返回:
        list: 所有 issues 的列表（已合并所有分页）
    
    API 文档:
        https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/#api-rest-api-3-search-jql-post
    
    示例:
        >>> issues = fetch_issues_jql(
        ...     "parent = CNTIN-730",
        ...     ["key", "summary", "status"]
        ... )
        >>> len(issues)
        167
    """
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    all_issues = []
    next_page_token = None
    page = 1
    
    while True:
        # 构建请求体
        payload = {
            "jql": jql,
            "maxResults": page_size,
            "fields": fields
        }
        if next_page_token:
            payload["nextPageToken"] = next_page_token
        
        try:
            # 发送 POST 请求
            # verify=False: 禁用 SSL 验证（Jira 使用自签名证书时）
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                verify=False,  # 生产环境建议配置 CA 证书后改为 True
                timeout=120    # 2 分钟超时
            )
            response.raise_for_status()
            data = response.json()
            
            # 提取 issues
            issues = data.get('issues', [])
            all_issues.extend(issues)
            
            # 检查是否还有更多页
            next_page_token = data.get('nextPageToken')
            if not next_page_token:
                break
            
            page += 1
            # 每 5 页显示一次进度
            if page % 5 == 0:
                print(f"      分页进度: {len(all_issues)} 个...")
                
        except Exception as e:
            print(f"    ⚠️ 请求失败: {e}")
            # 打印详细错误信息以便调试
            if hasattr(e, 'response'):
                print(f"       响应: {e.response.text[:500]}")
            break
    
    return all_issues


def parse_components(fields):
    """
    解析 components 字段为逗号分隔的字符串
    
    Jira 的 components 字段是对象数组，每个对象有 name 属性。
    例如：[{"name": "Frontend"}, {"name": "Backend"}] → "Frontend, Backend"
    
    参数:
        fields (dict): Jira issue 的 fields 对象
    
    返回:
        str: 逗号分隔的组件名称，如果没有则为空字符串
    """
    components = fields.get('components', [])
    return ', '.join([c.get('name', '') for c in components]) if components else ''


def parse_versions(fields, version_type):
    """
    解析 affectsVersions 或 fixVersions 字段
    
    参数:
        fields (dict): Jira issue 的 fields 对象
        version_type (str): 'versions' (affectsVersions) 或 'fixVersions'
    
    返回:
        str: 逗号分隔的版本名称
    """
    versions = fields.get(version_type, [])
    return ', '.join([v.get('name', '') for v in versions]) if versions else ''


def parse_linked_issues(fields):
    """
    解析 issue links，提取关联的 work items
    
    Jira 的 issuelinks 字段包含双向关系：
    - outwardIssue: 当前 ticket 链接到的其他 ticket
    - inwardIssue: 链接到当前 ticket 的其他 ticket
    
    此函数提取所有关联的 tickets，保留关系类型信息。
    
    参数:
        fields (dict): Jira issue 的 fields 对象
    
    返回:
        list: 关联 issues 的列表，每个元素是 dict {key, type}
    
    示例返回:
        [
            {"key": "CNTIN-100", "type": "relates to"},
            {"key": "CNTIN-101", "type": "is blocked by"}
        ]
    """
    issue_links = fields.get('issuelinks', [])
    linked = []
    
    for link in issue_links:
        # outwardIssue: 当前 ticket → 其他 ticket
        outward = link.get('outwardIssue')
        if outward:
            linked.append({
                'key': outward['key'],
                'type': link.get('type', {}).get('outward', 'links to')
            })
        
        # inwardIssue: 其他 ticket → 当前 ticket
        inward = link.get('inwardIssue')
        if inward:
            linked.append({
                'key': inward['key'],
                'type': link.get('type', {}).get('inward', 'is linked by')
            })
    
    return linked


def fetch_intake_cost_data(cursor):
    """
    抓取 CNTIN-730 下的所有 Intake 数据并存储到数据库
    
    这是主抓取函数，执行以下步骤：
    1. 构造 JQL 查询
    2. 指定需要的字段（包括自定义字段）
    3. 调用 fetch_issues_jql() 获取数据
    4. 解析和转换数据
    5. 清空旧数据并插入新数据
    6. 记录抓取日志
    
    参数:
        cursor: SQLite 数据库游标
    
    返回:
        list: 抓取到的 issues 列表
    
    注意:
        此函数会清空 intakes 表的所有数据，然后重新插入。
        这是一个全量刷新操作，不是增量更新。
    """
    print("\n📋 抓取 CNTIN-730 Intakes...")
    
    # 定义需要从 Jira 获取的字段
    # 标准字段
    standard_fields = [
        "key",           # Ticket 编号
        "summary",       # 标题
        "description",   # 描述（ADF 格式）
        "status",        # 状态
        "assignee",      # 负责人
        "reporter",      # 创建者
        "created",       # 创建时间
        "updated",       # 更新时间
        "labels",        # 标签
        "components",    # 组件
        "versions",      # 影响版本
        "fixVersions",   # 修复版本
        "issuelinks"     # 关联 issues
    ]
    
    # 自定义字段（可能随 Jira 配置变化）
    # TODO: 如果自定义字段 ID 变化，需要更新这里
    custom_fields = [
        "customfield_16143",  # InitiativeChildCount - 用于成本计算
        "customfield_16201",  # Cost/Estimated Cost
        "customfield_16144",  # Type/Intake Type
        "customfield_16145",  # Approver
        "customfield_16146",  # Scope
        "customfield_16147"   # Follow up
    ]
    
    fields = standard_fields + custom_fields
    
    # JQL 查询：获取 CNTIN-730 下的所有 Initiatives
    # CNTIN-730 是 Goal 类型，子项是 Initiative 类型
    jql = "project = CNTIN AND issuetype = Initiative AND parent = CNTIN-730 ORDER BY key ASC"
    
    print(f"   JQL: {jql}")
    print(f"   字段数: {len(fields)}")
    
    # 执行抓取
    issues = fetch_issues_jql(jql, fields)
    
    print(f"  ✓ 抓到 {len(issues)} 个 Intakes")
    
    # 清空旧数据（全量刷新）
    # 注意：这会删除所有现有数据，确保数据库与 Jira 同步
    cursor.execute("DELETE FROM intakes")
    print(f"   已清空旧数据")
    
    # 处理每个 issue 并插入数据库
    for idx, issue in enumerate(issues, 1):
        fields_data = issue['fields']
        
        # 解析关联 issues
        linked = parse_linked_issues(fields_data)
        
        # 解析 ADF description 为纯文本
        adf_desc = fields_data.get('description')
        plain_desc = parse_adf_to_text(adf_desc) if adf_desc else ''
        
        # 获取自定义字段值（如果字段不存在则使用默认值）
        intake_type = fields_data.get('customfield_16144') or 'TBD'
        cost_value = fields_data.get('customfield_16201') or 0
        approver = fields_data.get('customfield_16145') or ''
        scope = fields_data.get('customfield_16146') or ''
        follow_up = fields_data.get('customfield_16147') or ''
        
        # 插入数据库
        cursor.execute('''
            INSERT OR REPLACE INTO intakes (
                key, summary, description, status, status_category, assignee, reporter,
                created, updated, labels, components, affects_versions, fix_versions,
                initiative_child_count, linked_issues, issue_links,
                intake_type, cost_rmb, approver, scope, follow_up
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            issue['key'],
            fields_data.get('summary', ''),
            plain_desc,
            fields_data.get('status', {}).get('name', ''),
            fields_data.get('status', {}).get('statusCategory', {}).get('name', ''),
            fields_data.get('assignee', {}).get('displayName', 'Unassigned') if fields_data.get('assignee') else 'Unassigned',
            fields_data.get('reporter', {}).get('displayName', 'Unknown') if fields_data.get('reporter') else 'Unknown',
            fields_data.get('created', ''),
            fields_data.get('updated', ''),
            json.dumps(fields_data.get('labels', [])),
            parse_components(fields_data),
            parse_versions(fields_data, 'versions'),
            parse_versions(fields_data, 'fixVersions'),
            fields_data.get('customfield_16143') or 0,
            json.dumps(linked),
            json.dumps(fields_data.get('issuelinks', [])),
            intake_type if intake_type else 'TBD',
            float(cost_value) if cost_value else 0,
            approver,
            scope,
            follow_up
        ))
        
        # 每 50 条显示一次进度
        if idx % 50 == 0:
            print(f"     已处理 {idx}/{len(issues)}...")
    
    # 记录抓取日志
    cursor.execute(
        "INSERT INTO fetch_log (count, status, message) VALUES (?, ?, ?)",
        (len(issues), "success", f"Fetched {len(issues)} intakes from CNTIN-730")
    )
    
    return issues


def generate_stats(cursor):
    """
    生成并显示统计信息
    
    统计内容包括：
    - 总记录数
    - 按状态分类的数量
    - 有关联 issues 的记录数
    
    参数:
        cursor: SQLite 数据库游标
    """
    print("\n📊 数据统计:")
    
    # 总数
    cursor.execute("SELECT COUNT(*) FROM intakes")
    total = cursor.fetchone()[0]
    print(f"  - 总数: {total}")
    
    # 按状态分类统计
    cursor.execute('''
        SELECT status_category, COUNT(*) 
        FROM intakes 
        GROUP BY status_category 
        ORDER BY COUNT(*) DESC
    ''')
    status_counts = cursor.fetchall()
    
    for status, count in status_counts:
        print(f"  - {status}: {count}")
    
    # 统计有 linked issues 的数量
    cursor.execute("SELECT COUNT(*) FROM intakes WHERE linked_issues != '[]'")
    with_links = cursor.fetchone()[0]
    print(f"  - 有关联项: {with_links}")


def main():
    """
    主函数 - 程序入口点
    
    执行流程：
    1. 打印启动信息
    2. 初始化数据库
    3. 抓取数据
    4. 生成统计
    5. 提交事务或回滚
    6. 关闭连接
    
    异常处理：
    - 任何异常都会触发回滚，确保数据库一致性
    - 打印详细堆栈跟踪便于调试
    """
    print("🚀 FY26_Intake_Cost 数据抓取开始...")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"数据库: {DB_PATH}")
    
    conn, cursor = init_db()
    
    try:
        # 主流程
        fetch_intake_cost_data(cursor)
        generate_stats(cursor)
        
        # 提交事务
        conn.commit()
        print("\n✅ 数据抓取完成!")
        print(f"数据库已更新: {DB_PATH}")
        
    except Exception as e:
        # 出错时回滚事务
        conn.rollback()
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        # 确保关闭连接
        conn.close()


if __name__ == "__main__":
    main()
