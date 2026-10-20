
"""BERTopic-based consumer comment clustering engine."""

from collections import Counter

import numpy as np
import pandas as pd
from bertopic import BERTopic
from hdbscan import HDBSCAN
from umap import UMAP
from sklearn.feature_extraction.text import CountVectorizer


def analyze_topics(comments, embeddings):
    """
    Cluster comments using precomputed embeddings.

    Parameters
    ----------
    comments : pandas.DataFrame
        Required columns: analysis_id, video_id, comment_text
    embeddings : numpy.ndarray
        One embedding vector per comment, in matching row order.

    Returns
    -------
    dict
        Topic summary and fitted BERTopic model.
    """

    required = {"analysis_id", "video_id", "comment_text"}

    if not required.issubset(comments.columns):
        raise ValueError(
            f"Missing columns: {required - set(comments.columns)}"
        )

    if len(comments) != len(embeddings):
        raise ValueError(
            "Comment count and embedding count must match."
        )

    if len(comments) < 20:
        raise ValueError(
            "At least 20 comments are required for this configuration."
        )

    documents = comments["comment_text"].astype(str).tolist()

    umap_model = UMAP(
        n_neighbors=10,
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        random_state=42
    )

    hdbscan_model = HDBSCAN(
        min_cluster_size=5,
        min_samples=3,
        metric="euclidean",
        prediction_data=True
    )

    vectorizer_model = CountVectorizer(
        token_pattern=r"(?u)\b[가-힣A-Za-z]{2,}\b",
        ngram_range=(1, 2),
        min_df=1
    )

    model = BERTopic(
        language="multilingual",
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        calculate_probabilities=False,
        verbose=False
    )

    topics, _ = model.fit_transform(
        documents,
        np.asarray(embeddings)
    )

    result_df = comments[
        ["analysis_id", "video_id"]
    ].copy()

    result_df["topic"] = topics

    summary = (
        result_df.groupby("topic")
        .agg(
            comment_count=("analysis_id", "count"),
            unique_video_count=("video_id", "nunique")
        )
        .reset_index()
    )

    max_counts = (
        result_df.groupby(["topic", "video_id"])
        .size()
        .groupby(level=0)
        .max()
        .reset_index(name="max_video_comments")
    )

    summary = summary.merge(max_counts, on="topic")

    summary["max_video_share_pct"] = (
        summary["max_video_comments"]
        / summary["comment_count"] * 100
    ).round(1)

    topic_names = model.get_topic_info().set_index("Topic")["Name"]
    summary["topic_name_auto"] = summary["topic"].map(topic_names)

    return {
        "topic_summary": summary,
        "topic_assignments": result_df,
        "topic_model": model
    }
