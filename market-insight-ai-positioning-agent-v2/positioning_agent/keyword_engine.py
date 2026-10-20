
import json

def build_keyword_prompt(product_info):
    return f"""
당신은 한국 뷰티 시장조사 전문 AI Agent입니다.

다음 제품 정보를 바탕으로 YouTube 시장조사용
한국어 검색 키워드를 생성하세요.

제품 정보:
{json.dumps(product_info, ensure_ascii=False, indent=2)}

다음 네 가지 범주별로 키워드를 5개씩 생성하세요.

1. market_keywords:
   시장 전체의 트렌드와 제품 카테고리 탐색

2. consumer_need_keywords:
   소비자 고민, 니즈, 불만 및 구매 기준 탐색

3. own_product_keywords:
   입력된 브랜드와 제품 관련 검색

4. competitor_keywords:
   유사 기능 및 제품군 탐색

규칙:
- 실제 소비자가 YouTube에서 검색할 법한 자연스러운 표현 사용
- 입력 정보에 없는 성분이나 효능을 사실처럼 단정하지 말 것
- 경쟁 브랜드나 제품명을 임의로 만들어내지 말 것
- 네 범주 간 중복 최소화
- 결과는 반드시 JSON 객체로 반환

출력 형식:
{{
    "market_keywords": [],
    "consumer_need_keywords": [],
    "own_product_keywords": [],
    "competitor_keywords": []
}}
"""


KEYWORD_SELECTION_COUNTS = {
    "market_keywords": 2,
    "consumer_need_keywords": 3,
    "own_product_keywords": 2,
    "competitor_keywords": 1
}


def select_search_keywords(keyword_data, product_info=None):
    """Deterministically select up to 8 unique search keywords."""

    if not isinstance(keyword_data, dict):
        raise TypeError("keyword_data must be a dictionary.")

    selected = {
        category: []
        for category in KEYWORD_SELECTION_COUNTS
    }

    seen = set()

    for category, limit in KEYWORD_SELECTION_COUNTS.items():
        values = keyword_data.get(category)

        if not isinstance(values, list):
            raise ValueError(f"Invalid keyword category: {category}")

        if category == "own_product_keywords" and product_info is not None:
            values = rank_own_product_keywords(values, product_info)

        for value in values:
            if not isinstance(value, str):
                raise ValueError("Keywords must be strings.")

            keyword = " ".join(value.split())

            if not keyword:
                continue

            normalized = keyword.casefold()

            if normalized in seen:
                continue

            seen.add(normalized)
            selected[category].append(keyword)

            if len(selected[category]) >= limit:
                break

    return selected


def rank_own_product_keywords(keywords, product_info):
    """Rank own-product keywords by exact product relevance."""

    if not isinstance(keywords, list):
        raise TypeError("keywords must be a list.")

    if not isinstance(product_info, dict):
        raise TypeError("product_info must be a dictionary.")

    brand = str(product_info.get("brand") or "").strip().casefold()
    product = str(product_info.get("product_name") or "").strip().casefold()

    review_terms = ("후기", "리뷰", "내돈내산", "사용후기")

    def score(keyword):
        text = keyword.casefold()

        has_brand = bool(brand) and brand in text
        has_product = bool(product) and product in text
        has_review = any(term in text for term in review_terms)

        if has_brand and has_product:
            return 4
        if has_product and has_review:
            return 3
        if has_product:
            return 2
        if has_brand:
            return 1
        return 0

    return sorted(keywords, key=score, reverse=True)


def generate_and_select_keywords(
    api_key,
    product_info,
    model_name="gemini-3.8-flash"
):
    """Generate and select search keywords with Gemini."""

    import json
    from google import genai
    from google.genai import types

    if not isinstance(api_key, str) or not api_key.strip():
        raise ValueError("Gemini API key is required.")

    if not isinstance(product_info, dict) or not product_info:
        raise ValueError("Valid product information is required.")

    prompt = build_keyword_prompt(product_info)

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            temperature=0
        )
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    generated = json.loads(response.text)

    if not isinstance(generated, dict):
        raise ValueError("Keyword response must be a JSON object.")

    expected_categories = {
        "market_keywords",
        "consumer_need_keywords",
        "own_product_keywords",
        "competitor_keywords"
    }

    if set(generated) != expected_categories:
        raise ValueError("Unexpected keyword categories.")

    for category in expected_categories:
        values = generated[category]

        if (
            not isinstance(values, list)
            or len(values) != 5
            or any(
                not isinstance(value, str) or not value.strip()
                for value in values
            )
        ):
            raise ValueError(
                f"Invalid generated keywords: {category}"
            )

    selected = select_search_keywords(
        generated,
        product_info=product_info
    )

    # Improve overly broad own-product queries.
    improvement = improve_own_product_search_keywords(
        selected["own_product_keywords"],
        product_info,
        limit=KEYWORD_SELECTION_COUNTS["own_product_keywords"]
    )

    selected["own_product_keywords"] = improvement["keywords"]

    # Keep selected keyword counts and provenance explicit.
    keyword_quality = {
        "own_product_keyword_sources": improvement["keyword_sources"],
        "own_product_review_required": improvement["review_required"],
        "selection_method": "deterministic_with_product_query_improvement"
    }

    return {
        "model": model_name,
        "keyword_quality": keyword_quality,
        "generated_keywords": generated,
        "search_keywords": selected,
        "generated_count": sum(
            len(values) for values in generated.values()
        ),
        "selected_count": sum(
            len(values) for values in selected.values()
        )
    }


def assess_own_product_keyword_quality(keywords, product_info):
    """Flag weak own-product queries without changing the input."""

    if not isinstance(keywords, list):
        raise TypeError("keywords must be a list.")

    if not isinstance(product_info, dict):
        raise TypeError("product_info must be a dictionary.")

    brand = str(product_info.get("brand") or "").strip().casefold()
    product = str(product_info.get("product_name") or "").strip().casefold()

    if not brand or not product:
        raise ValueError("Brand and product name are required.")

    results = []

    for keyword in keywords:
        if not isinstance(keyword, str) or not keyword.strip():
            raise ValueError("Invalid keyword.")

        text = " ".join(keyword.split()).casefold()

        has_product = product in text
        has_brand = brand in text

        # Exact product name is the preferred signal.
        if has_product:
            status = "specific_product_query"
        elif has_brand:
            status = "brand_only_or_broad_query"
        else:
            status = "product_link_unconfirmed"

        results.append({
            "keyword": keyword,
            "quality_status": status,
            "requires_review": status != "specific_product_query"
        })

    return {
        "results": results,
        "all_specific": all(
            not item["requires_review"] for item in results
        ),
        "review_count": sum(
            item["requires_review"] for item in results
        )
    }


def improve_own_product_search_keywords(keywords, product_info, limit=2):
    """Keep specific queries and transparently supplement missing ones."""

    if not isinstance(keywords, list):
        raise TypeError("keywords must be a list.")

    if not isinstance(product_info, dict):
        raise TypeError("product_info must be a dictionary.")

    if not isinstance(limit, int) or isinstance(limit, bool) or limit < 1:
        raise ValueError("limit must be a positive integer.")

    brand = str(product_info.get("brand") or "").strip()
    product = str(product_info.get("product_name") or "").strip()

    if not brand or not product:
        raise ValueError("Brand and product name are required.")

    selected = []
    sources = []
    seen = set()

    for keyword in keywords:
        if not isinstance(keyword, str):
            raise TypeError("Keywords must be strings.")

        cleaned = " ".join(keyword.split())
        normalized = cleaned.casefold()

        if not cleaned or normalized in seen:
            continue

        if product.casefold() not in normalized:
            continue

        selected.append(cleaned)
        sources.append("ai_generated")
        seen.add(normalized)

        if len(selected) == limit:
            break

    # Only user-provided brand/product information is used.
    fallback_candidates = [
        f"{brand} {product} 후기",
        f"{product} 후기",
        f"{brand} {product}"
    ]

    for keyword in fallback_candidates:
        if len(selected) >= limit:
            break

        normalized = keyword.casefold()

        if normalized not in seen:
            selected.append(keyword)
            sources.append("rule_generated")
            seen.add(normalized)

    return {
        "keywords": selected,
        "keyword_sources": sources,
        "count": len(selected),
        "review_required": any(
            source == "rule_generated" for source in sources
        )
    }


def save_keyword_generation(result, project_dir):
    """Save validated keyword-generation results within one project."""

    import json
    from pathlib import Path

    if not isinstance(result, dict):
        raise TypeError("result must be a dictionary.")

    generated = result.get("generated_keywords")
    selected = result.get("search_keywords")
    quality = result.get("keyword_quality")

    if not isinstance(generated, dict):
        raise ValueError("Generated keywords are missing.")

    if not isinstance(selected, dict):
        raise ValueError("Search keywords are missing.")

    if not isinstance(quality, dict):
        raise ValueError("Keyword quality information is missing.")

    categories = set(KEYWORD_SELECTION_COUNTS)

    if set(generated) != categories or set(selected) != categories:
        raise ValueError("Unexpected keyword categories.")

    for category in categories:
        values = generated[category]
        chosen = selected[category]

        if (
            not isinstance(values, list)
            or len(values) != 5
            or not all(
                isinstance(v, str) and v.strip()
                for v in values
            )
        ):
            raise ValueError(f"Invalid generated keywords: {category}")

        if (
            not isinstance(chosen, list)
            or len(chosen) > KEYWORD_SELECTION_COUNTS[category]
            or not all(
                isinstance(v, str) and v.strip()
                for v in chosen
            )
        ):
            raise ValueError(f"Invalid selected keywords: {category}")

    generated_count = sum(len(v) for v in generated.values())
    selected_count = sum(len(v) for v in selected.values())

    if result.get("generated_count") != generated_count:
        raise ValueError("Generated keyword count mismatch.")

    if result.get("selected_count") != selected_count:
        raise ValueError("Selected keyword count mismatch.")

    project_dir = Path(project_dir)

    if not project_dir.is_dir():
        raise ValueError("Project directory does not exist.")

    if not (project_dir / "project_info.json").is_file():
        raise ValueError("Valid project metadata is required.")

    output_dir = project_dir / "youtube_analysis"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / "keyword_generation.json"

    # Exclusive creation protects existing analysis results.
    with output_path.open("x", encoding="utf-8") as f:
        json.dump(
            {
                "model": result.get("model"),
                "generated_keywords": generated,
                "search_keywords": selected,
                "keyword_quality": quality,
                "generated_count": generated_count,
                "selected_count": selected_count
            },
            f,
            ensure_ascii=False,
            indent=2
        )

    return output_path
