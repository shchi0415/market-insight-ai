
from pathlib import Path
import json
import pandas as pd

def generate_market_trends(
    project_dir,
    analysis_file="ai_comments_unified.csv"
):
    project_dir = Path(project_dir)

    posts_path = project_dir / "posts_clean.csv"
    comments_path = project_dir / analysis_file

    if not posts_path.exists():
        raise FileNotFoundError("게시물 데이터가 없습니다.")

    if not comments_path.exists():
        raise FileNotFoundError("AI 분석 결과가 없습니다.")

    posts = pd.read_csv(posts_path, low_memory=False)
    comments = pd.read_csv(comments_path, low_memory=False)

    required = {
        "relevance", "sentiment", "concern",
        "type", "text", "postUrl"
    }

    missing = required - set(comments.columns)

    if missing:
        raise ValueError(
            f"AI 분석 결과 필수 컬럼 누락: {missing}"
        )

    # 1. 스킨케어 관련 댓글 선별
    relevant = comments[
        comments["relevance"] == "관련"
    ].copy()

    # 2. 분석 버전별 표본 확인
    if "analysis_version" in comments.columns:
        version_counts = (
            comments["analysis_version"]
            .value_counts(dropna=False)
            .to_dict()
        )
    else:
        version_counts = {"unknown": len(comments)}

    # 3. 감성 분포
    sentiment = (
        relevant["sentiment"]
        .fillna("판단불가")
        .value_counts()
        .rename_axis("category")
        .reset_index(name="count")
    )

    # 4. 피부 고민 분포
    concerns = (
        relevant["concern"]
        .fillna("없음")
        .value_counts()
        .rename_axis("category")
        .reset_index(name="count")
    )

    # 5. 소비자 반응 유형
    reaction_types = (
        relevant["type"]
        .fillna("기타")
        .value_counts()
        .rename_axis("category")
        .reset_index(name="count")
    )

    # 6. 기본 지표
    overview = {
        "posts": len(posts),
        "analyzed_comments": len(comments),
        "relevant_comments": len(relevant),
        "irrelevant_comments": int(
            (comments["relevance"] == "무관").sum()
        ),
        "uncertain_comments": int(
            (comments["relevance"] == "불확실").sum()
        ),
        "relevance_rate": round(
            len(relevant) / len(comments) * 100, 2
        ) if len(comments) else 0,
        "analysis_versions": {
            str(k): int(v)
            for k, v in version_counts.items()
        },
        "methodology_note": (
            "인스타그램 수집 표본의 댓글 언급 분포입니다. "
            "시장 전체 수요나 시장점유율을 의미하지 않습니다. "
            "분석 버전이 혼합된 경우 분류 기준 차이에 유의해야 합니다."
        )
    }

    # 7. 프로젝트별 저장
    output_dir = project_dir / "market_trends"
    output_dir.mkdir(parents=True, exist_ok=True)

    sentiment.to_csv(
        output_dir / "sentiment.csv",
        index=False,
        encoding="utf-8-sig"
    )

    concerns.to_csv(
        output_dir / "concerns.csv",
        index=False,
        encoding="utf-8-sig"
    )

    reaction_types.to_csv(
        output_dir / "reaction_types.csv",
        index=False,
        encoding="utf-8-sig"
    )

    with open(
        output_dir / "overview.json",
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            overview,
            f,
            ensure_ascii=False,
            indent=2
        )

    return {
        "overview": overview,
        "sentiment": sentiment,
        "concerns": concerns,
        "reaction_types": reaction_types,
        "output_dir": output_dir
    }
