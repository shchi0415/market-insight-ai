
"""Validate and save product information for positioning projects."""

import json
import math
from pathlib import Path


def validate_product_info(product_info):
    """Validate product information without assuming claims are verified."""

    if not isinstance(product_info, dict):
        raise TypeError("제품 정보는 딕셔너리여야 합니다.")

    required_text = ["brand", "product_name", "category"]

    for field in required_text:
        value = product_info.get(field)
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"필수 입력값 누락: {field}")

    numeric_fields = [
        "volume_ml", "price_krw",
        "sale_price_krw", "rating", "review_count"
    ]

    for field in numeric_fields:
        value = product_info.get(field)

        if value is not None:
            if isinstance(value, bool) or not isinstance(
                value, (int, float)
            ):
                raise TypeError(f"숫자 입력 오류: {field}")

            if not math.isfinite(value) or value < 0:
                raise ValueError(f"유효하지 않은 숫자: {field}")

    for field in [
        "promotion",
        "marketing_claims",
        "ingredients",
        "target_customers",
        "verified_benefits"
    ]:
        value = product_info.get(field, [])

        if not isinstance(value, list):
            raise TypeError(f"리스트 입력 오류: {field}")

        if not all(isinstance(item, str) for item in value):
            raise TypeError(f"문자열 리스트가 필요함: {field}")

    return True


def save_product_info(project_dir, product_info):
    """Save validated product information without overwriting existing data."""

    project_dir = Path(project_dir).resolve()

    if not project_dir.is_dir():
        raise FileNotFoundError("프로젝트 폴더가 존재하지 않습니다.")

    validate_product_info(product_info)

    output_path = project_dir / "product_info.json"

    if output_path.exists():
        raise FileExistsError(
            "이미 제품 정보가 존재합니다. 자동 덮어쓰기를 방지합니다."
        )

    data = dict(product_info)
    data.setdefault("promotion", [])
    data.setdefault("marketing_claims", [])
    data.setdefault("ingredients", [])
    data.setdefault("target_customers", [])
    data.setdefault("verified_benefits", [])
    data.setdefault("source", "user_input")
    data.setdefault("verification_status", "unverified")

    serialized = json.dumps(
        data, ensure_ascii=False, indent=2, allow_nan=False
    )

    with output_path.open("x", encoding="utf-8") as file:
        file.write(serialized)

    return output_path
