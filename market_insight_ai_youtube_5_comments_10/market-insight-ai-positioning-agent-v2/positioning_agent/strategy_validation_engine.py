
"""Validate positioning strategy structure and flag review items."""

import re


def validate_positioning_strategy(strategy, expected_mode):
    """Validate generated strategy and identify review candidates."""

    if not isinstance(strategy, dict):
        raise TypeError("strategy must be a dictionary.")

    if strategy.get("strategy_mode") != expected_mode:
        raise ValueError("Strategy mode does not match.")

    required_sections = {
        "three_c": ["company", "customer", "competitor"],
        "swot": [
            "strengths", "weaknesses",
            "opportunities", "threats"
        ],
        "stp": ["segmentation", "targeting", "positioning"],
        "four_p": ["product", "price", "place", "promotion"]
    }

    for section, fields in required_sections.items():
        data = strategy.get(section)

        if not isinstance(data, dict):
            raise ValueError(f"Invalid section: {section}")

        missing = set(fields) - set(data)

        if missing:
            raise ValueError(
                f"Missing fields in {section}: {sorted(missing)}"
            )

    hypotheses = strategy.get("positioning_hypotheses")

    if not isinstance(hypotheses, list) or not hypotheses:
        raise ValueError("Positioning hypotheses are missing.")

    for index, hypothesis in enumerate(hypotheses):
        if not isinstance(hypothesis, dict):
            raise ValueError(f"Invalid hypothesis: {index}")

        if expected_mode == "product_based_hypotheses":
            if hypothesis.get("evidence_status") != "unverified":
                raise ValueError(
                    f"Hypothesis {index} must be unverified."
                )

        if not hypothesis.get("validation_plan"):
            raise ValueError(
                f"Hypothesis {index} requires a validation plan."
            )

    # 전체 전략에서 검토가 필요한 표현 탐지
    review_patterns = {
        "efficacy_claim": r"입증|증명|임상적|효과 보장",
        "market_claim": r"시장점유율|시장 지배|압도적 경쟁우위",
        "consumer_claim": r"피부 트러블|소비자 선호가 확인"
    }

    review_items = []

    def scan(value, path="strategy"):
        if isinstance(value, dict):
            for key, item in value.items():
                scan(item, f"{path}.{key}")

        elif isinstance(value, list):
            for index, item in enumerate(value):
                scan(item, f"{path}[{index}]")

        elif isinstance(value, str):
            for label, pattern in review_patterns.items():
                if re.search(pattern, value, re.IGNORECASE):
                    review_items.append({
                        "path": path,
                        "review_type": label,
                        "status": "requires_human_review"
                    })

    scan(strategy)

    return {
        "structure_valid": True,
        "strategy_mode": expected_mode,
        "hypothesis_count": len(hypotheses),
        "review_required": bool(review_items),
        "review_items": review_items,
        "note": (
            "키워드 기반 위험 표현 탐지이며 "
            "문맥상 주장 여부와 사실 정확성은 별도 검토 필요"
        )
    }


def package_strategy_result(
    strategy,
    validation_result,
    project_id
):
    """Package generated strategy with its validation metadata."""

    import copy

    if not isinstance(strategy, dict):
        raise TypeError("strategy must be a dictionary.")

    if not isinstance(validation_result, dict):
        raise TypeError("validation_result must be a dictionary.")

    if not isinstance(project_id, str) or not project_id.strip():
        raise ValueError("Valid project_id is required.")

    if validation_result.get("structure_valid") is not True:
        raise ValueError("Strategy structure validation is required.")

    if (
        strategy.get("strategy_mode")
        != validation_result.get("strategy_mode")
    ):
        raise ValueError("Strategy mode mismatch.")

    return {
        "schema_version": "2.0",
        "project": project_id,
        "generation_status": "draft",
        "strategy": copy.deepcopy(strategy),
        "validation": copy.deepcopy(validation_result),
        "review_status": (
            "requires_human_review"
            if validation_result.get("review_required")
            else "no_flagged_patterns"
        ),
        "disclaimer": (
            "AI가 생성한 전략 초안이며, 자동 검증 통과가 "
            "내용의 정확성이나 시장성을 보장하지 않습니다."
        )
    }
