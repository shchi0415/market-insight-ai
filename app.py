"""AI Positioning Agent: lean Streamlit application.

The Ongredients demo replays previously saved research; new projects retain
existing keyword, search and relevance engines. Legacy Instagram dashboards
have intentionally been removed from this app entrypoint only.
"""
import json
import os
import uuid
import shutil
from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="AI Positioning Agent", page_icon="📊", layout="wide"
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

/* Navigation links land on the rendered section heading, not an empty spacer. */
section[data-testid="stMain"] h2[id] {
    scroll-margin-top: 1.5rem;
}

/* 메인 페이지 구분선 */
section[data-testid="stMain"] hr {
    margin-top: 1.2rem;
    margin-bottom: 1.2rem;
    border: 0 !important;
    border-top: 6px solid rgba(165, 180, 200, 0.65) !important;
    opacity: 1 !important;
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




# ===== PROJECTS: NO LEGACY BEAUTY MARKET TEST AUTO-CREATION =====
APP_DIR = Path(__file__).resolve().parent
DATA_DIR = APP_DIR / "data"
PROJECTS_DIR = DATA_DIR / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
DEMO_ID = "dbc345844047"
DEMO_ASSETS = APP_DIR / "positioning_demo_data" / "ongredients_analysis"
manifest_path = DEMO_ASSETS / "demo_manifest.json"

if manifest_path.is_file():
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    demo_id = manifest.get("project_id", DEMO_ID)
    if demo_id != DEMO_ID:
        st.error("온그리디언츠 Demo 프로젝트 ID가 예상과 다릅니다.")
        st.stop()
    demo_folder = PROJECTS_DIR / DEMO_ID
    demo_folder.mkdir(parents=True, exist_ok=True)
    demo_info = demo_folder / "project_info.json"
    if not demo_info.exists():
        demo_info.write_text(json.dumps({
            "project_id": DEMO_ID,
            "project_name": manifest.get("project_name", "온그리디언츠 · AI 포지셔닝 분석 DEMO"),
            "demo_mode": True,
            "demo_type": "precomputed_analysis",
        }, ensure_ascii=False, indent=2), encoding="utf-8")

project_options = {}
for folder in sorted(PROJECTS_DIR.iterdir()):
    if not folder.is_dir() or folder.name == "87437a415e4d":
        continue  # Old example stays on disk but is hidden from this app.
    project_info = folder / "project_info.json"
    if project_info.is_file():
        try:
            info = json.loads(project_info.read_text(encoding="utf-8"))
            project_name = info.get("project_name", folder.name)
        except (OSError, ValueError, TypeError):
            project_name = folder.name
    else:
        project_name = folder.name
    project_options[folder.name] = {"label": project_name, "path": folder}

st.sidebar.subheader("분석 프로젝트")
with st.sidebar.expander("+ 새 프로젝트 생성", expanded=False):
    new_project_name = st.text_input("프로젝트 이름", key="new_project_name")
    if st.button("프로젝트 생성", key="create_new_project_button"):
        name = new_project_name.strip()
        if not name:
            st.error("프로젝트 이름을 입력해 주세요.")
        elif len(name) > 50:
            st.error("프로젝트 이름은 50자 이내로 입력해 주세요.")
        else:
            new_id = uuid.uuid4().hex[:12]
            dest = PROJECTS_DIR / new_id
            dest.mkdir(parents=True, exist_ok=False)
            (dest / "project_info.json").write_text(
                json.dumps({"project_id": new_id, "project_name": name},
                           ensure_ascii=False, indent=2), encoding="utf-8"
            )
            st.session_state["selected_project"] = new_id
            st.rerun()

project_options = dict(sorted(project_options.items(),
    key=lambda item: (item[0] != DEMO_ID, item[1]["label"])))
if not project_options:
    st.warning("프로젝트가 없습니다. 새 프로젝트를 생성해 주세요.")
    st.stop()

# Clear obsolete selection left over from the earlier example page.
if st.session_state.get("selected_project") not in project_options:
    st.session_state["selected_project"] = next(iter(project_options))
selected_project = st.sidebar.selectbox(
    "프로젝트 선택", options=list(project_options),
    format_func=lambda project_id: project_options[project_id]["label"],
    key="selected_project"
)
CURRENT_DATA_DIR = project_options[selected_project]["path"]

# The input form stores a product_info.json on disk. Reset only when a new
# browser session begins, not on Streamlit button-triggered reruns.
# Do not delete any of the precomputed Demo research assets.
if "_product_input_initialized_projects" not in st.session_state:
    st.session_state["_product_input_initialized_projects"] = set()
if selected_project not in st.session_state["_product_input_initialized_projects"]:
    saved_product_input = CURRENT_DATA_DIR / "product_info.json"
    if saved_product_input.is_file():
        try:
            saved_product_input.unlink()
        except OSError as exc:
            st.warning(f"이전 제품 입력값을 초기화하지 못했습니다: {exc}")
    st.session_state["_product_input_initialized_projects"].add(selected_project)

@st.dialog("프로젝트 삭제 확인")
def confirm_project_deletion():
    st.warning(f"'{project_options[selected_project]['label']}' 프로젝트를 삭제하시겠습니까?")
    st.caption("데이터는 삭제하지 않고 휴지통 폴더로 이동합니다.")
    a, b = st.columns(2)
    with a:
        if st.button("취소", use_container_width=True):
            st.rerun()
    with b:
        if st.button("삭제하기", type="primary", use_container_width=True):
            target = CURRENT_DATA_DIR.resolve()
            if (selected_project == DEMO_ID
                    or target.parent != PROJECTS_DIR.resolve()
                    or target.name != selected_project
                    or not target.is_dir()
                    or CURRENT_DATA_DIR.is_symlink()):
                st.error("삭제할 수 없는 프로젝트입니다.")
                return
            trash = DATA_DIR / "project_trash"
            trash.mkdir(exist_ok=True)
            shutil.move(str(target), str(trash / f"{selected_project}_{uuid.uuid4().hex[:8]}"))
            st.session_state.pop("selected_project", None)
            st.rerun()

if st.sidebar.button("🗑️ 프로젝트 삭제", disabled=(selected_project == DEMO_ID)):
    confirm_project_deletion()

# ===== SECTION NAVIGATION =====
st.sidebar.divider()
st.sidebar.markdown("### Navigation")
NAVIGATION = [
    ("01 · 제품 정보 입력", "product-input"),
    ("02 · 검색 키워드 생성", "youtube-keywords"),
    ("03 · YouTube 영상 검색", "youtube-search"),
    ("04 · AI 영상 관련성 평가", "video-relevance"),
    ("05 · 분석 영상 선별", "video-selection"),
    ("06 · 댓글 수집 및 소비자 인사이트 분석", "consumer-analysis"),
    ("07 · 시장 기회·포지셔닝 전략", "positioning-strategy"),
]
for label, anchor in NAVIGATION:
    st.sidebar.markdown(
        f'<a href="#{anchor}" target="_self" '
        'style="display:block;padding:6px 10px;text-decoration:none;'
        f'border-radius:6px">{label}</a>',
        unsafe_allow_html=True
    )

# A new Streamlit browser session is created on first visit / hard refresh.
# Do not execute this block on widget-triggered reruns; leave navigation anchors intact.
if "_initial_viewport_positioned" not in st.session_state:
    st.session_state["_initial_viewport_positioned"] = True
    import streamlit.components.v1 as components
    components.html("""
    <script>
    (() => {
      const root = window.parent;
      function scrollToPageTop() {
        try {
          const doc = root.document;
          // A previously selected sidebar anchor can be restored by the browser.
          if (root.location.hash) {
            root.history.replaceState(null, '', root.location.pathname + root.location.search);
          }
          const page = doc.querySelector('[data-testid="stAppViewContainer"]')
                    || doc.querySelector('section.main');
          if (page) page.scrollTop = 0;
          doc.documentElement.scrollTop = 0;
          doc.body.scrollTop = 0;
          root.scrollTo({top: 0, left: 0, behavior: 'instant'});
        } catch (_) {}
      }
      scrollToPageTop();
      root.requestAnimationFrame(scrollToPageTop);
      // Wait for Streamlit's initial render and browser scroll restoration.
      [120, 350, 800].forEach(ms => root.setTimeout(scrollToPageTop, ms));
    })();
    </script>
    """, height=0)

st.title("AI Positioning Agent")
st.caption("AI 기반 YouTube 시장조사 · 소비자 인사이트 · 제품 포지셔닝")
if selected_project == DEMO_ID:
    st.info("온그리디언츠 DEMO · 과거 분석 결과를 단계별로 재현합니다. "
            "실제 Gemini/YouTube API를 새로 호출하지 않습니다.")
else:
    st.caption("신규 프로젝트: 각 분석 단계는 입력값과 데이터 준비 상태에 따라 실행할 수 있습니다.")


# ===== POSITIONING AGENT V2 PRODUCT INPUT =====
from positioning_agent.product_input_ui import (
    render_product_input
)

st.header("01 · 제품 정보 입력", anchor="product-input")

with st.container(border=True):
    render_product_input(CURRENT_DATA_DIR)

# Only the first successful product save in Step 01 scrolls to the very top.
# Reading this on the following Streamlit rerun avoids changing the product form.
# Buttons in Steps 02-07 never trigger a scroll to top.
if not st.session_state.get("_step01_save_scrolled", False):
    product_path = CURRENT_DATA_DIR / "product_info.json"
    if product_path.is_file():
        st.session_state["_step01_save_scrolled"] = True
        import streamlit.components.v1 as components
        components.html("""
        <script>
        (() => {
          const root = window.parent;
          function scrollToPageTop() {
            try {
              const doc = root.document;
              const page = doc.querySelector('[data-testid="stAppViewContainer"]')
                        || doc.querySelector('section.main');
              if (page) page.scrollTop = 0;
              doc.documentElement.scrollTop = 0;
              doc.body.scrollTop = 0;
              root.scrollTo({top: 0, left: 0, behavior: 'instant'});
            } catch (_) {}
          }
          scrollToPageTop();
          root.requestAnimationFrame(scrollToPageTop);
          [100, 300].forEach(ms => root.setTimeout(scrollToPageTop, ms));
        })();
        </script>
        """, height=0)

st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)
st.divider()

# ===== STEP 9-164: AUTOMATED YOUTUBE KEYWORDS =====
st.header("02 · 검색 키워드 생성", anchor="youtube-keywords")
with st.container(border=True):
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

    is_ongredients_demo = selected_project == "dbc345844047"

    if is_ongredients_demo:
        demo_keyword_path = (
            Path(__file__).resolve().parent
            / "positioning_demo_data"
            / "ongredients_analysis"
            / "keyword_generation.json"
        )
        demo_keyword_revealed = st.session_state.get(
            "ongredients_demo_keywords_revealed", False
        )

        # 결과 공개 전에는 기존 결과를 표시하지 않는다.
        keyword_result_path = (
            demo_keyword_path
            if demo_keyword_revealed
            else CURRENT_DATA_DIR / "_demo_keywords_not_revealed.json"
        )

    keyword_product_path = CURRENT_DATA_DIR / "product_info.json"

    if is_ongredients_demo and not demo_keyword_revealed:
        st.caption(
            "시연 모드: 사전에 생성한 키워드 결과를 불러옵니다. "
            "Gemini API는 호출하지 않습니다."
        )

        if st.button(
            "검색 키워드 자동 생성",
            key="ongredients_demo_keyword_button"
        ):
            if demo_keyword_path.is_file():
                st.session_state[
                    "ongredients_demo_keywords_revealed"
                ] = True
                st.rerun()
            else:
                st.error("Demo 키워드 데이터가 없습니다.")

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

    elif is_ongredients_demo:
        st.info("위의 버튼을 눌러 Demo 키워드 결과를 확인해 주세요.")

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





st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)
st.divider()

# ===== STEP 9-181: YOUTUBE VIDEO SEARCH UI =====
if selected_project == "dbc345844047":
    st.header("03 · YouTube 영상 검색", anchor="youtube-search")
    with st.container(border=True):
        st.caption(
            "시연 모드: 기존 YouTube 검색 결과를 불러옵니다. "
            "실제 API는 호출하지 않습니다."
        )

        keyword_done = st.session_state.get(
            "ongredients_demo_keywords_revealed", False
        )

        youtube_done = st.session_state.get(
            "ongredients_demo_youtube_revealed", False
        )

        demo_youtube_path = (
            Path(__file__).resolve().parent
            / "positioning_demo_data"
            / "ongredients_analysis"
            / "youtube_search_demo.json"
        )

        if not keyword_done:
            st.info("먼저 검색 키워드 생성 단계를 완료해 주세요.")

        if not youtube_done:
            if st.button(
                "YouTube 영상 검색 실행",
                key="ongredients_demo_youtube_search",
                disabled=not keyword_done
            ):
                if demo_youtube_path.is_file():
                    st.session_state[
                        "ongredients_demo_youtube_revealed"
                    ] = True
                    st.rerun()
                else:
                    st.error("Demo 영상 검색 결과 파일이 없습니다.")

        if youtube_done:
            from positioning_agent.youtube_search_demo_ui import (
                render_youtube_search_demo
            )
            render_youtube_search_demo(demo_youtube_path)

else:
    # ===== STEP 9-181: YOUTUBE VIDEO SEARCH UI =====
    st.header("03 · YouTube 영상 검색", anchor="youtube-search")
    with st.container(border=True):
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




st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)
st.divider()

# ===== STEP 9-202: VIDEO RELEVANCE UI =====
st.header("04 · AI 영상 관련성 평가", anchor="video-relevance")
st.markdown(
    """<style>
    /* STEP 04의 수치 지표만 개별 카드로 표시 */
    .st-key-video_relevance_card [data-testid="stMetric"] {
        border: 1px solid rgba(137, 153, 172, 0.45);
        border-radius: 12px;
        padding: 16px 18px;
        background: rgba(137, 153, 172, 0.06);
        min-height: 112px;
    }
    </style>""",
    unsafe_allow_html=True,
)
with st.container(border=True, key="video_relevance_card"):
    import json as relevance_json
    from collections import Counter

    from positioning_agent.video_relevance_engine import (
        run_batched_video_relevance_safely
    )

    relevance_dir = CURRENT_DATA_DIR / "youtube_analysis"
    search_path = relevance_dir / "youtube_search_results.json"
    relevance_path = relevance_dir / "video_relevance_results.json"

   
    if selected_project == "dbc345844047":
        demo_dir = (
            Path(__file__).resolve().parent
            / "positioning_demo_data"
            / "ongredients_analysis"
        )

        demo_relevance_path = (
            demo_dir / "youtube_relevance_demo.json"
        )
        demo_search_path = (
            demo_dir / "youtube_search_demo.json"
        )

        youtube_done = st.session_state.get(
            "ongredients_demo_youtube_revealed", False
        )
        relevance_done = st.session_state.get(
            "ongredients_demo_relevance_revealed", False
        )

        st.caption(
            "시연 모드: 사전에 저장된 Gemini 평가 결과를 "
            "불러옵니다. 새로운 API 호출은 없습니다."
        )

        if not youtube_done:
            st.info(
                "먼저 YouTube 영상 자동 검색 단계를 "
                "완료해 주세요."
            )

        if not relevance_done:
            if st.button(
                "AI 영상 관련성 평가 실행",
                key="ongredients_demo_relevance_button",
                disabled=not youtube_done
            ):
                if (
                    demo_relevance_path.is_file()
                    and demo_search_path.is_file()
                ):
                    st.session_state[
                        "ongredients_demo_relevance_revealed"
                    ] = True
                    st.rerun()
                else:
                    st.error(
                        "Demo 관련성 평가 데이터가 없습니다."
                    )

        if relevance_done:
            if (
                demo_relevance_path.is_file()
                and demo_search_path.is_file()
            ):
                from positioning_agent.youtube_relevance_demo_ui import (
                    render_youtube_relevance_demo
                )

                render_youtube_relevance_demo(
                    demo_relevance_path,
                    demo_search_path
                )
            else:
                st.error(
                    "Demo 관련성 평가 데이터를 찾을 수 없습니다."
                )

    elif relevance_path.is_file():

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
                        "Gemini가 영상을 15개씩 나누어 평가하고 있습니다..."
                    ):
                        try:
                            result = run_batched_video_relevance_safely(
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

st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)
st.divider()

# ===== ONgredients DEMO: YOUTUBE VIDEO SELECTION =====
if selected_project == "dbc345844047":
    st.header("05 · 분석 영상 선별", anchor="video-selection")
    with st.container(border=True):
        st.caption(
            "시연 모드: 기존 규칙 기반 영상 선별 결과를 "
            "불러옵니다. API 호출은 없습니다."
        )

        relevance_done = st.session_state.get(
            "ongredients_demo_relevance_revealed", False
        )
        selection_done = st.session_state.get(
            "ongredients_demo_selection_revealed", False
        )

        demo_selection_dir = (
            Path(__file__).resolve().parent
            / "positioning_demo_data"
            / "ongredients_analysis"
        )

        selection_path = (
            demo_selection_dir / "video_selection_results.json"
        )
        search_path = (
            demo_selection_dir / "youtube_search_demo.json"
        )

        if not relevance_done:
            st.info("먼저 YouTube 영상 AI 관련성 평가를 완료해 주세요.")

        if not selection_done:
            if st.button(
                "분석 대상 영상 선별 실행",
                key="ongredients_demo_selection_button",
                disabled=not relevance_done
            ):
                if selection_path.is_file() and search_path.is_file():
                    st.session_state[
                        "ongredients_demo_selection_revealed"
                    ] = True
                    st.rerun()
                else:
                    st.error("Demo 영상 선별 데이터가 없습니다.")

        if selection_done:
            if selection_path.is_file() and search_path.is_file():
                from positioning_agent.youtube_selection_demo_ui import (
                    render_youtube_selection_demo
                )

                render_youtube_selection_demo(
                    selection_path,
                    search_path
                )
            else:
                st.error("Demo 영상 선별 데이터를 찾을 수 없습니다.")
# ===== END ONgredients DEMO: YOUTUBE VIDEO SELECTION =====



# ===== STEP 06: YOUTUBE COMMENT COLLECTION DEMO =====
st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)
st.divider()

st.header("06 · 댓글 수집 및 소비자 인사이트 분석", anchor="consumer-analysis")
st.subheader("06-1 · 댓글 수집·전처리")
with st.container():
    if selected_project == DEMO_ID:
        st.caption(
            "시연 모드: 과거에 수집·전처리한 YouTube 댓글의 집계 결과를 "
            "불러옵니다. YouTube API나 Gemini API를 새로 호출하지 않습니다."
        )
        selection_done = st.session_state.get(
            "ongredients_demo_selection_revealed", False
        )
        comment_done = st.session_state.get(
            "ongredients_demo_comments_revealed", False
        )
        summary_path = (
            Path(__file__).resolve().parent
            / "positioning_demo_data"
            / "ongredients_analysis"
            / "youtube_comments_demo_summary.json"
        )

        if not selection_done:
            st.info("먼저 05 · 분석 영상 선별을 완료해 주세요.")
        if not comment_done:
            if st.button(
                "YouTube 댓글 수집·전처리 결과 확인",
                key="ongredients_demo_comments_button",
                disabled=not selection_done,
            ):
                if summary_path.is_file():
                    st.session_state["ongredients_demo_comments_revealed"] = True
                    st.rerun()
                else:
                    st.error("댓글 수집 Demo 집계 파일을 찾을 수 없습니다.")

        if comment_done:
            if not summary_path.is_file():
                st.error("댓글 수집 Demo 집계 파일을 찾을 수 없습니다.")
            else:
                try:
                    with summary_path.open("r", encoding="utf-8") as f:
                        comment_summary = json.load(f)
                    stats = comment_summary["statistics"]
                    total = int(stats["total_comments"])
                    duplicates = int(stats["duplicate_extra"])
                    with st.container(border=True):
                        st.markdown("#### 댓글 수집 현황")
                        st.caption("선별한 영상에서 과거 수집한 댓글의 집계 결과입니다.")
                        c1, c2, c3 = st.columns(3, gap="medium")
                        c1.metric("수집 댓글", f"{total:,}개")
                        c2.metric("댓글 수집 영상", f"{int(stats['videos_with_comments']):,}개")
                        c3.metric("중복 추가 표시", f"{duplicates:,}개")

                    with st.container(border=True):
                        st.markdown("#### 영상 관련성별 댓글 분포")
                        core = int(stats["core_comments"])
                        adjacent = int(stats["adjacent_comments"])
                        relevance_total = core + adjacent
                        core_pct = core / relevance_total * 100 if relevance_total else 0
                        adjacent_pct = adjacent / relevance_total * 100 if relevance_total else 0

                        st.markdown(
                            f"""
                            <div style="display:flex; justify-content:space-between;
                                        align-items:center; gap:12px; flex-wrap:wrap;
                                        margin:12px 0 16px 0;">
                                <div style="font-size:1rem;">
                                    <span style="display:inline-block;width:10px;height:10px;
                                                 background:#2686E6;border-radius:50%;margin-right:6px;"></span>
                                    <b>핵심 관련(Core)</b>&nbsp; {core:,}개 · {core_pct:.1f}%
                                </div>
                                <div style="font-size:1rem;text-align:right;margin-left:auto;">
                                    <span style="display:inline-block;width:10px;height:10px;
                                                 background:#23B58D;border-radius:50%;margin-right:6px;"></span>
                                    <b>인접 관련(Adjacent)</b>&nbsp; {adjacent:,}개 · {adjacent_pct:.1f}%
                                </div>
                            </div>
                            <div style="display:flex;width:100%;height:14px;
                                        border-radius:8px;overflow:hidden;background:#30343F;">
                                <div style="width:{core_pct:.2f}%;background:#2686E6;"></div>
                                <div style="width:{adjacent_pct:.2f}%;background:#23B58D;"></div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        # Reserve space below the custom bar within the card boundary.
                        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)

                    with st.container(border=True):
                        st.markdown("#### 전처리 점검")
                        f1, f2, f3 = st.columns(3)
                        f1.metric("중복 추가 표시", f"{duplicates:,}개")
                        f2.metric("짧은 댓글 검토 표시", f"{int(stats['short_text_review']):,}개")
                        f3.metric("URL 포함 표시", f"{int(stats['url_present']):,}개")
                        st.caption(
                            f"규칙 기반으로 분석 가능 표시된 댓글은 {int(stats['analysis_eligible']):,}개입니다. "
                            f"중복 추가 표시를 제외한 단순 계산값은 {total - duplicates:,}개이지만, "
                            "최종 AI 분석 표본으로 검증된 수치는 아닙니다. "
                            "짧은 댓글과 URL 표시는 별도의 제외 건수가 아닙니다."
                        )
                    with st.expander("영상별 댓글 수집 현황 보기", expanded=False):
                        rows = [
                            {
                                "영상 ID": video.get("video_id", ""),
                                "관련성": video.get("video_relevance", ""),
                                "수집 댓글": int(video.get("comment_count", 0)),
                                "중복 추가 표시": int(video.get("duplicate_extra", 0)),
                            }
                            for video in comment_summary.get("videos", [])
                        ]
                        st.dataframe(rows, use_container_width=True, hide_index=True)
                    st.success("댓글 수집·전처리 집계 결과를 불러왔습니다.")
                except (OSError, ValueError, TypeError, KeyError) as error:
                    st.error("댓글 집계 데이터를 읽지 못했습니다. JSON 구조를 확인해 주세요.")

    else:
        st.info(
            "새 프로젝트에서의 YouTube 댓글 수집·분석 실행 기능은 "
            "아직 연결되지 않았습니다."
        )


st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)
st.divider()

st.header("06-2 · AI 소비자 분석", anchor="consumer-ai-analysis")
with st.container(border=True):
    if selected_project == DEMO_ID:
        if not st.session_state.get("ongredients_demo_comments_revealed", False):
            st.info("먼저 06-1 · 댓글 수집·전처리 단계를 완료해 주세요.")
        else:
            ai_summary_path = (
                Path(__file__).resolve().parent
                / "positioning_demo_data"
                / "ongredients_analysis"
                / "youtube_comment_ai_demo_summary.json"
            )
            ai_done = st.session_state.get("ongredients_demo_ai_comments_revealed", False)
            if not ai_done:
                if st.button(
                    "AI 소비자 니즈·감성 분석 결과 확인",
                    key="ongredients_demo_ai_comments_button",
                ):
                    if ai_summary_path.is_file():
                        st.session_state["ongredients_demo_ai_comments_revealed"] = True
                        st.rerun()
                    else:
                        st.error("AI 댓글 분석 Demo 집계 파일을 찾을 수 없습니다. JSON 파일을 먼저 업로드해 주세요.")
            if ai_done:
                if not ai_summary_path.is_file():
                    st.error("AI 댓글 분석 Demo 집계 파일을 찾을 수 없습니다.")
                else:
                    try:
                        with ai_summary_path.open("r", encoding="utf-8") as f:
                            ai_data = json.load(f)
                        sc = ai_data["sentiment"]
                        status = ai_data["analysis_status"]
                        n = int(ai_data["record_count"])
                        with st.container(border=True):
                            st.markdown("#### AI 댓글 분석 요약")
                            a1,a2,a3 = st.columns(3)
                            a1.metric("AI 분류 처리 댓글", f"{n:,}개")
                            a2.metric("분석 완료 상태", f"{int(status.get('analyzed',0)):,}개")
                            a3.metric("추가 검토 필요", f"{int(status.get('requires_review',0)):,}개")
                            st.caption("사전 저장된 Gemini 분석 결과입니다. 분류 결과는 사람의 검증을 거친 확정 판정이 아닙니다.")
                        with st.container(border=True):
                            st.markdown("#### 전체 댓글 감성 분포")
                            order = [("긍정","positive"),("중립","neutral"),("부정","negative"),("혼합","mixed"),("기타","not_applicable")]
                            sentiment_rows = [{"감성": name, "댓글 수": int(sc.get(key,0))} for name,key in order if sc.get(key,0)]
                            import altair as alt
                            chart = (
                                alt.Chart(alt.Data(values=sentiment_rows))
                                .mark_bar(color="#80C4F6", size=24)
                                .encode(
                                    y=alt.Y(
                                        "감성:N",
                                        sort=["긍정", "중립", "부정", "혼합", "기타"],
                                        title="감성",
                                        axis=alt.Axis(labelAngle=0),
                                    ),
                                    x=alt.X("댓글 수:Q", title="댓글 수"),
                                    tooltip=["감성:N", "댓글 수:Q"],
                                )
                                .properties(height=230)
                            )
                            st.altair_chart(chart, use_container_width=True)
                            st.dataframe(sentiment_rows, use_container_width=True, hide_index=True)
                            st.caption("영상에 대한 호감과 제품 평가 등이 혼재한 전체 댓글 감성입니다. 제품 만족도 분포로 해석하지 마세요.")
                        with st.container(border=True):
                            st.markdown("#### 소비자 니즈 관련 주요 주제")
                            themes = ai_data.get("themes_keyword_based_overlapping",{})
                            theme_rows = [{"주제": k, "관련 댓글 수": int(v)} for k,v in sorted(themes.items(), key=lambda kv:-kv[1])]
                            # 표와 동일한 행 순서 및 수치를 차트에 사용
                            theme_order = [row["주제"] for row in theme_rows]
                            if theme_rows:
                                theme_chart = (
                                    alt.Chart(alt.Data(values=theme_rows))
                                    .mark_bar(color="#80C4F6", size=24)
                                    .encode(
                                        y=alt.Y("주제:N", sort=theme_order, title="주제", axis=alt.Axis(labelAngle=0)),
                                        x=alt.X("관련 댓글 수:Q", title="관련 댓글 수"),
                                        tooltip=["주제:N", "관련 댓글 수:Q"],
                                    )
                                    .properties(height=max(220, len(theme_rows) * 36))
                                )
                                st.altair_chart(theme_chart, use_container_width=True)
                            st.dataframe(theme_rows, use_container_width=True, hide_index=True)
                            st.caption(f"'소비자 니즈'로 분류된 {int(ai_data.get('theme_denominator',0)):,}개 댓글의 텍스트를 키워드 규칙으로 묶은 탐색적 집계입니다. 한 댓글이 여러 주제에 포함될 수 있습니다.")
                        with st.container(border=True):
                            st.markdown("#### 분석 내용 유형 및 평가 대상")
                            st.write("**내용 분류** (복수 선택 가능)")
                            labels = ai_data.get("content_labels",{})
                            labels_ko = {"consumer_need":"소비자 니즈", "product_experience":"제품 경험", "product_evaluation":"제품 평가", "general_reaction":"일반 반응", "purchase_interest":"구매 관심", "irrelevant_spam":"무관/스팸"}
                            st.dataframe([{"유형":labels_ko.get(k,k),"댓글 수":v} for k,v in labels.items()], use_container_width=True, hide_index=True)
                            with st.expander("감성 평가 대상·스팸 검토 상태", expanded=False):
                                st.write("감성 평가 대상")
                                st.json(ai_data.get("sentiment_target",{}))
                                st.write("홍보·스팸 의심 여부 (검토용)")
                                st.json(ai_data.get("spam_review_status",{}))
                        st.success("AI 댓글 분석 결과를 불러왔습니다. 다음 07단계에서 시장 기회와 포지셔닝 전략을 확인할 수 있습니다.")
                    except (OSError, ValueError, TypeError, KeyError):
                        st.error("AI 댓글 분석 집계 데이터를 읽지 못했습니다. JSON 구조를 확인해 주세요.")
    else:
        st.info("새 프로젝트의 AI 소비자 분석 기능은 아직 연결되지 않았습니다.")

st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)
st.divider()

st.header("07 · 시장 기회·포지셔닝 전략", anchor="positioning-strategy")

# STEP 07: 시장 분석·전략 제안 통합 대시보드
# 이 함수는 기존 positioning_demo_dashboard.py의 차트·결과 렌더링을
# 유지하면서 중복된 최상위 제목과 별도 DEMO 섹션을 제거한 버전입니다.

def render_integrated_positioning_demo(project_dir):
    """Render saved analysis results without API calls."""

    project_dir = Path(project_dir)

    local_results = project_dir / "demo_results"

    public_results = (
        Path(__file__).resolve().parent
        / "positioning_demo_data"
        / "ongredients_analysis"
    )

    # 프로젝트 분석 결과가 있으면 사용하고,
    # 없으면 배포용 Demo 결과를 사용
    if local_results.is_dir():
        results_dir = local_results
    else:
        results_dir = public_results

    st.caption("기존 분석 데이터를 활용한 전략 Demo · 화면 조회 시 새로운 API 호출 없음")

    stages = [
        "07-1 · 시장 니즈 분석",
        "07-2 · 경쟁사·자사 제품 분석",
        "07-3 · Gemini 시장 기회 분석",
        "07-4 · STP 및 포지셔닝",
        "07-5 · 최종 마케팅 전략",
    ]

    selected_stage = st.radio(
        "07단계 세부 분석",
        stages,
        horizontal=True,
        key="positioning_demo_stage"
    )

    st.subheader(selected_stage)

    if selected_stage.startswith("07-1"):
        import json
        import pandas as pd

        evidence_path = (
            results_dir / "positioning_evidence.json"
        )

        if not evidence_path.is_file():
            st.warning("시장 분석 결과 파일이 없습니다.")
        else:
            with open(evidence_path, encoding="utf-8") as f:
                evidence = json.load(f)

            total = evidence["market_comment_count"]
            needs = evidence["market_need_counts"]

            st.metric(
                "분석 대상 YouTube 댓글",
                f"{total:,}건"
            )

            rows = [
                {
                    "니즈 카테고리": category,
                    "언급 댓글 수": count,
                    "언급 비율 (%)": round(
                        count / total * 100, 1
                    )
                }
                for category, count in needs.items()
            ]

            df = pd.DataFrame(rows).sort_values(
                "언급 댓글 수",
                ascending=False
            )

            # 표에서 사용하는 데이터프레임을 그대로 차트에 전달
            import altair as alt
            chart_rows = df.to_dict(orient="records")
            chart_order = df["니즈 카테고리"].tolist()
            if chart_rows:
                market_needs_chart = (
                    alt.Chart(alt.Data(values=chart_rows))
                    .mark_bar(color="#80C4F6", size=24)
                    .encode(
                        y=alt.Y("니즈 카테고리:N", sort=chart_order, title="니즈 카테고리", axis=alt.Axis(labelAngle=0)),
                        x=alt.X("언급 댓글 수:Q", title="언급 댓글 수"),
                        tooltip=["니즈 카테고리:N", "언급 댓글 수:Q", "언급 비율 (%):Q"],
                    )
                    .properties(height=max(240, len(chart_rows) * 38))
                )
                st.altair_chart(market_needs_chart, use_container_width=True)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                "YouTube 댓글 기반 탐색적 분석입니다. "
                "카테고리 간 중복 집계가 가능하며, "
                "비율은 전체 시장 소비자 비율이 아닙니다."
            )
    elif selected_stage.startswith("07-2"):
        import json
        import pandas as pd

        products = [
            ("에스트라 아토베리어365 크림",
             "aestura_analysis.json"),
            ("라운드랩 1025 독도 로션",
             "roundlab_analysis.json"),
            ("온그리디언츠 바쿠글로우 캡슐 로션",
             "own_consumer_responses.json"),
        ]

        rows = []

        for name, filename in products:
            path = results_dir / filename

            if not path.is_file():
                st.warning(f"분석 파일 없음: {filename}")
                continue

            with open(path, encoding="utf-8") as f:
                data = json.load(f)

            rows.append({
                "제품": name,
                "분석 댓글": data.get(
                    "analyzed_comments",
                    data.get("analyzed_comment_count", 0)
                ),
                "실사용 후기 후보": (
                    1 if filename == "own_consumer_responses.json"
                    else data.get("review_candidates", 0)
                )
            })

        if rows:
            df = pd.DataFrame(rows)

            st.markdown("#### 제품별 분석 데이터")
            st.dataframe(
                df,
                width="stretch",
                hide_index=True
            )

            st.caption(
                "실사용 후기 후보는 AI 분류 결과이며, "
                "실제 구매 여부가 확인된 리뷰는 아닙니다. "
                "제품별 표본 규모와 영상 구성이 달라 "
                "만족도나 제품 성능을 직접 비교할 수 없습니다."
            )

    elif selected_stage.startswith("07-3"):
        import json

        opportunity_path = (
            results_dir / "gemini_market_opportunities.json"
        )

        if not opportunity_path.is_file():
            st.warning("Gemini 시장 기회 분석 파일이 없습니다.")
        else:
            with open(opportunity_path, encoding="utf-8") as f:
                result = json.load(f)

            st.caption(
                "사전에 Gemini API로 생성한 분석 결과입니다. "
                "현재 화면에서는 API를 호출하지 않습니다."
            )

            st.markdown("#### 시장 인사이트")

            for i, item in enumerate(
                result.get("market_insights", []), 1
            ):
                with st.expander(
                    f"{i}. {item.get('insight', '시장 인사이트')}",
                    expanded=True
                ):
                    st.write("**분석 근거**")
                    st.write(item.get("evidence", ""))

                    st.write("**해석**")
                    st.write(item.get("interpretation", ""))

                    st.write("**분석 한계**")
                    st.write(item.get("limitations", ""))

            st.markdown("#### 잠재적 시장 기회")

            for i, item in enumerate(
                result.get("opportunity_areas", []), 1
            ):
                with st.expander(
                    f"{i}. {item.get('opportunity_name', '기회 영역')}"
                ):
                    st.write(
                        "**소비자 니즈:**",
                        item.get("consumer_need", "")
                    )
                    st.write(
                        "**경쟁사 취약점 가설:**",
                        item.get("competitor_gap_hypothesis", "")
                    )
                    st.write(
                        "**자사 제품 연결 가설:**",
                        item.get("own_product_fit_hypothesis", "")
                    )

                    st.write("**분석 근거**")
                    for evidence in item.get(
                        "supporting_evidence", []
                    ):
                        st.write("-", evidence)

                    st.write("**추가 검증 사항**")
                    for task in item.get("validation_needed", []):
                        st.write("-", task)

            st.markdown("#### 전략적 위험")

            for item in result.get("strategic_risks", []):
                st.warning(
                    f"**{item.get('risk', '')}**\n\n"
                    f"{item.get('reason', '')}"
                )

            st.markdown("#### 종합 분석")
            st.write(result.get("overall_summary", ""))

            st.caption(
                "시장 기회는 검증 전 전략 가설입니다. "
                "경쟁사의 객관적 결함이나 자사 제품의 "
                "우수성이 입증되었다는 의미는 아닙니다."
            )

    elif selected_stage.startswith("07-4"):
        import json

        stp_file = results_dir / "gemini_stp_strategy.json"
        review_file = results_dir / "stp_strategy_review.json"

        if not stp_file.is_file() or not review_file.is_file():
            st.warning("STP 분석 또는 검토 결과 파일이 없습니다.")
        else:
            with open(stp_file, encoding="utf-8") as f:
                stp_data = json.load(f)

            with open(review_file, encoding="utf-8") as f:
                review_data = json.load(f)

            st.caption(
                "사전 생성된 Gemini STP 분석 결과와 "
                "사람의 검토 의견을 함께 표시합니다."
            )

            st.markdown("#### 1. Segmentation · 시장 세분화")

            for i, segment in enumerate(
                stp_data.get("segmentation", []), 1
            ):
                with st.expander(
                    f"{i}. {segment.get('segment_name', '')}"
                ):
                    st.write("**주요 니즈:**", segment.get("needs", ""))
                    st.write("**분석 근거:**", segment.get("evidence", ""))
                    st.caption(segment.get("limitations", ""))

            st.markdown("#### 2. Targeting · 타깃 선정")

            targeting = stp_data.get("targeting", {})

            st.write(
                "**우선 검증 타깃:**",
                targeting.get("primary_target", "")
            )
            st.write(
                "**선정 근거:**",
                targeting.get("rationale", "")
            )
            st.write(
                "**반론 및 한계:**",
                targeting.get("counterarguments", "")
            )

            st.markdown("#### 3. Positioning · 후보 비교")

            for item in stp_data.get(
                "positioning_comparison", []
            ):
                with st.expander(
                    f"후보 {item.get('candidate_id', '')}"
                ):
                    st.write("**강점:**", item.get("strengths", ""))
                    st.write("**약점:**", item.get("weaknesses", ""))
                    st.write(
                        "**근거 수준:**",
                        item.get("evidence_quality", "")
                    )
                    st.write(
                        "**평가:**",
                        item.get("recommendation", "")
                    )

            st.markdown("#### 4. 전략 검토 및 수정")

            st.write(
                "**Gemini 최초 추천:**",
                review_data.get("gemini_recommendation", "")
            )
            st.write(
                "**검토 방향:**",
                review_data.get("review_decision", "")
            )

            st.info(
                "**수정된 포지셔닝 가설**\n\n"
                + review_data.get(
                    "revised_positioning_hypothesis", ""
                )
            )

            st.write(
                "**핵심 메시지 후보:**",
                review_data.get("message_hypothesis", "")
            )

            st.markdown("**검증 전 사용을 제한할 주장**")

            for claim in review_data.get(
                "claims_to_avoid_without_validation", []
            ):
                st.write("-", claim)

            st.caption(
                "세그먼트와 포지셔닝은 탐색적 가설이며, "
                "실제 구매 행동이나 제품 효능이 "
                "검증된 결과는 아닙니다."
            )

    elif selected_stage.startswith("07-5"):
        import json

        strategy_file = (
            results_dir / "gemini_final_strategy.json"
        )

        if not strategy_file.is_file():
            st.warning("최종 전략 분석 파일이 없습니다.")
        else:
            with open(strategy_file, encoding="utf-8") as f:
                strategy = json.load(f)

            st.caption(
                "사전에 Gemini로 생성한 전략 초안입니다. "
                "실제 성과가 검증된 전략은 아닙니다."
            )

            st.markdown("#### 1. 최종 포지셔닝")

            target = strategy.get("target_customer", {})
            positioning = strategy.get("positioning", {})

            st.write(
                "**우선 타깃 가설:**",
                target.get("description", "")
            )
            st.write(
                "**소비자 문제:**",
                target.get("consumer_problem", "")
            )

            st.info(
                "**포지셔닝 가설**\n\n"
                + positioning.get("statement", "")
            )

            st.write(
                "**핵심 가치 제안:**",
                positioning.get("value_proposition", "")
            )

            st.markdown("#### 2. 마케팅 메시지 후보")

            for i, item in enumerate(
                strategy.get("message_candidates", []), 1
            ):
                with st.expander(
                    f"메시지 {i}: {item.get('message', '')}"
                ):
                    st.write(
                        "**대상:**",
                        item.get("intended_audience", "")
                    )
                    st.write(
                        "**선정 이유:**",
                        item.get("rationale", "")
                    )
                    st.write(
                        "**표현 위험:**",
                        item.get("claim_risk", "")
                    )

            st.markdown("#### 3. 마케팅 실행 전략 및 KPI")

            for i, item in enumerate(
                strategy.get("action_plan", []), 1
            ):
                with st.expander(
                    f"전략 {i}: {item.get('action', '')}"
                ):
                    st.write(
                        "**목표:**",
                        item.get("objective", "")
                    )

                    st.write("**실행 방법**")
                    for step in item.get("execution_steps", []):
                        st.write("-", step)

                    st.write(
                        "**KPI:**",
                        item.get("kpi", "")
                    )
                    st.write(
                        "**측정 방법:**",
                        item.get("measurement_method", "")
                    )
                    st.write(
                        "**근거:**",
                        item.get("evidence_basis", "")
                    )
                    st.write(
                        "**추가 검증:**",
                        item.get("validation_needed", "")
                    )

            st.markdown("#### 4. 전략적 위험")

            for item in strategy.get("risks", []):
                st.warning(
                    f"**{item.get('risk', '')}**\n\n"
                    f"대응: {item.get('mitigation', '')}"
                )

            st.markdown("#### 5. 추가 필요 데이터")

            for item in strategy.get(
                "additional_data_needed", []
            ):
                st.write("-", item)

            st.markdown("#### 6. 최종 전략 요약")
            st.write(strategy.get("executive_summary", ""))

            st.caption(
                "본 전략은 검증 전 제안안입니다. "
                "실제 마케팅 실행 전 제품 효능, 사용감, "
                "소비자 반응 등에 대한 검증이 필요합니다."
            )

    else:
        st.caption("해당 단계의 분석 결과 연결 예정")

    if not results_dir.is_dir():
        st.warning("Demo 분석 결과 폴더를 찾을 수 없습니다.")


if selected_project == DEMO_ID:
    if st.session_state.get("ongredients_demo_ai_comments_revealed", False):
        with st.container(border=True):
            render_integrated_positioning_demo(CURRENT_DATA_DIR)
    else:
        with st.container(border=True):
            st.info("먼저 06-2 · AI 소비자 분석 결과를 확인해 주세요.")
else:
    from positioning_agent.strategy_dashboard import render_positioning_strategy_dashboard
    positioning_package_path = (
        CURRENT_DATA_DIR / "positioning_strategy" / "strategy_package.json"
    )
    if positioning_package_path.is_file():
        with st.container(border=True):
            render_positioning_strategy_dashboard(positioning_package_path)
    else:
        with st.container(border=True):
            st.info("아직 포지셔닝 전략 분석 결과가 없습니다.")
