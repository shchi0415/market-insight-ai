
"""Integrated consumer comment topic-analysis pipeline."""

import pandas as pd

from positioning_agent.embedding_engine import generate_embeddings
from positioning_agent.topic_engine import analyze_topics


REQUIRED_COLUMNS = {
    "analysis_id",
    "video_id",
    "comment_text"
}


def run_topic_pipeline(comments: pd.DataFrame):
    """Generate embeddings and analyze consumer comment topics."""

    if not isinstance(comments, pd.DataFrame):
        raise TypeError("comments must be a pandas DataFrame.")

    missing = REQUIRED_COLUMNS - set(comments.columns)

    if missing:
        raise ValueError(f"Missing columns: {sorted(missing)}")

    if len(comments) < 20:
        raise ValueError("At least 20 comments are required.")

    if comments["analysis_id"].isna().any():
        raise ValueError("analysis_id contains missing values.")

    if comments["analysis_id"].duplicated().any():
        raise ValueError("analysis_id must be unique.")

    if comments["video_id"].isna().any():
        raise ValueError("video_id contains missing values.")

    texts = comments["comment_text"]

    if texts.isna().any() or not texts.map(
        lambda x: isinstance(x, str) and bool(x.strip())
    ).all():
        raise ValueError("comment_text contains missing or empty values.")

    # Preserve input row order.
    clean_comments = comments[
        ["analysis_id", "video_id", "comment_text"]
    ].copy().reset_index(drop=True)

    embeddings = generate_embeddings(
        clean_comments["comment_text"].tolist()
    )

    results = analyze_topics(
        comments=clean_comments,
        embeddings=embeddings
    )

    return {
        "topic_summary": results["topic_summary"],
        "topic_assignments": results["topic_assignments"],
        "topic_model": results["topic_model"],
        "embedding_shape": embeddings.shape,
        "total_comments": len(clean_comments),
        "total_videos": clean_comments["video_id"].nunique()
    }
