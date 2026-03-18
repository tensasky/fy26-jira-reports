#!/usr/bin/env python3
"""
生成项目管理流程图PDF
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# 注册中文字体
font_paths = [
    '/System/Library/Fonts/PingFang.ttc',
    '/System/Library/Fonts/STHeiti Light.ttc',
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
    '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
]

chinese_font = None
for font_path in font_paths:
    if os.path.exists(font_path):
        try:
            pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
            chinese_font = 'ChineseFont'
            break
        except:
            continue

if not chinese_font:
    chinese_font = 'Helvetica'

def create_pdf():
    output_path = "/Users/admin/.openclaw/workspace/项目管理标准实施流程.pdf"
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm
    )
    
    # 定义样式
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=chinese_font,
        fontSize=24,
        textColor=colors.HexColor('#333333'),
        spaceAfter=12,
        alignment=TA_CENTER
    )
    
    subtitle_style = ParagraphStyle(
        'CustomSubtitle',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=12,
        textColor=colors.HexColor('#666666'),
        spaceAfter=30,
        alignment=TA_CENTER
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontName=chinese_font,
        fontSize=16,
        textColor=colors.HexColor('#2196F3'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontName=chinese_font,
        fontSize=13,
        textColor=colors.HexColor('#333333'),
        spaceAfter=10,
        spaceBefore=15
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=chinese_font,
        fontSize=10,
        textColor=colors.HexColor('#555555'),
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )
    
    story = []
    
    # 标题
    story.append(Paragraph("📊 项目管理标准实施流程", title_style))
    story.append(Paragraph("Project Management Standard Implementation Process", subtitle_style))
    story.append(Spacer(1, 20))
    
    # 流程概述
    story.append(Paragraph("📋 流程概述", heading1_style))
    story.append(Paragraph(
        "项目管理标准实施流程是基于PMBOK方法论的一套完整的项目管理方法论，包含五个核心阶段：启动、规划、执行、监控和收尾。每个阶段都有明确的任务、交付物和验收标准，确保项目能够按计划高质量完成。",
        normal_style
    ))
    story.append(Spacer(1, 10))
    
    # 流程图（用文字表格表示）
    story.append(Paragraph("🔄 主流程图", heading2_style))
    
    flow_data = [
        ['阶段', '输入', '主要活动', '输出'],
        ['项目启动', '商业论证', '立项、组建团队、启动会', '项目章程'],
        ['项目规划', '项目章程', '需求分析、WBS、计划制定', '项目管理计划'],
        ['项目执行', '项目管理计划', '按计划执行、团队建设', '可交付成果'],
        ['项目监控', '工作绩效数据', '进度/成本/质量控制', '变更请求、报告'],
        ['项目收尾', '可交付成果', '验收、总结、归档', '验收报告'],
    ]
    
    flow_table = Table(flow_data, colWidths=[3*cm, 3.5*cm, 5*cm, 3.5*cm])
    flow_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
    ]))
    story.append(flow_table)
    story.append(Spacer(1, 20))
    
    # 第一阶段
    story.append(Paragraph("🚀 一、项目启动阶段", heading1_style))
    story.append(Paragraph(
        "项目启动是项目管理的第一步，主要目标是明确项目目标、获得授权、组建团队。此阶段的成功决定了项目的基础是否牢固。",
        normal_style
    ))
    story.append(Spacer(1, 5))
    story.append(Paragraph("主要任务：", heading2_style))
    
    phase1_data = [
        ['序号', '任务名称', '关键活动', '负责角色'],
        ['1', '项目立项', '可行性研究、商业论证、编写项目建议书', '发起人'],
        ['2', '组建项目团队', '任命项目经理、确定核心成员、明确角色职责', '项目经理'],
        ['3', '召开启动会', '介绍项目背景、目标和计划、团队相互认识', '项目经理'],
        ['4', '制定项目章程', '正式授权项目、明确项目经理权限、确定高层级需求', '发起人/PM'],
    ]
    
    phase1_table = Table(phase1_data, colWidths=[1.5*cm, 3*cm, 7*cm, 2.5*cm])
    phase1_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E8F5E9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(phase1_table)
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>阶段交付物：</b>项目章程、项目建议书、可行性研究报告、项目启动会议纪要", normal_style))
    story.append(PageBreak())
    
    # 第二阶段
    story.append(Paragraph("📋 二、项目规划阶段", heading1_style))
    story.append(Paragraph(
        "规划阶段是项目成功的关键，需要制定详细的项目管理计划。规划的质量直接影响项目的执行效果。",
        normal_style
    ))
    story.append(Spacer(1, 5))
    story.append(Paragraph("主要任务：", heading2_style))
    
    phase2_data = [
        ['序号', '任务名称', '关键活动'],
        ['1', '需求分析', '收集需求、需求评审、需求确认、需求文档化'],
        ['2', '范围定义', '确定项目边界、制定范围说明书、定义验收标准'],
        ['3', 'WBS分解', '创建工作分解结构、定义工作包、分配责任'],
        ['4', '进度计划', '定义活动、活动排序、资源估算、制定进度表'],
        ['5', '资源计划', '识别资源需求、制定资源日历、资源平衡'],
        ['6', '成本计划', '成本估算、制定预算、确定成本控制基线'],
        ['7', '质量计划', '确定质量标准、制定质量保证措施、验收标准'],
        ['8', '风险计划', '识别风险、定性/定量评估、制定应对策略'],
        ['9', '沟通计划', '识别干系人、确定沟通方式、建立报告机制'],
    ]
    
    phase2_table = Table(phase2_data, colWidths=[1.5*cm, 3*cm, 10*cm])
    phase2_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9C27B0')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F3E5F5')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    story.append(phase2_table)
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>阶段交付物：</b>项目管理计划、WBS、进度计划、成本预算、风险登记册、沟通计划、质量管理计划", normal_style))
    story.append(PageBreak())
    
    # 第三阶段
    story.append(Paragraph("⚙️ 三、项目执行阶段", heading1_style))
    story.append(Paragraph(
        "执行阶段是按照计划完成项目工作的过程，需要协调资源、管理团队，确保项目按计划推进。",
        normal_style
    ))
    story.append(Spacer(1, 5))
    story.append(Paragraph("主要任务：", heading2_style))
    
    phase3_data = [
        ['序号', '任务名称', '关键活动', '负责角色'],
        ['1', '项目执行', '按计划开展工作、产出可交付成果、跟踪进度', '项目团队'],
        ['2', '团队建设', '培训、激励、绩效考核、冲突解决、团队活动', '项目经理'],
        ['3', '质量保证', '质量审计、过程改进、标准执行、检查点评审', '质量经理'],
        ['4', '采购管理', '供应商选择、合同签订、采购执行、供应商管理', '采购经理'],
    ]
    
    phase3_table = Table(phase3_data, colWidths=[1.5*cm, 3*cm, 7*cm, 2.5*cm])
    phase3_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF9800')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF3E0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(phase3_table)
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>阶段交付物：</b>可交付成果、工作绩效数据、变更请求、问题日志、团队绩效评估", normal_style))
    story.append(PageBreak())
    
    # 第四阶段
    story.append(Paragraph("📈 四、项目监控阶段", heading1_style))
    story.append(Paragraph(
        "监控阶段贯穿项目全过程，通过对比计划与实际，及时发现偏差并采取纠正措施，确保项目目标达成。",
        normal_style
    ))
    story.append(Spacer(1, 5))
    story.append(Paragraph("主要任务：", heading2_style))
    
    phase4_data = [
        ['序号', '任务名称', '关键活动', '频率'],
        ['1', '进度监控', '跟踪进度、分析偏差、调整计划、报告状态', '每周'],
        ['2', '成本控制', '监控支出、分析成本偏差、控制预算、预测完工成本', '每月'],
        ['3', '质量控制', '检查、测试、验收、缺陷修复、质量报告', '持续'],
        ['4', '变更管理', '变更申请、影响分析、审批流程、变更实施', '按需'],
        ['5', '风险监控', '跟踪已知风险、识别新风险、实施应对措施', '每周'],
    ]
    
    phase4_table = Table(phase4_data, colWidths=[1.5*cm, 3*cm, 7.5*cm, 2.5*cm])
    phase4_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#00BCD4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E0F7FA')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(phase4_table)
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>阶段交付物：</b>工作绩效报告、变更日志、更新的项目管理计划、风险登记册更新", normal_style))
    story.append(PageBreak())
    
    # 第五阶段
    story.append(Paragraph("✅ 五、项目收尾阶段", heading1_style))
    story.append(Paragraph(
        "收尾阶段标志着项目的正式结束，需要完成验收、总结和移交工作，确保项目成果得到有效利用。",
        normal_style
    ))
    story.append(Spacer(1, 5))
    story.append(Paragraph("主要任务：", heading2_style))
    
    phase5_data = [
        ['序号', '任务名称', '关键活动', '负责角色'],
        ['1', '项目验收', '最终产品验收、客户确认、签署验收单、移交成果', '项目经理'],
        ['2', '项目总结', '经验教训总结、项目绩效评估、团队表彰、庆功会', '项目经理'],
        ['3', '项目归档', '文档整理、知识沉淀、档案移交、建立知识库', '配置管理员'],
        ['4', '资源释放', '团队解散、设备归还、合同关闭、财务结算', '项目经理'],
    ]
    
    phase5_table = Table(phase5_data, colWidths=[1.5*cm, 3*cm, 7*cm, 2.5*cm])
    phase5_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#795548')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#EFEBE9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))
    story.append(phase5_table)
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>阶段交付物：</b>验收报告、项目总结报告、经验教训登记册、归档文件、释放的资源", normal_style))
    story.append(Spacer(1, 20))
    
    # 关键成功因素
    story.append(Paragraph("🔑 关键成功因素", heading1_style))
    
    success_data = [
        ['序号', '成功因素', '关键要点'],
        ['1', '明确的目标', '项目目标清晰、可衡量、可实现、相关性强、有时间限制(SMART)'],
        ['2', '有效的沟通', '保持信息透明、及时反馈问题、建立沟通渠道、管理干系人期望'],
        ['3', '风险管理', '提前识别风险、制定应对策略、持续监控、及时响应'],
        ['4', '变更控制', '严格变更流程、评估变更影响、控制范围蔓延、保持基线稳定'],
        ['5', '干系人管理', '识别所有干系人、分析期望和影响、制定管理策略、持续沟通'],
        ['6', '质量管理', '全过程质量控制、持续改进、预防胜于检查、满足客户需求'],
    ]
    
    success_table = Table(success_data, colWidths=[1.5*cm, 3.5*cm, 10*cm])
    success_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4CAF50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#E8F5E9')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
    ]))
    story.append(success_table)
    story.append(Spacer(1, 20))
    
    # 页脚
    story.append(Spacer(1, 30))
    story.append(Paragraph("— 基于PMBOK方法论 —", subtitle_style))
    
    doc.build(story)
    print(f"PDF已生成: {output_path}")
    return output_path

if __name__ == "__main__":
    create_pdf()
