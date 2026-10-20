
"""Precomputed YouTube video selection Demo."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st


def _show_selection_table(videos, search_lookup):
    rows = []

    for video in videos:
        video_id = video.get("video_id", "")
        info = search_lookup.get(video_id, {})

        purposes = video.get("purposes", [])
        purpose_labels = {
            "market_research": "시장조사",
            "brand_monitoring": "브랜드 모니터링",
        }

        rows.append({
            "영상 제목": info.get("title", "제목 정보 없음"),
            "선별 목적": ", ".join(
                purpose_labels.get(p, p) for p in purposes
            ),
            "시장조사 대상": (
                "예" if video.get("market_collection_eligible")
                else "아니오"
            ),
            "추가 검토 필요": (
                "예" if video.get("requires_review")
                else "아니오"
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


def render_youtube_selection_demo(selection_path, search_path):
    """Render saved video selections without API calls."""

    selection_data = json.loads(
        Path(selection_path).read_text(encoding="utf-8")
    )
    search_data = json.loads(
        Path(search_path).read_text(encoding="utf-8")
    )

    result = selection_data["selection_result"]
    videos = result["videos"]

    search_lookup = {
        item["video_id"]: item
        for item in search_data["videos"]
    }

    st.success("사전에 저장된 영상 선별 결과입니다.")
    st.caption(
        "시연 모드: 기존 규칙 기반 영상 선별 결과를 불러옵니다. "
        "새로운 API를 호출하지 않습니다. "
        "사람이 최종 검증한 결과는 아닙니다."
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("최종 선별 영상", len(videos))

    market_videos = [
        v for v in videos
        if v.get("market_collection_eligible") is True
    ]
    brand_videos = [
        v for v in videos
        if v.get("brand_monitoring") is True
    ]

    c2.metric("시장조사용", len(market_videos))
    c3.metric("브랜드 모니터링용", len(brand_videos))

    with st.expander(
        f"시장조사용 전체 영상 보기 ({len(market_videos)}개)",
        expanded=False
    ):
        _show_selection_table(market_videos, search_lookup)

    with st.expander(
        f"브랜드 모니터링용 영상 보기 ({len(brand_videos)}개)",
        expanded=False
    ):
        _show_selection_table(brand_videos, search_lookup)

    with st.expander(
        f"전체 {len(videos)}개 선별 영상 목록",
        expanded=False
    ):
        _show_selection_table(videos, search_lookup)

    st.caption(
        "브랜드 모니터링 영상은 자사 제품과의 정확한 일치가 "
        "검증되지 않았으므로 별도 검토가 필요합니다."
    )
