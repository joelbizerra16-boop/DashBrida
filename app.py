import streamlit as st

from utils.auth import initialize_authentication_state, render_logout_button, require_app_authentication
from utils.formatters import format_dataframe_ptbr, format_date, format_integer
from utils.load_data import get_dashboard_context, hide_default_sidebar_navigation, init_session_state, load_sheet_preview
from utils.theme import apply_brand_theme, render_kpi_card, render_page_header, render_section_gap

st.set_page_config(page_title="Sistema Logistico", layout="wide", initial_sidebar_state="expanded")
initialize_authentication_state()
init_session_state()
require_app_authentication()

apply_brand_theme()
hide_default_sidebar_navigation()
render_logout_button()

df, source_name, sheet_registry = get_dashboard_context()

render_page_header("Sistema Logistico", "Dashboard multi-paginas da BRIDA DISTRIBUIDORA")

col1, col2, col3 = st.columns(3)
with col1:
    render_kpi_card("Registros filtrados", format_integer(len(df)), tone="blue")
with col2:
    render_kpi_card("Fonte ativa", source_name, tone="muted")
with col3:
    render_kpi_card("Abas importadas", format_integer(len(sheet_registry)), tone="orange")

render_section_gap()

if not df.empty:
    st.info(
        f"Periodo filtrado: {format_date(df['Data'].min())} ate {format_date(df['Data'].max())}. "
        "Use o menu lateral do Streamlit para navegar entre as paginas."
    )

st.subheader("Abas importadas")
st.dataframe(
    format_dataframe_ptbr(
        sheet_registry.rename(
            columns={
                "sheet_name": "Aba",
                "table_name": "Tabela SQLite",
                "row_count": "Linhas",
            }
        )
    ),
    width="stretch",
)

if not sheet_registry.empty:
    render_section_gap()
    selected_sheet = st.selectbox(
        "Visualizar amostra da base importada",
        sheet_registry["sheet_name"].tolist(),
    )
    st.dataframe(format_dataframe_ptbr(load_sheet_preview(selected_sheet)), width="stretch")