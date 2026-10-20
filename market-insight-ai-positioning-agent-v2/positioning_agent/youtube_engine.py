
"""YouTube video discovery using the official Data API."""

import requests


KEYWORD_CATEGORIES = (
    "market_keywords",
    "consumer_need_keywords",
    "own_product_keywords",
    "competitor_keywords"
)

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"


def search_videos(api_key, keyword_data, max_results=5):
    """Search YouTube and deduplicate videos across keywords."""

    if not api_key:
        raise ValueError("YouTube API key is required.")

    if not isinstance(keyword_data, dict):
        raise TypeError("keyword_data must be a dictionary.")

    if not 1 <= max_results <= 50:
        raise ValueError("max_results must be between 1 and 50.")

    # General-project safety limit: no more than five unique videos in total.
    max_results = min(max_results, 5)
    results = {}

    for category in KEYWORD_CATEGORIES:
        keywords = keyword_data.get(category, [])

        if not isinstance(keywords, list):
            raise ValueError(f"{category} must be a list.")

        for keyword in keywords:
            if len(results) >= 5:
                return list(results.values())
            if not isinstance(keyword, str) or not keyword.strip():
                continue

            response = requests.get(
                SEARCH_URL,
                params={
                    "key": api_key,
                    "part": "snippet",
                    "q": keyword,
                    "type": "video",
                    "maxResults": max(1, min(max_results, 5 - len(results))),
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
                    if len(results) >= 5:
                        return list(results.values())
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


def get_video_comments(api_key, video_id, max_comments=10):
    """Collect public top-level comments via the YouTube Data API."""

    if not api_key:
        raise ValueError("YouTube API key is required.")

    if not isinstance(video_id, str) or not video_id.strip():
        raise ValueError("A valid video_id is required.")

    if not isinstance(max_comments, int) or not 1 <= max_comments <= 100:
        raise ValueError("max_comments must be between 1 and 100.")

    # Enforce the per-video ceiling even if callers request more.
    max_comments = min(max_comments, 10)
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


def save_video_search_results(videos, project_dir, search_keywords):
    """Save YouTube search results without overwriting existing data."""

    import json
    from pathlib import Path

    if not isinstance(videos, list):
        raise TypeError("videos must be a list.")

    if not isinstance(search_keywords, dict):
        raise TypeError("search_keywords must be a dictionary.")

    if set(search_keywords) != set(KEYWORD_CATEGORIES):
        raise ValueError("Unexpected search keyword categories.")

    normalized_keywords = {}

    for category in KEYWORD_CATEGORIES:
        keywords = search_keywords[category]

        if not isinstance(keywords, list):
            raise ValueError(f"Invalid keywords: {category}")

        if not all(
            isinstance(keyword, str) and keyword.strip()
            for keyword in keywords
        ):
            raise ValueError(f"Invalid keyword value: {category}")

        normalized_keywords[category] = list(keywords)

    seen_ids = set()

    for video in videos:
        if not isinstance(video, dict):
            raise ValueError("Every video must be a dictionary.")

        video_id = video.get("video_id")

        if not isinstance(video_id, str) or not video_id.strip():
            raise ValueError("Video ID is missing.")

        if video_id in seen_ids:
            raise ValueError("Duplicate video ID found.")

        seen_ids.add(video_id)

    project_dir = Path(project_dir)

    if not project_dir.is_dir():
        raise ValueError("Project directory does not exist.")

    if not (project_dir / "project_info.json").is_file():
        raise ValueError("Project metadata is missing.")

    output_dir = project_dir / "youtube_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "youtube_search_results.json"

    payload = {
        "source": "youtube_data_api_v3",
        "search_keywords": normalized_keywords,
        "video_count": len(videos),
        "videos": videos
    }

    # Exclusive creation prevents accidental overwrites.
    with output_path.open("x", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return output_path


def run_project_video_search(
    api_key,
    project_dir,
    max_results=10
):
    """Search YouTube once per keyword and save project results."""

    import json
    from pathlib import Path

    project_dir = Path(project_dir)

    keyword_path = (
        project_dir / "youtube_analysis" / "keyword_generation.json"
    )

    output_path = (
        project_dir / "youtube_analysis" / "youtube_search_results.json"
    )

    # Check before any API request.
    if output_path.exists():
        return {
            "status": "already_exists",
            "output_path": str(output_path),
            "api_requests": 0
        }

    if not keyword_path.is_file():
        raise FileNotFoundError("Keyword generation result is missing.")

    keyword_result = json.loads(
        keyword_path.read_text(encoding="utf-8")
    )

    search_keywords = keyword_result.get("search_keywords")

    if not isinstance(search_keywords, dict):
        raise ValueError("Search keywords are invalid.")

    if set(search_keywords) != set(KEYWORD_CATEGORIES):
        raise ValueError("Unexpected search keyword categories.")

    total_keywords = 0
    normalized = set()

    for category in KEYWORD_CATEGORIES:
        values = search_keywords[category]

        if not isinstance(values, list):
            raise ValueError(f"Invalid keyword list: {category}")

        for value in values:
            if not isinstance(value, str) or not value.strip():
                raise ValueError("Empty or invalid search keyword.")

            key = " ".join(value.split()).casefold()

            if key in normalized:
                raise ValueError("Duplicate search keyword.")

            normalized.add(key)
            total_keywords += 1

    if total_keywords == 0 or total_keywords > 8:
        raise ValueError("Expected between 1 and 8 search keywords.")

    if not isinstance(max_results, int) or not 1 <= max_results <= 50:
        raise ValueError("max_results must be between 1 and 50.")

    if not api_key:
        raise ValueError("YouTube API key is missing.")

    # Search stops once five unique videos have been collected.
    videos = search_videos(
        api_key=api_key,
        keyword_data=search_keywords,
        max_results=min(max_results, 5)
    )

    saved_path = save_video_search_results(
        videos=videos,
        project_dir=project_dir,
        search_keywords=search_keywords
    )

    return {
        "status": "completed",
        "output_path": str(saved_path),
        "api_requests": total_keywords,
        "estimated_quota_units": total_keywords * 100,
        "video_count": len(videos)
    }


def run_project_video_search_safely(
    api_key,
    project_dir,
    max_results=5
):
    """Prevent concurrent YouTube searches for the same project."""

    import os
    from pathlib import Path

    project_dir = Path(project_dir)

    if not project_dir.is_dir():
        raise ValueError("Project directory does not exist.")

    if not (project_dir / "project_info.json").is_file():
        raise ValueError("Project metadata is missing.")

    analysis_dir = project_dir / "youtube_analysis"
    analysis_dir.mkdir(parents=True, exist_ok=True)

    output_path = analysis_dir / "youtube_search_results.json"
    lock_path = analysis_dir / ".youtube_search.lock"

    if output_path.exists():
        return {
            "status": "already_exists",
            "output_path": str(output_path),
            "api_requests": 0
        }

    # Atomic exclusive creation: only one process gets the lock.
    try:
        fd = os.open(
            str(lock_path),
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600
        )
    except FileExistsError:
        return {
            "status": "already_running",
            "api_requests": 0
        }

    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(str(os.getpid()))

        # Check again after acquiring the lock.
        if output_path.exists():
            return {
                "status": "already_exists",
                "output_path": str(output_path),
                "api_requests": 0
            }

        return run_project_video_search(
            api_key=api_key,
            project_dir=project_dir,
            max_results=max_results
        )

    finally:
        lock_path.unlink(missing_ok=True)
