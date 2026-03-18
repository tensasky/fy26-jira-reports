#!/usr/bin/env python3
"""
FY26_INIT 报告生成脚本 v5.1
只显示带 FY26_INIT 标签的 Initiatives 及其向下的数据
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

# 配置
WORKSPACE = Path.home() / ".openclaw" / "workspace"
DB_PATH = WORKSPACE / "jira-reports" / "fy26_data.db"
OUTPUT_DIR = WORKSPACE / "jira-reports"

def generate_report():
    print("📊 开始生成报告...")
    print(f"数据库: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    # 1. 只获取带 FY26_INIT 标签的 Initiatives
    initiatives_query = '''
        SELECT DISTINCT i.key as init_key, i.summary as init_summary, 
               i.status as init_status, i.assignee as init_assignee
        FROM initiatives i
        WHERE i.labels LIKE '%FY26_INIT%'
        ORDER BY i.key
    '''
    
    initiatives = []
    total_epics_in_initiatives = 0
    
    for init_row in conn.execute(initiatives_query):
        init_key = init_row['init_key']
        
        # 获取该 Initiative 下的所有 Feature（不管是否有 Epic）
        features_query = '''
            SELECT f.key as feat_key, f.summary as feat_summary,
                   f.status as feat_status, f.assignee as feat_assignee
            FROM features f
            WHERE f.parent_key = ?
            ORDER BY f.key
        '''
        
        features = []
        epic_count = 0
        
        for feat_row in conn.execute(features_query, (init_key,)):
            feat_key = feat_row['feat_key']
            
            # 获取该 Feature 下的所有 Epic
            epics_query = '''
                SELECT key as epic_key, project as epic_project,
                       summary as epic_summary, status as epic_status,
                       assignee as epic_assignee, created as epic_created
                FROM epics
                WHERE parent_key = ?
                ORDER BY key
            '''
            
            epics = []
            for epic_row in conn.execute(epics_query, (feat_key,)):
                epics.append({
                    'epic_key': epic_row['epic_key'],
                    'epic_project': epic_row['epic_project'],
                    'epic_summary': epic_row['epic_summary'],
                    'epic_status': epic_row['epic_status'],
                    'epic_assignee': epic_row['epic_assignee'],
                    'epic_created': epic_row['epic_created'],
                    'plan_start': '-',
                    'plan_end': '-',
                    'epic_scope': '-',
                    'epic_desc': ''
                })
            
            epic_count += len(epics)
            
            features.append({
                'feat_key': feat_row['feat_key'],
                'feat_summary': feat_row['feat_summary'],
                'feat_status': feat_row['feat_status'],
                'feat_assignee': feat_row['feat_assignee'],
                'epics': epics
            })
        
        total_epics_in_initiatives += epic_count
        
        initiatives.append({
            'init_key': init_key,
            'init_summary': init_row['init_summary'],
            'init_status': init_row['init_status'],
            'init_assignee': init_row['init_assignee'],
            'has_epics': epic_count > 0,
            'epic_count': epic_count,
            'feature_count': len(features),
            'features': features
        })
    
    # 2. 孤儿 Epic（创建时间 >= 2026-02-01，无 parent）
    # 但只包括那些 parent Feature 属于 FY26_INIT Initiative 的
    orphan_epics_query = '''
        SELECT e.key as epic_key, e.project as epic_project,
               e.summary as epic_summary, e.status as epic_status,
               e.assignee as epic_assignee, e.created as epic_created
        FROM epics e
        WHERE e.parent_key IS NULL
        AND e.created >= '2026-02-01'
        ORDER BY e.created DESC
    '''
    
    orphan_epics = []
    for row in conn.execute(orphan_epics_query):
        orphan_epics.append({
            'epic_key': row['epic_key'],
            'epic_project': row['epic_project'],
            'epic_summary': row['epic_summary'],
            'epic_status': row['epic_status'],
            'epic_assignee': row['epic_assignee'],
            'epic_created': row['epic_created']
        })
    
    # 3. 孤儿 Feature（属于 FY26_INIT Initiative 但没有 Epic）
    orphan_features_query = '''
        SELECT f.key as feat_key, f.summary as feat_summary,
               f.status as feat_status, f.assignee as feat_assignee,
               f.parent_key as init_key
        FROM features f
        JOIN initiatives i ON f.parent_key = i.key
        WHERE i.labels LIKE '%FY26_INIT%'
        AND NOT EXISTS (
            SELECT 1 FROM epics e WHERE e.parent_key = f.key
        )
        ORDER BY f.key
    '''
    
    orphan_features = []
    for row in conn.execute(orphan_features_query):
        orphan_features.append({
            'feat_key': row['feat_key'],
            'feat_summary': row['feat_summary'],
            'feat_status': row['feat_status'],
            'feat_assignee': row['feat_assignee'],
            'init_key': row['init_key'] or '无'
        })
    
    # 4. 孤儿 Initiative（有 FY26_INIT 标签但无 Feature）
    orphan_initiatives_query = '''
        SELECT i.key as init_key, i.summary as init_summary,
               i.status as init_status, i.assignee as init_assignee
        FROM initiatives i
        WHERE i.labels LIKE '%FY26_INIT%'
        AND NOT EXISTS (
            SELECT 1 FROM features f WHERE f.parent_key = i.key
        )
        ORDER BY i.key
    '''
    
    orphan_initiatives = []
    for row in conn.execute(orphan_initiatives_query):
        orphan_initiatives.append({
            'init_key': row['init_key'],
            'init_summary': row['init_summary'],
            'init_status': row['init_status'],
            'init_assignee': row['init_assignee']
        })
    
    # 统计
    cursor = conn.execute('SELECT COUNT(*) FROM epics')
    total_epics_all = cursor.fetchone()[0]
    
    cursor = conn.execute('SELECT COUNT(*) FROM epics WHERE parent_key IS NOT NULL')
    total_epics_linked = cursor.fetchone()[0]
    
    # 计算有 Epic 的 Initiative 数量
    initiatives_with_epics = sum(1 for i in initiatives if i['epic_count'] > 0)
    
    stats = {
        'total_initiatives': len(initiatives),
        'initiatives_with_epics': initiatives_with_epics,
        'total_epics_in_fy26_init': total_epics_in_initiatives,
        'total_epics_all': total_epics_all,
        'total_epics_linked': total_epics_linked,
        'orphan_epics_count': len(orphan_epics),
        'orphan_features_count': len(orphan_features),
        'orphan_initiatives_count': len(orphan_initiatives)
    }
    
    # 生成 JSON 报告
    report = {
        'generated_at': datetime.now().isoformat(),
        'stats': stats,
        'normal_initiatives': initiatives,
        'orphan_epics': orphan_epics,
        'orphan_features': orphan_features,
        'orphan_initiatives': orphan_initiatives
    }
    
    date_str = datetime.now().strftime('%Y%m%d_%H%M')
    json_path = OUTPUT_DIR / f"fy26_report_v5_{date_str}.json"
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JSON 报告已保存: {json_path}")
    print(f"\n📊 统计:")
    print(f"   - FY26_INIT Initiatives: {stats['total_initiatives']}")
    print(f"   - 有 Epic 的: {stats['initiatives_with_epics']}")
    print(f"   - FY26_INIT 下的总 Epics: {stats['total_epics_in_fy26_init']}")
    print(f"   - 孤儿 Epic: {stats['orphan_epics_count']}")
    print(f"   - 孤儿 Feature: {stats['orphan_features_count']}")
    print(f"   - 孤儿 Initiative: {stats['orphan_initiatives_count']}")
    
    conn.close()
    return json_path

if __name__ == '__main__':
    generate_report()
