from __future__ import annotations

import streamlit as st

from utils.theme import get_logo_path

VALID_USERNAME = "Brida"
VALID_PASSWORD = "Brida123"


def initialize_authentication_state() -> None:
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False


def is_authenticated() -> bool:
    initialize_authentication_state()
    return bool(st.session_state["authenticated"])


def authenticate(username: str, password: str) -> bool:
    return username == VALID_USERNAME and password == VALID_PASSWORD


def _hide_navigation_for_login() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            background-color: #FFFFFF;
        }

        section[data-testid="stSidebar"] {display: none !important;}
        [data-testid="collapsedControl"] {display: none !important;}
        [data-testid="stSidebarNav"] {display: none !important;}
        header {display: none !important;}
        footer {display: none !important;}

        .main {
            display: flex;
            align-items: flex-start;
            justify-content: center;
            min-height: 100vh;
            padding-top: 8vh;
            transition: all 0.3s ease;
        }

        [data-testid="stHorizontalBlock"] {
            align-items: center;
        }

        .main > div {
            padding-top: 0rem;
        }

        .block-container {
            max-width: 1180px;
            width: 100%;
            padding-top: 1rem;
            padding-bottom: 1rem;
        }

        [data-testid="column"] {
            display: flex;
            align-items: center;
            justify-content: center;
        }

        [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child {
            align-items: flex-start;
        }

        [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child > div {
            display: flex;
            align-items: flex-start;
            justify-content: center;
        }

        [data-testid="column"] > div {
            width: 100%;
        }

        .login-container {
            width: 100%;
            max-width: 400px;
            margin-left: auto;
            margin-right: auto;
        }

        .login-box {
            width: min(100%, 430px);
            padding: 30px;
            border-radius: 12px;
            background-color: #FFFFFF;
            box-shadow: 0px 4px 20px rgba(0,0,0,0.05);
            margin-left: auto;
            margin-right: auto;
        }

        .login-title {
            color: #1F2A5A;
            font-size: 2rem;
            line-height: 1.1;
            font-weight: 800;
            margin: 0 0 0.6rem 0;
        }

        .login-subtitle {
            color: #7C8499;
            font-size: 0.96rem;
            line-height: 1.5;
            margin-bottom: 1.4rem;
        }

        div[data-testid="stForm"] {
            border: none;
            background: transparent;
            padding: 0;
        }

        div[data-testid="stTextInput"] label {
            color: #1F2A5A;
            font-weight: 600;
        }

        div[data-testid="stTextInput"] input,
        input {
            padding: 10px;
            border-radius: 6px;
            background: #FFFFFF;
            border: 1px solid #DDE3EE;
            color: #2F3447;
        }

        div[data-testid="stTextInput"] input:focus {
            border-color: #F25C05;
            box-shadow: 0 0 0 1px rgba(242, 92, 5, 0.2);
        }

        div[data-testid="stFormSubmitButton"] button,
        button {
            border-radius: 6px;
        }

        div[data-testid="stFormSubmitButton"] button {
            width: 100%;
            min-height: 48px;
            border: none;
            color: #FFFFFF;
            font-weight: 700;
            background: linear-gradient(135deg, #F25C05 0%, #FF7C38 100%);
            box-shadow: 0 10px 24px rgba(242, 92, 5, 0.2);
        }

        .logo-panel {
            width: 100%;
            max-width: 400px;
            min-height: 360px;
            margin-left: auto;
            margin-right: auto;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }

        .logo-container {
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }

        [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stImage"] {
            position: relative;
            top: -120px;
            display: flex;
            justify-content: center;
            width: 100%;
            animation: fadeUp 0.6s ease;
        }

        [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stImage"] img,
        .logo-panel img {
            max-width: 320px;
            width: 100%;
            height: auto;
            object-fit: contain;
            filter: drop-shadow(0 4px 12px rgba(0,0,0,0.08));
        }

        @keyframes fadeUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 900px) {
            .main {
                display: block;
                min-height: auto;
            }

            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 1.5rem;
            }

            [data-testid="column"] {
                display: block;
            }

            .login-container,
            .login-box,
            .logo-container,
            .logo-panel {
                width: 100%;
            }

            .logo-panel {
                min-height: 180px;
                padding-top: 0;
            }

            .logo-container,
            [data-testid="stHorizontalBlock"] > [data-testid="column"]:last-child [data-testid="stImage"] {
                top: 0;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_login_screen() -> None:
    initialize_authentication_state()
    logo_path = get_logo_path()

    col1, col2 = st.columns([1, 1], gap="large")

    with col1:
        st.markdown('<div class="login-container"><div class="login-box">', unsafe_allow_html=True)
        st.markdown('<div class="login-title">Acesso ao Sistema</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="login-subtitle">Informe usuario e senha para acessar os dashboards e recursos internos da BRIDA.</div>',
            unsafe_allow_html=True,
        )

        with st.form("login_form"):
            username = st.text_input("Usuario", placeholder="Digite seu usuario")
            password = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            submitted = st.form_submit_button("Entrar", use_container_width=True, type="primary")

        if submitted:
            if authenticate(username, password):
                st.session_state["authenticated"] = True
                st.rerun()
            st.error("Usuario ou senha invalidos. Verifique os dados e tente novamente.")

        st.markdown("</div></div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="logo-container"><div class="logo-panel">', unsafe_allow_html=True)
        if logo_path:
            st.image(logo_path, width=320)
        else:
            st.markdown(
                '<div style="color: #1F2A5A; font-size: 1rem; font-weight: 600; text-align: center;">Logo da empresa</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div></div>", unsafe_allow_html=True)


def require_app_authentication() -> None:
    initialize_authentication_state()
    if st.session_state["authenticated"]:
        return

    _hide_navigation_for_login()
    render_login_screen()
    st.stop()


def guard_page_access() -> None:
    initialize_authentication_state()
    if st.session_state["authenticated"]:
        return

    try:
        st.switch_page("app.py")
    except Exception:
        st.markdown(
            '<div style="padding: 2rem 1rem; color: #1F2A5A; font-weight: 600;">Acesso restrito. Retorne para a tela inicial e faca login.</div>',
            unsafe_allow_html=True,
        )
    st.stop()


def logout() -> None:
    st.session_state["authenticated"] = False
    st.rerun()


def render_logout_button() -> None:
    st.sidebar.markdown(
        """
        <style>
        div[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"] {
            border: 1px solid rgba(31, 42, 90, 0.12);
            background: rgba(255, 255, 255, 0.72);
            color: #6b7280;
            font-size: 0.82rem;
            padding: 0.45rem 0.75rem;
            border-radius: 10px;
            transition: all 0.2s ease;
            box-shadow: none;
        }

        div[data-testid="stSidebar"] div[data-testid="stButton"] button[kind="secondary"]:hover {
            background: rgba(31, 42, 90, 0.06);
            color: #1f2937;
            border-color: rgba(31, 42, 90, 0.2);
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.sidebar.button("🚪 Sair", key="logout_sidebar_button", type="secondary", use_container_width=True):
        logout()