
import json
from pathlib import Path

from google import genai
from google.genai import types

MODEL_NAME = "gemini-3.1-flash-lite"


def generate_strategy(
    strategy_input_path,
    output_path,
    api_key
):
    strategy_input_path = Path(strategy_input_path)
    output_path = Path(output_path)

    with open(strategy_input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if not api_key:
        raise ValueError("Gemini API 키가 없습니다.")

    prompt = """
너는 뷰티 산업 전문 시장조사 및 마케팅 전략 컨설턴트야.

제공된 Instagram 시장조사 데이터와 소비자 인사이트를 바탕으로
신규 브랜드의 시장 진입 전략을 제안해.

[핵심 원칙]
1. 특정 제품이나 포지셔닝을 사전에 정하지 않는다.
2. 데이터로 확인된 사실과 전략적 가설을 명확히 구분한다.
3. 인사이트 근거가 부족하면 확정적 결론을 내리지 않는다.
4. 인스타그램 댓글의 언급량을 시장 전체 수요로 해석하지 않는다.
5. 보습 관련 댓글이 많다는 이유만으로 시장 기회가
   가장 크다고 단정하지 않는다.
6. 경쟁 강도, 시장 규모, 실제 구매전환율 등
   제공되지 않은 수치는 만들어내지 않는다.
7. 구매 의향과 실제 구매를 구분한다.
8. 전략에는 반드시 추가 검증 방법을 포함한다.
9. 근거는 입력 데이터의 comment_key를 그대로 참조한다.
10. 제공된 데이터 이외의 사실을 근거로 제시하지 않는다.

[출력 형식]
다음 JSON 객체를 생성해.

{
  "executive_summary": "핵심 전략 요약",
  "market_findings": [
    {
      "finding": "데이터에서 관찰된 현상",
      "interpretation": "가능한 해석",
      "limitation": "해석의 한계"
    }
  ],
  "opportunities": [
    {
      "name": "시장 기회 가설",
      "target_customer": "가설적 핵심 고객",
      "consumer_problem": "해결하려는 소비자 문제",
      "value_proposition": "제안 가치",
      "positioning": "차별화 포지셔닝",
      "evidence_keys": ["근거 comment_key"],
      "confidence": "높음/중간/낮음",
      "uncertainty": "추가로 확인할 사항"
    }
  ],
  "recommended_strategy": {
    "targeting": "초기 고객 세그먼트 가설",
    "positioning": "포지셔닝 가설",
    "product_direction": "제품 방향성",
    "messaging": "핵심 메시지",
    "channel_strategy": "채널 전략 가설",
    "execution_plan": [
      {
        "action": "실행할 활동",
        "purpose": "실행 목적",
        "kpi": "측정 지표"
      }
    ]
  },
  "validation_experiments": [
    {
      "hypothesis": "검증할 가설",
      "experiment": "실험 방법",
      "metric": "측정 지표",
      "decision_rule": "가설 채택 또는 기각 기준의 설정 방법"
    }
  ],
  "limitations": ["데이터 및 전략 한계"]
}

[추가 지침]
- opportunities는 정확히 3개 작성.
- 각 기회에 데이터 내 실제 comment_key 1개 이상 연결.
- 근거가 약한 기회에는 confidence를 '낮음'으로 설정.
- 경쟁사 분석이 없다면 경쟁우위가 입증됐다고 말하지 마.
- 실험의 수치 목표는 근거 없이 단정하지 마.
- 반드시 한국어로 작성.
- JSON 외의 설명은 출력하지 마.

[분석 데이터]
""" + json.dumps(data, ensure_ascii=False)

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )

    result = json.loads(response.text)

    # 근거 ID가 실제 입력 데이터에 존재하는지 검증
    valid_keys = {
        item["comment_key"]
        for item in data.get("evidence", [])
    }

    for opportunity in result.get("opportunities", []):
        cited_keys = opportunity.get("evidence_keys", [])

        opportunity["evidence_keys"] = [
            key for key in cited_keys
            if key in valid_keys
        ]

        if not opportunity["evidence_keys"]:
            opportunity["confidence"] = "낮음"
            opportunity["uncertainty"] = (
                str(opportunity.get("uncertainty", ""))
                + " / 확인 가능한 직접 근거 없음"
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            result,
            f,
            ensure_ascii=False,
            indent=2
        )

    return result
