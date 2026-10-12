
import json
import time
from pathlib import Path

import pandas as pd
from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.1-flash-lite"
BATCH_SIZE = 20

BEHAVIOR_LABELS = [
    "호기심", "정보 저장", "사용 의향",
    "구매 의향", "실제 구매", "사용 경험",
    "행동 확인 불가"
]

VALIDATION_LABELS = [
    "직접 근거", "부분 근거", "근거 부족"
]

RELEVANCE_LABELS = ["관련", "무관", "불확실"]

OUTPUT_COLUMNS = [
    "comment_key", "postUrl", "text",
    "relevance", "type", "sentiment",
    "concern", "insight", "analysis_version",
    "market_relevance", "behavior_stage",
    "validation", "overclaim_detected",
    "corrected_insight", "evidence_quote", "reason"
]


def build_prompt(records):
    rules = """
너는 한국 스킨케어 소비자 리서치의 엄격한 근거 검증자야.

각 댓글을 원문만 기준으로 평가해.
AI가 작성한 기존 인사이트는 검증 대상이지 사실이 아니야.

[1. 시장 관련성]
market_relevance:
- 관련: 스킨케어, 피부 고민, 스킨케어 사용/구매 관련
- 무관: 색조 화장품, 인플루언서 외모, 이벤트 등
- 불확실: 맥락 부족으로 판단 어려움

[2. 소비자 행동 단계]
behavior_stage:
- 호기심: 궁금함, 관심, 긍정적인 감상
- 정보 저장: 메모, 저장, 북마크
- 사용 의향: 앞으로 사용하거나 시도할 생각
- 구매 의향: 직접 구매하거나 주문하겠다는 명시적 의사
- 실제 구매: 구매 또는 주문을 이미 완료함
- 사용 경험: 실제로 사용한 사실이 명시됨
- 행동 확인 불가: 위 행동을 확인할 수 없음

주의:
- '메모할게요'는 구매 의향이 아니다.
- '써봐야겠어요'는 실제 사용 경험이 아니다.
- '찾았다'는 효능 체감이 아니다.
- '좋네요'만으로 실제 사용했다고 판단하지 마.
- 타인을 위한 추천과 본인의 구매를 구분해.
- 제품을 칭찬했다고 실제 제품 사용 만족도를 추론하지 마.
- 여러 행동이 있으면 원문이 명시하는 가장 구체적인
  행동을 선택하되, 명시되지 않은 행동을 추측하지 마.

[3. 근거 검증]
validation:
- 직접 근거: 기존 AI 인사이트의 모든 핵심 주장이 원문에 명시됨
- 부분 근거: 일부는 맞지만 구매/사용/효능 등 과장 또는 추론이 있음
- 근거 부족: 근거를 확인할 수 없거나 시장과 무관함

overclaim_detected:
- true: 인사이트에 원문에 없는 구매, 사용, 효능, 피부 고민,
  구매 이유, 감정 또는 행동을 추가한 경우
- false: 그런 과장이 없는 경우

검증 규칙:
- market_relevance가 무관 또는 불확실이면
  validation은 반드시 근거 부족으로 처리.
- 인사이트에 과장이 있으면 직접 근거 판정 금지.
- 실제 사용이 없는데 효능 체감이라고 썼으면
  반드시 overclaim_detected=true.
- 구매 언급이 없는데 구매 계획으로 썼으면
  반드시 overclaim_detected=true.
- corrected_insight는 원문에서 확인되는 내용만
  짧고 정확하게 작성.
- 무관한 댓글은 corrected_insight를
  '구체적 인사이트 없음'으로 작성.
- evidence_quote는 원문에서 직접 가져온 짧은 근거.
  원문에 없는 문장을 만들어내지 마.
- 원문만으로 판단 불가능하면 보수적으로 판정.
- 모든 입력 ID를 정확히 한 번씩 반환.

반드시 JSON 객체로 반환:
{
  "results": [
    {
      "id": 0,
      "market_relevance": "관련",
      "behavior_stage": "정보 저장",
      "validation": "부분 근거",
      "overclaim_detected": true,
      "corrected_insight": "향후 참고를 위해 제품 정보를 메모함",
      "evidence_quote": "메모하고 갈게요",
      "reason": "원문에는 구매 계획이 명시되지 않음"
    }
  ]
}

검증할 데이터:
"""
    return rules + json.dumps(records, ensure_ascii=False)


def validate_insights_v4(
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

    # 기존 관련성 판단이 틀릴 수 있으므로
    # 관련 댓글의 인사이트 후보를 독립적으로 재검증
    candidates = data[
        (data["relevance"] == "관련")
        & data["type"].isin([
            "사용 후기", "소비자 니즈", "구매 관심"
        ])
        & data["insight"].notna()
        & (data["insight"] != "구체적 인사이트 없음")
    ].copy()

    candidates = candidates.drop_duplicates(
        subset=["comment_key"],
        keep="last"
    ).reset_index(drop=True)

    # 이전 실행 결과 재사용
    if output_path.exists():
        saved = pd.read_csv(output_path, low_memory=False)

        if "comment_key" not in saved.columns:
            raise ValueError("기존 결과에 comment_key가 없습니다.")

        saved = saved.drop_duplicates(
            subset=["comment_key"], keep="last"
        )
    else:
        saved = pd.DataFrame(columns=OUTPUT_COLUMNS)

    # 원문과 검증 대상 인사이트가 동일할 때만 이전 결과 사용
    compare_cols = [
        "comment_key", "text", "insight",
        "relevance", "type", "concern"
    ]

    if not saved.empty:
        previous = saved[compare_cols].fillna("").copy()
        previous["_completed"] = True

        matched = candidates.merge(
            previous,
            on=compare_cols,
            how="left"
        )

        completed_keys = set(
            matched.loc[
                matched["_completed"] == True,
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

    total = len(candidates)

    if progress_callback:
        progress_callback(len(completed_keys), total)

    if pending.empty:
        return saved

    if not api_key:
        raise ValueError("Gemini API 키가 없습니다.")

    client = genai.Client(api_key=api_key)

    completed_batches = 0

    for start in range(0, len(pending), BATCH_SIZE):
        if (
            max_batches is not None
            and completed_batches >= max_batches
        ):
            break

        batch = pending.iloc[start:start + BATCH_SIZE]

        records = []
        for i, (_, row) in enumerate(batch.iterrows()):
            records.append({
                "id": i,
                "comment": str(row["text"]),
                "ai_insight": str(row["insight"]),
                "type": str(row["type"]),
                "concern": str(row["concern"])
            })

        response_data = None
        last_error = None

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=build_prompt(records),
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
                f"검증 실패: {last_error}"
            )

        result_map = {
            item.get("id"): item
            for item in response_data.get("results", [])
            if isinstance(item, dict)
        }

        new_rows = []

        for i, (_, row) in enumerate(batch.iterrows()):
            item = result_map.get(i)

            if item is None:
                continue

            if item.get("market_relevance") not in RELEVANCE_LABELS:
                continue
            if item.get("behavior_stage") not in BEHAVIOR_LABELS:
                continue
            if item.get("validation") not in VALIDATION_LABELS:
                continue
            if not isinstance(item.get("overclaim_detected"), bool):
                continue

            # AI 응답을 그대로 신뢰하지 않고 기본 일관성 강제
            if item["market_relevance"] != "관련":
                item["validation"] = "근거 부족"

            if (
                item["overclaim_detected"]
                and item["validation"] == "직접 근거"
            ):
                item["validation"] = "부분 근거"

            corrected = str(
                item.get("corrected_insight", "")
            ).strip()

            if item["market_relevance"] != "관련":
                corrected = "구체적 인사이트 없음"

            evidence = str(
                item.get("evidence_quote", "")
            ).strip()

            # 실제 원문에 없는 인용은 인정하지 않음
            if evidence and evidence not in str(row["text"]):
                evidence = ""

            output_row = {
                col: row.get(col, "")
                for col in OUTPUT_COLUMNS
                if col not in [
                    "market_relevance", "behavior_stage",
                    "validation", "overclaim_detected",
                    "corrected_insight", "evidence_quote", "reason"
                ]
            }

            output_row.update({
                "market_relevance": item["market_relevance"],
                "behavior_stage": item["behavior_stage"],
                "validation": item["validation"],
                "overclaim_detected": item["overclaim_detected"],
                "corrected_insight": corrected,
                "evidence_quote": evidence,
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
                parents=True, exist_ok=True
            )
            saved.to_csv(
                output_path,
                index=False,
                encoding="utf-8-sig"
            )

        completed_batches += 1

        if progress_callback:
            progress_callback(
                min(
                    len(completed_keys)
                    + completed_batches * BATCH_SIZE,
                    total
                ),
                total
            )

    return saved
