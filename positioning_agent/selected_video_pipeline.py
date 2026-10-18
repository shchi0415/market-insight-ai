
"""Connect video relevance selection to YouTube topic analysis."""

from positioning_agent.video_relevance_engine import (
    select_videos_for_collection
)
from positioning_agent.youtube_topic_pipeline import (
    run_youtube_topic_analysis
)


def run_selected_video_analysis(
    youtube_api_key,
    relevance_result,
    max_core=20,
    max_adjacent=10,
    max_comments_per_video=30
):
    """Select relevant videos and analyze their comments."""

    selection = select_videos_for_collection(
        relevance_result=relevance_result,
        max_core=max_core,
        max_adjacent=max_adjacent
    )

    selected_ids = selection["selected_video_ids"]

    if not selected_ids:
        return {
            "status": "no_eligible_videos",
            "video_selection": selection,
            "analysis": None
        }

    analysis = run_youtube_topic_analysis(
        api_key=youtube_api_key,
        video_ids=selected_ids,
        max_comments_per_video=max_comments_per_video
    )

    return {
        "status": analysis["status"],
        "video_selection": selection,
        "analysis": analysis
    }
