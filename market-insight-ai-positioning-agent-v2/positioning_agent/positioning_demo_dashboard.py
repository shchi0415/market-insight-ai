
"""Precomputed positioning analysis demo dashboard."""

from pathlib import Path
import streamlit as st


def render_positioning_demo_dashboard(project_dir):
    """Render saved analysis results without API calls."""

    project_dir = Path(project_dir)

    local_results = project_dir / "demo_results"

    public_results = (
        Path(__file__).resolve().parent.parent
        / "positioning_demo_data"
        / "ongredients_analysis"
    )

    # 프로젝트 분석 결과가 있으면 사용하고,
    # 없으면 배포용 Demo 결과를 사용
    if local_results.is_dir():
        results_dir = local_results
    else:
        results_dir = public_results

    st.header("AI 제품 포지셔닝 분석 · DEMO")

    st.info(
        "본 화면은 사전에 수집·분석한 실제 데이터를 "
        "활용하는 Demo Mode입니다. "
        "화면 조회 시 AI 분석을 새로 실행하지 않습니다."
    )

    stages = [
        "01 · 시장 니즈 분석",
        "02 · 경쟁사·자사 제품 분석",
        "03 · Gemini 시장 기회 분석",
        "04 · STP 및 포지셔닝",
        "05 · 최종 마케팅 전략",
    ]

    selected_stage = st.radio(
        "분석 단계 선택",
        stages,
        horizontal=True,
        key="positioning_demo_stage"
    )

    st.subheader(selected_stage)

    if selected_stage.startswith("01"):
        import json
        import pandas as pd

        evidence_path = (
            results_dir / "positioning_evidence.json"
        )

        if not evidence_path.is_file():
            st.warning("시장 분석 결과 파일이 없습니다.")
        else:
            with open(evidence_path, encoding="utf-8") as f:
                evidence = json.load(f)

            total = evidence["market_comment_count"]
            needs = evidence["market_need_counts"]

            st.metric(
                "분석 대상 YouTube 댓글",
                f"{total:,}건"
            )

            rows = [
                {
                    "니즈 카테고리": category,
                    "언급 댓글 수": count,
                    "언급 비율 (%)": round(
                        count / total * 100, 1
                    )
                }
                for category, count in needs.items()
            ]

            df = pd.DataFrame(rows).sort_values(
                "언급 댓글 수",
                ascending=False
            )

            st.bar_chart(
                df.set_index("니즈 카테고리")[
                    "언급 댓글 수"
                ]
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "YouTube 댓글 기반 탐색적 분석입니다. "
                "카테고리 간 중복 집계가 가능하며, "
                "비율은 전체 시장 소비자 비율이 아닙니다."
            )
    elif selected_stage.startswith("02"):
        import json
        import pandas as pd

        products = [
            ("에스트라 아토베리어365 크림",
             "aestura_analysis.json"),
            ("라운드랩 1025 독도 로션",
             "roundlab_analysis.json"),
            ("온그리디언츠 바쿠글로우 캡슐 로션",
             "own_consumer_responses.json"),
        ]

        rows = []

        for name, filename in products:
            path = results_dir / filename

            if not path.is_file():
                st.warning(f"분석 파일 없음: {filename}")
                continue

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            rows.append({
                "제품": name,
                "분석 댓글": data.get(
                    "analyzed_comments",
                    data.get("analyzed_comment_count", 0)
                ),
                "실사용 후기 후보": (
                    1 if filename == "own_consumer_responses.json"
                    else data.get("review_candidates", 0)
                )
            })

        if rows:
            df = pd.DataFrame(rows)

            st.markdown("#### 제품별 분석 데이터")
            st.dataframe(
                df,
                width="stretch",
                hide_index=True
            )

            st.caption(
                "실사용 후기 후보는 AI 분류 결과이며, "
                "실제 구매 여부가 확인된 리뷰는 아닙니다. "
                "제품별 표본 규모와 영상 구성이 달라 "
                "만족도나 제품 성능을 직접 비교할 수 없습니다."
            )

    elif selected_stage.startswith("03"):
        import json

        opportunity_path = (
            results_dir / "gemini_market_opportunities.json"
        )

        if not opportunity_path.is_file():
            st.warning("Gemini 시장 기회 분석 파일이 없습니다.")
        else:
            with open(opportunity_path, encoding="utf-8") as f:
                result = json.load(f)

            st.caption(
                "사전에 Gemini API로 생성한 분석 결과입니다. "
                "현재 화면에서는 API를 호출하지 않습니다."
            )

            st.markdown("#### 시장 인사이트")

            for i, item in enumerate(
                result.get("market_insights", []), 1
            ):
                with st.expander(
                    f"{i}. {item.get('insight', '시장 인사이트')}",
                    expanded=True
                ):
                    st.write("**분석 근거**")
                    st.write(item.get("evidence", ""))

                    st.write("**해석**")
                    st.write(item.get("interpretation", ""))

                    st.write("**분석 한계**")
                    st.write(item.get("limitations", ""))

            st.markdown("#### 잠재적 시장 기회")

            for i, item in enumerate(
                result.get("opportunity_areas", []), 1
            ):
                with st.expander(
                    f"{i}. {item.get('opportunity_name', '기회 영역')}"
                ):
                    st.write(
                        "**소비자 니즈:**",
                        item.get("consumer_need", "")
                    )
                    st.write(
                        "**경쟁사 취약점 가설:**",
                        item.get("competitor_gap_hypothesis", "")
                    )
                    st.write(
                        "**자사 제품 연결 가설:**",
                        item.get("own_product_fit_hypothesis", "")
                    )

                    st.write("**분석 근거**")
                    for evidence in item.get(
                        "supporting_evidence", []
                    ):
                        st.write("-", evidence)

                    st.write("**추가 검증 사항**")
                    for task in item.get("validation_needed", []):
                        st.write("-", task)

            st.markdown("#### 전략적 위험")

            for item in result.get("strategic_risks", []):
                st.warning(
                    f"**{item.get('risk', '')}**\n\n"
                    f"{item.get('reason', '')}"
                )

            st.markdown("#### 종합 분석")
            st.write(result.get("overall_summary", ""))

            st.caption(
                "시장 기회는 검증 전 전략 가설입니다. "
                "경쟁사의 객관적 결함이나 자사 제품의 "
                "우수성이 입증되었다는 의미는 아닙니다."
            )

    elif selected_stage.startswith("04"):
        import json

        stp_file = results_dir / "gemini_stp_strategy.json"
        review_file = results_dir / "stp_strategy_review.json"

        if not stp_file.is_file() or not review_file.is_file():
            st.warning("STP 분석 또는 검토 결과 파일이 없습니다.")
        else:
            with open(stp_file, encoding="utf-8") as f:
                stp_data = json.load(f)

            with open(review_file, encoding="utf-8") as f:
                review_data = json.load(f)

            st.caption(
                "사전 생성된 Gemini STP 분석 결과와 "
                "사람의 검토 의견을 함께 표시합니다."
            )

            st.markdown("#### 1. Segmentation · 시장 세분화")

            for i, segment in enumerate(
                stp_data.get("segmentation", []), 1
            ):
                with st.expander(
                    f"{i}. {segment.get('segment_name', '')}"
                ):
                    st.write("**주요 니즈:**", segment.get("needs", ""))
                    st.write("**분석 근거:**", segment.get("evidence", ""))
                    st.caption(segment.get("limitations", ""))

            st.markdown("#### 2. Targeting · 타깃 선정")

            targeting = stp_data.get("targeting", {})

            st.write(
                "**우선 검증 타깃:**",
                targeting.get("primary_target", "")
            )
            st.write(
                "**선정 근거:**",
                targeting.get("rationale", "")
            )
            st.write(
                "**반론 및 한계:**",
                targeting.get("counterarguments", "")
            )

            st.markdown("#### 3. Positioning · 후보 비교")

            for item in stp_data.get(
                "positioning_comparison", []
            ):
                with st.expander(
                    f"후보 {item.get('candidate_id', '')}"
                ):
                    st.write("**강점:**", item.get("strengths", ""))
                    st.write("**약점:**", item.get("weaknesses", ""))
                    st.write(
                        "**근거 수준:**",
                        item.get("evidence_quality", "")
                    )
                    st.write(
                        "**평가:**",
                        item.get("recommendation", "")
                    )

            st.markdown("#### 4. 전략 검토 및 수정")

            st.write(
                "**Gemini 최초 추천:**",
                review_data.get("gemini_recommendation", "")
            )
            st.write(
                "**검토 방향:**",
                review_data.get("review_decision", "")
            )

            st.info(
                "**수정된 포지셔닝 가설**\n\n"
                + review_data.get(
                    "revised_positioning_hypothesis", ""
                )
            )

            st.write(
                "**핵심 메시지 후보:**",
                review_data.get("message_hypothesis", "")
            )

            st.markdown("**검증 전 사용을 제한할 주장**")

            for claim in review_data.get(
                "claims_to_avoid_without_validation", []
            ):
                st.write("-", claim)

            st.caption(
                "세그먼트와 포지셔닝은 탐색적 가설이며, "
                "실제 구매 행동이나 제품 효능이 "
                "검증된 결과는 아닙니다."
            )

    elif selected_stage.startswith("05"):
        import json

        strategy_file = (
            results_dir / "gemini_final_strategy.json"
        )

        if not strategy_file.is_file():
            st.warning("최종 전략 분석 파일이 없습니다.")
        else:
            with open(strategy_file, encoding="utf-8") as f:
                strategy = json.load(f)

            st.caption(
                "사전에 Gemini로 생성한 전략 초안입니다. "
                "실제 성과가 검증된 전략은 아닙니다."
            )

            st.markdown("#### 1. 최종 포지셔닝")

            target = strategy.get("target_customer", {})
            positioning = strategy.get("positioning", {})

            st.write(
                "**우선 타깃 가설:**",
                target.get("description", "")
            )
            st.write(
                "**소비자 문제:**",
                target.get("consumer_problem", "")
            )

            st.info(
                "**포지셔닝 가설**\n\n"
                + positioning.get("statement", "")
            )

            st.write(
                "**핵심 가치 제안:**",
                positioning.get("value_proposition", "")
            )

            st.markdown("#### 2. 마케팅 메시지 후보")

            for i, item in enumerate(
                strategy.get("message_candidates", []), 1
            ):
                with st.expander(
                    f"메시지 {i}: {item.get('message', '')}"
                ):
                    st.write(
                        "**대상:**",
                        item.get("intended_audience", "")
                    )
                    st.write(
                        "**선정 이유:**",
                        item.get("rationale", "")
                    )
                    st.write(
                        "**표현 위험:**",
                        item.get("claim_risk", "")
                    )

            st.markdown("#### 3. 마케팅 실행 전략 및 KPI")

            for i, item in enumerate(
                strategy.get("action_plan", []), 1
            ):
                with st.expander(
                    f"전략 {i}: {item.get('action', '')}"
                ):
                    st.write(
                        "**목표:**",
                        item.get("objective", "")
                    )

                    st.write("**실행 방법**")
                    for step in item.get("execution_steps", []):
                        st.write("-", step)

                    st.write(
                        "**KPI:**",
                        item.get("kpi", "")
                    )
                    st.write(
                        "**측정 방법:**",
                        item.get("measurement_method", "")
                    )
                    st.write(
                        "**근거:**",
                        item.get("evidence_basis", "")
                    )
                    st.write(
                        "**추가 검증:**",
                        item.get("validation_needed", "")
                    )

            st.markdown("#### 4. 전략적 위험")

            for item in strategy.get("risks", []):
                st.warning(
                    f"**{item.get('risk', '')}**\n\n"
                    f"대응: {item.get('mitigation', '')}"
                )

            st.markdown("#### 5. 추가 필요 데이터")

            for item in strategy.get(
                "additional_data_needed", []
            ):
                st.write("-", item)

            st.markdown("#### 6. 최종 전략 요약")
            st.write(strategy.get("executive_summary", ""))

            st.caption(
                "본 전략은 검증 전 제안안입니다. "
                "실제 마케팅 실행 전 제품 효능, 사용감, "
                "소비자 반응 등에 대한 검증이 필요합니다."
            )

    else:
        st.caption("해당 단계의 분석 결과 연결 예정")

    if not results_dir.is_dir():
        st.warning("Demo 분석 결과 폴더를 찾을 수 없습니다.")
