
import json
import time
import hashlib
from pathlib import Path

import pandas as pd
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.1-flash-lite"
BATCH_SIZE = 20

LABELS = {
    "relevance": ["관련", "무관", "불확실"],
    "type": [
        "사용 후기", "소비자 니즈", "구매 관심",
        "광고·이벤트", "단순 반응", "기타"
    ],
    "sentiment": [
        "긍정", "중립", "부정", "혼합", "판단불가"
    ],
    "concern": [
        "트러블", "보습·장벽", "모공·피지",
        "탄력", "미백·잡티", "민감성",
        "기타", "없음"
    ]
}

def comment_key(post_url, text):
    content = (
        str(post_url).strip().rstrip("/")
        + "\n"
        + str(text).strip()
    )
    return hashlib.sha256(
        content.encode("utf-8")
    ).hexdigest()

def build_prompt(records):
    return """
너는 한국 스킨케어 시장 소비자 리서치 분석가야.

아래 댓글을 하나씩 분류해.

반환 필드:
- id: 입력 ID
- relevance: 관련 / 무관 / 불확실
- type: 사용 후기 / 소비자 니즈 / 구매 관심 / 광고·이벤트 / 단순 반응 / 기타
- sentiment: 긍정 / 중립 / 부정 / 혼합 / 판단불가
- concern: 트러블 / 보습·장벽 / 모공·피지 / 탄력 / 미백·잡티 / 민감성 / 기타 / 없음
- insight: 댓글에서 직접 확인할 수 있는 핵심 내용

판단 규칙:
1. 스킨케어 소비자 반응과 무관하면 relevance는 '무관'.
2. 색조 화장품, 모델 외모, 팬밋업, 단순 응원은 스킨케어 분석에서 제외.
3. 실제 사용 경험이 명시되어야만 '사용 후기'로 분류.
4. 게시물 캡션은 맥락 파악에만 사용. 댓글에 없는 경험을 만들어내지 마.
5. 스킨케어 구매 관심과 실제 사용 경험을 구분.
6. insight는 추측하지 말고 댓글에 확인되는 내용만 기록.
7. 무관한 댓글의 insight는 '구체적 인사이트 없음'.
8. 정해진 라벨 이외의 값을 만들지 마.
9. 입력 ID를 모두 정확히 한 번씩 반환.

반드시 아래 JSON 객체 형식으로 출력:
{"results": [
  {"id": 0, "relevance": "관련", "type": "사용 후기",
   "sentiment": "긍정", "concern": "보습·장벽",
   "insight": "보습 지속력에 대한 긍정적인 사용 경험"}
]}

데이터:
""" + json.dumps(records, ensure_ascii=False)

def analyze_comments(
    merged_path,
    output_path,
    api_key,
    progress_callback=None,
    max_batches=None
):
    merged_path = Path(merged_path)
    output_path = Path(output_path)

    data = pd.read_csv(merged_path, low_memory=False)

    required = {"postUrl", "text"}
    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"필수 컬럼 누락: {missing}")

    data = data.dropna(subset=["postUrl", "text"]).copy()
    data["postUrl"] = data["postUrl"].astype(str).str.strip().str.rstrip("/")
    data["text"] = data["text"].astype(str).str.strip()
    data = data[data["text"] != ""].copy()

    data["comment_key"] = [
        comment_key(p, t)
        for p, t in zip(data["postUrl"], data["text"])
    ]

    # 동일한 URL·내용의 댓글도 개별 행으로 보존
    data["duplicate_index"] = data.groupby(
        "comment_key"
    ).cumcount()

    data["comment_key"] = [
        hashlib.sha256(
            (str(key) + "|" + str(idx)).encode("utf-8")
        ).hexdigest()
        for key, idx in zip(
            data["comment_key"],
            data["duplicate_index"]
        )
    ]

    data = data.reset_index(drop=True)

    result_columns = [
        "comment_key", "postUrl", "text",
        "relevance", "type", "sentiment",
        "concern", "insight"
    ]

    if output_path.exists():
        saved = pd.read_csv(output_path, low_memory=False)

        # 이전 결과가 일부만 저장되었어도 이어서 진행
        if "comment_key" not in saved.columns:
            raise ValueError("기존 결과에 comment_key 컬럼이 없습니다.")

        saved = saved.drop_duplicates(subset=["comment_key"], keep="last")
    else:
        saved = pd.DataFrame(columns=result_columns)

    completed = set(saved["comment_key"].dropna().astype(str))
    pending = data[~data["comment_key"].isin(completed)].copy()

    total = len(data)
    already_done = total - len(pending)

    if progress_callback:
        progress_callback(already_done, total)

    if pending.empty:
        return saved

    if not api_key:
        raise ValueError("Gemini API 키가 없습니다.")

    client = genai.Client(api_key=api_key)

    batches_done = 0

    for start in range(0, len(pending), BATCH_SIZE):
        if max_batches is not None and batches_done >= max_batches:
            break

        batch = pending.iloc[start:start + BATCH_SIZE]

        records = []
        for idx, (_, row) in enumerate(batch.iterrows()):
            caption = row.get("post_caption", "")
            if pd.isna(caption):
                caption = ""

            records.append({
                "id": idx,
                "comment": row["text"],
                "caption": str(caption)[:500]
            })

        prompt = build_prompt(records)

        response_data = None
        last_error = None

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json"
                    )
                )
                response_data = json.loads(response.text)
                break
            except Exception as e:
                last_error = e
                if attempt < 2:
                    time.sleep(2 ** attempt)

        if response_data is None:
            raise RuntimeError(
                f"배치 분석 실패 (시작 행 {start}): {last_error}"
            )

        results = response_data.get("results", [])
        result_map = {
            item.get("id"): item
            for item in results
            if isinstance(item, dict)
        }

        new_rows = []

        for idx, (_, row) in enumerate(batch.iterrows()):
            item = result_map.get(idx)

            # 누락된 응답은 저장하지 않고 다음 실행에서 다시 분석
            if item is None:
                continue

            valid = True
            for field, allowed in LABELS.items():
                if item.get(field) not in allowed:
                    valid = False

            if not valid:
                continue

            new_rows.append({
                "comment_key": row["comment_key"],
                "postUrl": row["postUrl"],
                "text": row["text"],
                "relevance": item["relevance"],
                "type": item["type"],
                "sentiment": item["sentiment"],
                "concern": item["concern"],
                "insight": str(item.get("insight", ""))
            })

        if new_rows:
            saved = pd.concat(
                [saved, pd.DataFrame(new_rows)],
                ignore_index=True
            )
            saved = saved.drop_duplicates(
                subset=["comment_key"],
                keep="last"
            )

            output_path.parent.mkdir(parents=True, exist_ok=True)

            # 중간 결과를 배치마다 저장
            saved.to_csv(
                output_path,
                index=False,
                encoding="utf-8-sig"
            )

        batches_done += 1

        if progress_callback:
            progress_callback(
                already_done + min(
                    (batches_done * BATCH_SIZE),
                    len(pending)
                ),
                total
            )

    return saved
