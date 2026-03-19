#!/bin/bash
# 抓取17个项目的 Epic-Story/Task 数据并生成 HTML 报告

source /Users/admin/.openclaw/workspace/.jira-config

OUTPUT_DIR="/Users/admin/.openclaw/workspace/jira-reports"
mkdir -p "$OUTPUT_DIR"
DATE_STR=$(date +%Y%m%d_%H%M)

PROJECTS="CNTD,CNTEST,CNENG,CNINFA,CNCA,CPR,EPCH,CNCRM,CNDIN,SWMP,CDM,CMDM,CNSCM,CNRTPRJ,CSCPVT,CNPMO,CYBERPJT"

echo "🚀 开始抓取17个项目的 Epic-Story-Subtask 数据..."
echo ""

# 抓取 Epics
echo "📋 抓取 Epics..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d "{
    \"jql\": \"project in ($PROJECTS) AND issuetype = Epic ORDER BY project ASC, key ASC\",
    \"maxResults\": 1000,
    \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"project\", \"customfield_10014\"]
  }" > "$OUTPUT_DIR/all_epics_${DATE_STR}.json"

EPIC_COUNT=$(cat "$OUTPUT_DIR/all_epics_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $EPIC_COUNT 个 Epics"

# 抓取 Stories
echo "📋 抓取 Stories..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d "{
    \"jql\": \"project in ($PROJECTS) AND issuetype = Story ORDER BY project ASC, key ASC\",
    \"maxResults\": 1000,
    \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"project\", \"parent\"]
  }" > "$OUTPUT_DIR/all_stories_${DATE_STR}.json"

STORY_COUNT=$(cat "$OUTPUT_DIR/all_stories_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $STORY_COUNT 个 Stories"

# 抓取 Tasks
echo "📋 抓取 Tasks..."
curl -s -u "${JIRA_USER_EMAIL}:${JIRA_API_TOKEN}" \
  -H "Accept: application/json" \
  -X POST \
  "${JIRA_BASE_URL}/rest/api/3/search/jql" \
  -H "Content-Type: application/json" \
  -d "{
    \"jql\": \"project in ($PROJECTS) AND issuetype = Task ORDER BY project ASC, key ASC\",
    \"maxResults\": 1000,
    \"fields\": [\"key\", \"summary\", \"description\", \"status\", \"assignee\", \"created\", \"updated\", \"project\", \"parent\"]
  }" > "$OUTPUT_DIR/all_tasks_${DATE_STR}.json"

TASK_COUNT=$(cat "$OUTPUT_DIR/all_tasks_${DATE_STR}.json" | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d.get('issues', [])))")
echo "  ✓ 找到 $TASK_COUNT 个 Tasks"

echo ""
echo "📊 生成 HTML 报告..."

python3 << PYTHON_SCRIPT
import json
import re
from datetime import datetime
from collections import defaultdict

OUTPUT_DIR = "/Users/admin/.openclaw/workspace/jira-reports"
DATE_STR = "$DATE_STR"

def extract_text_from_adf(doc):
    if not doc:
        return ""
    if isinstance(doc, str):
        return doc
    texts = []
    def traverse(node):
        if isinstance(node, dict):
            if node.get("type") == "text":
                texts.append(node.get("text", ""))
            for content in node.get("content", []):
                traverse(content)
        elif isinstance(node, list):
            for item in node:
                traverse(item)
    traverse(doc)
    return " ".join(texts)

def clean_text(text):
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', str(text))
    return text.strip()

# 加载数据
with open(f"{OUTPUT_DIR}/all_epics_{DATE_STR}.json", "r") as f:
    epic_data = json.load(f)
with open(f"{OUTPUT_DIR}/all_stories_{DATE_STR}.json", "r") as f:
    story_data = json.load(f)
with open(f"{OUTPUT_DIR}/all_tasks_{DATE_STR}.json", "r") as f:
    task_data = json.load(f)

epics = epic_data.get("issues", [])
stories = story_data.get("issues", [])
tasks = task_data.get("issues", [])

# 建立索引
epic_by_key = {e["key"]: e for e in epics}
story_by_key = {s["key"]: s for s in stories}
task_by_key = {t["key"]: t for t in tasks}

# 按项目分组
epic_by_project = defaultdict(list)
for e in epics:
    proj = e["fields"]["project"]["key"]
    epic_by_project[proj].append(e)

# 建立层级关系
epic_to_stories = defaultdict(list)
epic_to_tasks = defaultdict(list)
story_to_tasks = defaultdict(list)

# 解析 Story 的 Epic 关系
for s in stories:
    s_key = s["key"]
    fields = s["fields"]
    # 检查 Epic Link (customfield_10014)
    epic_link = fields.get("customfield_10014")
    if epic_link and epic_link in epic_by_key:
        epic_to_stories[epic_link].append(s_key)
    # 检查 parent
    parent = fields.get("parent")
    if parent and parent["key"] in epic_by_key:
        epic_to_stories[parent["key"]].append(s_key)

# 解析 Task 的关系
for t in tasks:
    t_key = t["key"]
    fields = t["fields"]
    parent = fields.get("parent")
    if parent:
        parent_key = parent["key"]
        if parent_key in epic_by_key:
            epic_to_tasks[parent_key].append(t_key)
        elif parent_key in story_by_key:
            story_to_tasks[parent_key].append(t_key)

# 生成 HTML
html_content = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jira Epic-Story-Task 报告</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #E31937 0%, #c41230 100%);
            color: white;
            padding: 40px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; font-weight: 300; }}
        .header .subtitle {{ opacity: 0.9; font-size: 1.1em; }}
        .header .date {{ opacity: 0.7; margin-top: 10px; font-size: 0.9em; }}
        
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            max-width: 1400px;
            margin: 0 auto;
        }}
        .stat-card {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid #E31937;
        }}
        .stat-card .number {{
            font-size: 2.5em;
            font-weight: 700;
            color: #E31937;
            margin-bottom: 5px;
        }}
        .stat-card .label {{ color: #666; font-size: 0.95em; }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 40px 40px;
        }}
        
        .project-section {{
            background: white;
            border-radius: 12px;
            margin-bottom: 25px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            overflow: hidden;
        }}
        .project-header {{
            background: #fafafa;
            padding: 20px 25px;
            border-bottom: 1px solid #eee;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .project-header h2 {{
            font-size: 1.3em;
            color: #333;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .project-header .badge {{
            background: #E31937;
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        
        .epic {{
            border-bottom: 1px solid #f0f0f0;
            padding: 20px 25px;
        }}
        .epic:last-child {{ border-bottom: none; }}
        
        .epic-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 12px;
        }}
        .epic-title {{
            font-size: 1.1em;
            font-weight: 600;
            color: #1a1a1a;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .epic-key {{
            background: #f0f0f0;
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            color: #666;
            font-family: monospace;
        }}
        .status {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 500;
        }}
        .status-new {{ background: #e3f2fd; color: #1976d2; }}
        .status-in-progress {{ background: #fff3e0; color: #f57c00; }}
        .status-done {{ background: #e8f5e9; color: #388e3c; }}
        .status-closed {{ background: #e8f5e9; color: #388e3c; }}
        .status-deferred {{ background: #fce4ec; color: #c2185b; }}
        .status-cancelled {{ background: #f5f5f5; color: #757575; }}
        .status-to-do {{ background: #f5f5f5; color: #757575; }}
        .status-backlog {{ background: #f3e5f5; color: #7b1fa2; }}
        .status-execution {{ background: #fff3e0; color: #f57c00; }}
        
        .epic-desc {{
            color: #555;
            margin-bottom: 15px;
            line-height: 1.7;
        }}
        
        .children {{
            margin-left: 20px;
            padding-left: 20px;
            border-left: 3px solid #e0e0e0;
        }}
        .child-item {{
            background: #fafafa;
            padding: 12px 15px;
            border-radius: 8px;
            margin-bottom: 10px;
        }}
        .child-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 5px;
        }}
        .child-title {{
            font-weight: 500;
            color: #444;
        }}
        .child-key {{
            font-size: 0.8em;
            color: #999;
            font-family: monospace;
        }}
        .child-type {{
            font-size: 0.75em;
            padding: 2px 8px;
            border-radius: 4px;
            background: #e0e0e0;
            color: #666;
        }}
        
        .subtasks {{
            margin-top: 8px;
            margin-left: 15px;
        }}
        .subtask {{
            font-size: 0.9em;
            color: #666;
            padding: 4px 0;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .subtask::before {{
            content: "└─";
            color: #ccc;
        }}
        
        .footer {{
            text-align: center;
            padding: 30px;
            color: #999;
            font-size: 0.9em;
        }}
        
        @media (max-width: 768px) {{
            .header {{ padding: 25px; }}
            .header h1 {{ font-size: 1.8em; }}
            .summary {{ padding: 20px; }}
            .container {{ padding: 0 20px 20px; }}
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Jira Epic-Story-Task 层级报告</h1>
        <div class="subtitle">17个项目数据汇总</div>
        <div class="date">生成时间: {datetime.now().strftime("%Y-%m-%d %H:%M")}</div>
    </div>
    
    <div class="summary">
        <div class="stat-card">
            <div class="number">{len(epics)}</div>
            <div class="label">Epics</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(stories)}</div>
            <div class="label">Stories</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(tasks)}</div>
            <div class="label">Tasks</div>
        </div>
        <div class="stat-card">
            <div class="number">{len(epic_by_project)}</div>
            <div class="label">项目数</div>
        </div>
    </div>
    
    <div class="container">
'''

# 按项目生成内容
for proj in sorted(epic_by_project.keys()):
    proj_epics = epic_by_project[proj]
    
    html_content += f'''
        <div class="project-section">
            <div class="project-header">
                <h2>📁 {proj}</h2>
                <span class="badge">{len(proj_epics)} Epics</span>
            </div>
'''
    
    for epic in proj_epics:
        epic_key = epic["key"]
        fields = epic["fields"]
        summary = fields.get("summary", "")
        status = fields.get("status", {}).get("name", "New")
        desc = clean_text(extract_text_from_adf(fields.get("description")))
        
        status_class = f"status-{status.lower().replace(' ', '-')}"
        
        html_content += f'''
            <div class="epic">
                <div class="epic-header">
                    <div class="epic-title">
                        <span class="epic-key">{epic_key}</span>
                        {summary}
                    </div>
                    <span class="status {status_class}">{status}</span>
                </div>
'''
        
        if desc:
            html_content += f'<div class="epic-desc">{desc[:200]}{"..." if len(desc) > 200 else ""}</div>'
        
        # 添加 Stories
        related_stories = epic_to_stories.get(epic_key, [])
        related_tasks = epic_to_tasks.get(epic_key, [])
        
        if related_stories or related_tasks:
            html_content += '<div class="children">'
            
            # Stories
            for story_key in related_stories[:10]:  # 最多显示10个
                if story_key in story_by_key:
                    story = story_by_key[story_key]
                    story_fields = story["fields"]
                    story_summary = story_fields.get("summary", "")
                    
                    html_content += f'''
                <div class="child-item">
                    <div class="child-header">
                        <span class="child-title">{story_summary}</span>
                        <div>
                            <span class="child-type">Story</span>
                            <span class="child-key">{story_key}</span>
                        </div>
                    </div>
'''
                    # Subtasks
                    subtasks = story_to_tasks.get(story_key, [])
                    if subtasks:
                        html_content += '<div class="subtasks">'
                        for sub_key in subtasks[:5]:
                            if sub_key in task_by_key:
                                sub = task_by_key[sub_key]
                                sub_summary = sub["fields"].get("summary", "")
                                html_content += f'<div class="subtask">{sub_key}: {sub_summary[:40]}{"..." if len(sub_summary) > 40 else ""}</div>'
                        if len(subtasks) > 5:
                            html_content += f'<div class="subtask">... 还有 {len(subtasks)-5} 个 Tasks</div>'
                        html_content += '</div>'
                    
                    html_content += '</div>'
            
            # Direct Tasks (under Epic)
            for task_key in related_tasks[:5]:
                if task_key in task_by_key:
                    task = task_by_key[task_key]
                    task_fields = task["fields"]
                    task_summary = task_fields.get("summary", "")
                    
                    html_content += f'''
                <div class="child-item">
                    <div class="child-header">
                        <span class="child-title">{task_summary}</span>
                        <div>
                            <span class="child-type">Task</span>
                            <span class="child-key">{task_key}</span>
                        </div>
                    </div>
                </div>
'''
            
            if len(related_stories) > 10 or len(related_tasks) > 5:
                html_content += f'<div class="child-item" style="text-align:center;color:#999;">... 还有 {max(0, len(related_stories)-10)} Stories, {max(0, len(related_tasks)-5)} Tasks</div>'
            
            html_content += '</div>'
        
        html_content += '</div>'
    
    html_content += '</div>'

html_content += '''
    </div>
    
    <div class="footer">
        报告由 OpenClaw 自动生成 | lululemon Jira 数据
    </div>
</body>
</html>
'''

# 保存 HTML
html_path = f"{OUTPUT_DIR}/jira_epic_report_{DATE_STR}.html"
with open(html_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ HTML 报告已生成: {html_path}")
print(f"   包含 {len(epics)} Epics, {len(stories)} Stories, {len(tasks)} Tasks")
print(f"   覆盖 {len(epic_by_project)} 个项目")

PYTHON_SCRIPT

echo ""
echo "📁 生成的文件:"
ls -lh "$OUTPUT_DIR"/*"${DATE_STR}"*.html