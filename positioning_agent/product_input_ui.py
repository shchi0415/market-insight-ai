
"""Streamlit product information input interface."""

import json
from pathlib import Path

from positioning_agent.product_input_engine import (
    save_product_info
)


def render_product_input(project_dir):
    """Render a project-specific product information form."""

    import streamlit as st

    project_dir = Path(project_dir)
    product_path = project_dir / "product_info.json"

    st.subheader("제품 정보 입력")

    # Saved project inputs are visible on every rerun, not hidden in a collapsed JSON.
    # Prevent edits after downstream analysis to avoid mismatched research results.
    if product_path.exists():
        try:
            with product_path.open(encoding="utf-8") as f:
                product_info = json.load(f)
            if not isinstance(product_info, dict):
                raise ValueError("저장된 제품 정보의 형식이 올바르지 않습니다.")
        except (OSError, ValueError, TypeError) as exc:
            st.error(f"저장된 제품 정보를 읽지 못했습니다: {type(exc).__name__}")
            return

        st.success("제품 정보가 저장되어 있습니다. 새로고침 후에도 저장된 내용을 표시합니다.")
        st.markdown("#### 저장된 제품 정보")
        main_fields = [
            ("브랜드명", product_info.get("brand") or "-"),
            ("제품명", product_info.get("product_name") or "-"),
            ("제품 카테고리", product_info.get("category") or "-"),
            ("용량 (ml)", product_info.get("volume_ml") or "-"),
            ("정가 (원)", product_info.get("price_krw") or "-"),
            ("판매가 (원)", product_info.get("sale_price_krw") or "-"),
        ]
        st.dataframe(
            [{"항목": name, "저장된 값": str(value)} for name, value in main_fields],
            hide_index=True, use_container_width=True,
        )
        for heading, field in [("주요 특징·마케팅 소구점", "marketing_claims"),
                               ("주요 성분", "ingredients")]:
            st.markdown(f"**{heading}**")
            entries = product_info.get(field) or []
            st.write(" / ".join(map(str, entries)) if isinstance(entries, list) and entries else "-")
        competitors = product_info.get("competitors") or []
        st.markdown("**경쟁사 정보**")
        if isinstance(competitors, list) and competitors:
            st.dataframe(
                [{"경쟁사": str(c.get("brand", "")), "제품명": str(c.get("product_name", ""))}
                 for c in competitors if isinstance(c, dict)],
                hide_index=True, use_container_width=True,
            )
        else:
            st.write("등록된 경쟁사가 없습니다.")
        with st.expander("저장된 원본 JSON 확인", expanded=False):
            st.json(product_info)
        st.caption("분석 결과와 입력 정보가 달라지지 않도록 저장 후 자동 수정은 제한됩니다.")
        return

    st.caption(
        "제품 정보를 입력하면 시장조사와 "
        "AI 포지셔닝 분석의 기초 자료로 활용됩니다."
    )


    # 온그리디언츠 예시 입력값
    example_values = {
        "example_brand": "온그리디언츠",
        "example_product_name": "바쿠글로우 캡슐 로션",
        "example_category": "수분·진정 로션",
        "example_volume": 150,
        "example_price": 28000,
        "example_sale_price": 24600,
        "example_claims": "\n".join([
            "바쿠글로우 캡슐 로션",
            "수분광 캡슐 콘셉트",
            "쿨링 및 피부 진정 소구"
        ]),
        "example_ingredients": "",
        "competitor_brand_1": "에스트라",
        "competitor_product_1": "아토베리어365 크림",
        "competitor_brand_2": "라운드랩",
        "competitor_product_2": "1025 독도 로션",
    }

    project_key = str(project_dir.resolve())
    if st.session_state.get("_product_form_project") != project_key:
        for key in example_values:
            st.session_state.pop(key, None)
        st.session_state["_product_form_project"] = project_key
        
    if project_dir.name == "dbc345844047":
        if st.button("[예시 정보 불러오기]"):
            st.session_state.update(example_values)
            st.rerun()

    with st.form("product_input_form"):
        brand = st.text_input("브랜드명 *", key="example_brand")
        product_name = st.text_input("제품명 *", key="example_product_name")
        category = st.text_input(
            "제품 카테고리 *",
            placeholder="예: 수분 로션", key="example_category"
        )

        volume_ml = st.number_input(
            "용량 (ml)",
            min_value=0,
            key="example_volume",
            step=1
        )

        price_krw = st.number_input(
            "정가 (원)",
            min_value=0,
            key="example_price",
            step=100
        )

        sale_price_krw = st.number_input(
            "판매가 (원)",
            min_value=0,
            key="example_sale_price",
            step=100
        )

        claims_text = st.text_area(
            "주요 특징·마케팅 소구점",
            placeholder="한 줄에 하나씩 입력",
            key="example_claims"
        )

        ingredients_text = st.text_area(
            "주요 성분 (선택)",
            placeholder="한 줄에 하나씩 입력",
            key="example_ingredients"
        )


        st.divider()
        st.markdown("#### 경쟁사 정보")
        st.caption(
            "비교할 경쟁 제품을 최대 5개까지 입력하세요. "
            "입력하지 않은 항목은 저장되지 않습니다."
        )

        competitor_inputs = []

        for i in range(1, 6):
            col1, col2 = st.columns(2)

            with col1:
                competitor_brand = st.text_input(
                    f"경쟁사 {i} 브랜드명",
                    key=f"competitor_brand_{i}"
                )

            with col2:
                competitor_product = st.text_input(
                    f"경쟁사 {i} 제품명",
                    key=f"competitor_product_{i}"
                )

            competitor_inputs.append(
                (competitor_brand, competitor_product)
            )

        submitted = st.form_submit_button(
            "제품 정보 저장",
            type="primary"
        )

    if submitted:
        # 경쟁사 정보의 부분 입력 방지
        incomplete = [
            i
            for i, (comp_brand, comp_product)
            in enumerate(competitor_inputs, start=1)
            if bool(comp_brand.strip()) != bool(comp_product.strip())
        ]

        if incomplete:
            st.error(
                "경쟁사 "
                + ", ".join(map(str, incomplete))
                + "의 브랜드명과 제품명을 모두 입력해 주세요."
            )
            st.stop()

        competitors = [
            {
                "brand": comp_brand.strip(),
                "product_name": comp_product.strip()
            }
            for comp_brand, comp_product in competitor_inputs
            if comp_brand.strip() and comp_product.strip()
        ]

        product_info = {
            "brand": brand.strip(),
            "product_name": product_name.strip(),
            "category": category.strip(),
            "volume_ml": volume_ml or None,
            "price_krw": price_krw or None,
            "sale_price_krw": sale_price_krw or None,
            "rating": None,
            "review_count": None,
            "promotion": [],
            "marketing_claims": [
                x.strip()
                for x in claims_text.splitlines()
                if x.strip()
            ],
            "ingredients": [
                x.strip()
                for x in ingredients_text.splitlines()
                if x.strip()
            ],
            "target_customers": [],
            "verified_benefits": [],
            "source": "user_input",
            "verification_status": "unverified",
            "competitors": competitors
        }

        try:
            saved_path = save_product_info(
                project_dir, product_info
            )
        except (ValueError, TypeError, FileExistsError, OSError) as e:
            st.error(f"제품 정보 저장 실패: {e}")
        else:
            st.success("제품 정보가 저장되었습니다.")
            st.caption(f"저장 파일: {saved_path.name}")
            st.rerun()
