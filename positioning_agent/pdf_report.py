"""PDF report assembled exclusively from previously saved STEP 07 results. No API calls."""
import io
import json
from pathlib import Path
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from datetime import date
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether, HRFlowable, PageBreak, Table, TableStyle

# Korean CID fonts are built into ReportLab. No external font file needed.
pdfmetrics.registerFont(UnicodeCIDFont('HYGothic-Medium'))
FONT = 'HYGothic-Medium'
HEADINGS = [
    ('07-1 · 시장 니즈 분석', 'consumer_needs_interpretation'),
    ('07-2 · 경쟁사·자사 제품 분석', 'product_competitor_analysis'),
    ('07-3 · Gemini 시장 기회 분석', None),
    ('07-4 · STP 및 포지셔닝', None),
    ('07-5 · 최종 마케팅 전략', None),
]
LABELS = {
    'need':'소비자 니즈', 'evidence':'근거', 'interpretation':'해석', 'limitations':'분석 한계',
    'own_product_summary':'자사 제품 분석', 'competitive_context':'경쟁 환경',
    'comparison_limitations':'비교 분석 한계', 'data_to_collect':'추가 필요 데이터',
    'insight':'핵심 인사이트', 'opportunity_name':'시장 기회', 'consumer_need':'관련 소비자 니즈',
    'supporting_evidence':'분석 근거', 'validation_needed':'추가 검증 사항',
    'risk':'위험 요인', 'reason':'근거', 'segment_name':'시장 세분화',
    'needs':'주요 니즈', 'targeting':'타깃 선정', 'primary_target':'우선 타깃',
    'rationale':'선정 근거', 'counterarguments':'반론과 한계',
    'candidate_name':'포지셔닝 후보', 'final_positioning':'최종 포지셔닝',
    'message':'마케팅 메시지', 'action':'실행 과제', 'objective':'목표',
    'execution_steps':'실행 방법', 'kpi':'KPI', 'measurement_method':'측정 방법',
    'evidence_basis':'근거 수준', 'executive_summary':'종합 요약',
}

def _load(path):
    p = Path(path)
    if not p.is_file():
        return {}
    try:
        d = json.loads(p.read_text(encoding='utf-8'))
        return d if isinstance(d, dict) else {}
    except (ValueError, OSError):
        return {}

def _txt(x):
    return escape(str(x)).replace('\n', '<br/>')

def _styles():
    return {
        'title': ParagraphStyle('KTitle', fontName=FONT, fontSize=19, leading=27, textColor=colors.HexColor('#13243B'), spaceAfter=13),
        'h1': ParagraphStyle('KH1', fontName=FONT, fontSize=13, leading=20, textColor=colors.HexColor('#16385A'), spaceBefore=17, spaceAfter=9, keepWithNext=True),
        'h2': ParagraphStyle('KH2', fontName=FONT, fontSize=10, leading=16, textColor=colors.HexColor('#24598C'), spaceBefore=10, spaceAfter=5, keepWithNext=True),
        'body': ParagraphStyle('KBody', fontName=FONT, fontSize=9, leading=15, spaceAfter=6, wordWrap='CJK'),
        'eyebrow': ParagraphStyle('KEyebrow', fontName=FONT, fontSize=10, leading=14, textColor=colors.HexColor('#3573B1'), spaceAfter=12),
        'cover': ParagraphStyle('KCover', fontName=FONT, fontSize=26, leading=39, textColor=colors.HexColor('#142A46'), spaceAfter=12),
        'cover_product': ParagraphStyle('KCoverProduct', fontName=FONT, fontSize=17, leading=26, textColor=colors.HexColor('#36516F')),
        'summary_label': ParagraphStyle('KSummaryLabel', fontName=FONT, fontSize=9, leading=15, textColor=colors.HexColor('#2D659A'), wordWrap='CJK'),
        'summary_value': ParagraphStyle('KSummaryValue', fontName=FONT, fontSize=9, leading=15, wordWrap='CJK'),
        'small': ParagraphStyle('KSmall', fontName=FONT, fontSize=8, leading=12, wordWrap='CJK'),
        'note': ParagraphStyle('KNote', fontName=FONT, fontSize=8.5, leading=14, textColor=colors.HexColor('#85572D'), spaceAfter=8, wordWrap='CJK'),
    }

def _append_value(story, val, styles, depth=0):
    if depth > 7:
        return
    if val is None or val == '' or val == [] or val == {}:
        story.append(Paragraph('-', styles['body']))
    elif isinstance(val, dict):
        for k, v in val.items():
            if k in ('strategy_mode', 'model', 'project_id'):
                continue
            story.append(Paragraph(_txt(LABELS.get(k, k.replace('_', ' '))), styles['h2']))
            _append_value(story, v, styles, depth + 1)
    elif isinstance(val, list):
        for i, item in enumerate(val, 1):
            if isinstance(item, dict):
                story.append(Paragraph(f'{i:02d}', styles['h2']))
                _append_value(story, item, styles, depth + 1)
            else:
                story.append(Paragraph('• ' + _txt(item), styles['body']))
    else:
        story.append(Paragraph(_txt(val), styles['body']))

def _single_line(value, length=230):
    text = ' '.join(str(value or '').split()).strip()
    return (text[:length - 1] + '…') if len(text) > length else (text or '-')


def _pick_summary(sections, demo):
    """Grounded, extractive statements only: never invent findings."""
    lookup = {name.split(' · ', 1)[0]: item for name, item in sections}
    needs = lookup.get('07-1', {})
    opportunity = lookup.get('07-3', {})
    targeting = lookup.get('07-4', {})
    marketing = lookup.get('07-5', {})
    items = []
    if demo:
        counts = needs.get('주제별 언급 수', {}) if isinstance(needs, dict) else {}
        if isinstance(counts, dict) and counts:
            name, n = max(counts.items(), key=lambda pair: float(pair[1]) if str(pair[1]).replace('.','',1).isdigit() else 0)
            items.append(('주요 시장 니즈', f'{name}: {n}건 언급'))
        observations = opportunity.get('market_insights', []) if isinstance(opportunity, dict) else []
        if observations and isinstance(observations[0], dict):
            items.append(('핵심 시장 인사이트', observations[0].get('insight', '-')))
        tar = targeting.get('targeting', {}) if isinstance(targeting, dict) else {}
        if isinstance(tar, dict):
            items.append(('우선 검증 타깃', tar.get('primary_target', '-')))
        if isinstance(marketing, dict):
            pos = marketing.get('positioning', {})
            if isinstance(pos, dict):
                items.append(('포지셔닝 가설', pos.get('statement', '-')))
    else:
        vals = needs.get('주요 니즈 및 해석', []) if isinstance(needs, dict) else []
        if vals and isinstance(vals[0], dict):
            items.append(('주요 소비자 니즈', vals[0].get('need', '-')))
        rows = opportunity.get('시장 인사이트', []) if isinstance(opportunity, dict) else []
        if rows and isinstance(rows[0], dict):
            items.append(('핵심 시장 인사이트', rows[0].get('insight', '-')))
        tar = targeting.get('타깃 선정', {}) if isinstance(targeting, dict) else {}
        if isinstance(tar, dict):
            items.append(('우선 검증 타깃', tar.get('primary_target', '-')))
        pos = targeting.get('최종 포지셔닝', {}) if isinstance(targeting, dict) else {}
        if isinstance(pos, dict):
            items.append(('포지셔닝 가설', pos.get('statement', '-')))
    return [(k, _single_line(v)) for k, v in items if v not in ('', None, '-')]


def _number(value):
    try:
        n = int(value)
        return max(0, n)
    except (TypeError, ValueError):
        return 0


def _bar_chart(rows, styles, title, max_rows=None):
    """ReportLab native vector bar chart, ordered exactly as supplied."""
    rows = [(str(k), _number(v)) for k, v in rows if _number(v) > 0]
    if max_rows is not None:
        rows = rows[:max_rows]
    if not rows:
        return []
    left_w, bar_w, right_w = 84, 340, 34
    row_h = 24
    height = 18 + row_h * len(rows)
    draw = Drawing(left_w + bar_w + right_w, height)
    maxval = max(n for _, n in rows)
    for i, (label, n) in enumerate(rows):
        y = height - 26 - i * row_h
        draw.add(String(0, y + 3, _single_line(label, 13), fontName=FONT,
                        fontSize=8, fillColor=colors.HexColor('#263954')))
        draw.add(Rect(left_w, y, bar_w, 11, fillColor=colors.HexColor('#EDF1F7'), strokeColor=None))
        draw.add(Rect(left_w, y, max(2, bar_w * n/maxval), 11,
                      fillColor=colors.HexColor('#4289CD'), strokeColor=None))
        draw.add(String(left_w + bar_w + 8, y + 2, str(n), fontName=FONT,
                        fontSize=8, fillColor=colors.HexColor('#263954')))
    # A ReportLab Drawing cannot split across pages.  Divide long charts into
    # page-safe chunks so a chart with many categories never exceeds the frame.
    out = []
    max_rows_per_chart = 11
    if len(rows) <= max_rows_per_chart:
        out.extend([Paragraph(_txt(title), styles['h2']), draw, Spacer(1, 5)])
    else:
        for start in range(0, len(rows), max_rows_per_chart):
            chunk = rows[start:start + max_rows_per_chart]
            chunk_height = 18 + row_h * len(chunk)
            chunk_draw = Drawing(left_w + bar_w + right_w, chunk_height)
            for j, (label, n) in enumerate(chunk):
                y = chunk_height - 26 - j * row_h
                chunk_draw.add(String(0, y + 3, _single_line(label, 13),
                                      fontName=FONT, fontSize=8,
                                      fillColor=colors.HexColor('#263954')))
                chunk_draw.add(Rect(left_w, y, bar_w, 11,
                                    fillColor=colors.HexColor('#EDF1F7'), strokeColor=None))
                chunk_draw.add(Rect(left_w, y, max(2, bar_w * n / maxval), 11,
                                    fillColor=colors.HexColor('#4289CD'), strokeColor=None))
                chunk_draw.add(String(left_w + bar_w + 8, y + 2, str(n),
                                      fontName=FONT, fontSize=8,
                                      fillColor=colors.HexColor('#263954')))
            chunk_title = title if start == 0 else f'{title} (계속)'
            out.extend([Paragraph(_txt(chunk_title), styles['h2']),
                        chunk_draw, Spacer(1, 5)])
    data = [[Paragraph('항목', styles['small']), Paragraph('댓글 수', styles['small'])]]
    data.extend([[Paragraph(_txt(k), styles['small']), Paragraph(str(v), styles['small'])] for k,v in rows])
    tab = Table(data, colWidths=[360, 99], hAlign='LEFT', repeatRows=1)
    tab.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#E9F0F9')),
        ('BOTTOMPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),
        ('LINEBELOW',(0,0),(-1,-1),0.2,colors.HexColor('#D8E1EC')),
    ]))
    out.append(tab)
    return out


def _create_pdf(title, sections, count=None, notes=(), charts=None, demo=False):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=(210*mm, 297*mm), topMargin=19*mm,
                            bottomMargin=17*mm, leftMargin=19*mm, rightMargin=19*mm,
                            title=title, author='AI Positioning Agent')
    sty = _styles()
    navy = colors.HexColor('#142A46')
    date_str = date.today().strftime('%Y.%m.%d')

    # 01 · Cover — a dedicated page
    story = [Spacer(1, 36*mm),
             Paragraph('AI POSITIONING AGENT', sty['eyebrow']),
             Spacer(1, 8*mm),
             Paragraph('시장조사 및<br/>제품 포지셔닝 보고서', sty['cover']),
             Spacer(1, 9*mm),
             Paragraph(_txt(title.replace(' · 시장조사 보고서','')), sty['cover_product']),
             Spacer(1, 8*mm),
             HRFlowable(width='100%', thickness=2.3, color=navy),
             Spacer(1, 8*mm),
             Paragraph('분석 형식: ' + ('사전 저장된 예시 데이터' if demo else '일반 프로젝트 · 실제 수집 데이터'), sty['body']),
             Paragraph('보고서 생성일: ' + date_str, sty['body'])]
    if count is not None:
        story.append(Paragraph(f'AI 분석 댓글: {count:,}개', sty['body']))
    story.extend([Spacer(1, 16*mm), Paragraph('이 보고서는 저장된 분석 결과를 정리한 탐색적 전략 문서입니다.', sty['note']), PageBreak()])

    # 02 · Executive Summary — a dedicated page
    story.append(Paragraph('EXECUTIVE SUMMARY', sty['eyebrow']))
    story.append(Paragraph('핵심 분석 요약', sty['title']))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#C8D7EA')))
    story.append(Spacer(1, 8*mm))
    for label, val in _pick_summary(sections, demo):
        data = [[Paragraph(_txt(label), sty['summary_label']), Paragraph(_txt(val), sty['summary_value'])]]
        table = Table(data, colWidths=[110, 349], hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#F3F7FC')),
                                   ('VALIGN',(0,0),(-1,-1),'TOP'),
                                   ('LEFTPADDING',(0,0),(-1,-1),10),('RIGHTPADDING',(0,0),(-1,-1),10),
                                   ('TOPPADDING',(0,0),(-1,-1),11),('BOTTOMPADDING',(0,0),(-1,-1),11)]))
        story.append(table)
        story.append(Spacer(1, 6))
    if count is not None and count < 100:
        story.append(Spacer(1, 7*mm))
        story.append(Paragraph('표본 부족 · 전략 신뢰성 유의', sty['h1']))
        story.append(Paragraph(f'AI 분석 댓글 {count:,}개는 시장 전체를 대표하기 어렵습니다. 아래 시장 기회 및 전략은 검증 전 탐색적 가설이므로 추가 데이터와 실험을 통한 검증이 필요합니다.', sty['note']))
    for note in notes:
        story.append(Paragraph(_txt(note), sty['note']))
    story.extend([Spacer(1, 10*mm), Paragraph('분석 범위', sty['h1']),
                  Paragraph('07-1 시장 니즈  |  07-2 경쟁사·자사 제품  |  07-3 시장 기회  |  07-4 STP·포지셔닝  |  07-5 마케팅 전략',sty['body']),
                  PageBreak()])

    # 03 · The report, with charts before data/tables in the applicable section.
    for i, (heading, value) in enumerate(sections):
        if i:
            story.append(Spacer(1, 5*mm))
        story.append(Paragraph(_txt(heading), sty['h1']))
        if i == 0 and charts:
            if charts.get('needs'):
                story.extend(_bar_chart(charts['needs'], sty, '소비자 니즈별 언급 현황'))
            if charts.get('sentiment'):
                story.extend(_bar_chart(charts['sentiment'], sty, '전체 댓글 감성 분포'))
        _append_value(story, value, sty)
    story.append(Spacer(1, 8))
    story.append(Paragraph('본 보고서는 저장된 분석 결과를 자동 편집하였습니다. 데이터의 대표성, 인과관계, 효과 및 실제 성과는 별도로 검증되지 않았습니다.', sty['note']))

    def decorate(canvas, doc):
        canvas.saveState()
        page = doc.page
        if page != 1:
            canvas.setStrokeColor(colors.HexColor('#D8E1EA'))
            canvas.line(19*mm, 285*mm, 191*mm, 285*mm)
            canvas.setFont(FONT, 8)
            canvas.setFillColor(colors.HexColor('#607284'))
            canvas.drawString(19*mm, 11*mm, 'AI Positioning Agent | Market Research')
            canvas.drawRightString(191*mm, 11*mm, str(page))
        canvas.restoreState()
    doc.build(story, onFirstPage=decorate, onLaterPages=decorate)
    return buf.getvalue()

def generate_project_report(project_dir, *, demo=False, demo_assets=None):
    """Return PDF bytes; raise FileNotFoundError if STEP 07 has not been generated."""
    project_dir = Path(project_dir)
    info = _load(project_dir / 'project_info.json')
    title = str(info.get('project_name') or '제품 포지셔닝 분석') + ' · 시장조사 보고서'
    if demo:
        data = Path(demo_assets)
        evidence = _load(data / 'positioning_evidence.json')
        opportunities = _load(data / 'gemini_market_opportunities.json')
        stp = _load(data / 'gemini_stp_strategy.json')
        final = _load(data / 'gemini_final_strategy.json')
        if not opportunities or not stp or not final:
            raise FileNotFoundError('예시 프로젝트 STEP 07 데이터가 부족합니다.')
        # Cover every section shown in the Sample Analysis STEP 07 dashboard.
        # The competitive products and the human STP review are distinct inputs
        # and must not be silently omitted from the full report.
        product_rows = []
        for filename, fallback_name in [
            ('aestura_analysis.json', '에스트라 아토베리어365 크림'),
            ('roundlab_analysis.json', '라운드랩 1025 독도 로션'),
            ('own_consumer_responses.json', '온그리디언츠 바쿠글로우 캡슐 로션'),
        ]:
            item = _load(data / filename)
            if item:
                product_rows.append({
                    '제품': item.get('product_name') or fallback_name,
                    '분석 댓글': item.get('analyzed_comments', item.get('analyzed_comment_count', 0)),
                    '실사용 후기 후보': (
                        1 if filename == 'own_consumer_responses.json'
                        else item.get('review_candidates', 0)
                    ),
                    '원본 분석 세부 내용': item,
                })
            else:
                product_rows.append({'제품': fallback_name, '분석 결과': '-'})
        review = _load(data / 'stp_strategy_review.json')
        sections = [
            ('07-1 · 시장 니즈 분석', {
                '분석 대상 YouTube 댓글': evidence.get('market_comment_count', '-'),
                '시장 니즈별 언급 댓글 수': evidence.get('market_need_counts', {}),
                '분석 관련 추가 정보': {k:v for k,v in evidence.items()
                                  if k not in ('market_comment_count', 'market_need_counts', 'competitor_analysis')},
            }),
            ('07-2 · 경쟁사·자사 제품 분석', {
                '제품별 분석 데이터': product_rows,
                '기존 데이터의 경쟁 환경 분석': evidence.get('competitor_analysis', {}) or '-',
                '주의': '제품별 표본 규모와 영상 구성이 달라 만족도와 제품 성능을 직접 비교할 수 없습니다.',
            }),
            ('07-3 · Gemini 시장 기회 분석', opportunities),
            ('07-4 · STP 및 포지셔닝', {
                '시장 세분화': stp.get('segmentation', []),
                '타깃 선정': stp.get('targeting', {}),
                '포지셔닝 후보 비교': stp.get('positioning_comparison', []),
                '추천 포지셔닝': stp.get('recommended_positioning', {}),
                '마케팅 실행 제안': stp.get('marketing_actions', []),
                '분석 한계': stp.get('analysis_limitations', '-'),
                '전략 검토 및 수정': review or '-',
            }),
            ('07-5 · 최종 마케팅 전략', final),
        ]
        ai_demo = _load(data / 'youtube_comment_ai_demo_summary.json')
        stats = _load(data / 'youtube_comments_demo_summary.json').get('statistics', {})
        count = _number(ai_demo.get('record_count'))
        charts = {
            'needs': list((evidence.get('market_need_counts') or {}).items()),
            'sentiment': [(label, (ai_demo.get('sentiment') or {}).get(key, 0)) for label, key in [('긍정','positive'),('중립','neutral'),('부정','negative'),('혼합','mixed'),('기타','not_applicable')]],
        }
        return _create_pdf(title, sections, count=count, charts=charts, demo=True, notes=('사전 저장된 예시 분석 · 추가 API 호출 없음',))

    package = _load(project_dir / 'positioning_strategy' / 'strategy_package_v2.json')
    if package.get('strategy_version') != 2 or not isinstance(package.get('strategy'), dict):
        raise FileNotFoundError('STEP 07 신규 분석 결과가 없습니다.')
    s = package['strategy']
    ai = _load(project_dir / 'youtube_analysis' / 'consumer_ai_analysis.json')
    try:
        count = max(0, int(ai.get('record_count', 0)))
    except (TypeError, ValueError):
        count = 0
    comp = dict(s.get('product_competitor_analysis') or {})
    # Do not present unverified competitor comparisons as actual research.
    comp.pop('competitive_context', None)
    comp['경쟁사별 소비자 반응 비교'] = '-'
    comp['경쟁사 대비 우위·열위'] = '-'
    comp['경쟁사별 검증된 지표'] = '-'
    sections = [
        ('07-1 · 시장 니즈 분석', {'주제별 언급 현황': ai.get('need_topics', {}), '주요 니즈 및 해석':s.get('consumer_needs_interpretation', [])}),
        ('07-2 · 경쟁사·자사 제품 분석', comp),
        ('07-3 · Gemini 시장 기회 분석', {'시장 인사이트':s.get('market_insights', []), '잠재적 시장 기회':s.get('opportunity_areas', []), '전략적 위험':s.get('strategic_risks', [])}),
        ('07-4 · STP 및 포지셔닝', {'시장 세분화':s.get('segmentation', []), '타깃 선정':s.get('targeting', {}), '포지셔닝 후보':s.get('positioning_candidates', []), '최종 포지셔닝':s.get('final_positioning', {})}),
        ('07-5 · 최종 마케팅 전략', {'최종 포지셔닝':s.get('final_positioning', {}), '마케팅 메시지':s.get('message_candidates', []), '실행 계획 및 KPI':s.get('action_plan', [])}),
    ]
    counts = ai.get('need_topics', {})
    if isinstance(counts, list):
        counts = {str(x.get('topic', x.get('label', '-'))): x.get('count', 0) for x in counts if isinstance(x, dict)}
    if not isinstance(counts, dict):
        counts = {}
    sentiment = ai.get('sentiment', {})
    if not isinstance(sentiment, dict):
        sentiment = {}
    charts = {'needs': sorted(counts.items(), key=lambda kv: -_number(kv[1])),
              'sentiment': [(label, sentiment.get(key, 0)) for label, key in [('긍정','positive'),('중립','neutral'),('부정','negative'),('혼합','mixed'),('기타','not_applicable')]]}
    return _create_pdf(title, sections, count=count, charts=charts,
                       notes=('YouTube 댓글 기반 탐색적 분석입니다. 경쟁사 실측 데이터가 없으면 비교 항목을 공란으로 표시합니다.',))
