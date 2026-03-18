import sys
sys.path.insert(0, '/Users/admin/.openclaw/workspace/skills/cellcog')

try:
    from cellcog import CellCogClient
    
    client = CellCogClient()
    
    prompt = """创建一个RAID风险管理培训演示文稿，30页左右，用于交付团队培训。

主题：RAID风险管理框架培训

内容结构：
1. 封面 - RAID风险管理培训
2. 目录
3. 什么是RAID - R风险、A假设、I问题、D依赖关系
4. 为什么使用RAID - 主动识别风险、跟踪问题、记录假设、管理依赖
5. RAID在Jira中的管理 - Work Type、Kanban Board
6. Risk风险详解 - 定义、影响评分、概率评分、风险暴露分数
7. Action Item行动项详解
8. Issue问题详解
9. Decision决策详解
10. 如何在Jira中创建RAID条目 - 步骤说明
11. RAID字段详解 - Summary/Description/Assignee等
12. 风险与问题升级概述
13. 升级触发条件
14. 三级升级模型 - Team/Program/Enterprise
15. Team Level团队层 - 定义、使用场景、示例
16. Program Level项目群层 - 定义、使用场景、示例
17. Enterprise Level企业层 - 定义、使用场景、示例
18. 升级最佳实践
19. RAID层级结构 - Team/Program/Enterprise
20. 健康报告指标 - 项目健康度、风险暴露、问题处理效率
21. RAID + 层级如何驱动健康报告
22. 核心健康输入指标
23. 向上汇总逻辑
24. 团队层收益
25. 项目群层收益
26. 企业层收益
27. RAID管理最佳实践 - 定期更新、清晰描述
28. RAID管理最佳实践 - 及时升级、沟通、持续改进
29. RAID条目模板示例
30. 总结与QA

设计要求：
- 风格：简约、专业
- 背景：lululemon品牌红色（#C8102E）
- 字体：清晰易读的中文字体
- 布局：留白充足，内容层次分明
- 受众：交付团队（项目经理、Scrum Master、开发团队）
- 语言：简体中文

每个slide应该有清晰的标题和简洁的内容要点。"""

    result = client.create_chat(
        prompt=prompt,
        notify_session_key="agent:main:main",
        task_label="raid-training-ppt",
        chat_mode="agent"
    )
    
    print("✓ PPT生成任务已提交")
    print(f"任务ID: {result.get('task_id', 'unknown')}")
    print("完成后将通知您")
    
except Exception as e:
    print(f"错误: {e}")
    import traceback
    traceback.print_exc()
