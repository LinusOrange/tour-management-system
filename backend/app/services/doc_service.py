from docx import Document
from docx.shared import Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io

def create_study_tour_docx(data: dict):
    doc = Document()
    
    # 设置大标题
    title = doc.add_heading(f"《{data['location']['name']}》研学课程方案", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # 第一部分：研学基地 (来自数据库)
    doc.add_heading('一、 研学基地概况', level=1)
    doc.add_paragraph(f"基地名称：{data['location']['name']}")
    doc.add_paragraph(f"基地地址：{data['location']['address']}")
    doc.add_paragraph(data['location']['description']) # 这是我们之前生成的 500 字介绍

    # 第二/三/四部分：AI 生成的内容
    for idx, (title, key) in enumerate([('二、 课程背景', 'background'), ('三、 研学目标', 'goals'), ('四、 课程亮点', 'highlights')], 2):
        doc.add_heading(title, level=1)
        doc.add_paragraph(data['ai_sections'].get(key, ''))

    # 第五部分：研学流程 (来自排产工作台)
    doc.add_heading('五、 研学行程安排', level=1)
    table = doc.add_table(rows=1, cols=3)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = '序号'
    hdr_cells[1].text = '活动名称'
    hdr_cells[2].text = '时长'
    
    for i, act in enumerate(data['activities'], 1):
        row_cells = table.add_row().cells
        row_cells[0].text = str(i)
        row_cells[1].text = act['title']
        row_cells[2].text = f"{act['duration']} min"

    # 将文档存入内存流
    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream