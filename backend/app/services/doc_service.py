from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
import io


def create_study_tour_docx(data: dict):
    doc = Document()

    title_text = data.get('title') or '研学课程方案'
    title = doc.add_heading(f"《{title_text}》", 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    ai_sections = data.get('ai_sections', {})
    locations = data.get('locations', [])
    timeline = data.get('timeline', [])

    # 第一部分：研学基地（来自排产工作台+AI润色）
    doc.add_heading('一、研学基地', level=1)
    section_1 = ai_sections.get('section_1_base', '').strip()
    if section_1:
        doc.add_paragraph(section_1)
    else:
        for loc in locations:
            doc.add_paragraph(f"基地名称：{loc.get('name', '未命名基地')}")
            doc.add_paragraph(f"基地地址：{loc.get('address', '待补充')}")
            doc.add_paragraph(loc.get('description', '暂无基地描述'))
            doc.add_paragraph('')

    # 第二/三/四部分：AI 生成
    section_map = [
        ('二、课程背景', 'section_2_background'),
        ('三、研学目标', 'section_3_goals'),
        ('四、课程亮点', 'section_4_highlights')
    ]
    for heading, key in section_map:
        doc.add_heading(heading, level=1)
        doc.add_paragraph(ai_sections.get(key, '内容生成失败，请手动补充。'))

    # 第五部分：研学流程（AI流程说明 + 时间轴表格）
    doc.add_heading('五、研学流程', level=1)
    doc.add_paragraph(ai_sections.get('section_5_process', ''))

    table = doc.add_table(rows=1, cols=4)
    table.style = 'Table Grid'
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = '序号'
    hdr_cells[1].text = '时间段'
    hdr_cells[2].text = '活动名称'
    hdr_cells[3].text = '基地/时长'

    for i, act in enumerate(timeline, 1):
        row_cells = table.add_row().cells
        row_cells[0].text = str(i)
        row_cells[1].text = act.get('display_time', '时间待定')
        row_cells[2].text = act.get('title', '未命名活动')
        row_cells[3].text = f"{act.get('location_name', '待定基地')} / {act.get('duration', 0)} 分钟"

    file_stream = io.BytesIO()
    doc.save(file_stream)
    file_stream.seek(0)
    return file_stream
