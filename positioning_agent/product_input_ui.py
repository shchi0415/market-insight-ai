
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

    # 기존 제품 정보가 있으면 자동 덮어쓰기 금지
    if product_path.exists():
        st.success("이 프로젝트에는 저장된 제품 정보가 있습니다.")

        with open(product_path, encoding="utf-8") as f:
            product_info = json.load(f)

        with st.expander("저장된 데이터 확인", expanded=False):
            st.json(product_info)
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
        "example_ingredients": ""
    }

    project_key = str(project_dir.resolve())
    if st.session_state.get("_product_form_project") != project_key:
        for key in example_values:
            st.session_state.pop(key, None)
        st.session_state["_product_form_project"] = project_key

    if st.button("온그리디언츠 예시 불러오기"):
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

        submitted = st.form_submit_button(
            "제품 정보 저장",
            type="primary"
        )

    if submitted:
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
            "verification_status": "unverified"
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
