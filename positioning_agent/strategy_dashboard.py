"""Reusable five-stage research presentation for a saved general project.

Shows facts from the current project's STEP 06-2 JSON and optional AI-generated
STEP 07 draft. Never falls back to the demonstration project's data.
"""
import json
from pathlib import Path


def _read(path):
    try:
        val = json.loads(Path(path).read_text(encoding="utf-8"))
        return val if isinstance(val, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}


def _show_value(st, value):
    if isinstance(value, dict):
        for key, part in value.items():
            st.markdown(f"**{key}**")
            _show_value(st, part)
    elif isinstance(value, list):
        for item in value:
            if isinstance(item, (dict, list)):
                _show_value(st, item)
            else:
                st.write("•", item)
    else:
        st.write(value if value not in (None, "") else "정보 없음 · 추가 검증 필요")


def _ordered_chart(st, rows, name_key, count_key):
    if not rows:
        return
    try:
        import altair as alt
        order = [row[name_key] for row in rows]
        chart = (alt.Chart(alt.Data(values=rows))
                 .mark_bar(size=23, color="#80C4F6")
                 .encode(y=alt.Y(f"{name_key}:N", sort=order, title=None,
                                 axis=alt.Axis(labelAngle=0)),
                         x=alt.X(f"{count_key}:Q", title="댓글 수"),
                         tooltip=[alt.Tooltip(f"{name_key}:N"), alt.Tooltip(f"{count_key}:Q")])
                 .properties(height=max(190, 39 * len(rows))))
        st.altair_chart(chart, use_container_width=True)
    except (ValueError, TypeError, KeyError, ImportError):
        st.caption("그래프를 표시할 수 없어 집계표를 대신 보여줍니다.")
    st.dataframe(rows, use_container_width=True, hide_index=True)


def render_positioning_strategy_dashboard(package_path):
    """Show a five-stage report modeled after Sample Analysis STEP 07."""
    import streamlit as st

    package_path = Path(package_path)
    if not package_path.is_file():
        st.info("아직 생성된 포지셔닝 전략이 없습니다.")
        return
    package = _read(package_path)
    strategy = package.get("strategy", {})
    if not isinstance(strategy, dict):
        st.error("저장된 전략 데이터가 올바르지 않습니다.")
        return

    root = package_path.parent.parent
    ai = _read(root / "youtube_analysis" / "consumer_ai_analysis.json")
    product = _read(root / "product_info.json")
    count = ai.get("record_count", 0)
    try:
        count = max(0, int(count))
    except (TypeError, ValueError):
        count = 0

    st.caption("현재 프로젝트의 실제 댓글 집계 및 AI 전략 초안 · 추가 검증 필요")
    stages = [
        "07-1 · 시장 니즈 분석",
        "07-2 · 경쟁사·자사 제품 분석",
        "07-3 · Gemini 시장 기회 분석",
        "07-4 · STP 및 포지셔닝",
        "07-5 · 최종 마케팅 전략",
    ]
    stage = st.radio("07단계 세부 분석", stages, horizontal=True,
                     key=f"general_strategy_stage_{root.name}")
    st.subheader(stage)

    if stage.startswith("07-1"):
        st.metric("분석에 활용한 YouTube 댓글", f"{count:,}개")
        needs = ai.get("need_topics", {})
        if not isinstance(needs, dict):
            needs = {}
        rows = [{"니즈 주제": str(k), "언급 댓글 수": v}
                for k, v in needs.items() if isinstance(v, int) and not isinstance(v, bool) and v > 0]
        rows.sort(key=lambda x: (-x["언급 댓글 수"], x["니즈 주제"]))
        if rows:
            st.markdown("#### 소비자 니즈 관련 주요 주제")
            _ordered_chart(st, rows, "니즈 주제", "언급 댓글 수")
        else:
            st.info("06-2에 집계된 니즈 주제가 없어 빈도 분석을 표시할 수 없습니다.")
        sentiments = ai.get("sentiment", {})
        if isinstance(sentiments, dict) and sentiments:
            labels = [("positive", "긍정"), ("neutral", "중립"),
                      ("negative", "부정"), ("mixed", "혼합"), ("not_applicable", "기타")]
            sentiment_rows = [{"감성": label, "댓글 수": sentiments[key]}
                              for key, label in labels if isinstance(sentiments.get(key), int)]
            if sentiment_rows:
                st.markdown("#### 댓글 감성 분포")
                _ordered_chart(st, sentiment_rows, "감성", "댓글 수")
        st.caption("주제는 중복될 수 있으며, 선별된 소수 YouTube 댓글은 시장 전체를 대표하지 않습니다.")

    elif stage.startswith("07-2"):
        st.markdown("#### 자사 제품 정보")
        available = {k: v for k, v in product.items()
                     if k in {"brand", "product_name", "category", "price", "volume",
                              "features", "ingredients", "competitors"} and v not in ("", None, [], {})}
        if available:
            _show_value(st, available)
        else:
            st.info("저장된 제품 입력 정보를 확인할 수 없습니다.")
        st.markdown("#### 3C 관점의 비교 가설")
        _show_value(st, strategy.get("three_c", {}))
        st.warning("경쟁사별 댓글·가격·판매량의 검증된 비교 데이터가 없습니다. "
                   "이 화면의 경쟁사 관련 서술은 분석 가설이며 실제 비교 결과가 아닙니다.")

    elif stage.startswith("07-3"):
        st.markdown("#### 시장 인사이트")
        insights = strategy.get("market_insights", [])
        if isinstance(insights, list) and insights:
            for i, item in enumerate(insights, 1):
                with st.expander(f"인사이트 {i}", expanded=True):
                    _show_value(st, item)
        else:
            st.write(strategy.get("executive_summary", "추가 분석 필요"))
        st.markdown("#### 잠재적 시장 기회")
        opportunities = strategy.get("opportunity_areas", [])
        if isinstance(opportunities, list) and opportunities:
            for i, item in enumerate(opportunities, 1):
                with st.expander(f"기회 {i}", expanded=True):
                    _show_value(st, item)
        else:
            _show_value(st, strategy.get("swot", {}).get("opportunities", "추가 검증 필요"))
        st.markdown("#### 위험 및 한계")
        risks = strategy.get("strategic_risks", [])
        _show_value(st, risks if risks else strategy.get("swot", {}).get("threats", "추가 검증 필요"))
        st.caption("시장 기회는 Gemini가 제안한 검증 전 가설이며 확정된 수요를 의미하지 않습니다.")

    elif stage.startswith("07-4"):
        stp = strategy.get("stp", {})
        st.markdown("#### 1. Segmentation · 시장 세분화")
        _show_value(st, stp.get("segmentation", "추가 검증 필요"))
        st.markdown("#### 2. Targeting · 타깃 선정")
        _show_value(st, stp.get("targeting", "추가 검증 필요"))
        st.markdown("#### 3. Positioning · 포지셔닝 후보")
        hypotheses = strategy.get("positioning_hypotheses", [])
        if isinstance(hypotheses, list) and hypotheses:
            for i, item in enumerate(hypotheses, 1):
                with st.expander(f"포지셔닝 후보 {i}", expanded=True):
                    _show_value(st, item)
        else:
            _show_value(st, stp.get("positioning", "추가 검증 필요"))
        st.caption("STP의 세그먼트와 타깃은 실제 인구통계 및 구매 데이터로 검증되지 않았습니다.")

    else:
        st.markdown("#### 핵심 포지셔닝 제안")
        st.write(strategy.get("executive_summary", "추가 검증 필요"))
        st.markdown("#### 마케팅 실행 전략 · 4P")
        four_p = strategy.get("four_p", {})
        for field, label in [("product", "Product · 제품"), ("price", "Price · 가격"),
                             ("place", "Place · 유통"), ("promotion", "Promotion · 프로모션")]:
            st.markdown(f"**{label}**")
            _show_value(st, four_p.get(field, "추가 검증 필요"))
        st.markdown("#### 실행 계획 및 KPI")
        actions = strategy.get("action_plan", [])
        if isinstance(actions, list) and actions:
            for i, item in enumerate(actions, 1):
                with st.expander(f"실행 전략 {i}", expanded=True):
                    _show_value(st, item)
        else:
            st.info("기존에 생성한 전략에는 KPI별 실행 계획이 없습니다. 신규 전략 생성 시 포함됩니다.")
        items = package.get("validation", {}).get("review_items", [])
        if items:
            st.markdown("#### 추가 검토 항목")
            st.dataframe(items, use_container_width=True, hide_index=True)
        st.caption("제시한 KPI와 실행 전략은 제안이며, 실제 성과를 예측·보장하지 않습니다.")
