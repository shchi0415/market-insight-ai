
from pathlib import Path
import pandas as pd
import re

# 실제 사용 경험을 명시적으로 보여주는 표현
USE_PATTERNS = [
    r"써봤", r"써보니", r"써보니까",
    r"사용해봤", r"사용해보니", r"사용했",
    r"발라봤", r"발라보니", r"바르고 나서",
    r"쓰고 있", r"사용 중", r"쓰는 중",
    r"다 써", r"재구매", r"몇 통째"
]

# 구매 의향을 명시하는 표현
PURCHASE_PATTERNS = [
    r"구매할", r"구매해야", r"구매하려",
    r"살게", r"사야겠", r"사려고",
    r"주문할", r"주문해야", r"장바구니",
    r"구매하고\s*싶", r"사고\s*싶",
    r"주문하고\s*싶", r"살\s*생각",
    r"구매할\s*생각"
]

# 실제 구매를 명시하는 표현
PURCHASED_PATTERNS = [
    r"구매했", r"구매완료", r"샀어",
    r"샀는데", r"주문했", r"결제했"
]

# 미사용을 명시하는 표현
NOT_USED_PATTERNS = [
    r"안\s*써봤", r"안\s*써봄",
    r"못\s*써봤", r"사용\s*전",
    r"써본\s*적\s*없"
]


def matches_any(text, patterns):
    return any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in patterns
    )


def check_insight_quality(input_path, output_path):
    input_path = Path(input_path)
    output_path = Path(output_path)

    df = pd.read_csv(input_path, low_memory=False)

    required = {
        "text", "behavior_stage",
        "market_relevance", "validation",
        "corrected_insight", "evidence_quote"
    }

    missing = required - set(df.columns)

    if missing:
        raise ValueError(f"필수 컬럼 누락: {missing}")

    flags = []

    for _, row in df.iterrows():
        text = str(row["text"])
        stage = str(row["behavior_stage"])

        issues = []

        has_use = matches_any(text, USE_PATTERNS)
        has_not_used = matches_any(text, NOT_USED_PATTERNS)
        has_purchase = matches_any(text, PURCHASE_PATTERNS)
        has_purchased = matches_any(text, PURCHASED_PATTERNS)

        # 실제 사용 경험 검토
        if stage == "사용 경험":
            if not has_use or has_not_used:
                issues.append("사용 경험 근거 확인 필요")

        # 구매 의향 검토
        if stage == "구매 의향":
            if not has_purchase and not has_purchased:
                issues.append("구매 의향 근거 확인 필요")

        # 실제 구매 검토
        if stage == "실제 구매":
            if not has_purchased:
                issues.append("실제 구매 근거 확인 필요")

        # 원문 근거 인용 확인
        quote = row.get("evidence_quote", "")

        if pd.notna(quote) and str(quote).strip():
            if str(quote).strip() not in text:
                issues.append("근거 인용 불일치")

        # 시장 무관 댓글의 인사이트 잔존 여부
        relevance = str(row["market_relevance"])
        corrected = str(row["corrected_insight"])

        if relevance != "관련":
            if corrected != "구체적 인사이트 없음":
                issues.append("시장 무관 인사이트 잔존")

        flags.append({
            "quality_status": (
                "재검토 필요" if issues else "자동 검사 통과"
            ),
            "quality_issues": " / ".join(issues)
        })

    flag_df = pd.DataFrame(flags, index=df.index)
    result = pd.concat([df, flag_df], axis=1)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    result.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    return result
