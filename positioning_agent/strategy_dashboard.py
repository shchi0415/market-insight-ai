"""Readable, evidence-aware STEP 07 report for ordinary projects.

Only reads data saved for this project; never shows sample research for ordinary projects.
"""
import json
from pathlib import Path

LABELS = {
    'need':'소비자 니즈','evidence':'분석 근거','interpretation':'해석','limitations':'분석 한계',
    'own_product_summary':'자사 제품 정보','competitive_context':'경쟁 환경',
    'comparison_limitations':'비교 분석 한계','data_to_collect':'추가로 수집할 데이터',
    'insight':'핵심 인사이트','opportunity_name':'시장 기회','consumer_need':'관련 소비자 니즈',
    'supporting_evidence':'분석 근거','validation_needed':'추가 검증 사항',
    'risk':'위험 요인','reason':'발생 가능 이유',
    'segment_name':'세분시장','needs':'주요 니즈',
    'primary_target':'우선 타깃 가설','rationale':'선정 이유','counterarguments':'반대 근거·한계',
    'candidate_name':'포지셔닝 후보','statement':'포지셔닝 문장','benefits':'기대 가치',
    'evidence_level':'근거 수준','weaknesses':'한계','validation_plan':'검증 계획',
    'selected_candidate':'선택한 후보','message':'메시지 후보','intended_audience':'대상 고객',
    'claim_risk':'광고 표현 유의점','action':'실행 과제','objective':'목표',
    'execution_steps':'실행 단계','kpi':'KPI','measurement_method':'측정 방법',
    'evidence_basis':'근거 수준',
}

def _read(path):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8'))
        return value if isinstance(value, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _value(st, value):
    if value is None or value == '' or value == [] or value == {}:
        st.write('-')
    elif isinstance(value, list):
        for element in value:
            if isinstance(element, dict):
                _detail(st, element)
            elif element not in (None, ''):
                st.markdown(f'- {str(element)}')
    elif isinstance(value, dict):
        _detail(st, value)
    else:
        st.write(value)


def _detail(st, item, *, omit=()):
    if not isinstance(item, dict):
        _value(st, item)
        return
    for key, val in item.items():
        if key in omit or key == 'strategy_mode':
            continue
        st.markdown(f'**{LABELS.get(key, key.replace("_", " "))}**')
        _value(st, val)


def _cards(st, items, *, title_key, default_label):
    if not isinstance(items, list) or not items:
        st.write('-')
        return
    for number, item in enumerate(items, 1):
        if isinstance(item, dict):
            title = str(item.get(title_key) or f'{default_label} {number}')
            with st.container(border=True):
                st.markdown(f'**{number:02d} · {title}**')
                _detail(st, item, omit=(title_key,))
        else:
            with st.container(border=True):
                st.markdown(f'**{number:02d} · {default_label}**')
                _value(st, item)


def _ordered_chart(st, rows, name_key, count_key):
    if not rows:
        st.write('-')
        return
    try:
        import altair as alt
        order = [str(row[name_key]) for row in rows]
        chart = (alt.Chart(alt.Data(values=rows))
                 .mark_bar(size=23, color='#80C4F6')
                 .encode(y=alt.Y(f'{name_key}:N', sort=order, title=None,
                                 axis=alt.Axis(labelAngle=0)),
                         x=alt.X(f'{count_key}:Q', title='댓글 수'),
                         tooltip=[alt.Tooltip(f'{name_key}:N'), alt.Tooltip(f'{count_key}:Q')])
                 .properties(height=max(190, len(rows) * 39)))
        st.altair_chart(chart, use_container_width=True)
    except (ValueError, TypeError, KeyError, ImportError):
        st.caption('그래프를 표시할 수 없어 집계표만 표시합니다.')
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_positioning_strategy_dashboard(package_path):
    import streamlit as st
    package_path = Path(package_path)
    if not package_path.is_file():
        st.info('아직 생성된 포지셔닝 전략이 없습니다.')
        return
    package = _read(package_path)
    strategy = package.get('strategy', {})
    if not isinstance(strategy, dict):
        st.error('저장된 전략 데이터가 올바르지 않습니다.')
        return

    project_dir = package_path.parent.parent
    ai = _read(project_dir / 'youtube_analysis' / 'consumer_ai_analysis.json')
    count = ai.get('record_count', 0)
    try:
        count = max(0, int(count))
    except (TypeError, ValueError):
        count = 0

    st.caption('현재 프로젝트의 수집 데이터 기반 탐색적 분석 · 전략 제안은 검증 전 가설입니다.')
    stages = [
        '07-1 · 시장 니즈 분석', '07-2 · 경쟁사·자사 제품 분석',
        '07-3 · Gemini 시장 기회 분석', '07-4 · STP 및 포지셔닝',
        '07-5 · 최종 마케팅 전략',
    ]
    stage = st.radio('07단계 세부 분석', stages, horizontal=True,
                     key=f'general_strategy_stage_{project_dir.name}')
    st.subheader(stage)

    if package.get('strategy_version') != 2:
        st.info('이전에 저장한 분석 결과입니다. 새로운 분석 결과를 생성하면 표시할 수 있습니다.')
        return

    if stage.startswith('07-1'):
        st.metric('분석에 활용한 YouTube 댓글', f'{count:,}개')
        needs = ai.get('need_topics', {})
        if isinstance(needs, dict):
            rows = [{'니즈 주제': str(k), '언급 댓글 수': v}
                    for k, v in needs.items()
                    if isinstance(v, int) and not isinstance(v, bool) and v > 0]
            rows.sort(key=lambda row: -row['언급 댓글 수'])
            st.markdown('#### 주제별 언급 현황')
            _ordered_chart(st, rows, '니즈 주제', '언급 댓글 수')
        st.markdown('#### 주요 니즈와 해석')
        _cards(st, strategy.get('consumer_needs_interpretation'),
               title_key='need', default_label='소비자 니즈')
        st.caption('주제는 중복 집계될 수 있으며 시장 전체의 수요 비율을 의미하지 않습니다.')

    elif stage.startswith('07-2'):
        details = strategy.get('product_competitor_analysis', {})
        details = details if isinstance(details, dict) else {}
        st.markdown('#### 자사 제품')
        with st.container(border=True):
            st.markdown('**자사 제품 정보 및 관찰 사항**')
            _value(st, details.get('own_product_summary'))
        st.markdown('#### 경쟁사 분석')
        # STEP 01의 경쟁사 이름은 경쟁사별 실제 분석 데이터가 아닙니다.
        # 현행 STEP 06-2에는 경쟁사별 실측 집계가 없으므로 생성된 비교 문구도 표시하지 않습니다.
        with st.container(border=True):
            st.markdown('**경쟁사별 소비자 반응 비교**')
            st.write('-')
            st.markdown('**경쟁사 대비 우위·열위**')
            st.write('-')
            st.markdown('**경쟁사별 검증된 지표**')
            st.write('-')
        st.caption('경쟁사별 댓글·가격·성과 데이터가 분석에 포함되지 않아 비교 결과를 표시하지 않습니다.')
        st.markdown('#### 추가로 필요한 데이터')
        with st.container(border=True):
            _value(st, details.get('data_to_collect'))

    elif stage.startswith('07-3'):
        st.markdown('#### 시장 인사이트')
        _cards(st, strategy.get('market_insights'), title_key='insight', default_label='시장 인사이트')
        st.markdown('#### 잠재적 시장 기회')
        _cards(st, strategy.get('opportunity_areas'), title_key='opportunity_name', default_label='시장 기회')
        st.markdown('#### 전략적 위험')
        _cards(st, strategy.get('strategic_risks'), title_key='risk', default_label='위험 요인')

    elif stage.startswith('07-4'):
        st.markdown('#### 1. Segmentation · 시장 세분화')
        _cards(st, strategy.get('segmentation'), title_key='segment_name', default_label='세분시장')
        st.markdown('#### 2. Targeting · 우선 검증 타깃')
        with st.container(border=True):
            _detail(st, strategy.get('targeting', {}))
        st.markdown('#### 3. Positioning · 포지셔닝 후보 비교')
        _cards(st, strategy.get('positioning_candidates'), title_key='candidate_name', default_label='포지셔닝 후보')
        st.markdown('#### 최종 포지셔닝 가설')
        with st.container(border=True):
            _detail(st, strategy.get('final_positioning', {}))

    else:
        st.markdown('#### 포지셔닝 전략')
        with st.container(border=True):
            _detail(st, strategy.get('final_positioning', {}))
        st.markdown('#### 마케팅 메시지 후보')
        _cards(st, strategy.get('message_candidates'), title_key='message', default_label='마케팅 메시지')
        st.markdown('#### 실행 계획 및 KPI')
        _cards(st, strategy.get('action_plan'), title_key='action', default_label='실행 과제')
        st.caption('실행 방안과 KPI는 검증 전 제안이며 실측된 성과가 아닙니다.')
