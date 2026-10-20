
"""Display precomputed YouTube search results for the Demo."""

import json
from pathlib import Path

import pandas as pd
import streamlit as st


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

    for category_key, category_name in categories.items():
        category_videos = [
            video for video in videos
            if category_key in video.get("matched_categories", [])
        ]

        st.markdown(f"#### {category_name}")
        st.caption(f"검색 결과 {len(category_videos)}개 영상")

        if not category_videos:
            st.info("해당 카테고리의 영상이 없습니다.")
            continue

        # 검색 결과에 저장된 순서대로 최대 3개 표시.
        # 관련성이나 품질에 따른 순위는 아님.
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

        st.divider()

    with st.expander(
        f"전체 수집 영상 보기 ({len(videos)}개)",
        expanded=False
    ):
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

    st.caption(
        "하나의 영상이 여러 검색 구분에 포함될 수 있습니다. "
        "대표 영상은 저장된 검색 결과 순서대로 표시하며, "
        "추천 순위나 관련성 평가 결과를 의미하지 않습니다."
    )
