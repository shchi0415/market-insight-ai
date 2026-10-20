
import json
import time
from pathlib import Path

import pandas as pd
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.1-flash-lite"
BATCH_SIZE = 20

VALIDATION_LABELS = [
    "직접 근거",
    "부분 근거",
    "근거 부족"
]

OUTPUT_COLUMNS = [
    "comment_key",
    "postUrl",
    "text",
    "relevance",
    "type",
    "sentiment",
    "concern",
    "insight",
    "market_relevance",
    "validation",
    "corrected_insight",
    "reason",
    "analysis_version"
]


def build_validation_prompt(records):
    instruction = """
너는 한국 스킨케어 시장조사의 소비자 인사이트 검증 담당자야.

각 댓글에 대해 두 단계로 판단해.

[1단계: 시장 관련성]
market_relevance:
- 관련: 스킨케어 제품, 피부 고민, 성분, 제형, 사용 경험 등과 관련된 소비자 발언
- 무관: 색조 화장품, 인플루언서 외모, 팬밋업, 이벤트 반응 등
- 불확실: 맥락이 부족해 관련성을 판단하기 어려운 댓글

스킨케어와 관련된 브랜드라는 이유만으로
모든 댓글을 '관련'으로 판단하지 마.

[2단계: 인사이트 근거 검증]
validation:
- 직접 근거: AI 인사이트의 핵심 내용이 댓글에 명시됨
- 부분 근거: 일부 근거는 있으나 과장이나 추론이 포함됨
- 근거 부족: 댓글에 근거가 없거나 시장 분석에 부적절함

[중요 규칙]
1. 스킨케어 무관 댓글은 validation을 '근거 부족'으로 지정.
2. 원문에 없는 피부 고민이나 제품 효능을 만들어내지 마.
3. '궁금하다', '메모한다'는 관심 표현이지 구매 확정이 아님.
4. '써봐야겠다'는 사용 의향이지 실제 구매 또는 사용 경험이 아님.
5. 실제 사용 후기가 아니라면 효능 체감으로 해석하지 마.
6. 다른 사람의 피부 고민을 댓글 작성자 본인의 고민으로 해석하지 마.
7. 댓글과 AI 인사이트가 완전히 일치하더라도
   스킨케어와 무관하면 최종 인사이트에서 제외.
8. 댓글이 모호하면 보수적으로 판단.
9. 게시물 캡션은 소비자가 직접 말한 내용이 아님.
10. 모든 입력 ID를 정확히 한 번씩 반환.

[반환 필드]
- id: 입력 ID
- market_relevance: 관련 / 무관 / 불확실
- validation: 직접 근거 / 부분 근거 / 근거 부족
- corrected_insight: 실제 댓글에 근거한 수정 인사이트
- reason: 판정 이유

market_relevance가 '무관' 또는 '불확실'이면
corrected_insight는 '구체적 인사이트 없음'으로 작성해.

반드시 아래 형식의 JSON 객체만 반환:
{
  "results": [
    {
      "id": 0,
      "market_relevance": "관련",
      "validation": "직접 근거",
      "corrected_insight": "원문으로 확인되는 소비자 인사이트",
      "reason": "판정 근거"
    }
  ]
}

데이터:
"""
    return instruction + json.dumps(records, ensure_ascii=False)


def validate_insights(
    analysis_path,
    output_path,
    api_key,
    max_batches=1,
    progress_callback=None
):
    analysis_path = Path(analysis_path)
    output_path = Path(output_path)

    data = pd.read_csv(analysis_path, low_memory=False)

    required = {
        "comment_key", "postUrl", "text",
        "relevance", "type", "sentiment",
        "concern", "insight"
    }

    missing = required - set(data.columns)
    if missing:
        raise ValueError(f"필수 컬럼 누락: {missing}")

    # 실제 스킨케어 관련 인사이트 후보만 검증
    candidates = data[
        (data["relevance"] == "관련")
        & data["type"].isin([
            "사용 후기",
            "소비자 니즈",
            "구매 관심"
        ])
        & data["insight"].notna()
        & (data["insight"] != "구체적 인사이트 없음")
    ].copy()

    candidates = candidates.drop_duplicates(
        subset=["comment_key"],
        keep="last"
    ).reset_index(drop=True)

    if output_path.exists():
        saved = pd.read_csv(output_path, low_memory=False)

        if "comment_key" not in saved.columns:
            raise ValueError(
                "저장된 검증 결과에 comment_key 컬럼이 없습니다."
            )

        saved = saved.drop_duplicates(
            subset=["comment_key"],
            keep="last"
        )
    else:
        saved = pd.DataFrame(columns=OUTPUT_COLUMNS)

    # 통합 데이터가 변경되면 기존 검증 결과를 재사용하지 않도록
    # 동일한 인사이트·분류·원문일 때만 재사용
    compare_cols = [
        "comment_key", "text", "insight",
        "relevance", "type", "concern"
    ]

    if len(saved):
        previous = saved[compare_cols].fillna("").copy()
        previous["_saved"] = True

        matched = candidates.merge(
            previous,
            on=compare_cols,
            how="left"
        )

        completed_keys = set(
            matched.loc[
                matched["_saved"] == True,
                "comment_key"
            ]
        )

        saved = saved[
            saved["comment_key"].isin(completed_keys)
        ].copy()
    else:
        completed_keys = set()

    pending = candidates[
        ~candidates["comment_key"].isin(completed_keys)
    ].copy()

    if progress_callback:
        progress_callback(
            len(completed_keys),
            len(candidates)
        )

    if pending.empty:
        return saved

    if not api_key:
        raise ValueError("Gemini API 키가 없습니다.")

    client = genai.Client(api_key=api_key)

    batches_completed = 0

    for start in range(0, len(pending), BATCH_SIZE):

        if max_batches is not None:
            if batches_completed >= max_batches:
                break

        batch = pending.iloc[start:start + BATCH_SIZE]

        records = [
            {
                "id": i,
                "comment": row["text"],
                "insight": row["insight"],
                "type": row["type"],
                "concern": row["concern"]
            }
            for i, (_, row) in enumerate(batch.iterrows())
        ]

        response_data = None
        last_error = None

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=build_validation_prompt(records),
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
                f"검증 배치 실패: {last_error}"
            )

        result_map = {
            item.get("id"): item
            for item in response_data.get("results", [])
            if isinstance(item, dict)
        }

        new_rows = []

        for i, (_, row) in enumerate(batch.iterrows()):
            item = result_map.get(i)

            if not item:
                continue

            if item.get("validation") not in VALIDATION_LABELS:
                continue

            if item.get("market_relevance") not in [
                "관련", "무관", "불확실"
            ]:
                continue

            if item["market_relevance"] != "관련":
                item["validation"] = "근거 부족"

            corrected = str(
                item.get("corrected_insight", "")
            ).strip()

            if item["validation"] == "근거 부족":
                corrected = "구체적 인사이트 없음"

            output_row = {
                col: row.get(col, "")
                for col in OUTPUT_COLUMNS
                if col not in [
                    "market_relevance",
                    "validation",
                    "corrected_insight",
                    "reason"
                ]
            }

            output_row.update({
                "market_relevance": item["market_relevance"],
                "validation": item["validation"],
                "corrected_insight": corrected,
                "reason": str(item.get("reason", ""))
            })

            new_rows.append(output_row)

        if new_rows:
            saved = pd.concat(
                [saved, pd.DataFrame(new_rows)],
                ignore_index=True
            ).drop_duplicates(
                subset=["comment_key"],
                keep="last"
            )

            output_path.parent.mkdir(
                parents=True,
                exist_ok=True
            )

            saved.to_csv(
                output_path,
                index=False,
                encoding="utf-8-sig"
            )

        batches_completed += 1

        if progress_callback:
            progress_callback(
                len(completed_keys) + min(
                    batches_completed * BATCH_SIZE,
                    len(pending)
                ),
                len(candidates)
            )

    return saved
