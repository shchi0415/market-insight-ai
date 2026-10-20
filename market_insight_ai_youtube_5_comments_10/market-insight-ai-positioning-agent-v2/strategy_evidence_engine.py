
import json
from pathlib import Path
from collections import Counter


def verify_strategy_evidence(project_dir):
    project_dir = Path(project_dir)

    strategy_dir = project_dir / "marketing_strategy"

    input_path = strategy_dir / "strategy_input.json"
    strategy_path = strategy_dir / "strategy_v2.json"
    output_path = strategy_dir / "strategy_evidence_audit.json"

    with open(input_path, "r", encoding="utf-8") as f:
        source = json.load(f)

    with open(strategy_path, "r", encoding="utf-8") as f:
        strategy = json.load(f)

    evidence_map = {
        item["comment_key"]: item
        for item in source.get("evidence", [])
    }

    audits = []

    for index, opportunity in enumerate(
        strategy.get("opportunities", []), start=1
    ):
        cited_keys = opportunity.get("evidence_keys", [])

        if not isinstance(cited_keys, list):
            cited_keys = []

        counts = Counter(cited_keys)
        duplicate_keys = [
            key for key, count in counts.items()
            if count > 1
        ]

        unique_keys = list(dict.fromkeys(cited_keys))

        valid_keys = [
            key for key in unique_keys
            if key in evidence_map
        ]

        missing_keys = [
            key for key in unique_keys
            if key not in evidence_map
        ]

        evidence_details = []

        for key in valid_keys:
            item = evidence_map[key]

            evidence_details.append({
                "comment_key": key,
                "consumer_comment": item.get(
                    "consumer_comment", ""
                ),
                "validated_insight": item.get(
                    "validated_insight", ""
                ),
                "concern": item.get("concern", ""),
                "behavior_stage": item.get(
                    "behavior_stage", ""
                ),
                "source_url": item.get(
                    "source_url", ""
                )
            })

        valid_count = len(valid_keys)

        # URL을 정규화해 서로 다른 게시물 수 계산
        unique_posts = {
            str(item.get("source_url", "")).strip().rstrip("/")
            for item in evidence_details
            if str(item.get("source_url", "")).strip()
        }
        unique_post_count = len(unique_posts)

        # MVP 내부 점검 규칙 (통계적 신뢰도가 아님)
        if valid_count == 0:
            evidence_status = "근거 없음"
        elif valid_count < 3 or unique_post_count < 2:
            evidence_status = "근거 매우 제한적"
        elif valid_count < 5 or unique_post_count < 3:
            evidence_status = "추가 검증 필요"
        else:
            evidence_status = "근거 수량 확보"

        audits.append({
            "opportunity_number": index,
            "opportunity_name": opportunity.get(
                "name", ""
            ),
            "target_customer": opportunity.get(
                "target_customer", ""
            ),
            "positioning": opportunity.get(
                "positioning", ""
            ),
            "ai_confidence": opportunity.get(
                "confidence", ""
            ),
            "cited_count": len(cited_keys),
            "valid_evidence_count": valid_count,
            "unique_post_count": unique_post_count,
            "duplicate_keys": duplicate_keys,
            "missing_keys": missing_keys,
            "evidence_status": evidence_status,
            "evidence_details": evidence_details,
            "semantic_support_checked": False
        })

    result = {
        "project": project_dir.name,
        "opportunity_audits": audits,
        "audit_scope": (
            "근거 ID 존재 여부, 중복 및 근거 수량 확인. "
            "인용 댓글이 전략 주장을 의미적으로 뒷받침하는지는 "
            "아직 검증하지 않았습니다."
        ),
        "count_threshold_note": (
            "근거 수량 경고는 개발용 점검 기준이며 "
            "통계적 유의성이나 전략의 성공 확률을 의미하지 않습니다."
        )
    }

    output_path.parent.mkdir(
        parents=True, exist_ok=True
    )

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    return result, output_path
