
"""YouTube video discovery using the official Data API."""

import requests


KEYWORD_CATEGORIES = (
    "market_keywords",
    "consumer_need_keywords",
    "own_product_keywords",
    "competitor_keywords"
)

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def search_videos(api_key, keyword_data, max_results=10):
    """Search YouTube and deduplicate videos across keywords."""

    if not api_key:
        raise ValueError("YouTube API key is required.")

    if not isinstance(keyword_data, dict):
        raise TypeError("keyword_data must be a dictionary.")

    if not 1 <= max_results <= 50:
        raise ValueError("max_results must be between 1 and 50.")

    results = {}

    for category in KEYWORD_CATEGORIES:
        keywords = keyword_data.get(category, [])

        if not isinstance(keywords, list):
            raise ValueError(f"{category} must be a list.")

        for keyword in keywords:
            if not isinstance(keyword, str) or not keyword.strip():
                continue

            response = requests.get(
                SEARCH_URL,
                params={
                    "key": api_key,
                    "part": "snippet",
                    "q": keyword,
                    "type": "video",
                    "maxResults": max_results,
                    "regionCode": "KR",
                    "relevanceLanguage": "ko"
                },
                timeout=30
            )

            response.raise_for_status()
            payload = response.json()

            for item in payload.get("items", []):
                video_id = item.get("id", {}).get("videoId")

                if not video_id:
                    continue

                snippet = item.get("snippet", {})

                if video_id not in results:
                    results[video_id] = {
                        "video_id": video_id,
                        "title": snippet.get("title", ""),
                        "description": snippet.get("description", ""),
                        "published_at": snippet.get("publishedAt", ""),
                        "channel_id": snippet.get("channelId", ""),
                        "matched_keywords": [],
                        "matched_categories": []
                    }

                record = results[video_id]

                if keyword not in record["matched_keywords"]:
                    record["matched_keywords"].append(keyword)

                if category not in record["matched_categories"]:
                    record["matched_categories"].append(category)

    return list(results.values())


VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


def get_video_details(api_key, video_ids):
    """Retrieve public video metadata in batches of up to 50."""

    if not api_key:
        raise ValueError("YouTube API key is required.")

    if not isinstance(video_ids, list):
        raise TypeError("video_ids must be a list.")

    unique_ids = list(dict.fromkeys(video_ids))

    results = []

    for start in range(0, len(unique_ids), 50):
        batch = unique_ids[start:start + 50]

        response = requests.get(
            VIDEOS_URL,
            params={
                "key": api_key,
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(batch)
            },
            timeout=30
        )

        response.raise_for_status()

        for item in response.json().get("items", []):
            snippet = item.get("snippet", {})
            statistics = item.get("statistics", {})
            content = item.get("contentDetails", {})

            results.append({
                "video_id": item["id"],
                "title": snippet.get("title", ""),
                "published_at": snippet.get("publishedAt", ""),
                "default_language": snippet.get("defaultLanguage"),
                "view_count": int(statistics.get("viewCount", 0)),
                "comment_count": (
                    int(statistics["commentCount"])
                    if "commentCount" in statistics
                    else None
                ),
                "duration": content.get("duration", "")
            })

    return results


COMMENTS_URL = "https://www.googleapis.com/youtube/v3/commentThreads"


def get_video_comments(api_key, video_id, max_comments=30):
    """Collect public top-level comments via the YouTube Data API."""

    if not api_key:
        raise ValueError("YouTube API key is required.")

    if not isinstance(video_id, str) or not video_id.strip():
        raise ValueError("A valid video_id is required.")

    if not isinstance(max_comments, int) or not 1 <= max_comments <= 100:
        raise ValueError("max_comments must be between 1 and 100.")

    response = requests.get(
        COMMENTS_URL,
        params={
            "key": api_key,
            "part": "snippet",
            "videoId": video_id,
            "maxResults": max_comments,
            "order": "relevance",
            "textFormat": "plainText"
        },
        timeout=30
    )

    response.raise_for_status()

    comments = []

    for item in response.json().get("items", []):
        snippet = item.get("snippet", {}).get(
            "topLevelComment", {}
        ).get("snippet", {})

        text = snippet.get("textDisplay", "").strip()

        if text:
            comments.append({
                "video_id": video_id,
                "comment_text": text
            })

    return comments
