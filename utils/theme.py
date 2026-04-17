from __future__ import annotations

from datetime import datetime
from pathlib import Path

import streamlit as st

BRIDA_BLUE = "#1F2A5A"
BRIDA_ORANGE = "#F25C05"
BRIDA_WHITE = "#FFFFFF"
BRIDA_BG = "#F5F6FA"
BRIDA_TEXT = "#2F3447"
BRIDA_MUTED = "#7C8499"
BRIDA_BORDER = "#E3E7F0"
BRIDA_LIGHT_BLUE = "#EAF0FF"
BRIDA_LIGHT_ORANGE = "#FFF1E8"
BRIDA_GRAY_BLUE = "#8A97B8"
BRIDA_GREEN = "#1F9D72"

ROOT_DIR = Path(__file__).resolve().parent.parent


def get_logo_path() -> str | None:
    candidates = [
        ROOT_DIR / "logo.png",
        ROOT_DIR / "logo.jpg",
        ROOT_DIR / "logo.jpeg",
        ROOT_DIR / "baixados.png",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return None


def apply_brand_theme() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --brida-blue: {BRIDA_BLUE};
            --brida-orange: {BRIDA_ORANGE};
            --brida-white: {BRIDA_WHITE};
            --brida-bg: {BRIDA_BG};
            --brida-text: {BRIDA_TEXT};
            --brida-muted: {BRIDA_MUTED};
            --brida-border: {BRIDA_BORDER};
            --brida-light-blue: {BRIDA_LIGHT_BLUE};
            --brida-light-orange: {BRIDA_LIGHT_ORANGE};
            --brida-gray-blue: {BRIDA_GRAY_BLUE};
            --brida-green: {BRIDA_GREEN};
        }}

        .stApp {{
            background: var(--brida-bg);
            color: var(--brida-text);
        }}

        .block-container {{
            padding-top: 1.25rem;
            padding-bottom: 1.5rem;
            max-width: 1320px;
        }}

        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #f7f8fc 0%, #eef1f8 100%);
            border-right: 1px solid var(--brida-border);
        }}

        [data-testid="stSidebarContent"] {{
            padding-top: 0.65rem;
        }}

        [data-testid="stHeader"] {{
            background: rgba(245, 246, 250, 0.85);
        }}

        h1, h2, h3 {{
            color: var(--brida-blue);
            letter-spacing: -0.02em;
        }}

        .brida-page-header {{
            padding: 0 0 0.7rem 0;
            margin-bottom: 1rem;
            border-bottom: 1px solid var(--brida-border);
        }}

        .brida-update-notice {{
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            padding: 0.35rem 0.7rem;
            margin: 0 0 0.8rem 0;
            background: rgba(31, 42, 90, 0.06);
            border: 1px solid rgba(31, 42, 90, 0.12);
            border-radius: 999px;
            color: var(--brida-muted);
            font-size: 0.78rem;
            line-height: 1.2;
        }}

        .brida-update-notice strong {{
            color: var(--brida-blue);
            font-weight: 700;
        }}

        .brida-page-title {{
            color: var(--brida-blue);
            font-size: 2rem;
            font-weight: 800;
            margin: 0;
        }}

        .brida-page-subtitle {{
            color: var(--brida-muted);
            font-size: 0.92rem;
            margin-top: 0.25rem;
        }}

        .brida-sidebar-brand {{
            text-align: center;
            padding: 0.1rem 0 0.6rem 0;
        }}

        .brida-sidebar-brand img {{
            max-height: 120px;
            width: auto;
            object-fit: contain;
        }}

        .brida-sidebar-brand-title {{
            color: var(--brida-blue);
            font-size: 0.92rem;
            font-weight: 800;
            margin-top: 0.35rem;
            letter-spacing: 0.04em;
        }}

        .brida-sidebar-brand-subtitle {{
            color: var(--brida-muted);
            font-size: 0.76rem;
        }}

        .brida-kpi-card {{
            background: var(--brida-white);
            border: 1px solid var(--brida-border);
            border-radius: 14px;
            padding: 0.7rem 0.85rem 0.75rem 0.85rem;
            box-shadow: 0 6px 16px rgba(31, 42, 90, 0.06);
            min-height: 88px;
        }}

        .brida-kpi-label {{
            color: var(--brida-muted);
            font-size: 0.77rem;
            font-weight: 600;
            margin-bottom: 0.35rem;
        }}

        .brida-kpi-value {{
            font-size: 1.38rem;
            font-weight: 800;
            line-height: 1.1;
            color: var(--brida-blue);
            word-break: break-word;
        }}

        .brida-kpi-value.is-orange {{
            color: var(--brida-orange);
        }}

        .brida-kpi-value.is-muted {{
            color: var(--brida-gray-blue);
        }}

        .brida-kpi-value.is-green {{
            color: var(--brida-green);
        }}

        .brida-chart-note {{
            background: var(--brida-white);
            border: 1px solid var(--brida-border);
            border-radius: 14px;
            padding: 0.7rem 0.85rem;
            margin: 0.3rem 0 0.85rem 0;
            box-shadow: 0 5px 14px rgba(31, 42, 90, 0.04);
        }}

        .brida-chart-note-title {{
            color: var(--brida-blue);
            font-weight: 700;
            font-size: 0.92rem;
            margin-bottom: 0.35rem;
        }}

        .brida-chart-note-line {{
            color: var(--brida-text);
            font-size: 0.84rem;
            margin: 0.12rem 0;
        }}

        .brida-insight-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 0.7rem;
            margin: 0.55rem 0 1rem 0;
        }}

        .brida-insight-card {{
            padding: 12px;
            border-radius: 10px;
            background-color: var(--brida-bg);
            border-left: 4px solid var(--brida-blue);
            border-top: 1px solid var(--brida-border);
            border-right: 1px solid var(--brida-border);
            border-bottom: 1px solid var(--brida-border);
            margin-bottom: 10px;
            box-shadow: 0 4px 10px rgba(31, 42, 90, 0.04);
        }}

        .brida-insight-card.is-primary {{
            background: var(--brida-light-blue);
        }}

        .brida-insight-card.is-warning {{
            background: var(--brida-light-orange);
            border-left: 4px solid var(--brida-orange);
        }}

        .brida-insight-title {{
            font-size: 14px;
            font-weight: 600;
            color: #2E2E2E;
            margin-bottom: 0.15rem;
        }}

        .brida-insight-value {{
            font-size: 16px;
            font-weight: 500;
            color: var(--brida-text);
            margin-top: 4px;
        }}

        .brida-section-gap {{
            height: 0.55rem;
        }}

        .brida-plot-container {{
            background: var(--brida-white);
            border: 1px solid var(--brida-border);
            border-radius: 16px;
            padding: 0.5rem 0.55rem 0.35rem 0.55rem;
            box-shadow: 0 6px 16px rgba(31, 42, 90, 0.04);
            margin-bottom: 0.3rem;
        }}

        div[data-testid="stMetric"] {{
            background: transparent;
            border: none;
            box-shadow: none;
            padding: 0;
        }}

        div[data-testid="stDataFrame"], div[data-testid="stTable"] {{
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--brida-border);
            box-shadow: 0 8px 18px rgba(31, 42, 90, 0.05);
        }}

        .stAlert {{
            border-radius: 16px;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:
    logo_path = get_logo_path()
    content = ""
    if logo_path:
        content += f'<img src="data:image/png;base64,{_image_to_base64(logo_path)}" alt="BRIDA logo" />'
    content += """
        <div class="brida-sidebar-brand-title">BRIDA DISTRIBUIDORA</div>
        <div class="brida-sidebar-brand-subtitle">Painel logístico e financeiro</div>
    """
    st.sidebar.markdown(
        f'<div class="brida-sidebar-brand">{content}</div>',
        unsafe_allow_html=True,
    )
    st.sidebar.divider()


def render_page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="brida-page-header">
            <div class="brida-page-title">{title}</div>
            <div class="brida-page-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_global_update_notice(source_name: str, updated_at: str | None) -> None:
    if not updated_at:
        return

    try:
        formatted_timestamp = datetime.fromisoformat(updated_at).strftime("%d/%m/%Y %H:%M")
    except ValueError:
        formatted_timestamp = updated_at

    st.markdown(
        f"""
        <div class="brida-update-notice">
            <strong>Planilha atualizada</strong>
            <span>{formatted_timestamp} | Fonte: {source_name}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, tone: str = "blue") -> None:
    tone_class = {
        "blue": "",
        "orange": "is-orange",
        "muted": "is-muted",
        "green": "is-green",
    }.get(tone, "")
    st.markdown(
        f"""
        <div class="brida-kpi-card">
            <div class="brida-kpi-label">{label}</div>
            <div class="brida-kpi-value {tone_class}">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_plotly_figure(
    fig,
    *,
    color_sequence: list[str] | None = None,
    abbreviate_y_axis: bool = False,
    abbreviate_x_axis: bool = False,
):
    fig.update_layout(
        paper_bgcolor=BRIDA_WHITE,
        plot_bgcolor=BRIDA_WHITE,
        font={"color": BRIDA_TEXT, "family": "Segoe UI, Arial, sans-serif"},
        title={"font": {"color": BRIDA_BLUE, "size": 16}},
        margin={"l": 12, "r": 80, "t": 44, "b": 12},
        legend={"orientation": "v", "yanchor": "top", "y": 1, "xanchor": "left", "x": 1.02},
        height=320,
        uniformtext_minsize=10,
        uniformtext_mode="hide",
    )
    fig.update_xaxes(showgrid=True, gridcolor="#EDF0F6", zeroline=False)
    fig.update_yaxes(showgrid=True, gridcolor="#EDF0F6", zeroline=False)
    if abbreviate_x_axis:
        fig.update_xaxes(tickformat="~s")
    if abbreviate_y_axis:
        fig.update_yaxes(tickformat="~s")
    if color_sequence:
        fig.update_layout(colorway=color_sequence)
    return fig


def render_insight_cards(items: list[dict[str, str]]) -> None:
    cards = [
        insight_card(
            item["title"],
            item["value"],
            item.get("tone", "is-primary"),
        )
        for item in items
    ]

    st.markdown(
        f"<div class='brida-insight-grid'>{''.join(cards)}</div>",
        unsafe_allow_html=True,
    )


def insight_card(title: str, value: str, tone: str = "is-primary") -> str:
    return f"""
<div class="brida-insight-card {tone}">
    <div class="brida-insight-title">{title}</div>
    <div class="brida-insight-value">{value}</div>
</div>
"""


def render_section_gap() -> None:
    st.markdown("<div class='brida-section-gap'></div>", unsafe_allow_html=True)


def open_chart_container():
    return st.container(border=False)


def _image_to_base64(path: str) -> str:
    import base64

    return base64.b64encode(Path(path).read_bytes()).decode("utf-8")