
"""Precomputed YouTube AI relevance evaluation Demo."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st


LABELS = {
    "Core": "핵심 관련",
    "Adjacent": "인접 관련",
    "Uncertain": "추가 검토",
    "Exclude": "제외",
}

CONFIDENCE = {
    "high": "높음",
    "medium": "보통",
    "low": "낮음",
}


def _show_table(videos, search_lookup):
    rows = []

    for video in videos:
        video_id = video.get("video_id", "")
        search_info = search_lookup.get(video_id, {})

        rows.append({
            "영상 제목": search_info.get("title", "제목 정보 없음"),
            "AI 분류": LABELS.get(
                video.get("relevance"),
                video.get("relevance", "")
            ),
            "판단 신뢰도": CONFIDENCE.get(
                video.get("confidence"),
                "정보 없음"
            ),
            "분류 이유": video.get("reason", ""),
            "추가 검토 필요": (
                "예" if video.get("requires_review") else "아니오"
            ),
            "YouTube 링크": (
                f"https://www.youtube.com/watch?v={video_id}"
            ),
        })

    st.dataframe(
        pd.DataFrame(rows),
        hide_index=True,
        width="stretch",
        column_config={
            "YouTube 링크": st.column_config.LinkColumn(
                "YouTube 링크",
                display_text="영상 보기"
            )
        }
    )


def render_youtube_relevance_demo(
    relevance_path,
    search_path
):
    """Display saved AI evaluations without API calls."""

    relevance_data = json.loads(
        Path(relevance_path).read_text(encoding="utf-8")
    )

    search_data = json.loads(
        Path(search_path).read_text(encoding="utf-8")
    )

    videos = relevance_data["videos"]

    search_lookup = {
        item["video_id"]: item
        for item in search_data["videos"]
    }

    st.success("저장된 AI 영상 관련성 평가 결과입니다.")

    st.caption(
        "시연 모드: 사전에 Gemini로 분석한 결과입니다. "
        "현재 API를 호출하지 않습니다. "
        "영상 제목·설명 기반 분류이며, "
        "실제 영상 시청 또는 사람의 검증 결과는 아닙니다."
    )

    st.metric("AI 평가 완료 영상", len(videos))

    counts = {
        label: sum(
            item.get("relevance") == label
            for item in videos
        )
        for label in LABELS
    }

    cols = st.columns(4)

    for col, (label, name) in zip(cols, LABELS.items()):
        col.metric(name, counts[label])

    st.caption(
        f"추가 검토 필요 표시: "
        f"{sum(bool(v.get('requires_review')) for v in videos)}개 "
        "(AI 분류의 '추가 검토'와는 별도)"
    )

    selected = st.radio(
        "관련성 분류 선택",
        options=list(LABELS),
        format_func=lambda key: LABELS[key],
        horizontal=True,
        key="ongredients_demo_relevance_category"
    )

    selected_videos = [
        item for item in videos
        if item.get("relevance") == selected
    ]

    with st.expander(
        f"선택한 분류의 전체 영상 보기 ({len(selected_videos)}개)",
        expanded=False
    ):
        _show_table(selected_videos, search_lookup)

    with st.expander(
        f"전체 {len(videos)}개 영상 평가 결과",
        expanded=False
    ):
        _show_table(videos, search_lookup)

    st.caption(
        "판단 신뢰도는 AI가 기록한 정성적 분류값이며 "
        "통계적으로 검증된 정확도나 확률이 아닙니다. "
        "정확한 모델 버전은 기존 기록에서 확인되지 않습니다."
    )
