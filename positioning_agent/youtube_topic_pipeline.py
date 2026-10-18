
"""YouTube collection and consumer-topic analysis pipeline."""

from positioning_agent.youtube_engine import get_video_comments
from positioning_agent.comment_preprocess import preprocess_comments
from positioning_agent.topic_pipeline import run_topic_pipeline


def run_youtube_topic_analysis(
    api_key,
    video_ids,
    max_comments_per_video=30
):
    """Collect comments, screen candidates, and run BERTopic."""

    if not isinstance(video_ids, list) or not video_ids:
        raise ValueError("video_ids must be a non-empty list.")

    # Remove duplicate video IDs while preserving order.
    unique_video_ids = list(dict.fromkeys(video_ids))

    collected = []
    collection_errors = []

    for video_id in unique_video_ids:
        try:
            comments = get_video_comments(
                api_key=api_key,
                video_id=video_id,
                max_comments=max_comments_per_video
            )
            collected.extend(comments)

        except Exception as exc:
            collection_errors.append({
                "video_id": video_id,
                "error_type": type(exc).__name__
            })

    if not collected:
        raise ValueError("No comments were collected.")

    preprocessing = preprocess_comments(collected)

    candidates = preprocessing["analysis_candidates"]

    if len(candidates) < 20:
        return {
            "status": "insufficient_data",
            "preprocessing_summary": preprocessing["summary"],
            "collection_errors": collection_errors,
            "topic_analysis": None
        }

    analysis = run_topic_pipeline(candidates)

    return {
        "status": "completed",
        "preprocessing_summary": preprocessing["summary"],
        "collection_errors": collection_errors,
        "topic_analysis": analysis
    }
