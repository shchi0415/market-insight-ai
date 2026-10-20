
"""Streamlit dashboard for AI positioning strategy drafts."""

import json
from pathlib import Path


def render_positioning_strategy_dashboard(package_path):
    """Render a packaged positioning strategy in Streamlit."""

    import streamlit as st

    package_path = Path(package_path)

    if not package_path.is_file():
        st.info("아직 생성된 포지셔닝 전략이 없습니다.")
        return

    with open(package_path, "r", encoding="utf-8") as f:
        package = json.load(f)

    strategy = package.get("strategy", {})
    validation = package.get("validation", {})

    st.subheader("AI 제품 포지셔닝 전략")

    if package.get("generation_status") == "draft":
        st.caption("AI 생성 전략 초안 · 추가 검증 필요")

    if package.get("review_status") == "requires_human_review":
        st.warning(
            "일부 전략 표현에 추가 검토가 필요합니다. "
            "아래 검토 항목을 확인해주세요."
        )

    st.markdown("#### 핵심 전략 요약")
    st.write(strategy.get("executive_summary", ""))

    st.markdown("#### 포지셔닝 가설")
    for index, item in enumerate(
        strategy.get("positioning_hypotheses", []),
        start=1
    ):
        with st.expander(f"가설 {index}", expanded=True):
            st.write(item.get("hypothesis", ""))
            st.caption(
                "근거 상태: "
                + item.get("evidence_status", "미확인")
            )
            st.write("검증 계획:", item.get("validation_plan", ""))

    sections = {
        "3C 분석": "three_c",
        "SWOT 분석": "swot",
        "STP 전략": "stp",
        "4P 전략": "four_p"
    }

    for title, key in sections.items():
        st.markdown(f"#### {title}")
        data = strategy.get(key, {})

        if isinstance(data, dict):
            for field, value in data.items():
                st.markdown(f"**{field}**")
                st.write(value)

    st.markdown("#### 추가 검토 항목")

    items = validation.get("review_items", [])

    if items:
        st.dataframe(
            items,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(
            "자동 패턴 검사에서 검토 항목이 발견되지 않았습니다. "
            "내용 검증이 완료됐다는 뜻은 아닙니다."
        )

    st.caption(
        package.get(
            "disclaimer",
            "AI 생성 전략은 추가 검증이 필요한 초안입니다."
        )
    )
