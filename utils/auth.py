from __future__ import annotations

import streamlit as st


def ensure_authenticated() -> None:
    return None


def logout() -> None:
    st.session_state.clear()
    st.rerun()


def render_logout_button() -> None:
    st.markdown(
        """
        <style>
        div[data-testid="stButton"] button[kind="secondary"] {
            border: none;
            background: transparent;
            color: #6b7280;
            font-size: 13px;
            padding: 6px 10px;
            border-radius: 6px;
            transition: all 0.2s ease;
            box-shadow: none;
        }

        div[data-testid="stButton"] button[kind="secondary"]:hover {
            background: rgba(0, 0, 0, 0.05);
            color: #1f2937;
            border: none;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns([10, 1])
    with col2:
        if st.button("Sair", key="logout_top_button", type="secondary", use_container_width=True):
            logout()