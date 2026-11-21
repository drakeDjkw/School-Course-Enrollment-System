"""Сборка файлов Excel (.xlsx) и Word (.docx) из табличных данных."""

from datetime import date
from io import BytesIO

from docx import Document
from docx.shared import Pt
from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter

XLSX_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
DOCX_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _text(value):
    return "" if value is None else str(value)


def build_xlsx(title, headers, rows):
    wb = Workbook()
    ws = wb.active
    ws.title = title[:31]  # Excel ограничивает имя листа 31 символом

    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
    for row in rows:
        ws.append(row)
        for cell, value in zip(ws[ws.max_row], row):
            if isinstance(value, date):
                cell.number_format = "YYYY-MM-DD"

    # ширина колонок по самому длинному значению
    for index, header in enumerate(headers, start=1):
        longest = max([len(_text(header))] + [len(_text(row[index - 1])) for row in rows])
        ws.column_dimensions[get_column_letter(index)].width = min(longest + 2, 50)
    ws.freeze_panes = "A2"

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def build_docx(title, headers, rows):
    doc = Document()
    doc.add_heading(title, level=1)
    doc.add_paragraph(f"Записей: {len(rows)}")

    table = doc.add_table(rows=1, cols=len(headers))
    table.style = "Table Grid"
    for cell, header in zip(table.rows[0].cells, headers):
        cell.text = ""
        run = cell.paragraphs[0].add_run(header)
        run.bold = True
    for row in rows:
        for cell, value in zip(table.add_row().cells, row):
            cell.text = _text(value)

    for paragraph in doc.paragraphs:
        for run in paragraph.runs:
            run.font.size = Pt(11)

    buffer = BytesIO()
    doc.save(buffer)
    return buffer.getvalue()
