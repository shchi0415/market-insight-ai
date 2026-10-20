
"""Basic quality and privacy-risk screening for YouTube comments."""

import re
import pandas as pd


RISK_PATTERNS = {
    "email": r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",
    "phone": r"(?<!\d)01[016789][-\s]?\d{3,4}[-\s]?\d{4}(?!\d)",
    "account": r"(?<!\w)@[A-Za-z0-9._]{2,}",
    "url": r"https?://\S+|www\.\S+",
    "sensitive_health": (
        r"진단받|처방받|병원에서|치료받|"
        r"피부염|주사피부|약\s?복용|"
        r"스테로이드|항생제"
    )
}


def detect_risks(text):
    """Return risk-pattern categories found in a comment."""
    return [
        name for name, pattern in RISK_PATTERNS.items()
        if re.search(pattern, text, flags=re.IGNORECASE)
    ]


def preprocess_comments(comments):
    """
    Screen comments and prepare BERTopic input candidates.

    This is a preliminary risk screen, NOT anonymization.
    """

    if not isinstance(comments, list):
        raise TypeError("comments must be a list of dictionaries.")

    rows = []

    for item in comments:
        if not isinstance(item, dict):
            raise TypeError("Each comment must be a dictionary.")

        video_id = item.get("video_id")
        text = item.get("comment_text")

        if not isinstance(video_id, str) or not video_id.strip():
            continue

        if not isinstance(text, str) or not text.strip():
            continue

        rows.append({
            "video_id": video_id,
            "comment_text": text.strip()
        })

    if not rows:
        raise ValueError("No usable comments were provided.")

    df = pd.DataFrame(rows)

    # Remove exact duplicate comments within the same video.
    df = df.drop_duplicates(
        subset=["video_id", "comment_text"]
    ).reset_index(drop=True)

    df["text_length"] = df["comment_text"].str.len()
    df["korean_char_count"] = (
        df["comment_text"].str.count(r"[가-힣]")
    )

    df["quality_candidate"] = (
        (df["text_length"] >= 10)
        & (df["korean_char_count"] >= 5)
    )

    df["risk_flags"] = df["comment_text"].apply(detect_risks)
    df["needs_privacy_review"] = df["risk_flags"].apply(bool)

    selected = df[
        df["quality_candidate"]
        & ~df["needs_privacy_review"]
    ].copy().reset_index(drop=True)

    held = df[
        ~df["quality_candidate"]
        | df["needs_privacy_review"]
    ].copy().reset_index(drop=True)

    selected["analysis_id"] = [
        f"YT_{i:04d}" for i in range(1, len(selected) + 1)
    ]

    analysis_df = selected[
        ["analysis_id", "video_id", "comment_text"]
    ].copy()

    summary = {
        "input_count": len(comments),
        "unique_valid_count": len(df),
        "analysis_candidate_count": len(analysis_df),
        "review_hold_count": len(held),
        "unique_video_count": analysis_df["video_id"].nunique()
    }

    return {
        "analysis_candidates": analysis_df,
        "review_hold": held,
        "summary": summary
    }
