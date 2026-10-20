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
