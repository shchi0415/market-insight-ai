
from pathlib import Path
import json
import pandas as pd


def build_strategy_input(project_dir, max_evidence=40):
    project_dir = Path(project_dir)

    trends_path = project_dir / "market_trends" / "overview.json"
    quality_path = project_dir / "verified_insights_quality.csv"

    if not trends_path.exists():
        raise FileNotFoundError(
            "Market Trends 분석 결과가 없습니다."
        )

    if not quality_path.exists():
        raise FileNotFoundError(
            "Consumer Insights 검증 결과가 없습니다."
        )

    with open(trends_path, "r", encoding="utf-8") as f:
        trends = json.load(f)

    quality = pd.read_csv(quality_path, low_memory=False)

    required = {
        "market_relevance", "validation",
        "quality_status", "corrected_insight",
        "text", "concern", "behavior_stage"
    }

    missing = required - set(quality.columns)

    if missing:
        raise ValueError(f"필수 컬럼 누락: {missing}")

    # 전략의 핵심 근거로 사용할 인사이트
    eligible = quality[
        (quality["market_relevance"] == "관련")
        & (quality["validation"] == "직접 근거")
        & (quality["quality_status"] == "자동 검사 통과")
    ].copy()

    # 원문이 있는 근거만 사용
    eligible = eligible[
        eligible["text"].notna()
        & eligible["corrected_insight"].notna()
    ]

    # 고유 댓글 기준 중복 제거
    if "comment_key" in eligible.columns:
        eligible = eligible.drop_duplicates(
            subset=["comment_key"],
            keep="last"
        )

    # 피부 고민 분포
    concerns = (
        eligible["concern"]
        .fillna("없음")
        .value_counts()
        .to_dict()
    )

    # 행동 단계 분포
    behavior = (
        eligible["behavior_stage"]
        .fillna("행동 확인 불가")
        .value_counts()
        .to_dict()
    )

    # 근거 인사이트 선정
    evidence_rows = eligible.head(max_evidence)

    evidence = []

    for _, row in evidence_rows.iterrows():
        evidence.append({
            "comment_key": str(
                row.get("comment_key", "")
            ),
            "consumer_comment": str(row["text"]),
            "validated_insight": str(
                row["corrected_insight"]
            ),
            "concern": str(row["concern"]),
            "behavior_stage": str(
                row["behavior_stage"]
            ),
            "source_url": str(
                row.get("postUrl", "")
            )
        })

    # 전체 검증 결과 요약
    validation_counts = (
        quality["validation"]
        .value_counts()
        .to_dict()
    )

    quality_counts = (
        quality["quality_status"]
        .value_counts()
        .to_dict()
    )

    strategy_input = {
        "project": project_dir.name,
        "market_overview": trends,
        "consumer_insights": {
            "total_validated": len(quality),
            "eligible_evidence": len(eligible),
            "concern_distribution": {
                str(k): int(v)
                for k, v in concerns.items()
            },
            "behavior_distribution": {
                str(k): int(v)
                for k, v in behavior.items()
            },
            "validation_distribution": {
                str(k): int(v)
                for k, v in validation_counts.items()
            },
            "quality_distribution": {
                str(k): int(v)
                for k, v in quality_counts.items()
            }
        },
        "evidence": evidence,
        "research_limitations": [
            "인스타그램 수집 표본이므로 전체 시장을 대표하지 않음",
            "AI 및 규칙 기반 근거 판정은 인간의 최종 검증이 아님",
            "시장 동향 데이터에는 v1/v2 분석 기준이 혼합될 수 있음",
            "소비자 댓글은 실제 판매량이나 구매 전환율을 증명하지 않음",
            "검증된 표본 범위 밖으로 결론을 일반화하지 말 것",
            "전략 제안은 확정된 사업 기회가 아닌 검증 가능한 가설로 제시"
        ]
    }

    output_dir = project_dir / "marketing_strategy"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "strategy_input.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            strategy_input,
            f,
            ensure_ascii=False,
            indent=2
        )

    return strategy_input, output_path
