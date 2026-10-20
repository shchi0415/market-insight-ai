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

    if package.get("strategy_version") != 2:
        st.warning("이 결과는 구형 3C·SWOT·4P 분석입니다. 새 분석 실행으로 교체할 수 있습니다.")
        return

    if stage.startswith("07-1"):
        st.metric("분석에 활용한 YouTube 댓글", f"{count:,}개")
        needs = ai.get("need_topics", {})
        if isinstance(needs, dict):
            rows = [{"니즈 주제": str(k), "언급 댓글 수": v}
                    for k, v in needs.items() if isinstance(v, int) and v > 0]
            rows.sort(key=lambda r: -r["언급 댓글 수"])
            if rows:
                _ordered_chart(st, rows, "니즈 주제", "언급 댓글 수")
        st.markdown("#### 주요 니즈 해석")
        _show_value(st, strategy.get("consumer_needs_interpretation", []))
        st.caption("주제는 중복 집계 가능하며 시장 전체의 수요 비율이 아닙니다.")

    elif stage.startswith("07-2"):
        st.markdown("#### 자사 제품 및 경쟁 환경")
        _show_value(st, strategy.get("product_competitor_analysis", {}))
        st.warning("경쟁사별 수집·분류 데이터가 없어 직접적인 제품별 우열이나 만족도 비교는 불가능합니다.")

    elif stage.startswith("07-3"):
        st.markdown("#### 시장 인사이트")
        for i, item in enumerate(strategy.get("market_insights", []), 1):
            with st.expander(f"인사이트 {i}", expanded=True):
                _show_value(st, item)
        st.markdown("#### 잠재적 시장 기회")
        for i, item in enumerate(strategy.get("opportunity_areas", []), 1):
            with st.expander(item.get("opportunity_name", f"기회 {i}"), expanded=True):
                _show_value(st, item)
        st.markdown("#### 전략적 위험")
        _show_value(st, strategy.get("strategic_risks", []))

    elif stage.startswith("07-4"):
        st.markdown("#### 1. Segmentation · 시장 세분화")
        _show_value(st, strategy.get("segmentation", []))
        st.markdown("#### 2. Targeting · 우선 검증 타깃")
        _show_value(st, strategy.get("targeting", {}))
        st.markdown("#### 3. Positioning · 포지셔닝 후보 비교")
        for i, item in enumerate(strategy.get("positioning_candidates", []), 1):
            with st.expander(item.get("candidate_name", f"후보 {i}"), expanded=True):
                _show_value(st, item)
        st.markdown("#### 최종 포지셔닝 가설")
        _show_value(st, strategy.get("final_positioning", {}))

    else:
        st.markdown("#### 포지셔닝 전략")
        _show_value(st, strategy.get("final_positioning", {}))
        st.markdown("#### 마케팅 메시지 후보")
        _show_value(st, strategy.get("message_candidates", []))
        st.markdown("#### 실행 계획 및 KPI")
        for i, item in enumerate(strategy.get("action_plan", []), 1):
            with st.expander(item.get("action", f"실행 전략 {i}"), expanded=True):
                _show_value(st, item)
        st.caption("모든 실행 방안과 KPI는 검증 전 제안이며 예측 성과가 아닙니다.")
