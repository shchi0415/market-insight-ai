
from pathlib import Path
import pandas as pd
import hashlib

def make_base_key(post_url, text):
    raw = (
        str(post_url).strip().rstrip("/")
        + "\n"
        + str(text).strip()
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def sync_ai_results(project_dir):
    project_dir = Path(project_dir)

    original_path = project_dir / "ai_comments.csv"
    improved_path = project_dir / "ai_comments_v2.csv"
    output_path = project_dir / "ai_comments_unified.csv"

    if not original_path.exists():
        raise FileNotFoundError(
            "기존 AI 분석 데이터가 없습니다."
        )

    original = pd.read_csv(original_path, low_memory=False)

    # 원본 댓글 식별자 생성
    original["base_key"] = [
        make_base_key(p, t)
        for p, t in zip(
            original["postUrl"],
            original["text"]
        )
    ]

    original["duplicate_index"] = (
        original.groupby("base_key").cumcount()
    )

    original["comment_key"] = [
        hashlib.sha256(
            (str(key) + "|" + str(idx)).encode("utf-8")
        ).hexdigest()
        for key, idx in zip(
            original["base_key"],
            original["duplicate_index"]
        )
    ]

    original["analysis_version"] = "v1"

    if improved_path.exists():
        improved = pd.read_csv(
            improved_path,
            low_memory=False
        )

        fields = [
            "relevance",
            "type",
            "sentiment",
            "concern",
            "insight"
        ]

        improved = improved[
            ["comment_key"] + fields
        ].drop_duplicates(
            subset=["comment_key"],
            keep="last"
        )

        improved = improved.rename(
            columns={
                f: "v2_" + f
                for f in fields
            }
        )

        combined = original.merge(
            improved,
            on="comment_key",
            how="left",
            validate="one_to_one"
        )

        has_v2 = combined["v2_relevance"].notna()

        for field in fields:
            combined[field] = combined[
                "v2_" + field
            ].combine_first(combined[field])

        combined.loc[
            has_v2,
            "analysis_version"
        ] = "v2"

        combined = combined.drop(
            columns=["v2_" + f for f in fields]
        )

    else:
        combined = original

    combined = combined.drop(
        columns=["base_key", "duplicate_index"],
        errors="ignore"
    )

    if len(combined) != len(original):
        raise ValueError(
            "동기화 과정에서 댓글 개수가 달라졌습니다."
        )

    # 기존 파일은 덮어쓰지 않음
    combined.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig"
    )

    return {
        "total": len(combined),
        "v1": int(
            (combined["analysis_version"] == "v1").sum()
        ),
        "v2": int(
            (combined["analysis_version"] == "v2").sum()
        ),
        "output_path": output_path
    }
