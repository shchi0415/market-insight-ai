
from pathlib import Path
from xml.sax.saxutils import escape
import re
import shutil

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    PageBreak, HRFlowable
)
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def register_report_fonts(font_dir=None):
    """ReportLab 내장 한글 CID 폰트를 사용합니다."""
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont

    if "HYSMyeongJo-Medium" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(
            UnicodeCIDFont("HYSMyeongJo-Medium")
        )

def generate_pdf_report(
    project_dir,
    font_dir=None
):
    project_dir = Path(project_dir)
    strategy_dir = project_dir / "marketing_strategy"

    md_path = strategy_dir / "market_strategy_report_v2.md"
    pdf_path = strategy_dir / "market_strategy_report_v2.pdf"

    if not md_path.is_file():
        raise FileNotFoundError(
            f"Markdown 보고서가 없습니다: {md_path}"
        )

    if font_dir is None:
        font_dir = Path(__file__).resolve().parent / "fonts"
    register_report_fonts(font_dir)

    NAVY = colors.HexColor("#172B4D")
    BLUE = colors.HexColor("#3266A8")
    GRAY = colors.HexColor("#596579")
    LIGHT = colors.HexColor("#E6EBF1")

    styles = {
        "cover_title": ParagraphStyle(
            "CoverTitle",
            fontName="HYSMyeongJo-Medium",
            fontSize=25,
            leading=39,
            textColor=NAVY,
            alignment=TA_CENTER,
            wordWrap="CJK"
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            fontName="HYSMyeongJo-Medium",
            fontSize=12,
            leading=21,
            textColor=GRAY,
            alignment=TA_CENTER,
            wordWrap="CJK"
        ),
        "cover_note": ParagraphStyle(
            "CoverNote",
            fontName="HYSMyeongJo-Medium",
            fontSize=8,
            leading=14,
            textColor=GRAY,
            alignment=TA_CENTER,
            wordWrap="CJK"
        ),
        "heading1": ParagraphStyle(
            "ReportHeading1",
            fontName="HYSMyeongJo-Medium",
            fontSize=15,
            leading=23,
            textColor=NAVY,
            spaceBefore=20,
            spaceAfter=11,
            keepWithNext=True,
            wordWrap="CJK"
        ),
        "heading2": ParagraphStyle(
            "ReportHeading2",
            fontName="HYSMyeongJo-Medium",
            fontSize=11,
            leading=18,
            textColor=BLUE,
            spaceBefore=14,
            spaceAfter=7,
            keepWithNext=True,
            wordWrap="CJK"
        ),
        "body": ParagraphStyle(
            "ReportBody",
            fontName="HYSMyeongJo-Medium",
            fontSize=9,
            leading=16,
            textColor=NAVY,
            spaceAfter=7,
            wordWrap="CJK"
        ),
        "bullet": ParagraphStyle(
            "ReportBullet",
            fontName="HYSMyeongJo-Medium",
            fontSize=9,
            leading=16,
            leftIndent=13,
            firstLineIndent=-9,
            textColor=NAVY,
            spaceAfter=6,
            wordWrap="CJK"
        ),
        "note": ParagraphStyle(
            "ReportNote",
            fontName="HYSMyeongJo-Medium",
            fontSize=8,
            leading=14,
            textColor=GRAY,
            leftIndent=10,
            spaceAfter=8,
            wordWrap="CJK"
        )
    }

    def format_inline(value):
        value = escape(str(value))

        return re.sub(
            r"\*\*(.+?)\*\*",
            r"<b>\1</b>",
            value
        )

    def add_footer(canvas, doc):
        canvas.saveState()

        width, height = A4

        canvas.setStrokeColor(LIGHT)
        canvas.line(
            19 * mm, 19 * mm,
            width - 19 * mm, 19 * mm
        )

        canvas.setFont("HYSMyeongJo-Medium", 8)
        canvas.setFillColor(GRAY)

        canvas.drawString(
            19 * mm, 13 * mm,
            "AI Market Insight - Strategy Report"
        )

        canvas.drawRightString(
            width - 19 * mm, 13 * mm,
            str(doc.page)
        )

        canvas.restoreState()

    story = []

    # 표지
    story.append(Spacer(1, 58 * mm))

    story.append(Paragraph(
        "AI 기반<br/>시장 진입 전략 보고서",
        styles["cover_title"]
    ))

    story.append(Spacer(1, 10 * mm))

    story.append(HRFlowable(
        width="45%",
        thickness=2,
        color=BLUE,
        hAlign="CENTER"
    ))

    story.append(Spacer(1, 12 * mm))

    story.append(Paragraph(
        "Market Intelligence &amp; Consumer Insights",
        styles["cover_subtitle"]
    ))

    story.append(Spacer(1, 7 * mm))

    story.append(Paragraph(
        "Instagram 데이터 기반 시장 기회 탐색 및 전략 가설",
        styles["cover_subtitle"]
    ))

    story.append(Spacer(1, 22 * mm))

    story.append(Paragraph(
        f"Project ID: {escape(project_dir.name)}",
        styles["cover_subtitle"]
    ))

    story.append(Spacer(1, 28 * mm))

    story.append(Paragraph(
        "본 보고서는 AI 분석 및 제한된 소셜미디어 표본에 기반한 "
        "초기 전략 제안서입니다.",
        styles["cover_note"]
    ))

    story.append(PageBreak())

    # Markdown 본문 변환
    markdown = md_path.read_text(encoding="utf-8")

    for raw_line in markdown.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("# "):
            continue

        if line.startswith("## "):
            story.append(Paragraph(
                format_inline(line[3:]),
                styles["heading1"]
            ))

        elif line.startswith("### "):
            story.append(Paragraph(
                format_inline(line[4:]),
                styles["heading2"]
            ))

        elif line.startswith("- "):
            story.append(Paragraph(
                "• " + format_inline(line[2:]),
                styles["bullet"]
            ))

        elif line.startswith("> "):
            story.append(Paragraph(
                format_inline(line[2:]),
                styles["note"]
            ))

        elif line == "---":
            story.append(HRFlowable(
                width="100%",
                thickness=0.5,
                color=LIGHT,
                spaceBefore=8,
                spaceAfter=12
            ))

        else:
            story.append(Paragraph(
                format_inline(line),
                styles["body"]
            ))

    # 새 PDF를 먼저 임시 파일에 생성
    temp_path = strategy_dir / "market_strategy_report_v2_temp.pdf"

    doc = SimpleDocTemplate(
        str(temp_path),
        pagesize=A4,
        rightMargin=21 * mm,
        leftMargin=21 * mm,
        topMargin=24 * mm,
        bottomMargin=25 * mm,
        title="AI 기반 시장 진입 전략 보고서",
        author="Market Insight AI"
    )

    try:
        doc.build(
            story,
            onFirstPage=add_footer,
            onLaterPages=add_footer
        )

        if not temp_path.is_file():
            raise RuntimeError("PDF 생성에 실패했습니다.")

        if pdf_path.exists():
            shutil.copy2(
                pdf_path,
                strategy_dir / "market_strategy_report_v2_backup.pdf"
            )

        temp_path.replace(pdf_path)

    finally:
        if temp_path.exists():
            temp_path.unlink()

    return pdf_path
