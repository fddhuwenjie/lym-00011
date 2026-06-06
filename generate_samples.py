import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Frame, PageTemplate, BaseDocTemplate
)
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import fitz
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import io
import numpy as np

SAMPLES_DIR = Path(__file__).parent / "samples"
SAMPLES_DIR.mkdir(exist_ok=True)


def register_fonts():
    try:
        pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc'))
        pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
        return True
    except:
        return False


HAS_CN_FONTS = register_fonts()

if HAS_CN_FONTS:
    CN_FONT = 'SimSun'
    CN_BOLD = 'SimHei'
else:
    CN_FONT = 'Helvetica'
    CN_BOLD = 'Helvetica-Bold'


def generate_sample1_single_column():
    filename = SAMPLES_DIR / "sample1_single_column.pdf"
    
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="单栏文本示例文档",
        author="PDF抽取测试",
        subject="单栏文本测试"
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=CN_BOLD,
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=CN_BOLD,
        fontSize=16,
        spaceBefore=15,
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=CN_FONT,
        fontSize=12,
        leading=18,
        alignment=TA_JUSTIFY,
        firstLineIndent=24
    )
    
    story = []
    
    story.append(Paragraph("Python 编程语言简介", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("一、Python 的起源与发展", heading_style))
    story.append(Paragraph(
        "Python 是一种广泛使用的高级编程语言，由 Guido van Rossum 于 1989 年底发明，"
        "并于 1991 年首次发布。Python 的设计哲学强调代码的可读性和简洁的语法，"
        "尤其是使用空格缩进来划分代码块。Python 允许开发者用更少的代码行来表达想法，"
        "这使得它成为初学者和专业开发者都喜爱的编程语言。",
        body_style
    ))
    story.append(Paragraph(
        "Python 得名于英国喜剧团体 Monty Python，而不是蛇。Van Rossum 希望 Python 成为一种"
        "有趣的语言，因此命名时参考了他最喜欢的电视节目《Monty Python's Flying Circus》。"
        "这种轻松的命名方式也体现了 Python 社区的文化和精神。",
        body_style
    ))
    
    story.append(Paragraph("二、Python 的主要特点", heading_style))
    story.append(Paragraph(
        "Python 具有许多优秀的特性，使其在众多编程语言中脱颖而出。首先，它是一种解释型语言，"
        "不需要编译即可运行，这大大加快了开发周期。其次，Python 支持多种编程范式，包括"
        "面向对象编程、命令式编程、函数式编程和过程式编程。这种灵活性使得 Python 能够"
        "适应各种不同的应用场景和开发风格。",
        body_style
    ))
    story.append(Paragraph(
        "Python 的标准库非常丰富，涵盖了网络编程、文件处理、正则表达式、数据处理等"
        "众多领域。除此之外，Python 还有一个庞大的第三方库生态系统，通过 PyPI "
        "（Python Package Index）可以方便地安装和使用各种功能强大的库。",
        body_style
    ))
    
    story.append(Paragraph("三、Python 的应用领域", heading_style))
    story.append(Paragraph(
        "如今，Python 已经成为最受欢迎的编程语言之一，广泛应用于各个领域。在 Web 开发方面，"
        "Django 和 Flask 等框架提供了快速构建 Web 应用的能力。在数据科学和机器学习领域，"
        "NumPy、Pandas、Matplotlib、Scikit-learn 和 TensorFlow 等库使 Python 成为"
        "数据分析和人工智能开发的首选语言。",
        body_style
    ))
    story.append(Paragraph(
        "此外，Python 还常用于自动化运维、科学计算、网络爬虫、游戏开发等领域。"
        "许多知名公司如 Google、Facebook、Netflix、Dropbox 和 NASA 都在使用 Python "
        "进行各种开发工作。可以说，Python 已经成为现代软件开发不可或缺的工具之一。",
        body_style
    ))
    
    story.append(PageBreak())
    
    story.append(Paragraph("四、Python 2 与 Python 3", heading_style))
    story.append(Paragraph(
        "Python 有两个主要版本：Python 2 和 Python 3。Python 2 发布于 2000 年，"
        "Python 3 发布于 2008 年，是一个不向后兼容的主要版本修订。由于 Python 3 "
        "引入了许多重要的改进，Python 社区决定在 2020 年 1 月 1 日停止对 Python 2 的"
        "官方支持。现在所有新的开发工作都应该使用 Python 3。",
        body_style
    ))
    
    story.append(Paragraph("五、学习 Python 的建议", heading_style))
    story.append(Paragraph(
        "对于想要学习 Python 的初学者，建议从官方文档开始，同时结合实践项目来加深理解。"
        "Python 社区非常活跃，有许多优质的教程、书籍和在线课程可供选择。重要的是要"
        "保持耐心，多写代码，多参与开源项目，这样才能真正掌握这门强大的编程语言。",
        body_style
    ))
    
    doc.build(story)
    print(f"+ 生成样本1: {filename.name} (单栏文本)")
    return filename


def generate_sample2_multi_column():
    filename = SAMPLES_DIR / "sample2_multi_column.pdf"
    
    doc = BaseDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="多栏排版示例文档",
        author="PDF抽取测试",
        subject="双栏学术论文格式"
    )
    
    frame1 = Frame(doc.leftMargin, doc.bottomMargin, 
                   (doc.width - 0.5*cm) / 2, doc.height, id='col1')
    frame2 = Frame(doc.leftMargin + (doc.width + 0.5*cm) / 2, doc.bottomMargin,
                   (doc.width - 0.5*cm) / 2, doc.height, id='col2')
    
    doc.addPageTemplates([PageTemplate(id='TwoCol', frames=[frame1, frame2])])
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=CN_BOLD,
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=15
    )
    author_style = ParagraphStyle(
        'Author',
        parent=styles['Normal'],
        fontName=CN_FONT,
        fontSize=11,
        alignment=TA_CENTER,
        spaceAfter=10
    )
    abstract_style = ParagraphStyle(
        'Abstract',
        parent=styles['BodyText'],
        fontName=CN_FONT,
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY,
        leftIndent=20,
        rightIndent=20
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=CN_BOLD,
        fontSize=13,
        spaceBefore=12,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=CN_FONT,
        fontSize=10,
        leading=14,
        alignment=TA_JUSTIFY
    )
    
    story = []
    
    story.append(Paragraph("基于深度学习的图像识别技术研究", title_style))
    story.append(Paragraph("张三¹  李四²  王五¹", author_style))
    story.append(Paragraph("¹某某大学  ²某某研究院", author_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("<b>摘要：</b>本文提出了一种基于卷积神经网络的图像识别方法，"
                           "通过改进网络结构和优化训练策略，在多个基准数据集上取得了"
                           "优异的识别准确率。实验结果表明，所提方法相比传统方法具有"
                           "更好的特征提取能力和鲁棒性，能够有效处理复杂场景下的"
                           "图像识别任务。", abstract_style))
    story.append(Spacer(1, 0.3*cm))
    
    story.append(Paragraph("1 引言", heading_style))
    story.append(Paragraph(
        "图像识别是计算机视觉领域的核心研究问题之一，旨在让计算机能够自动理解"
        "和解释图像内容。随着深度学习技术的快速发展，卷积神经网络（CNN）已成为"
        "图像识别任务的主流方法。AlexNet在2012年ImageNet竞赛中的成功，标志着"
        "深度学习时代的到来。",
        body_style
    ))
    story.append(Paragraph(
        "近年来，研究者们提出了各种改进的CNN结构，如VGGNet、GoogLeNet、ResNet等，"
        "不断刷新图像识别的准确率记录。然而，在复杂真实场景中，由于光照变化、"
        "遮挡、视角变化等因素的影响，图像识别仍然面临诸多挑战。",
        body_style
    ))
    
    story.append(Paragraph("2 相关工作", heading_style))
    story.append(Paragraph(
        "传统的图像识别方法主要依赖手工设计的特征提取器，如SIFT、HOG、SURF等。"
        "这些方法需要专家知识来设计合适的特征，且在复杂场景下的泛化能力有限。"
        "与传统方法不同，深度学习方法能够自动从数据中学习特征表示，大大减少了"
        "对人工特征工程的依赖。",
        body_style
    ))
    story.append(Paragraph(
        "Krizhevsky等人提出的AlexNet首次证明了深度CNN在大规模图像识别任务中的"
        "有效性。随后，Simonyan和Zisserman提出了VGGNet，通过使用更小的3×3卷积核"
        "和更深的网络结构，进一步提高了识别性能。He等人提出的残差网络（ResNet）"
        "通过引入跳跃连接，成功训练了超过1000层的深度网络。",
        body_style
    ))
    
    story.append(Paragraph("3 方法", heading_style))
    story.append(Paragraph(
        "本文提出的方法主要包括三个部分：特征提取网络、注意力机制和分类器。"
        "特征提取网络采用改进的ResNet结构，通过引入多尺度特征融合模块来增强"
        "网络对不同尺度目标的感知能力。注意力机制用于自适应地聚焦于图像中的"
        "关键区域，抑制无关背景信息的干扰。",
        body_style
    ))
    story.append(Paragraph(
        "在训练阶段，我们采用了标签平滑、混合训练和知识蒸馏等策略来提高模型的"
        "泛化能力。标签平滑通过软化目标标签来减少模型对训练数据的过拟合。"
        "混合训练通过随机组合样本对来增加训练数据的多样性。知识蒸馏则利用"
        "大模型的软标签来指导小模型的学习。",
        body_style
    ))
    
    story.append(Paragraph("4 实验", heading_style))
    story.append(Paragraph(
        "为了验证所提方法的有效性，我们在三个常用的基准数据集上进行了实验："
        "CIFAR-10、CIFAR-100和ImageNet。所有实验均在配备NVIDIA V100 GPU的"
        "服务器上进行，使用PyTorch深度学习框架实现。",
        body_style
    ))
    story.append(Paragraph(
        "实验结果表明，我们的方法在三个数据集上均取得了优于现有方法的性能。"
        "在ImageNet数据集上，Top-1准确率达到了82.3%，Top-5准确率达到了96.1%。"
        "此外，通过消融实验，我们验证了各个组件的有效性，证明了所提方法的"
        "合理性和优越性。",
        body_style
    ))
    
    story.append(Paragraph("5 结论", heading_style))
    story.append(Paragraph(
        "本文提出了一种基于改进卷积神经网络的图像识别方法，通过多尺度特征融合"
        "和注意力机制增强了网络的特征提取能力。实验结果表明，所提方法在多个"
        "基准数据集上取得了优异的性能。未来的研究工作将进一步探索如何将该方法"
        "应用于视频识别和目标检测等更多计算机视觉任务。",
        body_style
    ))
    
    doc.build(story)
    print(f"+ 生成样本2: {filename.name} (双栏排版)")
    return filename


def generate_sample3_tables():
    filename = SAMPLES_DIR / "sample3_tables.pdf"
    
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="含表格示例文档",
        author="PDF抽取测试",
        subject="表格识别测试"
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=CN_BOLD,
        fontSize=18,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=CN_BOLD,
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=CN_FONT,
        fontSize=11,
        leading=16
    )
    
    story = []
    
    story.append(Paragraph("销售数据统计报告", title_style))
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("一、产品销售数据表", heading_style))
    story.append(Paragraph(
        "下表展示了本公司2024年各产品在不同季度的销售数据，包括销售数量、"
        "单价和销售额等详细信息。",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))
    
    data1 = [
        ["产品名称", "Q1销量", "Q2销量", "Q3销量", "Q4销量", "单价(元)", "年度总额(元)"],
        ["产品A", "1,200", "1,350", "1,500", "1,800", "299", "1,751,150"],
        ["产品B", "850", "920", "1,100", "1,250", "599", "2,363,050"],
        ["产品C", "2,100", "2,300", "2,500", "2,800", "129", "1,242,900"],
        ["产品D", "650", "780", "890", "950", "899", "2,919,230"],
        ["产品E", "1,500", "1,650", "1,720", "1,900", "399", "2,894,730"],
    ]
    
    t1 = Table(data1, colWidths=[2.5*cm, 1.8*cm, 1.8*cm, 1.8*cm, 1.8*cm, 2*cm, 3*cm])
    t1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CN_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey])
    ]))
    story.append(t1)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("二、员工绩效评估表", heading_style))
    story.append(Paragraph(
        "下表是各部门员工的年度绩效评估结果，包含工作态度、专业技能、"
        "团队协作和创新能力四个维度的评分。",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))
    
    data2 = [
        ["部门", "员工姓名", "工作态度", "专业技能", "团队协作", "创新能力", "综合评分", "等级"],
        ["技术部", "张三", "95", "92", "88", "90", "91.25", "A"],
        ["技术部", "李四", "88", "96", "85", "92", "90.25", "A"],
        ["市场部", "王五", "90", "85", "93", "88", "89.00", "B+"],
        ["市场部", "赵六", "92", "80", "95", "86", "88.25", "B+"],
        ["人事部", "孙七", "95", "82", "94", "80", "87.75", "B"],
        ["财务部", "周八", "88", "90", "86", "84", "87.00", "B"],
    ]
    
    t2 = Table(data2, colWidths=[1.8*cm, 2*cm, 1.5*cm, 1.5*cm, 1.5*cm, 1.5*cm, 2*cm, 1.5*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CN_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('SPAN', (0, 1), (0, 2)),
        ('SPAN', (0, 3), (0, 4)),
        ('BACKGROUND', (0, 1), (0, 2), colors.lightblue),
        ('BACKGROUND', (0, 3), (0, 4), colors.lightgreen),
        ('BACKGROUND', (0, 5), (0, 5), colors.lightyellow),
        ('BACKGROUND', (0, 6), (0, 6), colors.lightpink),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(PageBreak())
    
    story.append(Paragraph("三、产品规格参数对比表", heading_style))
    story.append(Paragraph(
        "下表对比了三款旗舰手机的详细规格参数。",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))
    
    data3 = [
        ["参数项", "手机A", "手机B", "手机C"],
        ["发布日期", "2024-03-15", "2024-02-20", "2024-01-10"],
        ["处理器", "骁龙8 Gen3", "天玑9300", "麒麟9010"],
        ["屏幕尺寸", "6.8英寸", "6.78英寸", "6.9英寸"],
        ["屏幕分辨率", "2800×1260", "3168×1440", "2800×1260"],
        ["后置主摄", "5000万像素", "2亿像素", "5000万像素"],
        ["电池容量", "5500mAh", "5000mAh", "5700mAh"],
        ["充电功率", "80W有线/50W无线", "120W有线/50W无线", "88W有线/50W无线"],
        ["起售价格", "¥4,999", "¥4,299", "¥6,499"],
    ]
    
    t3 = Table(data3, colWidths=[3*cm, 4*cm, 4*cm, 4*cm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CN_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('BACKGROUND', (0, 1), (0, -1), colors.HexColor('#ecf0f1')),
        ('FONTNAME', (0, 1), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(t3)
    story.append(Spacer(1, 0.5*cm))
    
    story.append(Paragraph("四、月度库存表", heading_style))
    story.append(Paragraph(
        "下表是本月各仓库的库存统计。",
        body_style
    ))
    story.append(Spacer(1, 0.3*cm))
    
    data4 = [
        ["仓库编号", "商品种类", "库存数量", "库存价值(元)", "最近更新"],
        ["WH-001", "156", "12,450", "1,250,000", "2024-12-01"],
        ["WH-002", "89", "8,920", "890,500", "2024-12-02"],
        ["WH-003", "234", "25,680", "3,200,000", "2024-12-01"],
        ["WH-004", "67", "5,430", "456,800", "2024-12-03"],
        ["WH-005", "178", "18,900", "2,100,000", "2024-12-01"],
        ["合计", "724", "71,380", "7,897,300", "-"],
    ]
    
    t4 = Table(data4, colWidths=[3*cm, 2.5*cm, 3*cm, 3.5*cm, 3*cm])
    t4.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.seagreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), CN_BOLD),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), CN_FONT),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#fff3cd')),
        ('FONTNAME', (0, -1), (-1, -1), CN_BOLD),
    ]))
    story.append(t4)
    
    doc.build(story)
    print(f"+ 生成样本3: {filename.name} (含表格)")
    return filename


def generate_sample4_toc():
    filename = SAMPLES_DIR / "sample4_toc.pdf"
    
    doc = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
        title="软件设计文档",
        author="开发团队",
        subject="完整目录与书签示例"
    )
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=CN_BOLD,
        fontSize=20,
        alignment=TA_CENTER,
        spaceAfter=30
    )
    h1_style = ParagraphStyle(
        'H1',
        parent=styles['Heading1'],
        fontName=CN_BOLD,
        fontSize=18,
        spaceBefore=20,
        spaceAfter=15
    )
    h2_style = ParagraphStyle(
        'H2',
        parent=styles['Heading2'],
        fontName=CN_BOLD,
        fontSize=14,
        spaceBefore=15,
        spaceAfter=10
    )
    h3_style = ParagraphStyle(
        'H3',
        parent=styles['Heading3'],
        fontName=CN_BOLD,
        fontSize=12,
        spaceBefore=12,
        spaceAfter=8
    )
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontName=CN_FONT,
        fontSize=11,
        leading=17,
        alignment=TA_JUSTIFY,
        firstLineIndent=22
    )
    toc_title_style = ParagraphStyle(
        'TOCTitle',
        parent=styles['Heading1'],
        fontName=CN_BOLD,
        fontSize=16,
        alignment=TA_CENTER,
        spaceAfter=20
    )
    toc_entry_style = ParagraphStyle(
        'TOCEntry',
        parent=styles['BodyText'],
        fontName=CN_FONT,
        fontSize=11,
        leading=18,
        leftIndent=0
    )
    toc_sub_style = ParagraphStyle(
        'TOCSub',
        parent=styles['BodyText'],
        fontName=CN_FONT,
        fontSize=10,
        leading=16,
        leftIndent=20
    )
    toc_subsub_style = ParagraphStyle(
        'TOCSubSub',
        parent=styles['BodyText'],
        fontName=CN_FONT,
        fontSize=9,
        leading=14,
        leftIndent=40
    )
    
    story = []
    
    story.append(Paragraph("企业资源规划系统（ERP）设计文档", title_style))
    story.append(Paragraph("版本：v2.1.0", ParagraphStyle('ver', parent=styles['Normal'], alignment=TA_CENTER, fontName=CN_FONT, fontSize=12)))
    story.append(Paragraph("发布日期：2024年12月", ParagraphStyle('date', parent=styles['Normal'], alignment=TA_CENTER, fontName=CN_FONT, fontSize=12, spaceAfter=30)))
    story.append(PageBreak())
    
    story.append(Paragraph("目  录", toc_title_style))
    story.append(Paragraph("第1章  引言 .......................................................... 3", toc_entry_style))
    story.append(Paragraph("    1.1  项目背景 ............................................ 3", toc_sub_style))
    story.append(Paragraph("    1.2  项目目标 ............................................ 4", toc_sub_style))
    story.append(Paragraph("    1.3  文档范围 ............................................ 5", toc_sub_style))
    story.append(Paragraph("第2章  总体架构设计 .................................................. 6", toc_entry_style))
    story.append(Paragraph("    2.1  系统架构概述 ........................................ 6", toc_sub_style))
    story.append(Paragraph("        2.1.1  分层架构设计 ................................. 6", toc_subsub_style))
    story.append(Paragraph("        2.1.2  模块划分 ..................................... 7", toc_subsub_style))
    story.append(Paragraph("    2.2  技术选型 ............................................ 8", toc_sub_style))
    story.append(Paragraph("    2.3  部署架构 ............................................ 9", toc_sub_style))
    story.append(Paragraph("第3章  功能模块设计 .................................................. 11", toc_entry_style))
    story.append(Paragraph("    3.1  财务管理模块 ........................................ 11", toc_sub_style))
    story.append(Paragraph("    3.2  人力资源模块 ........................................ 13", toc_sub_style))
    story.append(Paragraph("    3.3  供应链管理模块 ...................................... 15", toc_sub_style))
    story.append(Paragraph("    3.4  客户关系管理模块 .................................... 17", toc_sub_style))
    story.append(Paragraph("第4章  数据库设计 .................................................... 19", toc_entry_style))
    story.append(Paragraph("    4.1  数据库架构 .......................................... 19", toc_sub_style))
    story.append(Paragraph("    4.2  核心数据表设计 ...................................... 20", toc_sub_style))
    story.append(Paragraph("第5章  接口设计 ...................................................... 22", toc_entry_style))
    story.append(Paragraph("第6章  安全性设计 .................................................... 24", toc_entry_style))
    story.append(Paragraph("第7章  性能优化 ...................................................... 26", toc_entry_style))
    story.append(PageBreak())
    
    story.append(Paragraph("第1章 引言", h1_style))
    story.append(Paragraph("1.1 项目背景", h2_style))
    story.append(Paragraph(
        "随着企业规模的不断扩大和业务的日益复杂，传统的分散式管理系统已经无法满足"
        "企业发展的需求。各部门之间信息孤岛严重，数据共享困难，决策支持能力不足。"
        "为了提高企业的运营效率，降低管理成本，增强企业的核心竞争力，公司决定"
        "开发一套全新的企业资源规划（ERP）系统。",
        body_style
    ))
    story.append(Paragraph(
        "本ERP系统将整合企业的财务管理、人力资源管理、供应链管理、客户关系管理等"
        "核心业务模块，实现业务流程的标准化和信息资源的共享化，为企业管理层提供"
        "及时、准确、全面的决策支持。",
        body_style
    ))
    
    story.append(Paragraph("1.2 项目目标", h2_style))
    story.append(Paragraph(
        "本项目的主要目标包括：建立统一的企业信息平台，消除信息孤岛；实现业务流程"
        "的自动化和标准化，提高运营效率30%以上；提供实时的数据分析和报表功能，"
        "支持科学决策；构建可扩展的系统架构，满足未来5年的业务发展需求；确保系统"
        "的安全性、稳定性和可靠性，达到99.9%的系统可用性。",
        body_style
    ))
    
    story.append(Paragraph("1.3 文档范围", h2_style))
    story.append(Paragraph(
        "本文档详细描述了ERP系统的设计方案，包括总体架构设计、功能模块设计、"
        "数据库设计、接口设计、安全性设计和性能优化策略等内容。本文档的读者包括"
        "项目管理人员、系统架构师、开发人员、测试人员以及相关业务人员。",
        body_style
    ))
    story.append(PageBreak())
    
    story.append(Paragraph("第2章 总体架构设计", h1_style))
    story.append(Paragraph("2.1 系统架构概述", h2_style))
    story.append(Paragraph("2.1.1 分层架构设计", h3_style))
    story.append(Paragraph(
        "本系统采用经典的分层架构模式，从上到下依次为：表现层、应用层、业务逻辑层、"
        "数据访问层和数据层。各层之间通过明确的接口进行通信，实现了关注点分离，"
        "提高了系统的可维护性和可扩展性。",
        body_style
    ))
    story.append(Paragraph(
        "表现层负责用户界面的展示和用户交互的处理；应用层负责协调业务逻辑的执行，"
        "实现业务流程的编排；业务逻辑层包含核心的业务规则和领域逻辑；数据访问层"
        "负责与数据库的交互，提供数据持久化服务；数据层则是数据的物理存储。",
        body_style
    ))
    
    story.append(Paragraph("2.1.2 模块划分", h3_style))
    story.append(Paragraph(
        "系统划分为四大核心业务模块：财务管理模块、人力资源模块、供应链管理模块和"
        "客户关系管理模块。每个模块又进一步细分为多个子模块，各模块之间通过标准"
        "接口进行通信，实现了高内聚低耦合的设计原则。",
        body_style
    ))
    
    story.append(Paragraph("2.2 技术选型", h2_style))
    story.append(Paragraph(
        "后端采用Java Spring Boot作为核心开发框架，使用MyBatis Plus作为ORM框架，"
        "数据库采用MySQL 8.0，缓存使用Redis，消息队列使用RabbitMQ。前端采用"
        "Vue 3 + TypeScript + Element Plus技术栈。微服务架构使用Spring Cloud"
        " Alibaba，服务注册与发现使用Nacos，配置中心使用Apollo。",
        body_style
    ))
    
    story.append(Paragraph("2.3 部署架构", h2_style))
    story.append(Paragraph(
        "系统采用容器化部署方案，使用Docker进行应用打包，Kubernetes进行容器编排。"
        "部署环境分为开发环境、测试环境、预发布环境和生产环境。生产环境采用"
        "多可用区部署，确保系统的高可用性。使用Nginx作为反向代理和负载均衡器，"
        "ELK Stack进行日志收集和分析，Prometheus + Grafana进行系统监控。",
        body_style
    ))
    story.append(PageBreak())
    
    story.append(Paragraph("第3章 功能模块设计", h1_style))
    story.append(Paragraph("3.1 财务管理模块", h2_style))
    story.append(Paragraph(
        "财务管理模块是ERP系统的核心模块之一，包括总账管理、应收应付管理、固定资产"
        "管理、成本核算、预算管理和报表分析等子模块。该模块实现了财务数据的"
        "自动化处理，减少了人工操作，提高了财务数据的准确性和及时性。",
        body_style
    ))
    story.append(Paragraph(
        "总账管理模块支持多账簿、多币种核算，提供灵活的凭证管理和期末处理功能。"
        "应收应付管理模块实现了对客户和供应商往来账款的全面管理，支持账龄分析、"
        "坏账计提等功能。固定资产管理模块支持资产的全生命周期管理，包括资产购置、"
        "折旧、调拨、处置等。",
        body_style
    ))
    
    story.append(Paragraph("3.2 人力资源模块", h2_style))
    story.append(Paragraph(
        "人力资源模块涵盖了企业人力资源管理的各个方面，包括组织管理、人事管理、"
        "考勤管理、薪酬管理、绩效管理、招聘管理和培训管理等子模块。该模块帮助"
        "企业实现人力资源管理的信息化、规范化和流程化。",
        body_style
    ))
    
    story.append(Paragraph("3.3 供应链管理模块", h2_style))
    story.append(Paragraph(
        "供应链管理模块包括采购管理、库存管理、销售管理和物流管理等子模块。"
        "该模块实现了从采购到销售的完整供应链流程管理，帮助企业优化库存水平，"
        "提高供应链响应速度，降低运营成本。",
        body_style
    ))
    
    story.append(Paragraph("3.4 客户关系管理模块", h2_style))
    story.append(Paragraph(
        "客户关系管理模块包括客户信息管理、销售机会管理、客户服务管理和"
        "数据分析等子模块。该模块帮助企业建立以客户为中心的经营理念，提高"
        "客户满意度和忠诚度，促进销售业绩的增长。",
        body_style
    ))
    story.append(PageBreak())
    
    story.append(Paragraph("第4章 数据库设计", h1_style))
    story.append(Paragraph("4.1 数据库架构", h2_style))
    story.append(Paragraph(
        "系统采用主从复制和读写分离的数据库架构。主库负责数据写入操作，多个从库"
        "负责数据读取操作，通过中间件实现读写路由。对于超大规模的数据表，采用"
        "分库分表方案，使用ShardingSphere进行数据分片。冷热数据分离存储，"
        "历史数据归档到低成本存储介质。",
        body_style
    ))
    
    story.append(Paragraph("4.2 核心数据表设计", h2_style))
    story.append(Paragraph(
        "系统设计了数十张核心数据表，包括组织机构表、员工信息表、客户信息表、"
        "供应商信息表、产品信息表、订单表、发票表、会计科目表、凭证表等。"
        "所有数据表都遵循第三范式设计原则，确保数据的一致性和完整性。建立了"
        "完善的索引策略，优化查询性能。",
        body_style
    ))
    story.append(PageBreak())
    
    story.append(Paragraph("第5章 接口设计", h1_style))
    story.append(Paragraph(
        "系统采用RESTful API设计风格，所有接口都遵循统一的设计规范。接口版本通过"
        "URL路径进行控制，如/api/v1/resource。使用HTTP状态码表示请求结果，"
        "2xx表示成功，4xx表示客户端错误，5xx表示服务器错误。所有接口都支持"
        "JSON格式的请求和响应数据。",
        body_style
    ))
    story.append(Paragraph(
        "接口认证采用JWT Token方案，用户登录后获取访问令牌，后续请求在Header中"
        "携带该令牌。接口权限通过RBAC模型进行控制，确保用户只能访问其权限范围内"
        "的资源。所有接口都有详细的文档说明，使用Swagger/OpenAPI规范进行描述。",
        body_style
    ))
    story.append(PageBreak())
    
    story.append(Paragraph("第6章 安全性设计", h1_style))
    story.append(Paragraph(
        "系统从多个层面进行安全性设计。在应用层，实现了完善的认证和授权机制，"
        "防止未授权访问。在数据层，敏感数据采用加密存储，重要操作进行审计日志"
        "记录。在网络层，使用HTTPS协议加密传输，部署Web应用防火墙（WAF）防御"
        "常见的Web攻击。在系统层，服务器进行安全加固，定期进行漏洞扫描和"
        "安全评估。",
        body_style
    ))
    story.append(Paragraph(
        "系统还实现了数据备份和灾难恢复机制，定期进行全量备份和增量备份，确保"
        "数据安全。制定了详细的安全应急预案，定期进行安全演练。",
        body_style
    ))
    story.append(PageBreak())
    
    story.append(Paragraph("第7章 性能优化", h1_style))
    story.append(Paragraph(
        "系统从多个维度进行性能优化。在前端，采用代码分割、懒加载、缓存等技术"
        "提升页面加载速度。在后端，使用多级缓存策略（本地缓存 + 分布式缓存）"
        "减少数据库访问。数据库层面，优化SQL语句，建立合适的索引，进行分库分表。"
        "架构层面，采用微服务架构，实现服务的独立部署和扩展。",
        body_style
    ))
    story.append(Paragraph(
        "通过CDN加速静态资源访问，使用消息队列实现业务的异步处理。进行容量规划"
        "和压力测试，确保系统能够承受预期的业务压力。建立完善的性能监控体系，"
        "实时监控系统性能指标，及时发现和解决性能问题。",
        body_style
    ))
    
    doc.build(story)
    
    temp_filename = filename.with_name(filename.stem + "_temp.pdf")
    filename.rename(temp_filename)
    
    doc_with_toc = fitz.open(str(temp_filename))
    
    toc = [
        [1, "第1章 引言", 3],
        [2, "1.1 项目背景", 3],
        [2, "1.2 项目目标", 3],
        [2, "1.3 文档范围", 3],
        [1, "第2章 总体架构设计", 4],
        [2, "2.1 系统架构概述", 4],
        [3, "2.1.1 分层架构设计", 4],
        [3, "2.1.2 模块划分", 4],
        [2, "2.2 技术选型", 4],
        [2, "2.3 部署架构", 4],
        [1, "第3章 功能模块设计", 5],
        [2, "3.1 财务管理模块", 5],
        [2, "3.2 人力资源模块", 5],
        [2, "3.3 供应链管理模块", 5],
        [2, "3.4 客户关系管理模块", 5],
        [1, "第4章 数据库设计", 6],
        [2, "4.1 数据库架构", 6],
        [2, "4.2 核心数据表设计", 6],
        [1, "第5章 接口设计", 7],
        [1, "第6章 安全性设计", 8],
        [1, "第7章 性能优化", 9],
    ]
    
    doc_with_toc.set_toc(toc)
    doc_with_toc.save(str(filename))
    doc_with_toc.close()
    
    temp_filename.unlink()
    
    print(f"+ 生成样本4: {filename.name} (含目录书签)")
    return filename


def generate_sample5_scanned():
    filename = SAMPLES_DIR / "sample5_scanned.pdf"
    
    width, height = int(8.27 * 300), int(11.69 * 300)
    
    images = []
    
    for page_num in range(3):
        img = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            title_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 48)
            heading_font = ImageFont.truetype("C:/Windows/Fonts/simhei.ttf", 32)
            body_font = ImageFont.truetype("C:/Windows/Fonts/simsun.ttc", 24)
        except:
            title_font = ImageFont.load_default()
            heading_font = ImageFont.load_default()
            body_font = ImageFont.load_default()
        
        margin = 150
        y = margin
        
        if page_num == 0:
            draw.text((width//2, y), "项目可行性研究报告", font=title_font, fill='black', anchor='ma')
            y += 100
            draw.text((width//2, y), "——关于建设智慧城市数据中心的建议", font=heading_font, fill='darkgray', anchor='ma')
            y += 120
            
            draw.text((margin, y), "一、项目背景", font=heading_font, fill='black')
            y += 60
            
            paragraphs = [
                "随着我国城市化进程的不断加快，城市管理面临着越来越多的挑战。人口膨胀、"
                "交通拥堵、环境污染、资源短缺等问题日益突出，传统的城市管理模式已经难以"
                "适应新形势下的发展需求。",
                "智慧城市建设成为城市可持续发展的必然选择。通过运用物联网、云计算、大数据、"
                "人工智能等新一代信息技术，全面感知、互联、分析、整合城市运行核心系统的"
                "各项关键信息，从而实现对城市管理和服务的智能化响应。",
                "数据中心作为智慧城市的核心基础设施，承载着海量城市数据的存储、处理和"
                "分析任务，是智慧城市建设的重中之重。建设一个高水平的智慧城市数据中心，"
                "对于提升城市管理水平、改善公共服务质量、促进产业转型升级具有重要意义。"
            ]
            
            for para in paragraphs:
                words = para
                line_height = 36
                max_width = width - 2 * margin
                
                current_line = ""
                for char in words:
                    test_line = current_line + char
                    bbox = draw.textbbox((0, 0), test_line, font=body_font)
                    if bbox[2] - bbox[0] <= max_width:
                        current_line = test_line
                    else:
                        draw.text((margin, y), current_line, font=body_font, fill='black')
                        y += line_height
                        current_line = char
                if current_line:
                    draw.text((margin, y), current_line, font=body_font, fill='black')
                    y += line_height
                y += 20
        
        elif page_num == 1:
            draw.text((margin, y), "二、项目建设的必要性", font=heading_font, fill='black')
            y += 60
            
            points = [
                "（一）提升城市治理能力的需要",
                "    通过建设智慧城市数据中心，可以实现城市各部门数据的整合与共享，打破"
                "信息孤岛，提高政府决策的科学性和精准性。",
                "",
                "（二）优化公共服务供给的需要",
                "    基于统一的数据中心平台，可以开发各类智慧应用，如智慧交通、智慧医疗、"
                "智慧教育等，为市民提供更加便捷、高效、优质的公共服务。",
                "",
                "（三）促进数字经济发展的需要",
                "    数据中心的建设将带动大数据、云计算、人工智能等相关产业的发展，形成"
                "新的经济增长点，推动城市产业结构优化升级。",
                "",
                "（四）保障城市安全运行的需要",
                "    数据中心可以实时监测城市运行状态，及时发现和处置各类安全隐患，"
                "提高城市应急管理能力，保障城市安全稳定运行。"
            ]
            
            for point in points:
                if point == "":
                    y += 15
                    continue
                
                line_height = 36
                max_width = width - 2 * margin
                
                current_line = ""
                for char in point:
                    test_line = current_line + char
                    bbox = draw.textbbox((0, 0), test_line, font=body_font)
                    if bbox[2] - bbox[0] <= max_width:
                        current_line = test_line
                    else:
                        draw.text((margin, y), current_line, font=body_font, fill='black')
                        y += line_height
                        current_line = char
                if current_line:
                    draw.text((margin, y), current_line, font=body_font, fill='black')
                    y += line_height
        
        else:
            draw.text((margin, y), "三、项目建设方案", font=heading_font, fill='black')
            y += 60
            
            content = [
                "本项目拟分三期进行建设：",
                "",
                "一期工程（2025年）：完成数据中心基础设施建设，包括机房装修、供电系统、"
                "制冷系统、消防系统等，采购和部署必要的服务器、存储设备和网络设备，"
                "搭建基础云平台。",
                "",
                "二期工程（2026年）：完成数据整合平台建设，实现各部门业务系统的数据对接"
                "和数据共享。建设城市大数据平台，开发基础分析应用。",
                "",
                "三期工程（2027年）：完善智慧应用体系，开发智慧交通、智慧环保、智慧安防"
                "等典型应用。建立完善的运营管理体系，确保数据中心持续稳定运行。"
            ]
            
            line_height = 36
            max_width = width - 2 * margin
            
            for para in content:
                if para == "":
                    y += 15
                    continue
                    
                current_line = ""
                for char in para:
                    test_line = current_line + char
                    bbox = draw.textbbox((0, 0), test_line, font=body_font)
                    if bbox[2] - bbox[0] <= max_width:
                        current_line = test_line
                    else:
                        draw.text((margin, y), current_line, font=body_font, fill='black')
                        y += line_height
                        current_line = char
                if current_line:
                    draw.text((margin, y), current_line, font=body_font, fill='black')
                    y += line_height
            
            y += 40
            draw.text((margin, y), "四、投资估算", font=heading_font, fill='black')
            y += 60
            
            draw.text((margin, y), "项目总投资约为5亿元人民币，其中基础设施建设投资2亿元，", font=body_font, fill='black')
            y += 36
            draw.text((margin, y), "软硬件采购投资1.5亿元，应用开发投资1亿元，其他费用0.5亿元。", font=body_font, fill='black')
        
        img_array = np.array(img)
        noise = np.random.normal(0, 15, img_array.shape).astype(np.int16)
        img_array = np.clip(img_array.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        img = Image.fromarray(img_array)
        
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        images.append(img)
    
    doc = fitz.open()
    
    for idx, img in enumerate(images):
        img_byte_arr = io.BytesIO()
        img.save(img_byte_arr, format='PNG', dpi=(300, 300))
        img_bytes = img_byte_arr.getvalue()
        
        page = doc.new_page(width=A4[0], height=A4[1])
        rect = fitz.Rect(0, 0, A4[0], A4[1])
        page.insert_image(rect, stream=img_bytes)
    
    doc.set_metadata({
        "title": "项目可行性研究报告（扫描件）",
        "author": "规划设计院",
        "subject": "扫描文档测试",
        "creator": "PDF抽取测试",
        "producer": "PIL + PyMuPDF"
    })
    
    doc.save(str(filename))
    doc.close()
    
    print(f"+ 生成样本5: {filename.name} (扫描转PDF)")
    return filename


if __name__ == "__main__":
    print("正在生成测试PDF样本...\n")
    
    try:
        generate_sample1_single_column()
    except Exception as e:
        print(f"- 样本1生成失败: {e}")
    
    try:
        generate_sample2_multi_column()
    except Exception as e:
        print(f"- 样本2生成失败: {e}")
    
    try:
        generate_sample3_tables()
    except Exception as e:
        print(f"- 样本3生成失败: {e}")
    
    try:
        generate_sample4_toc()
    except Exception as e:
        print(f"- 样本4生成失败: {e}")
    
    try:
        generate_sample5_scanned()
    except Exception as e:
        print(f"- 样本5生成失败: {e}")
    
    print(f"\n+ 样本生成完成！所有样本保存在: {SAMPLES_DIR}")
    pdf_files = list(SAMPLES_DIR.glob("*.pdf"))
    print(f"共生成 {len(pdf_files)} 个PDF文件:")
    for f in pdf_files:
        size_kb = f.stat().st_size / 1024
        print(f"  - {f.name} ({size_kb:.1f} KB)")
