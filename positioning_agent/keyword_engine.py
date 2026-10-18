
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
