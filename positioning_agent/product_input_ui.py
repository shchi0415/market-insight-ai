
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

        st.json(product_info)
        return

    st.caption(
        "제품 정보를 입력하면 시장조사와 "
        "AI 포지셔닝 분석의 기초 자료로 활용됩니다."
    )

    with st.form("product_input_form"):
        brand = st.text_input("브랜드명 *")
        product_name = st.text_input("제품명 *")
        category = st.text_input(
            "제품 카테고리 *",
            placeholder="예: 수분 로션"
        )

        volume_ml = st.number_input(
            "용량 (ml)",
            min_value=0,
            value=0,
            step=1
        )

        price_krw = st.number_input(
            "정가 (원)",
            min_value=0,
            value=0,
            step=100
        )

        sale_price_krw = st.number_input(
            "판매가 (원)",
            min_value=0,
            value=0,
            step=100
        )

        claims_text = st.text_area(
            "주요 특징·마케팅 소구점",
            placeholder="한 줄에 하나씩 입력"
        )

        ingredients_text = st.text_area(
            "주요 성분 (선택)",
            placeholder="한 줄에 하나씩 입력"
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
