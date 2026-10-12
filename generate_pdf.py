import os
import re
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable, Preformatted
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        if self._pageNumber == 1:
            return  # Suppress running header/footer on cover/first page
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Running Header
        self.drawString(54, 750, "ReimburseAI — Technical Design Document (v1.0.0)")
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 744, 558, 744)
        
        # Running Footer
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(558, 36, page_str)
        self.drawString(54, 36, "Confidential — Corporate Finance Automation Architecture")
        self.line(54, 46, 558, 46)
        self.restoreState()

def build_pdf(md_path: str, pdf_path: str):
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Replace currency symbol to prevent Type1 font encoding issues
    md_text = md_text.replace("₹", "Rs. ")

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#1e1b4b")   # Deep Indigo
    c_secondary = colors.HexColor("#312e81") # Indigo-900
    c_text = colors.HexColor("#1e293b")      # Slate-800
    c_code_bg = colors.HexColor("#f8fafc")   # Slate-50
    c_callout_bg = colors.HexColor("#f1f5f9")# Slate-100

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=30,
        textColor=c_primary,
        spaceAfter=6
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#4338ca"),
        spaceAfter=15
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=14,
        textColor=colors.HexColor("#475569")
    )

    h1_style = ParagraphStyle(
        'SecH1',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=15,
        leading=19,
        textColor=c_primary,
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'SecH2',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=c_secondary,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )

    h3_style = ParagraphStyle(
        'SecH3',
        parent=styles['Heading3'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=8,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12.5,
        textColor=c_text,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'DocBullet',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=c_text,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=2
    )

    code_style = ParagraphStyle(
        'DocCode',
        parent=styles['Code'],
        fontName='Courier',
        fontSize=7.2,
        leading=9.5,
        textColor=colors.HexColor("#0f172a")
    )

    callout_style = ParagraphStyle(
        'DocCallout',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=8,
        leading=11.5,
        textColor=colors.HexColor("#334155")
    )

    story = []

    lines = md_text.split("\n")
    i = 0
    n = len(lines)

    in_code_block = False
    code_lines = []
    code_type = ""

    while i < n:
        line = lines[i]

        # Code block handling (Mermaid or regular code)
        if line.strip().startswith("```"):
            if not in_code_block:
                in_code_block = True
                code_type = line.strip()[3:].strip().lower()
                code_lines = []
            else:
                in_code_block = False
                code_content = "\n".join(code_lines)
                
                header_label = f"Code: {code_type.upper()}" if code_type else "Source / Configuration"
                if "mermaid" in code_type:
                    header_label = "Architecture Specification Diagram (Mermaid)"

                # For code blocks under 25 lines, wrap in a neat styled table
                if len(code_lines) <= 25:
                    tbl_data = [
                        [Paragraph(f"<b>{header_label}</b>", meta_style)],
                        [Preformatted(code_content, code_style)]
                    ]
                    code_tbl = Table(tbl_data, colWidths=[504])
                    code_tbl.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
                        ('BACKGROUND', (0, 1), (-1, 1), c_code_bg),
                        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
                        ('TOPPADDING', (0, 0), (-1, -1), 3),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                        ('LEFTPADDING', (0, 0), (-1, -1), 6),
                        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                    ]))
                    story.append(code_tbl)
                else:
                    # For longer code/diagrams, split into Preformatted chunks so ReportLab splits gracefully
                    story.append(Paragraph(f"<b>{header_label}</b>", meta_style))
                    story.append(Spacer(1, 2))
                    story.append(Preformatted(code_content, code_style))

                story.append(Spacer(1, 6))
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        stripped = line.strip()

        # Markdown Table Detection
        if stripped.startswith("|") and stripped.endswith("|"):
            table_lines = []
            while i < n and lines[i].strip().startswith("|") and lines[i].strip().endswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            
            # Parse table
            if len(table_lines) >= 2:
                rows = []
                for idx, tline in enumerate(table_lines):
                    if idx == 1 and ("---" in tline or ":---" in tline):
                        continue  # Skip separator line
                    cells = [c.strip() for c in tline.split("|")[1:-1]]
                    row_cells = []
                    for c_text_item in cells:
                        # Clean bold tags
                        clean_c = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', c_text_item)
                        clean_c = re.sub(r'\*(.*?)\*', r'<i>\1</i>', clean_c)
                        clean_c = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', clean_c)
                        p_cell = Paragraph(clean_c, body_style)
                        row_cells.append(p_cell)
                    rows.append(row_cells)
                
                num_cols = max(len(r) for r in rows) if rows else 1
                col_width = 504 / num_cols
                col_widths = [col_width] * num_cols
                # Custom column width balancing if 2-4 cols
                if num_cols == 2:
                    col_widths = [140, 364]
                elif num_cols == 3:
                    col_widths = [130, 110, 264]
                elif num_cols == 4:
                    col_widths = [100, 100, 80, 224]

                t_obj = Table(rows, colWidths=col_widths, repeatRows=1)
                t_obj.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#e0e7ff")),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor("#1e1b4b")),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                    ('TOPPADDING', (0, 0), (-1, -1), 3),
                    ('LEFTPADDING', (0, 0), (-1, -1), 4),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                    ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#c7d2fe")),
                    ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ]))
                story.append(t_obj)
                story.append(Spacer(1, 6))
            continue

        # Blank line
        if not stripped:
            story.append(Spacer(1, 3))
            i += 1
            continue

        # Horizontal rule
        if stripped in ["---", "***", "___"]:
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cbd5e1"), spaceBefore=4, spaceAfter=6))
            i += 1
            continue

        # Document Header
        if stripped.startswith("# Technical Design Document"):
            story.append(Paragraph(stripped[2:], title_style))
            story.append(Paragraph("ReimburseAI — Autonomous Corporate Expense & Reimbursement Copilot", subtitle_style))
            i += 1
            continue

        # Headers
        if stripped.startswith("## "):
            h_text = stripped[3:].strip()
            # Clean bold
            h_text = re.sub(r'\*\*(.*?)\*\*', r'\1', h_text)
            story.append(Paragraph(h_text, h1_style))
            i += 1
            continue

        if stripped.startswith("### "):
            h_text = stripped[4:].strip()
            h_text = re.sub(r'\*\*(.*?)\*\*', r'\1', h_text)
            story.append(Paragraph(h_text, h2_style))
            i += 1
            continue

        if stripped.startswith("#### "):
            h_text = stripped[5:].strip()
            h_text = re.sub(r'\*\*(.*?)\*\*', r'\1', h_text)
            story.append(Paragraph(h_text, h3_style))
            i += 1
            continue

        # Blockquotes / Callout
        if stripped.startswith(">"):
            quote_text = stripped[1:].strip()
            quote_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', quote_text)
            quote_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', quote_text)
            quote_text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', quote_text)
            callout_data = [[Paragraph(quote_text, callout_style)]]
            callout_tbl = Table(callout_data, colWidths=[504])
            callout_tbl.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), c_callout_bg),
                ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ('LINELEFT', (0, 0), (-1, -1), 2.5, colors.HexColor("#4f46e5")),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ]))
            story.append(callout_tbl)
            story.append(Spacer(1, 4))
            i += 1
            continue

        # Bullet items
        if stripped.startswith(("- ", "* ", "• ")):
            b_text = stripped[2:].strip()
            b_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', b_text)
            b_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', b_text)
            b_text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', b_text)
            story.append(Paragraph(f"• {b_text}", bullet_style))
            i += 1
            continue

        # Numbered list
        match_num = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if match_num:
            num = match_num.group(1)
            item_text = match_num.group(2)
            item_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', item_text)
            item_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', item_text)
            item_text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', item_text)
            story.append(Paragraph(f"<b>{num}.</b> {item_text}", bullet_style))
            i += 1
            continue

        # Regular Body Paragraph
        p_text = stripped
        p_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', p_text)
        p_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', p_text)
        p_text = re.sub(r'`(.*?)`', r'<font name="Courier">\1</font>', p_text)
        story.append(Paragraph(p_text, body_style))
        i += 1

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated PDF: {pdf_path}")

if __name__ == "__main__":
    md_file = os.path.join(os.path.dirname(__file__), "TECHNICAL_DESIGN_DOCUMENT.md")
    pdf_file = os.path.join(os.path.dirname(__file__), "TECHNICAL_DESIGN_DOCUMENT.pdf")
    build_pdf(md_file, pdf_file)
