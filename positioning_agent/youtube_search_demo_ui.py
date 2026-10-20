
"""Display precomputed YouTube search results for the Demo."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st


def _video_table(videos, categories):
    """Create a table of videos with clickable links."""
    rows = []

    for video in videos:
        matched = [
            categories[key]
            for key in video.get("matched_categories", [])
            if key in categories
        ]

        rows.append({
            "분석 구분": ", ".join(matched),
            "영상 제목": video.get("title", ""),
            "게시일": (
                video.get("published_at") or ""
            )[:10],
            "YouTube 링크": video.get("youtube_url", "")
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


def render_youtube_search_demo(data_path):
    """Render saved search results without API calls."""

    data_path = Path(data_path)
    data = json.loads(data_path.read_text(encoding="utf-8"))

    videos = data["videos"]
    categories = data["categories"]

    st.success("사전에 수집한 YouTube 영상 검색 결과입니다.")
    st.caption(
        "시연 모드: 저장된 데이터를 불러왔으며 "
        "YouTube API는 호출하지 않았습니다. "
        "아직 영상 관련성 평가 전 단계입니다."
    )

    st.metric("수집된 고유 영상", len(videos))

    category_keys = list(categories.keys())

    selected_category = st.radio(
        "분석 구분 선택",
        options=category_keys,
        format_func=lambda key: categories[key],
        horizontal=True,
        key="ongredients_demo_video_category"
    )

    category_name = categories[selected_category]

    category_videos = [
        video for video in videos
        if selected_category in video.get("matched_categories", [])
    ]

    st.markdown(f"#### {category_name}")
    st.caption(f"검색된 영상 {len(category_videos)}개")

    # 저장된 검색 결과 순서 기준, 최대 3개.
    for video in category_videos[:3]:
        title = video.get("title") or "제목 없음"
        published = (
            video.get("published_at") or "게시일 정보 없음"
        )[:10]
        url = video.get("youtube_url", "")

        st.markdown(f"**{title}**")
        st.caption(f"게시일: {published}")

        if url:
            st.markdown(f"[YouTube에서 영상 보기]({url})")

    # 펼쳐보기 1: 선택한 카테고리에 속한 영상 전체
    with st.expander(
        f"선택한 카테고리의 전체 영상 보기 "
        f"({len(category_videos)}개)",
        expanded=False
    ):
        _video_table(category_videos, categories)

    st.divider()

    # 펼쳐보기 2: 전체 고유 영상 62개
    with st.expander(
        f"전체 {len(videos)}개 영상 목록",
        expanded=False
    ):
        _video_table(videos, categories)

    st.caption(
        "한 영상이 여러 분석 구분에 속할 수 있습니다. "
        "대표 영상은 검색 결과 저장 순서대로 표시하며 "
        "관련성 평가 결과나 추천 순위를 의미하지 않습니다."
    )
