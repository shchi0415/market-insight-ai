
"""Build grounded Gemini prompts for consumer topic interpretation."""

import json


def build_topic_interpretation_prompt(topic_data):
    """Create a topic interpretation prompt without calling an API."""

    if not isinstance(topic_data, dict):
        raise TypeError("topic_data must be a dictionary.")

    topics = topic_data.get("topics")

    if not isinstance(topics, list) or not topics:
        raise ValueError("topics must be a non-empty list.")

    data_json = json.dumps(
        topic_data,
        ensure_ascii=False,
        indent=2
    )

    return f"""
당신은 한국 뷰티 시장조사 분석가입니다.

다음 데이터는 YouTube 댓글의 BERTopic 군집화 결과입니다.
제공된 대표 단어와 집계 통계만 근거로 사용하세요.

[분석 데이터]
{data_json}

[분석 규칙]
1. 토픽 번호는 의미가 고정된 분류 코드가 아닙니다.
2. topic_id가 -1이면 미분류로 처리하세요.
3. 다음 중 하나의 category를 선택하세요.
   - consumer_need
   - product_experience
   - content_reaction
   - uncertain
4. 대표 단어만으로 소비자 의도나 구체적 경험을 확인할 수 없으면
   category를 uncertain으로 지정하세요.
5. 명확한 근거가 없는 구매 의도, 시장 규모, 감성, 제품 효능은
   만들어내지 마세요.
6. confidence는 high, medium, low 중 선택하세요.
   이는 통계적 신뢰도가 아니라 해석의 명확성입니다.
7. 특정 영상 편중과 표본 선정의 한계를 반영하세요.
8. 원본 댓글이 제공되지 않았으므로 실제 소비자 발언을
   인용하거나 만들어내지 마세요.
9. 모든 입력 토픽을 정확히 한 번씩 반환하세요.
10. 출력은 반드시 JSON 객체로 작성하세요.

[출력 형식]
{{
  "topics": [
    {{
      "topic_id": 0,
      "topic_name": "한국어 토픽명",
      "category": "consumer_need",
      "confidence": "medium",
      "interpretation": "근거에 기반한 짧은 해석",
      "supporting_keywords": ["키워드1", "키워드2"],
      "limitations": "해석의 한계",
      "requires_review": true
    }}
  ]
}}

출력 형식에 사용된 예시 값은 실제 분석 결과가 아닙니다.
"""


def validate_topic_interpretation(input_data, output_data):
    """Validate Gemini topic output structure and keyword references."""

    allowed_categories = {
        "consumer_need",
        "product_experience",
        "content_reaction",
        "uncertain"
    }

    allowed_confidence = {"high", "medium", "low"}

    if not isinstance(input_data, dict):
        raise TypeError("input_data must be a dictionary.")

    if not isinstance(output_data, dict):
        raise TypeError("output_data must be a dictionary.")

    input_topics = input_data.get("topics")
    output_topics = output_data.get("topics")

    if not isinstance(input_topics, list):
        raise ValueError("Input topics must be a list.")

    if not isinstance(output_topics, list):
        raise ValueError("Output topics must be a list.")

    input_ids = [t["topic_id"] for t in input_topics]
    output_ids = [t["topic_id"] for t in output_topics]

    if len(set(input_ids)) != len(input_ids):
        raise ValueError("Duplicate input topic IDs.")

    if len(set(output_ids)) != len(output_ids):
        raise ValueError("Duplicate output topic IDs.")

    if set(input_ids) != set(output_ids):
        raise ValueError("Input and output topic IDs do not match.")

    input_lookup = {
        t["topic_id"]: t for t in input_topics
    }

    for topic in output_topics:
        topic_id = topic["topic_id"]

        if topic.get("category") not in allowed_categories:
            raise ValueError(f"Invalid category: {topic_id}")

        if topic.get("confidence") not in allowed_confidence:
            raise ValueError(f"Invalid confidence: {topic_id}")

        if not isinstance(topic.get("requires_review"), bool):
            raise ValueError(f"Invalid review flag: {topic_id}")

        for field in [
            "topic_name",
            "interpretation",
            "limitations"
        ]:
            value = topic.get(field)

            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Invalid {field}: {topic_id}")

        keywords = topic.get("supporting_keywords")

        if not isinstance(keywords, list):
            raise ValueError(f"Invalid keywords: {topic_id}")

        allowed_keywords = set(
            input_lookup[topic_id].get("representative_keywords", [])
        )

        if not all(
            isinstance(word, str) and word in allowed_keywords
            for word in keywords
        ):
            raise ValueError(
                f"Unsupported evidence keyword: {topic_id}"
            )

    return True


def combine_topic_results(
    topic_summary,
    ai_input,
    ai_output,
    held_topics
):
    """Combine BERTopic statistics, AI interpretations, and held topics."""

    import copy

    validate_topic_interpretation(ai_input, ai_output)

    ai_lookup = {
        topic["topic_id"]: topic
        for topic in ai_output["topics"]
    }

    held_lookup = {
        topic["topic_id"]: topic
        for topic in held_topics
    }

    records = []

    for _, row in topic_summary.iterrows():
        topic_id = int(row["topic"])

        record = {
            "topic_id": topic_id,
            "comment_count": int(row["comment_count"]),
            "unique_video_count": int(row["unique_video_count"]),
            "max_video_share_pct": float(
                row["max_video_share_pct"]
            )
        }

        if topic_id == -1:
            record.update({
                "topic_name": "미분류",
                "category": "unclassified",
                "status": "excluded",
                "requires_review": True,
                "interpretation": None
            })

        elif topic_id in held_lookup:
            record.update({
                "topic_name": "판단 보류",
                "category": "uncertain",
                "status": "insufficient_evidence",
                "requires_review": True,
                "interpretation": None
            })

        elif topic_id in ai_lookup:
            interpretation = ai_lookup[topic_id]

            record.update({
                "topic_name": interpretation["topic_name"],
                "category": interpretation["category"],
                "status": "ai_interpreted",
                "confidence": interpretation["confidence"],
                "requires_review": interpretation["requires_review"],
                "interpretation": interpretation["interpretation"],
                "limitations": interpretation["limitations"],
                "supporting_keywords": copy.deepcopy(
                    interpretation["supporting_keywords"]
                )
            })

        else:
            raise ValueError(
                f"Unprocessed topic: {topic_id}"
            )

        records.append(record)

    return {
        "analysis_type": "youtube_consumer_topics",
        "analysis_stage": "exploratory",
        "sample": copy.deepcopy(
            ai_input["sample_context"]
        ),
        "topics": records
    }


def run_topic_interpretation(
    api_key,
    topic_summary,
    ai_input,
    held_topics,
    model_name="gemini-3.8-flash"
):
    """Run Gemini interpretation, validation, and result integration."""

    import json
    from google import genai
    from google.genai import types

    if not api_key:
        raise ValueError("Gemini API key is required.")

    if not ai_input.get("topics"):
        raise ValueError("No topics are ready for AI interpretation.")

    prompt = build_topic_interpretation_prompt(ai_input)

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0.1
        )
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    ai_output = json.loads(response.text)

    validate_topic_interpretation(
        ai_input,
        ai_output
    )

    final_result = combine_topic_results(
        topic_summary=topic_summary,
        ai_input=ai_input,
        ai_output=ai_output,
        held_topics=held_topics
    )

    return final_result
