
import json
import os
from google import genai
from google.genai import types


import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Market Insight AI",
    page_icon="📊",
    layout="wide"
)


# ===== STEP 29-2B: LOGIN GATE =====
import hashlib
import hmac

def verify_login(username, password):
    saved_username = st.secrets.get("LOGIN_USERNAME", "")
    saved_salt = st.secrets.get("LOGIN_SALT", "")
    saved_hash = st.secrets.get("LOGIN_PASSWORD_HASH", "")

    if not all([saved_username, saved_salt, saved_hash]):
        return False

    try:
        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(saved_salt),
            600_000
        )

        return (
            hmac.compare_digest(username, saved_username)
            and hmac.compare_digest(
                candidate_hash,
                bytes.fromhex(saved_hash)
            )
        )
    except (ValueError, TypeError):
        return False


if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.markdown(
        "<div style='height: 8vh'></div>",
        unsafe_allow_html=True
    )

    left, center, right = st.columns([1, 1.4, 1])

    with center:
        st.title("Market Insight AI")
        st.caption("AI 기반 시장 인사이트 플랫폼")
        st.divider()

        with st.form("login_form"):
            login_id = st.text_input("아이디")
            login_password = st.text_input(
                "비밀번호",
                type="password"
            )

            submitted = st.form_submit_button(
                "로그인",
                type="primary",
                use_container_width=True
            )

        if submitted:
            if verify_login(login_id, login_password):
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")

    st.stop()

with st.sidebar:
    st.caption("로그인 상태")
    st.write(st.secrets.get("LOGIN_USERNAME", "사용자"))

    if st.button("로그아웃", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

# ===== END LOGIN GATE =====

# ===== STEP 29-6B: DASHBOARD DESIGN SYSTEM =====
st.markdown("""
<style>

/* 메인 페이지 제목 */
section[data-testid="stMain"] h1 {
    font-size: 2.5rem;
    font-weight: 750;
    letter-spacing: -0.035em;
}

/* Project Overview 및 STEP 01~04 제목 */
section[data-testid="stMain"] h2 {
    font-size: 1.85rem;
    font-weight: 700;
    letter-spacing: -0.025em;
    padding-top: 0.2rem;
}

/* 섹션 내부 소제목 */
section[data-testid="stMain"] h3 {
    font-size: 1.3rem;
    font-weight: 650;
    letter-spacing: -0.015em;
}

/* 버튼 디자인 통일 */
section[data-testid="stMain"] .stButton button,
section[data-testid="stMain"] .stDownloadButton button {
    border-radius: 9px;
    min-height: 2.65rem;
    font-weight: 550;
}

/* 메인 페이지 구분선 */
section[data-testid="stMain"] hr {
    margin-top: 1.2rem;
    margin-bottom: 1.2rem;
    opacity: 0.55;
}

/* 데이터 표 모서리 */
section[data-testid="stMain"] [data-testid="stDataFrame"] {
    border-radius: 10px;
    overflow: hidden;
}

/* 캡션 가독성 */
section[data-testid="stMain"] [data-testid="stCaptionContainer"] {
    line-height: 1.5;
}

</style>
""", unsafe_allow_html=True)
# ===== END DASHBOARD DESIGN SYSTEM =====



import shutil
DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ===== DEMO PROJECT INITIALIZATION =====
DEMO_SOURCE = (
    Path(__file__).resolve().parent
    / "demo_data"
    / "87437a415e4d"
)

DEMO_TARGET = (
    DATA_DIR
    / "projects"
    / "87437a415e4d"
)

if DEMO_SOURCE.exists():
    DEMO_TARGET.mkdir(parents=True, exist_ok=True)

    # 배포된 예시 프로젝트를 최신 데이터와 동기화
    # 일반 사용자가 생성한 다른 프로젝트는 변경하지 않음
    for source_file in DEMO_SOURCE.rglob("*"):
        if source_file.is_file():
            relative = source_file.relative_to(DEMO_SOURCE)
            target_file = DEMO_TARGET / relative

            target_file.parent.mkdir(
                parents=True, exist_ok=True
            )

            if (
                not target_file.exists()
                or source_file.read_bytes() != target_file.read_bytes()
            ):
                shutil.copy2(source_file, target_file)
# ===== END DEMO PROJECT INITIALIZATION =====

# ===== STEP 21-3: PROJECT SELECTOR =====

PROJECTS_DIR = DATA_DIR / "projects"

project_options = {}

if PROJECTS_DIR.exists():
    for folder in sorted(PROJECTS_DIR.iterdir()):
        if folder.is_dir():

            info_path = folder / "project_info.json"

            if info_path.exists():
                try:
                    with open(info_path, encoding="utf-8") as f:
                        info = json.load(f)

                    display_name = info.get(
                        "project_name", folder.name
                    )
                except (OSError, ValueError, TypeError):
                    display_name = folder.name
            else:
                display_name = folder.name

            # 내부 ID로 프로젝트를 구분하고, 화면에는 이름만 표시
            label = (
                "[예시] Beauty Market Test"
                if folder.name == "87437a415e4d"
                else display_name
            )

            project_options[folder.name] = {
                "label": label,
                "path": folder
            }

st.sidebar.subheader("분석 프로젝트")

# ===== STEP 27-11B-2: CREATE PROJECT =====
import re
import uuid

with st.sidebar.expander("+ 새 프로젝트 생성", expanded=False):
    new_project_name = st.text_input(
        "프로젝트 이름",
        placeholder="예: Beauty Market Test",
        key="new_project_name"
    )

    if st.button(
        "프로젝트 생성",
        key="create_new_project_button"
    ):
        project_name = new_project_name.strip()

        if not project_name:
            st.error("프로젝트 이름을 입력해주세요.")

        elif len(project_name) > 50:
            st.error("프로젝트 이름은 50자 이내로 입력해주세요.")

        else:
            # 파일명 대신 고유 ID를 사용해 안전하게 분리
            new_id = uuid.uuid4().hex[:12]

            new_project_dir = DATA_DIR / "projects" / new_id
            new_project_dir.mkdir(parents=True, exist_ok=False)

            # 프로젝트 표시용 이름 별도 저장
            import json

            metadata = {
                "project_id": new_id,
                "project_name": project_name
            }

            (new_project_dir / "project_info.json").write_text(
                json.dumps(
                    metadata,
                    ensure_ascii=False,
                    indent=2
                ),
                encoding="utf-8"
            )

            st.session_state["newly_created_project_id"] = new_id
            st.rerun()



# 시연용 프로젝트를 목록 맨 위에 표시
project_options = dict(
    sorted(
        project_options.items(),
        key=lambda item: (
            0 if item[1]["label"] == "[예시] Beauty Market Test" else 1,
            item[1]["label"],
            item[0]
        )
    )
)

if not project_options:
    st.warning("프로젝트가 없습니다. 먼저 프로젝트를 생성해주세요.")
    st.stop()

# 새 프로젝트 생성 후 해당 프로젝트 자동 선택
new_project_id = st.session_state.pop(
    "newly_created_project_id", None
)

if new_project_id in project_options:
    st.session_state["selected_project"] = new_project_id

# 삭제 후 기본 예시 프로젝트로 이동
if st.session_state.pop("return_to_demo_project", False):
    if "87437a415e4d" in project_options:
        st.session_state["selected_project"] = "87437a415e4d"

selected_project = st.sidebar.selectbox(
    "프로젝트 선택",
    options=list(project_options.keys()),
    format_func=lambda project_id: project_options[project_id]["label"],
    key="selected_project"
)

CURRENT_DATA_DIR = project_options[selected_project]["path"]



# ===== POSITIONING AGENT V2 PRODUCT INPUT =====
from positioning_agent.product_input_ui import (
    render_product_input
)

with st.expander("제품 정보 입력 및 확인", expanded=False):
    render_product_input(CURRENT_DATA_DIR)


# ===== STEP 9-164: AUTOMATED YOUTUBE KEYWORDS =====
with st.expander("YouTube 시장조사 · 검색 키워드", expanded=False):
    import json as keyword_json
    from positioning_agent.keyword_engine import (
        generate_and_select_keywords,
        save_keyword_generation
    )

    keyword_result_path = (
        CURRENT_DATA_DIR
        / "youtube_analysis"
        / "keyword_generation.json"
    )

    keyword_product_path = CURRENT_DATA_DIR / "product_info.json"

    if keyword_result_path.is_file():
        try:
            keyword_result = keyword_json.loads(
                keyword_result_path.read_text(encoding="utf-8")
            )

            st.success("검색 키워드 생성 결과가 저장되어 있습니다.")

            st.caption(
                "AI 생성 및 규칙 기반 보완 키워드입니다. "
                "검색 결과나 시장 수요가 검증된 것은 아닙니다."
            )

            keyword_sections = {
                "market_keywords": (
                    "시장 동향 분석",
                    "시장 전반의 트렌드를 파악하기 위한 검색어"
                ),
                "consumer_need_keywords": (
                    "소비자 니즈 분석",
                    "소비자의 피부 고민과 구매 니즈를 살펴볼 검색어"
                ),
                "own_product_keywords": (
                    "자사 제품 분석",
                    "자사 제품 관련 콘텐츠를 찾기 위한 검색어"
                ),
                "competitor_keywords": (
                    "경쟁 제품 분석",
                    "유사 제품과 비교 콘텐츠를 탐색할 검색어"
                )
            }

            selected_keywords = keyword_result.get(
                "search_keywords", {}
            )

            total_keywords = sum(
                len(selected_keywords.get(category, []))
                for category in keyword_sections
            )

            st.markdown(
                f"**YouTube 검색 키워드 · 총 {total_keywords}개**"
            )

            for category, (title, description) in keyword_sections.items():
                keywords = selected_keywords.get(category, [])

                st.markdown(f"#### {title}")
                st.caption(description)

                if keywords:
                    st.markdown(
                        "　 ·　 ".join(
                            f"`{keyword}`" for keyword in keywords
                        )
                    )
                else:
                    st.caption("생성된 검색어가 없습니다.")

            if keyword_result.get(
                "keyword_quality", {}
            ).get("own_product_review_required"):
                st.info(
                    "일부 자사 제품 검색어는 규칙으로 보완되었습니다."
                )

        except (OSError, ValueError, TypeError):
            st.warning("저장된 키워드 결과를 읽지 못했습니다.")

    elif not keyword_product_path.is_file():
        st.info("먼저 제품 정보를 입력하고 저장해 주세요.")

    else:
        st.caption(
            "현재 프로젝트의 제품 정보를 바탕으로 "
            "YouTube 검색 키워드를 생성합니다."
        )
        st.caption(
            "Gemini API 1회가 호출될 수 있으며, "
            "서비스 이용 조건에 따라 비용이 발생할 수 있습니다."
        )

        if st.button(
            "검색 키워드 자동 생성",
            key=f"generate_keywords_{selected_project}"
        ):
            try:
                gemini_key = st.secrets.get("GEMINI_API_KEY")

                if not gemini_key:
                    st.error("Gemini API 키가 설정되어 있지 않습니다.")

                else:
                    product_data = keyword_json.loads(
                        keyword_product_path.read_text(encoding="utf-8")
                    )

                    with st.spinner("검색 키워드를 생성하고 있습니다..."):
                        keyword_result = generate_and_select_keywords(
                            api_key=gemini_key,
                            product_info=product_data
                        )

                        save_keyword_generation(
                            keyword_result,
                            CURRENT_DATA_DIR
                        )

                    st.success("검색 키워드 생성 및 저장 완료!")
                    st.rerun()

            except FileExistsError:
                st.info("이미 키워드 결과가 저장되어 있습니다.")
                st.rerun()

            except Exception:
                st.error(
                    "키워드 생성 중 오류가 발생했습니다. "
                    "기존 프로젝트 데이터는 유지됩니다."
                )





# ===== STEP 9-181: YOUTUBE VIDEO SEARCH UI =====
with st.expander("YouTube 영상 자동 검색", expanded=False):
    import json as youtube_json

    from positioning_agent.youtube_engine import (
        run_project_video_search_safely
    )

    youtube_analysis_dir = CURRENT_DATA_DIR / "youtube_analysis"

    youtube_keyword_path = (
        youtube_analysis_dir / "keyword_generation.json"
    )

    youtube_result_path = (
        youtube_analysis_dir / "youtube_search_results.json"
    )

    if youtube_result_path.is_file():
        try:
            saved_search = youtube_json.loads(
                youtube_result_path.read_text(encoding="utf-8")
            )

            st.success("YouTube 영상 검색이 완료되었습니다.")
            st.metric(
                "수집된 고유 영상",
                saved_search.get("video_count", 0)
            )
            st.caption(
                "검색 결과에 포함된 영상은 아직 AI 관련성 평가를 "
                "거치지 않았습니다."
            )

        except (OSError, ValueError, TypeError):
            st.warning("저장된 영상 검색 결과를 읽지 못했습니다.")

    elif not youtube_keyword_path.is_file():
        st.info("먼저 YouTube 검색 키워드를 생성해 주세요.")

    else:
        try:
            saved_keywords = youtube_json.loads(
                youtube_keyword_path.read_text(encoding="utf-8")
            )["search_keywords"]

            keyword_count = sum(
                len(values) for values in saved_keywords.values()
            )

            st.write(f"**검색 예정 키워드: {keyword_count}개**")
            st.write(
                f"**예상 YouTube API 할당량: "
                f"{keyword_count * 100:,}단위**"
            )

            st.caption(
                "YouTube Data API의 search.list 요청은 "
                "검색어당 일반적으로 100단위를 사용합니다."
            )

            if st.button(
                "YouTube 영상 검색 실행",
                key=f"youtube_search_{selected_project}"
            ):
                youtube_key = st.secrets.get("YOUTUBE_API_KEY")

                if not youtube_key:
                    st.error(
                        "YouTube API 키가 설정되지 않았습니다."
                    )

                else:
                    with st.spinner(
                        "YouTube 영상을 검색하고 있습니다..."
                    ):
                        try:
                            result = run_project_video_search_safely(
                                api_key=youtube_key,
                                project_dir=CURRENT_DATA_DIR,
                                max_results=10
                            )

                            if result["status"] == "completed":
                                st.success(
                                    f"검색 완료: "
                                    f"{result['video_count']}개 영상"
                                )
                                st.rerun()

                            elif result["status"] == "already_exists":
                                st.info(
                                    "이미 저장된 검색 결과를 사용합니다."
                                )
                                st.rerun()

                            elif result["status"] == "already_running":
                                st.warning(
                                    "현재 프로젝트의 영상 검색이 "
                                    "이미 진행 중입니다."
                                )

                        except Exception:
                            st.error(
                                "영상 검색 중 오류가 발생했습니다. "
                                "일부 API 할당량이 사용되었을 수 있습니다. "
                                "원인을 확인하기 전에는 재실행하지 마세요."
                            )

        except (OSError, ValueError, TypeError, KeyError):
            st.warning(
                "저장된 검색 키워드를 읽지 못했습니다."
            )



# ===== STEP 9-202: VIDEO RELEVANCE UI =====
with st.expander("YouTube 영상 AI 관련성 평가", expanded=False):
    import json as relevance_json
    from collections import Counter

    from positioning_agent.video_relevance_engine import (
        run_project_video_relevance_safely
    )

    relevance_dir = CURRENT_DATA_DIR / "youtube_analysis"
    search_path = relevance_dir / "youtube_search_results.json"
    relevance_path = relevance_dir / "video_relevance_results.json"

    if relevance_path.is_file():
        try:
            saved_relevance = relevance_json.loads(
                relevance_path.read_text(encoding="utf-8")
            )

            classified_videos = saved_relevance[
                "relevance_result"
            ]["videos"]

            counts = Counter(
                video["relevance"]
                for video in classified_videos
            )

            st.success("영상 AI 관련성 평가 결과가 저장되어 있습니다.")
            st.caption(
                "영상 제목·설명 기반 AI 분류이며, "
                "실제 영상 내용을 시청하거나 사람이 검증한 결과는 아닙니다."
            )

            st.metric("평가 완료 영상", len(classified_videos))

            labels = {
                "Core": "핵심 관련",
                "Adjacent": "인접 관련",
                "Uncertain": "추가 검토",
                "Exclude": "제외"
            }

            for label, description in labels.items():
                st.write(
                    f"**{description}: {counts.get(label, 0)}개**"
                )

        except (OSError, ValueError, TypeError, KeyError):
            st.warning("저장된 영상 평가 결과를 읽지 못했습니다.")

    elif not search_path.is_file():
        st.info("먼저 YouTube 영상 자동 검색을 실행해 주세요.")

    else:
        try:
            search_data = relevance_json.loads(
                search_path.read_text(encoding="utf-8")
            )

            video_count = len(search_data["videos"])

            st.write(f"**AI 평가 예정 영상: {video_count}개**")

            st.caption(
                "Gemini API를 사용해 영상의 제목, 설명, "
                "검색 카테고리를 평가합니다."
            )

            st.caption(
                "실제 영상 시청이나 댓글 분석은 수행하지 않습니다. "
                "API 사용량과 비용이 발생할 수 있습니다."
            )

            if st.button(
                "AI 영상 관련성 평가 실행",
                key=f"video_relevance_{selected_project}"
            ):
                gemini_key = st.secrets.get("GEMINI_API_KEY")

                if not gemini_key:
                    st.error("Gemini API 키가 설정되지 않았습니다.")

                else:
                    with st.spinner(
                        "Gemini가 영상 관련성을 평가하고 있습니다..."
                    ):
                        try:
                            result = run_project_video_relevance_safely(
                                api_key=gemini_key,
                                project_dir=CURRENT_DATA_DIR
                            )

                            if result["status"] == "completed":
                                st.success("AI 영상 관련성 평가 완료!")
                                st.rerun()

                            elif result["status"] == "already_exists":
                                st.info("기존 평가 결과를 불러옵니다.")
                                st.rerun()

                            elif result["status"] == "already_running":
                                st.warning(
                                    "현재 프로젝트에서 AI 평가가 "
                                    "이미 진행 중입니다."
                                )

                        except Exception as error:
                            import logging

                            error_type = type(error).__name__
                            status_code = getattr(error, "code", None)

                            if status_code is None:
                                status_code = getattr(
                                    error, "status_code", None
                                )

                            safe_status = (
                                str(status_code)
                                if isinstance(status_code, int)
                                and 400 <= status_code <= 599
                                else "확인 불가"
                            )

                            logging.getLogger(__name__).error(
                                "Video relevance evaluation failed: "
                                "type=%s, status=%s",
                                error_type,
                                safe_status
                            )

                            st.error(
                                "영상 관련성 평가 중 오류가 발생했습니다. "
                                "원인 확인 전 재실행하지 마세요."
                            )
                            st.caption(
                                f"오류 유형: {error_type} / "
                                f"HTTP 상태: {safe_status}"
                            )

        except (OSError, ValueError, TypeError, KeyError):
            st.warning("저장된 영상 검색 결과를 읽지 못했습니다.")

@st.cache_data
def load_data(data_dir):
    posts_path = data_dir / "posts_clean.csv"

    posts = (
        pd.read_csv(posts_path)
        if posts_path.exists()
        else pd.DataFrame()
    )

    ai_path = data_dir / "ai_comments.csv"
    comments = (
        pd.read_csv(ai_path)
        if ai_path.exists()
        else pd.DataFrame()
    )

    verified_path = data_dir / "verified_insights.csv"
    verified = (
        pd.read_csv(verified_path)
        if verified_path.exists()
        else pd.DataFrame(columns=["validation"])
    )

    market_path = data_dir / "market_dashboard.csv"
    market = (
        pd.read_csv(market_path)
        if market_path.exists()
        else pd.DataFrame()
    )

    return posts, comments, verified, market

posts, comments, verified, market = load_data(CURRENT_DATA_DIR)

st.sidebar.caption(f"현재 프로젝트: {CURRENT_DATA_DIR.name}")

# ===== STEP 29-3C: SCROLL NAVIGATION =====
st.sidebar.markdown("""
<style>
/* 사이드바 전체 요소 사이 간격 축소 */
section[data-testid="stSidebar"]
[data-testid="stVerticalBlock"] {
    gap: 0.45rem;
}

/* 사이드바 구분선 위아래 여백 축소 */
section[data-testid="stSidebar"] hr {
    margin: 0.35rem 0;
}
</style>
""", unsafe_allow_html=True)

st.sidebar.markdown("### Navigation")

navigation_items = [
    ("Project Overview", "project-overview"),
    ("01 · Data & AI Analysis", "step-01-data-and-ai-analysis"),
    ("02 · Market Trends", "step-02-market-trends"),
    ("03 · Consumer Insights", "step-03-consumer-insights"),
    ("04 · Marketing Strategy", "step-04-marketing-strategy"),
]

for label, anchor in navigation_items:
    st.sidebar.markdown(
        f'<a href="#{anchor}" target="_self" '
        f'style="display:block; padding:4px 10px; '
        f'text-decoration:none; border-radius:6px; '
        f'font-size:16px; line-height:1.25;">'
        f'{label}</a>',
        unsafe_allow_html=True
    )
# ===== END SCROLL NAVIGATION =====

# ===== POSITIONING AGENT V2 PROJECT DELETE =====
import shutil

@st.dialog("프로젝트 삭제 확인")
def confirm_project_deletion():
    selected_label = project_options[selected_project]["label"]

    st.warning(
        f"'{selected_label}' 프로젝트를 삭제하시겠습니까?"
    )
    st.caption(
        "삭제하면 프로젝트 목록에서 사라지며, "
        "데이터는 휴지통 폴더에 보관됩니다."
    )

    cancel_col, delete_col = st.columns(2)

    with cancel_col:
        if st.button(
            "취소",
            use_container_width=True
        ):
            st.rerun()

    with delete_col:
        if st.button(
            "삭제하기",
            type="primary",
            use_container_width=True
        ):
            target = project_options[selected_project]["path"].resolve()
            projects_root = PROJECTS_DIR.resolve()

            if (
                selected_project == "87437a415e4d"
                or target.parent != projects_root
                or target.name != selected_project
                or not target.is_dir()
                or project_options[selected_project]["path"].is_symlink()
            ):
                st.error("삭제할 수 없는 프로젝트입니다.")
                return

            trash_dir = DATA_DIR / "project_trash"
            trash_dir.mkdir(parents=True, exist_ok=True)

            import uuid
            trash_target = (
                trash_dir /
                f"{selected_project}_{uuid.uuid4().hex[:8]}"
            )

            try:
                shutil.move(str(target), str(trash_target))
                st.session_state.pop("selected_project", None)
                st.session_state["return_to_demo_project"] = True
                st.rerun()
            except OSError:
                st.error("프로젝트 이동 중 오류가 발생했습니다.")

st.sidebar.divider()

if st.sidebar.button(
    "🗑️ 프로젝트 삭제",
    key="open_project_delete_dialog",
    disabled=(selected_project == "87437a415e4d"),
    use_container_width=True
):
    confirm_project_deletion()

# ===== END POSITIONING AGENT V2 PROJECT DELETE =====








direct = verified[
    verified["validation"] == "직접 근거"
].copy()

st.title("Market Insight AI")
st.caption("AI 기반 소비자 인사이트 및 시장 진입 전략")

# CSV 데이터 업로드
st.divider()
# NAV_SECTION: overview
st.header("Project Overview")

# ===== STEP 29-5C: PROJECT DASHBOARD =====
overview_dir = CURRENT_DATA_DIR

# 프로젝트 표시 이름
project_info_path = overview_dir / "project_info.json"
overview_name = (
    "기존 시장 분석"
    if overview_dir == DATA_DIR
    else overview_dir.name
)

if project_info_path.exists():
    try:
        with open(project_info_path, encoding="utf-8") as f:
            overview_name = json.load(f).get(
                "project_name", overview_name
            )
    except (ValueError, OSError, TypeError):
        pass

st.caption(f"CURRENT PROJECT  /  {overview_name}")

# 최신 프로젝트 파일 기준으로 KPI 계산
posts_file = overview_dir / "posts_clean.csv"
comments_file = overview_dir / "comments_clean.csv"

ai_file = overview_dir / "ai_comments_unified.csv"
if not ai_file.exists():
    ai_file = overview_dir / "ai_comments_v2.csv"
if not ai_file.exists():
    ai_file = overview_dir / "ai_comments.csv"

quality_file = overview_dir / "verified_insights_quality.csv"
strategy_file_overview = (
    overview_dir / "marketing_strategy" / "strategy_v2.json"
)

def overview_csv_count(path):
    if not path.exists():
        return 0
    try:
        return len(pd.read_csv(path, low_memory=False))
    except (OSError, ValueError, pd.errors.ParserError):
        return 0

post_count = overview_csv_count(posts_file)
comment_count = overview_csv_count(comments_file)
ai_count = overview_csv_count(ai_file)
insight_count = overview_csv_count(quality_file)

# KPI 카드 스타일
st.markdown("""
<style>
div[data-testid="stMetric"] {
    background: rgba(128, 145, 170, 0.08);
    border: 1px solid rgba(160, 175, 195, 0.15);
    border-radius: 12px;
    padding: 18px 20px;
}
div[data-testid="stMetricLabel"] {
    font-size: 15px;
}
</style>
""", unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)

c1.metric("수집 게시물", f"{post_count:,}")
c2.metric("수집 댓글", f"{comment_count:,}")
c3.metric("AI 분석 완료", f"{ai_count:,}")
c4.metric(
    "AI 검증 인사이트",
    f"{insight_count:,}" if quality_file.exists() else "미실행"
)

st.markdown("#### AI Analysis Progress")

progress_ratio = (
    min(ai_count / comment_count, 1.0)
    if comment_count
    else 0.0
)

st.progress(progress_ratio)

st.caption(
    f"댓글 {ai_count:,} / {comment_count:,}개 분석 완료 "
    f"({progress_ratio * 100:.1f}%)"
)

if strategy_file_overview.exists():
    overview_status = "마케팅 전략 보고서 생성 완료"
elif quality_file.exists():
    overview_status = "소비자 인사이트 검증 완료 · 전략 생성 대기"
elif comment_count > 0 and ai_count >= comment_count:
    overview_status = "AI 댓글 분석 완료 · 소비자 인사이트 검증 대기"
elif ai_count > 0:
    overview_status = "AI 댓글 분석 진행 중"
elif comment_count > 0:
    overview_status = "데이터 업로드 완료 · AI 분석 대기"
else:
    overview_status = "새 프로젝트 · CSV 업로드 대기"

st.caption(f"● {overview_status}")

# ===== END PROJECT DASHBOARD =====

st.divider()

# 2. 시장분석 그래프

# NAV_SECTION: data-analysis
st.header("STEP 01 · Data & AI Analysis")

if CURRENT_DATA_DIR.name == "87437a415e4d":
    st.subheader("01 · CSV 데이터 준비")
    st.success("데이터 업로드 완료")

    demo_files = [
        ("게시물 데이터", "posts_clean.csv"),
        ("댓글 데이터", "comments_clean.csv"),
    ]

    for label, filename in demo_files:
        file_path = CURRENT_DATA_DIR / filename

        if file_path.exists():
            col1, col2 = st.columns([4, 1])

            with col1:
                count = len(pd.read_csv(file_path))
                st.markdown(f"**{label}**")
                st.caption(f"{filename} · {count:,}개")

            with col2:
                st.download_button(
                    "다운로드",
                    data=file_path.read_bytes(),
                    file_name=filename,
                    mime="text/csv",
                    key=f"demo_csv_{filename}"
                )

    st.caption(
        "실제 수집 데이터의 건수를 보존한 시연용 CSV입니다. "
        "원본 게시물·댓글 내용은 포함되지 않습니다."
    )

    st.divider()

    st.subheader("02 · AI 댓글 분석")
    ai_file = CURRENT_DATA_DIR / "ai_comments_v2.csv"

    if ai_file.exists():
        ai_count_demo = len(pd.read_csv(ai_file))
        st.success("Gemini AI 댓글 분석 완료")

        st.metric("AI 분석 완료", f"{ai_count_demo:,}개")
        st.progress(1.0)
        st.caption(
            f"댓글 {ai_count_demo:,} / {ai_count_demo:,}개 분석 완료 (100%)"
        )

else:
    st.subheader("01 · CSV 데이터 준비")
    st.caption(
        "Instagram 게시물과 댓글 CSV를 업로드한 후 "
        "데이터를 정제하고 현재 프로젝트에 저장합니다."
    )

    # 현재 프로젝트에 저장된 데이터 확인
    existing_posts_path = CURRENT_DATA_DIR / "posts_clean.csv"
    existing_comments_path = CURRENT_DATA_DIR / "comments_clean.csv"
    existing_merged_path = CURRENT_DATA_DIR / "merged.csv"

    if all(
        path.exists()
        for path in [
            existing_posts_path,
            existing_comments_path,
            existing_merged_path
        ]
    ):
        st.caption(
            "✓ 현재 프로젝트에 데이터가 저장되어 있습니다. "
            "새 CSV를 업로드하지 않아도 아래 AI 댓글 분석을 실행할 수 있습니다."
        )
    else:
        st.caption(
            "아직 저장된 데이터가 없습니다. "
            "게시물과 댓글 CSV를 업로드해주세요."
        )

    col1, col2 = st.columns(2)

    with col1:
        uploaded_posts = st.file_uploader(
            "게시물 CSV 업로드",
            type=["csv"],
            key="posts_upload"
        )

    with col2:
        uploaded_comments = st.file_uploader(
            "댓글 CSV 업로드",
            type=["csv"],
            key="comments_upload"
        )

    if uploaded_posts is not None and uploaded_comments is not None:
        try:
            new_posts = pd.read_csv(
                uploaded_posts,
                low_memory=False
            )

            new_comments = pd.read_csv(
                uploaded_comments,
                low_memory=False
            )

            st.success("CSV 파일 업로드 완료!")

            c1, c2 = st.columns(2)
            c1.metric("업로드된 게시물", len(new_posts))
            c2.metric("업로드된 댓글", len(new_comments))

            # 새 프로젝트에 정제 데이터 저장
            if st.button("CSV 정제 및 저장", type="primary"):
                import hashlib
                import io

                required_post = {"url", "caption"}
                required_comment = {"postUrl", "text"}

                if not required_post.issubset(new_posts.columns):
                    st.error("게시물 CSV에 url 또는 caption 컬럼이 없습니다.")

                elif not required_comment.issubset(new_comments.columns):
                    st.error("댓글 CSV에 postUrl 또는 text 컬럼이 없습니다.")

                else:
                    # 업로드 데이터 기반 프로젝트 ID 생성
                    fingerprint = hashlib.sha256(
                        pd.util.hash_pandas_object(
                            new_posts[["url", "caption"]].fillna(""),
                            index=False
                        ).values.tobytes()
                        +
                        pd.util.hash_pandas_object(
                            new_comments[["postUrl", "text"]].fillna(""),
                            index=False
                        ).values.tobytes()
                    ).hexdigest()[:12]

                    # 사이드바에서 선택한 프로젝트에 저장
                    new_dir = CURRENT_DATA_DIR

                    # 기존 시장 분석 루트는 덮어쓰지 않도록 보호
                    if new_dir == DATA_DIR:
                        st.error(
                            "먼저 사이드바에서 분석 프로젝트를 선택해주세요."
                        )
                        st.stop()

                    new_dir.mkdir(parents=True, exist_ok=True)

                    # 게시물 정제
                    clean_posts = new_posts.dropna(
                        subset=["url"]
                    ).copy()

                    clean_posts["url"] = (
                        clean_posts["url"]
                        .astype(str)
                        .str.strip()
                        .str.rstrip("/")
                    )

                    clean_posts = clean_posts.drop_duplicates(
                        subset=["url"]
                    )

                    # 댓글 정제
                    clean_comments = new_comments.dropna(
                        subset=["text", "postUrl"]
                    ).copy()

                    clean_comments["text"] = (
                        clean_comments["text"]
                        .astype(str)
                        .str.strip()
                    )

                    clean_comments = clean_comments[
                        clean_comments["text"] != ""
                    ]

                    clean_comments["postUrl"] = (
                        clean_comments["postUrl"]
                        .astype(str)
                        .str.strip()
                        .str.rstrip("/")
                    )

                    # 댓글 고유 ID가 있으면 해당 ID 기준 중복 제거
                    if "id" in clean_comments.columns:
                        clean_comments = clean_comments.drop_duplicates(
                            subset=["id"]
                        )
                    else:
                        keys = ["postUrl", "text"]
                        if "timestamp" in clean_comments.columns:
                            keys.append("timestamp")
                        clean_comments = clean_comments.drop_duplicates(
                            subset=keys
                        )

                    # 게시물과 댓글 연결
                    clean_posts = clean_posts.reset_index(drop=True)
                    clean_comments = clean_comments.reset_index(drop=True)

                    # 게시물 URL 컬럼명 변경
                    post_lookup = clean_posts[
                        ["url", "caption"]
                    ].rename(columns={
                        "url": "matched_post_url",
                        "caption": "post_caption"
                    })

                    # 댓글과 게시물 연결
                    joined = clean_comments.merge(
                        post_lookup,
                        left_on="postUrl",
                        right_on="matched_post_url",
                        how="left"
                    )

                    # 파일 저장
                    clean_posts.to_csv(
                        new_dir / "posts_clean.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )

                    clean_comments.to_csv(
                        new_dir / "comments_clean.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )

                    joined.to_csv(
                        new_dir / "merged.csv",
                        index=False,
                        encoding="utf-8-sig"
                    )

                    st.session_state["active_project"] = str(new_dir)

                    st.success("선택한 프로젝트에 CSV 저장 완료!")
                    st.write("저장된 프로젝트:", new_dir.name)

                    c1, c2, c3 = st.columns(3)
                    c1.metric("정제 게시물", len(clean_posts))
                    c2.metric("정제 댓글", len(clean_comments))
                    c3.metric(
                        "게시물 연결 성공",
                        int(joined["matched_post_url"].notna().sum())
                    )

                    st.info(
                        "CSV 정제와 저장이 완료되었습니다. "
                        "Gemini AI 자동 분석은 다음 단계에서 연결합니다."
                    )

        except Exception as e:
            st.error(f"CSV 파일 읽기 오류: {e}")




    # 1. 요약

    # ===== STEP 22-2: FULL AI ANALYSIS =====

    st.divider()

    st.subheader("02 · AI 댓글 분석")
    st.caption(
        "Gemini가 댓글의 관련성, 감성, 피부 고민, 소비자 반응을 분석합니다."
    )

    st.write(
        "선택한 프로젝트의 댓글을 Gemini AI로 분석합니다. "
        "이미 분석된 댓글은 다시 분석하지 않습니다."
    )

    import importlib
    import market_ai_engine

    importlib.reload(market_ai_engine)
    analyze_comments = market_ai_engine.analyze_comments

    analysis_project = str(CURRENT_DATA_DIR)

    if not analysis_project:
        analysis_project = str(CURRENT_DATA_DIR)

    analysis_dir = Path(analysis_project)

    merged_path = analysis_dir / "merged.csv"
    ai_output_path = analysis_dir / "ai_comments_v2.csv"

    if merged_path.exists():

        st.caption(f"분석 대상: {analysis_dir.name}")

        max_batches = st.number_input(
            "이번에 분석할 배치 수 (1배치 = 최대 20개 댓글)",
            min_value=1,
            max_value=1000,
            value=1,
            step=1,
            help="분석 결과는 자동 저장됩니다. 다음 실행에서는 미분석 댓글부터 이어서 처리합니다."
        )

        if st.button(
            "AI 댓글 분석 실행",
            type="primary",
            key="full_ai_analysis"
        ):

            api_key = st.secrets.get("GEMINI_API_KEY")

            if not api_key:
                st.error("Gemini API 키가 설정되지 않았습니다.")

            else:
                progress_bar = st.progress(0)
                status = st.empty()

                def update_progress(completed, total):
                    ratio = completed / total if total else 1.0
                    progress_bar.progress(min(ratio, 1.0))
                    status.write(
                        f"분석 진행: {completed:,} / {total:,}개"
                    )

                try:
                    with st.spinner("Gemini AI 분석 중..."):
                        results = analyze_comments(
                            merged_path=merged_path,
                            output_path=ai_output_path,
                            api_key=api_key,
                            progress_callback=update_progress,
                            max_batches=int(max_batches)
                        )

                    # ===== STEP 25-7C: AUTO REFRESH =====
                    import importlib
                    import market_sync_engine
                    import market_trends_engine

                    importlib.reload(market_sync_engine)
                    importlib.reload(market_trends_engine)

                    # 기존 v1 분석이 있는 프로젝트만 통합
                    if (analysis_dir / "ai_comments.csv").exists():
                        market_sync_engine.sync_ai_results(
                            analysis_dir
                        )
                        analysis_source = "ai_comments_unified.csv"
                    else:
                        analysis_source = "ai_comments_v2.csv"

                    # 최신 AI 결과로 시장 동향 다시 생성
                    market_trends_engine.generate_market_trends(
                        project_dir=analysis_dir,
                        analysis_file=analysis_source
                    )

                    st.success(
                        f"분석 결과 {len(results):,}개 저장 및 "
                        "시장 동향 갱신 완료!"
                    )

                    st.dataframe(
                        results.tail(20),
                        use_container_width=True
                    )

                    st.caption(
                        f"저장 위치: {ai_output_path}"
                    )

                except Exception as e:
                    st.error(f"AI 분석 오류: {e}")

    else:
        st.info(
            "분석 가능한 merged.csv 파일이 없습니다. "
            "먼저 게시물과 댓글 CSV를 업로드해주세요."
        )


    # ===== DEVELOPER TOOLS =====
    with st.expander("Developer Tools · Gemini 10개 댓글 테스트", expanded=False):
        st.subheader("Gemini 분석 테스트")

        active_project = str(CURRENT_DATA_DIR)

        if active_project:

            project_path = Path(active_project)
            merged_path = project_path / "merged.csv"

            if st.button("Gemini 댓글 10개 분석 테스트"):

                if not merged_path.exists():
                    st.error("분석할 데이터가 없습니다.")

                else:
                    api_key = st.secrets.get("GEMINI_API_KEY")

                    if not api_key:
                        st.error(
                            "Gemini API 키가 설정되지 않았습니다."
                        )
                    else:
                        client = genai.Client(api_key=api_key)

                        data = pd.read_csv(merged_path)

                        sample = (
                            data.drop_duplicates(subset=["postUrl"])
                            .sample(
                                n=min(10, data["postUrl"].nunique()),
                                random_state=42
                            )
                        )

                        records = [
                            {
                                "id": i,
                                "comment": str(row["text"]),
                                "caption": str(
                                    row.get("post_caption", "")
                                )[:500]
                            }
                            for i, (_, row) in enumerate(
                                sample.iterrows()
                            )
                        ]

                        prompt = """
                        너는 한국 스킨케어 소비자 분석가야.

                        각 댓글을 다음 기준으로 엄격하게 분류해.

                        1. id: 입력 ID
                        2. relevance: 관련 / 무관 / 불확실
                        3. type: 사용 후기 / 소비자 니즈 / 구매 관심 /
                           광고·이벤트 / 단순 반응 / 기타
                        4. sentiment: 긍정 / 중립 / 부정 /
                           혼합 / 판단불가
                        5. concern: 트러블 / 보습·장벽 / 모공·피지 /
                           탄력 / 미백·잡티 / 민감성 / 기타 / 없음
                        6. insight: 실제 댓글로 확인되는 핵심 정보

                        규칙:
                        - 스킨케어와 무관한 댓글은 '무관'으로 분류한다.
                        - 색조 화장품, 모델 외모, 팬밋업 관련 댓글은
                          스킨케어 소비자 반응에서 제외한다.
                        - 댓글이 실제 사용을 언급하지 않았다면
                          '사용 후기'로 분류하지 않는다.
                        - 구매 관심과 실제 구매 의향을 구분한다.
                        - 단순 이모지나 제품명으로 니즈를 추측하지 않는다.
                        - 게시물 캡션은 맥락 이해에만 활용한다.
                        - 위 분류값 이외의 표현은 사용하지 않는다.
                        - 분석할 수 없으면 insight는
                          '구체적 인사이트 없음'으로 작성한다.
                        - 모든 ID를 정확히 한 번씩 반환한다.

                        반드시 JSON 객체로 반환해:
                        {"results": [...]}

                        데이터:
                        """ + json.dumps(
                            records,
                            ensure_ascii=False
                        )

                        try:
                            with st.spinner(
                                "Gemini가 댓글을 분석하고 있습니다..."
                            ):
                                response = client.models.generate_content(
                                    model="gemini-3.1-flash-lite",
                                    contents=prompt,
                                    config=types.GenerateContentConfig(
                                        response_mime_type="application/json",
                                        temperature=0
                                    )
                                )

                            results = json.loads(
                                response.text
                            )["results"]

                            result_df = pd.DataFrame(results)

                            st.success("AI 분석 완료!")
                            st.dataframe(
                                result_df,
                                use_container_width=True
                            )

                            result_df.to_csv(
                                project_path / "ai_test_results.csv",
                                index=False,
                                encoding="utf-8-sig"
                            )

                        except Exception as e:
                            st.error(f"분석 오류: {e}")

        else:
            st.info(
                "먼저 CSV를 업로드하고 "
                "새 분석 프로젝트를 생성해주세요."
            )


# NAV_SECTION: market-trends
st.header("STEP 02 · Market Trends")

# ===== STEP 25-3: AUTO MARKET TRENDS =====

trends_dir = CURRENT_DATA_DIR / "market_trends"

if (trends_dir / "overview.json").exists():

    import json

    with open(
        trends_dir / "overview.json",
        "r",
        encoding="utf-8"
    ) as f:
        trends_overview = json.load(f)

    st.caption(
        "현재 프로젝트의 AI 댓글 분석 결과를 기반으로 "
        "생성된 시장 동향입니다."
    )

    t1, t2, t3 = st.columns(3)

    t1.metric(
        "AI 분석 댓글",
        f'{trends_overview["analyzed_comments"]:,}'
    )

    t2.metric(
        "스킨케어 관련 댓글",
        f'{trends_overview["relevant_comments"]:,}'
    )

    t3.metric(
        "관련 댓글 비율",
        f'{trends_overview["relevance_rate"]}%'
    )

    with st.expander("분석 데이터 상세 정보", expanded=False):
        versions = trends_overview.get("analysis_versions", {})

        st.caption("AI 분석 버전별 댓글 수")

        if isinstance(versions, dict):
            for version, count in versions.items():
                display_version = (
                    "버전 정보 미기록"
                    if version == "unknown"
                    else str(version)
                )
                st.write(f"{display_version}: {count:,}개")
        else:
            st.write(versions)

        st.caption(
            "버전 정보 미기록은 분석 모델이 확인되지 않았다는 뜻이며, "
            "분석에 실패했다는 의미는 아닙니다."
        )

    graph_files = [
        ("감성 분포", "sentiment.csv"),
        ("피부 고민 분포", "concerns.csv"),
        ("소비자 반응 유형", "reaction_types.csv")
    ]

    for graph_title, filename in graph_files:

        graph_path = trends_dir / filename

        if graph_path.exists():
            graph_data = pd.read_csv(graph_path)

            st.subheader(graph_title)

            graph_data = graph_data.sort_values(
                "count",
                ascending=True
            )

            fig = px.bar(
                graph_data,
                x="count",
                y="category",
                orientation="h",
                text="count"
            )

            fig.update_layout(
                xaxis_title="댓글 수",
                yaxis_title=None,
                height=max(220, len(graph_data) * 42),
                margin=dict(l=20, r=20, t=15, b=30)
            )

            fig.update_traces(
                textposition="outside",
                cliponaxis=False
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

    st.caption(
        "ⓘ " + str(trends_overview.get("methodology_note", ""))
    )

else:
    st.info(
        "이 프로젝트의 Market Trends 데이터가 없습니다. "
        "AI 분석을 완료한 후 시장 동향을 생성해주세요."
    )

st.divider()

# 3. 소비자 인사이트

# NAV_SECTION: consumer-insights
st.header("STEP 03 · Consumer Insights")

# ===== STEP 26-8A: INSIGHT VALIDATION UI =====

st.subheader("AI 소비자 인사이트 검증")

st.caption(
    "댓글 원문과 AI 인사이트를 비교해 근거 수준과 "
    "소비자 행동 단계를 평가합니다."
)

validation_source = CURRENT_DATA_DIR / "ai_comments_unified.csv"

# 기존 v1 데이터가 없는 새 프로젝트에서는 v2 결과 사용
if not validation_source.exists():
    validation_source = CURRENT_DATA_DIR / "ai_comments_v2.csv"

validation_output = CURRENT_DATA_DIR / "verified_insights_v4.csv"
quality_output = CURRENT_DATA_DIR / "verified_insights_quality.csv"

if validation_source.exists():

    import importlib
    import consumer_insights_engine_v4
    import insight_quality_engine

    # 코드 변경 시 최신 엔진 적용
    importlib.reload(consumer_insights_engine_v4)
    importlib.reload(insight_quality_engine)

    v_batches = st.number_input(
        "이번 실행에서 검증할 최대 배치 수 (1배치 = 20개)",
        min_value=1,
        max_value=1000,
        value=1,
        step=1,
        key="insight_validation_batches"
    )

    if st.button(
        "소비자 인사이트 검증 시작",
        key="run_insight_validation"
    ):

        api_key = st.secrets.get("GEMINI_API_KEY")

        if not api_key:
            st.error("Gemini API 키가 설정되지 않았습니다.")

        else:
            progress = st.progress(0)
            status = st.empty()

            def validation_progress(completed, total):
                ratio = completed / total if total else 1.0
                progress.progress(min(ratio, 1.0))
                status.write(
                    f"인사이트 검증 진행: {completed:,} / {total:,}개"
                )

            try:
                with st.spinner("AI 인사이트 검증 중..."):

                    validation_result = (
                        consumer_insights_engine_v4.validate_insights_v4(
                            analysis_path=validation_source,
                            output_path=validation_output,
                            api_key=api_key,
                            max_batches=int(v_batches),
                            progress_callback=validation_progress
                        )
                    )

                    quality_result = (
                        insight_quality_engine.check_insight_quality(
                            input_path=validation_output,
                            output_path=quality_output
                        )
                    )

                st.success(
                    f"인사이트 {len(validation_result):,}개 검증 완료! "
                    "품질 검사 결과도 저장했습니다."
                )

                st.write(
                    quality_result["quality_status"].value_counts()
                )

                # 아래 대시보드에서 최신 파일을 다시 읽도록 실행
                st.rerun()

            except Exception as e:
                st.error(f"인사이트 검증 오류: {e}")

else:
    st.info(
        "AI 댓글 분석 결과가 없습니다. "
        "STEP 02에서 댓글 분석을 먼저 진행해주세요."
    )

st.divider()



# ===== STEP 26-7A: VERIFIED INSIGHTS DASHBOARD =====

quality_path = CURRENT_DATA_DIR / "verified_insights_quality.csv"

if quality_path.exists():
    quality_df = pd.read_csv(quality_path, low_memory=False)

    st.caption(
        "AI가 도출한 인사이트의 근거 수준과 "
        "소비자 행동 단계를 분석한 결과입니다."
    )

    total_checked = len(quality_df)

    direct_count = int((
        (quality_df["market_relevance"] == "관련")
        & (quality_df["validation"] == "직접 근거")
        & (quality_df["quality_status"] == "자동 검사 통과")
    ).sum())

    review_count = int(
        (quality_df["quality_status"] == "재검토 필요").sum()
    )

    c1, c2, c3 = st.columns(3)
    c1.metric("검사한 인사이트", total_checked)
    c2.metric("직접 근거 · 규칙 통과", direct_count)
    c3.metric("재검토 필요", review_count)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("근거 검증 수준")
        counts = quality_df["validation"].value_counts().reset_index()
        counts.columns = ["category", "count"]
        counts = counts.sort_values("count", ascending=True)
        fig = px.bar(
            counts,
            x="count",
            y="category",
            orientation="h",
            text="count"
        )
        fig.update_layout(
            xaxis_title="댓글 수",
            yaxis_title=None,
            height=max(240, len(counts) * 48),
            margin=dict(l=10, r=35, t=15, b=30)
        )
        fig.update_traces(
            textposition="outside",
            cliponaxis=False
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("소비자 행동 단계")
        counts = quality_df["behavior_stage"].value_counts().reset_index()
        counts.columns = ["category", "count"]
        counts = counts.sort_values("count", ascending=True)
        fig = px.bar(
            counts,
            x="count",
            y="category",
            orientation="h",
            text="count"
        )
        fig.update_layout(
            xaxis_title="댓글 수",
            yaxis_title=None,
            height=max(240, len(counts) * 48),
            margin=dict(l=10, r=35, t=15, b=30)
        )
        fig.update_traces(
            textposition="outside",
            cliponaxis=False
        )
        st.plotly_chart(fig, use_container_width=True)


    # ===== STEP 26-7D: INSIGHT DETAIL VIEW =====
    st.subheader("소비자 인사이트 상세보기")

    verified_view = quality_df[
        (quality_df["market_relevance"] == "관련")
        & (quality_df["validation"] == "직접 근거")
        & (quality_df["quality_status"] == "자동 검사 통과")
    ].copy()

    if verified_view.empty:
        st.info("현재 표시할 인사이트가 없습니다.")

    else:
        # 1. 필터
        f1, f2 = st.columns(2)

        concern_options = ["전체"] + sorted(
            verified_view["concern"].dropna().unique().tolist()
        )

        behavior_options = ["전체"] + sorted(
            verified_view["behavior_stage"].dropna().unique().tolist()
        )

        with f1:
            selected_concern = st.selectbox(
                "피부 고민",
                options=concern_options,
                key="v4_concern_filter"
            )

        with f2:
            selected_behavior = st.selectbox(
                "소비자 행동 단계",
                options=behavior_options,
                key="v4_behavior_filter"
            )

        filtered_view = verified_view.copy()

        if selected_concern != "전체":
            filtered_view = filtered_view[
                filtered_view["concern"] == selected_concern
            ]

        if selected_behavior != "전체":
            filtered_view = filtered_view[
                filtered_view["behavior_stage"] == selected_behavior
            ]

        st.caption(
            f"선택한 조건에 해당하는 인사이트: {len(filtered_view)}개"
        )

        # 2. 인사이트 선택
        if filtered_view.empty:
            st.info("선택한 조건에 해당하는 인사이트가 없습니다.")

        else:
            filtered_view = filtered_view.reset_index(drop=True)

            options = list(range(len(filtered_view)))

            selected_idx = st.selectbox(
                "확인할 인사이트 선택",
                options=options,
                format_func=lambda i: (
                    f"{i + 1}. "
                    + str(filtered_view.iloc[i]["corrected_insight"])[:85]
                ),
                key="v4_insight_selector"
            )

            selected = filtered_view.iloc[selected_idx]

            # 3. 상세보기
            st.markdown("#### AI가 도출한 소비자 인사이트")
            st.write(selected["corrected_insight"])

            d1, d2, d3 = st.columns(3)

            with d1:
                with st.container(border=True):
                    st.caption("피부 고민")
                    st.write(str(selected["concern"]))

            with d2:
                with st.container(border=True):
                    st.caption("소비자 행동 단계")
                    st.write(str(selected["behavior_stage"]))

            with d3:
                with st.container(border=True):
                    st.caption("근거 수준")
                    st.write(str(selected["validation"]))

            st.markdown("#### 소비자 댓글 원문")
            st.info(str(selected["text"]))

            st.markdown("#### 직접 인용 근거")
            st.write(
                str(selected.get("evidence_quote", ""))
            )

            with st.expander("AI 검증 이유 및 분석 정보"):
                st.write("검증 이유:", selected["reason"])
                st.write(
                    "기존 AI 인사이트:",
                    selected["insight"]
                )
                st.write(
                    "과장 탐지:",
                    selected["overclaim_detected"]
                )
                st.write(
                    "품질 검사:",
                    selected["quality_status"]
                )

            post_url = str(selected.get("postUrl", ""))

            if post_url.startswith("https://"):
                st.link_button(
                    "원본 인스타그램 게시물 확인",
                    post_url
                )

    st.divider()

    review_df = quality_df[
        quality_df["quality_status"] == "재검토 필요"
    ]

    with st.expander(
        f"재검토 필요 댓글 ({len(review_df)}개)"
    ):
        st.dataframe(
            review_df[
                [
                    "text",
                    "behavior_stage",
                    "corrected_insight",
                    "quality_issues"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

    st.caption(
        "AI 및 규칙 기반 검증 결과는 참고용이며, "
        "최종 인사이트의 정확성을 보장하지 않습니다."
    )

else:
    st.info(
        "아직 품질 검사가 완료된 인사이트 데이터가 없습니다."
    )

st.divider()


options = ["전체"]

if "concern" in direct.columns:
    options += sorted(
        direct["concern"].dropna().unique().tolist()
    )

if direct.empty:
    st.info("이 프로젝트에는 기존 v1 인사이트 데이터가 없습니다.")
else:
    # ===== STEP 26-7C: INSIGHTS UI CLEANUP =====
    with st.expander("기존 v1 인사이트 분석 (참고용)", expanded=False):
        st.caption("기존 AI 분석 기준으로 생성된 결과이며, 최신 v4 검증 결과와 구분해 확인해주세요.")

        selected = st.selectbox("피부 고민 선택", options)

        filtered = direct.copy()

        if selected != "전체":
            filtered = filtered[
                filtered["concern"] == selected
            ]

        st.dataframe(
            filtered[
                [
                    "comment_id",
                    "concern",
                    "type",
                    "text",
                    "corrected_insight"
                ]
            ],
            use_container_width=True,
            hide_index=True
        )

        st.caption(
            "직접 근거는 AI 기반 검증 결과이며 "
            "사람의 최종 검증을 의미하지 않습니다."
        )

        st.divider()

    # 4. AI 전략 보고서


# NAV_SECTION: marketing-strategy
st.header("STEP 04 · Marketing Strategy")






# ===== STEP 27-9D: UNIFIED FRESHNESS UI =====

st.subheader("데이터 및 전략 최신성")

import strategy_input_compare_engine
import strategy_version_engine

try:
    comparison = (
        strategy_input_compare_engine.compare_strategy_input(
            project_dir=CURRENT_DATA_DIR
        )
    )

    version = strategy_version_engine.check_source_version(
        CURRENT_DATA_DIR
    )

    input_status = comparison.get("status", "확인 불가")
    strategy_status = version.get("status", "확인 불가")

    is_demo_freshness = (
        CURRENT_DATA_DIR.name == "87437a415e4d"
    )

    if is_demo_freshness and strategy_status == "기록된 파일과 일치":
        st.success(
            "예시 프로젝트 분석 완료 · "
            "저장된 마케팅 전략 및 PDF 보고서를 열람할 수 있습니다."
        )
        st.caption(
            "실제 Instagram 데이터 기반 분석 결과를 "
            "익명화하여 제공하는 읽기 전용 시연입니다."
        )

    elif (
        comparison.get("changed") is False
        and strategy_status == "기록된 파일과 일치"
    ):
        st.success(
            "분석 데이터와 전략 버전이 모두 일치합니다."
        )

    elif comparison.get("changed") is True:
        st.warning(
            "분석 데이터가 변경되었습니다. "
            "최신 데이터로 전략을 다시 생성해주세요."
        )

    else:
        st.warning(
            "전략 생성 당시의 데이터 버전이 확인되지 않습니다. "
            "전략 재검증이 필요합니다."
        )

    with st.expander("데이터 최신성 상세 정보", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            st.metric("분석 데이터", input_status)

        with col2:
            st.metric("전략 생성 버전", strategy_status)

        if "saved_evidence_count" in comparison:
            c1, c2 = st.columns(2)

            with c1:
                st.metric(
                    "저장된 전략 근거",
                    comparison["saved_evidence_count"]
                )

            with c2:
                st.metric(
                    "현재 전략 근거 후보",
                    comparison["current_evidence_count"]
                )

        st.markdown("**파일별 검사 결과**")

        for name, status in version.get("details", {}).items():
            st.write(f"{name}: {status}")

        st.caption(
            "파일 일치 여부는 전략의 정확성이나 "
            "시장 성공 가능성을 의미하지 않습니다."
        )

except Exception as e:
    st.warning(
        f"데이터 최신성 확인 중 오류가 발생했습니다: {e}"
    )

st.divider()

# ===== STEP 27-7D: STRATEGY PIPELINE UI =====

st.subheader("AI 마케팅 전략 자동 생성")

st.caption(
    "시장 동향 및 소비자 인사이트를 바탕으로 전략을 생성하고, "
    "근거 점검과 PDF 보고서 작성을 자동으로 진행합니다."
)

strategy_input_available = (
    (CURRENT_DATA_DIR / "market_trends" / "overview.json").exists()
    and (CURRENT_DATA_DIR / "verified_insights_quality.csv").exists()
)

if strategy_input_available:

    strategy_file = (
        CURRENT_DATA_DIR
        / "marketing_strategy"
        / "strategy_v2.json"
    )

    # ===== STEP 27-8F: REUSE UI CHECK =====
    import strategy_version_engine

    current_version = strategy_version_engine.check_source_version(
        CURRENT_DATA_DIR
    )

    can_reuse_strategy = (
        strategy_file.exists()
        and current_version.get("status") == "기록된 파일과 일치"
    )

    if not can_reuse_strategy:
        st.warning(
            "현재 전략의 데이터 버전이 확인되지 않거나 "
            "변경되었습니다. 새로운 Gemini 전략 생성이 필요합니다."
        )

    # Streamlit 세션에 남아 있는 이전 선택값도 초기화
    if not can_reuse_strategy:
        st.session_state["strategy_pipeline_reuse"] = False

    use_saved_strategy = st.checkbox(
        "기존 전략 재사용 (Gemini API 호출 없음)",
        value=can_reuse_strategy,
        disabled=not can_reuse_strategy,
        key="strategy_pipeline_reuse"
    )

    if not use_saved_strategy:
        st.caption(
            "새 전략을 생성하면 Gemini API가 호출됩니다. "
            "기존 전략 파일은 새로운 결과로 갱신됩니다."
        )

    is_demo_project = (
        CURRENT_DATA_DIR.name == "87437a415e4d"
    )

    if is_demo_project:
        st.info(
            "예시 프로젝트입니다. 이미 생성된 마케팅 전략과 "
            "PDF 보고서를 아래에서 확인할 수 있습니다."
        )

    if st.button(
        "AI 마케팅 전략 자동 생성",
        key="run_strategy_pipeline",
        type="primary",
        disabled=is_demo_project
    ):

        try:
            import importlib
            import strategy_pipeline_engine

            importlib.reload(strategy_pipeline_engine)

            # Gemini 전략을 새로 생성할 때만 API 키 필요
            if use_saved_strategy and strategy_file.exists():
                pipeline_api_key = None
            else:
                pipeline_api_key = st.secrets.get(
                    "GEMINI_API_KEY"
                )

                if not pipeline_api_key:
                    st.error(
                        "Gemini API 키가 설정되어 있지 않습니다."
                    )
                    st.stop()

            progress_bar = st.progress(0)
            status_placeholder = st.empty()

            def update_strategy_progress(step, message):
                progress_bar.progress(min(step / 7, 1.0))
                status_placeholder.write(
                    f"STEP {step}/7 · {message}"
                )

            with st.spinner("마케팅 전략을 생성하고 있습니다..."):

                pipeline_result = (
                    strategy_pipeline_engine.run_strategy_pipeline(
                        project_dir=CURRENT_DATA_DIR,
                        api_key=pipeline_api_key,
                        font_dir=str(Path(__file__).resolve().parent / "fonts"),
                        progress_callback=update_strategy_progress,
                        reuse_existing=use_saved_strategy
                    )
                )

            st.success(
                "AI 마케팅 전략 및 PDF 보고서 생성 완료!"
            )

            st.write(
                "시장 기회 가설:",
                pipeline_result["opportunity_count"],
                "개"
            )

            st.write(
                "전략 근거 후보:",
                pipeline_result["evidence_count"],
                "개"
            )

            if pipeline_result["gemini_called"]:
                st.caption("Gemini API 호출: 1회")
            else:
                st.caption("기존 Gemini 전략 재사용")

            st.info(
                "아래에서 최신 전략과 PDF 보고서를 확인할 수 있습니다."
            )

        except Exception as e:
            st.error(f"전략 자동 생성 오류: {e}")

else:
    st.info(
        "현재 프로젝트에 시장 동향 또는 검증된 소비자 인사이트가 "
        "없습니다. 앞선 분석 단계를 먼저 진행해주세요."
    )

st.divider()

# ===== STEP 27-5B: LATEST STRATEGY REPORT =====

st.subheader("최신 AI 마케팅 전략 보고서")

latest_report_path = (
    CURRENT_DATA_DIR
    / "marketing_strategy"
    / "market_strategy_report_v2.md"
)

if latest_report_path.exists():

    latest_report = latest_report_path.read_text(
        encoding="utf-8"
    )

    st.caption(
        "현재 프로젝트의 AI 전략 및 댓글 근거를 "
        "통합한 보고서입니다."
    )

    with st.expander("최신 전략 보고서 보기", expanded=False):
        st.markdown(latest_report)



    with st.expander("고급 설정 · PDF 다시 생성", expanded=False):
        st.markdown("#### PDF 보고서 생성")

        st.caption(
            "현재 선택한 프로젝트의 최신 Markdown 보고서를 "
            "Noto Sans KR 디자인의 PDF로 변환합니다."
        )

        if st.button(
            "PDF 보고서 생성 / 갱신",
            key="generate_strategy_pdf_button"
        ):
            try:
                import importlib
                import pdf_report_engine

                importlib.reload(pdf_report_engine)

                with st.spinner("PDF 보고서를 생성하고 있습니다..."):
                    generated_pdf = pdf_report_engine.generate_pdf_report(
                        project_dir=CURRENT_DATA_DIR,
                        font_dir=str(Path(__file__).resolve().parent / "fonts")
                    )

                st.success("PDF 보고서 생성 완료!")
                st.caption(f"저장 파일: {generated_pdf.name}")

            except Exception as e:
                st.error(f"PDF 보고서 생성 실패: {e}")

    # ===== STEP 27-5D-2: PDF DOWNLOAD =====
    pdf_report_path = (
        CURRENT_DATA_DIR
        / "marketing_strategy"
        / "market_strategy_report_v2.pdf"
    )

    if pdf_report_path.exists():
        st.download_button(
            label="📄 PDF 전략 보고서 다운로드",
            data=pdf_report_path.read_bytes(),
            file_name="market_strategy_report.pdf",
            mime="application/pdf",
            key="download_strategy_pdf"
        )
    else:
        st.info(
            "PDF 보고서가 아직 없습니다. "
            "PDF 생성 단계를 먼저 실행해주세요."
        )

    with st.expander("개발용 Markdown 다운로드"):

        st.download_button(
            label="Markdown 원본 다운로드",
            data=latest_report,
            file_name="market_strategy_report_v2.md",
            mime="text/markdown",
            key="download_latest_strategy_report"
        )

else:
    st.info(
        "현재 프로젝트의 최신 전략 보고서가 없습니다. "
        "전략 보고서 생성 후 확인할 수 있습니다."
    )

st.divider()


# ===== STEP 27-4A: STRATEGY DASHBOARD =====

st.subheader("AI 기반 시장 진입 전략")

st.caption(
    "AI가 제안한 시장 기회 가설을 실제 소비자 댓글과 "
    "연결하여 보여줍니다. 전략의 성공 가능성이 검증된 것은 아닙니다."
)

import json as strategy_json

structured_path = (
    CURRENT_DATA_DIR
    / "marketing_strategy"
    / "strategy_structured.json"
)

if structured_path.exists():

    with open(structured_path, "r", encoding="utf-8") as f:
        structured_data = strategy_json.load(f)

    opportunities = structured_data.get("opportunities", [])

    if opportunities:

        st.markdown("#### 시장 기회 가설 비교")

        comparison = []

        for op in opportunities:

            summary = op.get("evidence_summary", {})
            hypothesis = op.get("strategic_hypothesis", {})

            comparison.append({
                "시장 기회": op.get("opportunity_name", ""),
                "타깃 고객": hypothesis.get("target_customer", ""),
                "근거 댓글": summary.get("comment_count", 0),
                "고유 게시물": summary.get("unique_post_count", 0),
                "검토 상태": op.get("status", "")
            })

        st.dataframe(
            comparison,
            use_container_width=True,
            hide_index=True
        )

        st.markdown("#### 전략별 근거 분석")

        selected_opportunity = st.selectbox(
            "검토할 시장 기회 선택",
            options=list(range(len(opportunities))),
            format_func=lambda i: opportunities[i].get(
                "opportunity_name", f"가설 {i + 1}"
            ),
            key="strategy_opportunity_selector"
        )

        op = opportunities[selected_opportunity]
        hypothesis = op.get("strategic_hypothesis", {})
        summary = op.get("evidence_summary", {})

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "근거 댓글",
                summary.get("comment_count", 0)
            )

        with col2:
            st.metric(
                "고유 게시물",
                summary.get("unique_post_count", 0)
            )

        st.markdown("**타깃 고객 가설**")
        st.write(hypothesis.get("target_customer", ""))

        st.markdown("**포지셔닝 가설**")
        st.write(hypothesis.get("positioning", ""))

        st.markdown("**실제 소비자 반응**")

        for i, evidence in enumerate(
            op.get("observed_facts", []),
            start=1
        ):

            with st.expander(f"근거 댓글 {i}", expanded=(i == 1)):

                st.write(
                    "**소비자 반응:**",
                    evidence.get("fact", "")
                )

                st.write(
                    "**댓글 원문:**",
                    evidence.get("comment", "")
                )

                url = evidence.get("source_url", "")

                if isinstance(url, str) and url.startswith(
                    ("https://www.instagram.com/",
                     "http://www.instagram.com/")
                ):
                    st.markdown(
                        f"[인스타그램 원문 보기]({url})"
                    )

        st.markdown("**추가 검증 필요사항**")

        for need in op.get("validation_needs", []):
            st.write("•", need)

        st.info(
            "위 소비자 반응은 AI가 원문에 근거한다고 판정한 "
            "결과입니다. 별도의 인간 검증 및 추가 시장조사가 필요합니다."
        )

    else:
        st.info("생성된 시장 기회 가설이 없습니다.")

else:
    st.info(
        "아직 해당 프로젝트의 마케팅 전략 결과가 없습니다. "
        "전략 생성 및 근거 검증을 먼저 진행해주세요."
    )

st.divider()



# ===== STEP 29-9D: LEGACY REPORT =====
report_path = CURRENT_DATA_DIR / "market_strategy_report.md"

with st.expander("이전 버전 시장분석 보고서 (참고용)", expanded=False):
    if report_path.exists():
        report = report_path.read_text(encoding="utf-8")

        st.caption(
            "과거 분석 방식으로 생성된 보고서입니다. "
            "최신 AI 전략 보고서는 위 PDF 다운로드를 이용해주세요."
        )

        st.markdown(report)

        st.download_button(
            "이전 보고서 다운로드",
            data=report,
            file_name="market_strategy_report_legacy.md",
            mime="text/markdown",
            key="download_legacy_report"
        )
    else:
        st.caption("이 프로젝트에는 이전 버전 보고서가 없습니다.")

st.divider()

# ===== END LEGACY REPORT =====

st.caption("Market Insight AI | Research Prototype")




# AI 분석 테스트
st.divider()


# ===== POSITIONING AGENT V2 DASHBOARD =====
# Existing strategy dashboard remains unchanged.

from positioning_agent.strategy_dashboard import (
    render_positioning_strategy_dashboard
)

positioning_package_path = (
    CURRENT_DATA_DIR
    / "positioning_strategy"
    / "strategy_package.json"
)

if positioning_package_path.is_file():
    st.divider()
    render_positioning_strategy_dashboard(
        positioning_package_path
    )



# ===== STEP 9-133: COMMENT CLASSIFICATION RESULTS =====
st.divider()
st.subheader("YouTube 댓글 AI 분류 결과")

classification_path = (
    CURRENT_DATA_DIR
    / "youtube_analysis"
    / "comment_classifications.json"
)

if classification_path.is_file():
    try:
        import json

        classification_data = json.loads(
            classification_path.read_text(encoding="utf-8")
        )

        classification_records = classification_data.get(
            "classifications", []
        )

        if (
            classification_data.get("validation_status") != "unverified"
            or not isinstance(classification_records, list)
        ):
            st.warning("댓글 분류 결과 형식을 확인해야 합니다.")

        else:
            st.caption(
                "AI 자동 분류 결과입니다. "
                "댓글 내용 및 제품 효능이 검증된 것은 아닙니다."
            )

            display_records = [
                {
                    "근거 ID": item.get("evidence_id", ""),
                    "분류": ", ".join(item.get("labels", []))
                }
                for item in classification_records
                if isinstance(item, dict)
            ]

            st.dataframe(
                display_records,
                use_container_width=True,
                hide_index=True
            )

    except (OSError, ValueError, TypeError):
        st.warning("댓글 분류 결과를 불러오지 못했습니다.")

else:
    st.info(
        "현재 프로젝트에 저장된 YouTube 댓글 "
        "AI 분류 결과가 없습니다."
    )
