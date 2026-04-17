import plotly.express as px
import streamlit as st

from utils.auth import ensure_authenticated, render_logout_button
from utils.chart_text import render_chart_description
from utils.formatters import abreviar_valor, format_currency, format_dataframe_ptbr, format_date, format_integer, format_ratio
from utils.load_data import get_dashboard_context
from utils.metrics import build_daily_analysis, calculate_kpis, get_daily_highlights
from utils.theme import apply_brand_theme, render_insight_cards, render_kpi_card, render_page_header, render_section_gap, style_plotly_figure

st.set_page_config(page_title="Geral", layout="wide", initial_sidebar_state="expanded")
apply_brand_theme()
ensure_authenticated()
render_logout_button()

df, _, _ = get_dashboard_context()

render_page_header("Geral", "Visao executiva de receita, volume e eficiencia da operacao")

if df.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

kpis = calculate_kpis(df)
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    render_kpi_card("Receita", f"R$ {format_integer(kpis['receita'])}", tone="blue")
with col2:
    render_kpi_card("Peso", format_integer(kpis["peso"]), tone="muted")
with col3:
    render_kpi_card("Quantidade", format_integer(kpis["quantidade"]), tone="muted")
with col4:
    render_kpi_card("R$/KG", format_ratio(kpis["r_kg"]), tone="orange")
with col5:
    render_kpi_card("Ticket Medio", format_currency(kpis["ticket_medio"]), tone="green")

render_section_gap()

daily_df = build_daily_analysis(df)
best_day, worst_day = get_daily_highlights(daily_df)

if best_day is not None and worst_day is not None:
    render_insight_cards(
        [
            {
                "title": "🔥 Melhor dia",
                "value": f"{format_date(best_day['Data'])} | {format_currency(best_day['ValorTotal'])}",
                "tone": "is-primary",
            },
            {
                "title": "⚠️ Pior dia",
                "value": f"{format_date(worst_day['Data'])} | {format_currency(worst_day['ValorTotal'])}",
                "tone": "is-warning",
            },
        ]
    )

render_section_gap()
st.subheader("Analise diaria")
st.dataframe(format_dataframe_ptbr(daily_df.sort_values("Data", ascending=False)), width="stretch")

render_section_gap()
chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    with st.container():
        receita_chart = px.line(daily_df, x="Data", y="ValorTotal", title="Receita por dia")
        receita_chart.update_traces(line={"color": "#1F2A5A", "width": 2.6})
        receita_chart.update_traces(hovertemplate="R$ %{y:,.2f}<extra></extra>")
        style_plotly_figure(receita_chart, abbreviate_y_axis=True)
        st.plotly_chart(receita_chart, width="stretch", key="geral_receita_dia")
        render_chart_description(
            "Receita por Dia",
            "Mostra a evolucao do faturamento ao longo do periodo filtrado.",
            f"Picos indicam dias mais fortes; o melhor dia atual foi {format_date(best_day['Data']) if best_day is not None else '-'}.",
            "Use para identificar sazonalidade e reforcar a operacao comercial nos dias mais rentaveis.",
        )

with chart_col2:
    with st.container():
        mix_df = df.groupby("TIPO", as_index=False)["ValorTotal"].sum()
        mix_chart = px.bar(mix_df, x="TIPO", y="ValorTotal", title="Mix por tipo")
        mix_chart.update_traces(
            text=[abreviar_valor(v) for v in mix_df["ValorTotal"]],
            textposition="outside",
            textfont={"size": 10},
            cliponaxis=False,
            hovertemplate="R$ %{y:,.2f}<extra></extra>",
        )
        style_plotly_figure(mix_chart, color_sequence=["#1F2A5A", "#F25C05", "#8A97B8"], abbreviate_y_axis=True)
        st.plotly_chart(mix_chart, width="stretch", key="geral_mix_tipo")
        dominant_type = mix_df.sort_values("ValorTotal", ascending=False).iloc[0]["TIPO"]
        render_chart_description(
            "Mix por Tipo",
            "Mostra a participacao de cada operacao na receita total.",
            f"Barras maiores indicam maior dependencia; hoje o tipo lider e {dominant_type}.",
            "Ajuda a reduzir concentracao excessiva e orientar prioridades comerciais.",
        )

render_section_gap()
chart_col3, chart_col4 = st.columns(2)
with chart_col3:
    with st.container():
        peso_chart = px.line(daily_df, x="Data", y="PesoTotal", title="Peso por dia")
        peso_chart.update_traces(line={"color": "#8A97B8", "width": 2.6})
        peso_chart.update_traces(hovertemplate="%{y:,.2f} KG<extra></extra>")
        style_plotly_figure(peso_chart, abbreviate_y_axis=True)
        st.plotly_chart(peso_chart, width="stretch", key="geral_peso_dia")
        render_chart_description(
            "Peso por Dia",
            "Representa o volume logistico movimentado no periodo.",
            "Altas indicam maior esforco operacional e necessidade de capacidade.",
            "Compare com a receita para avaliar se o crescimento operacional gera retorno suficiente.",
        )

with chart_col4:
    with st.container():
        rkg_chart = px.line(daily_df, x="Data", y="R$/KG", title="R$/KG por dia")
        rkg_chart.update_traces(line={"color": "#F25C05", "width": 2.6})
        rkg_chart.update_traces(hovertemplate="%{y:,.2f}<extra></extra>")
        style_plotly_figure(rkg_chart)
        st.plotly_chart(rkg_chart, width="stretch", key="geral_rkg_dia")
        render_chart_description(
            "R$/KG por Dia",
            f"Mede a eficiencia da operacao em receita por peso; a media atual e {format_ratio(kpis['r_kg'])}.",
            "Quanto maior a linha, melhor o retorno por quilo transportado.",
            "Quedas recorrentes indicam mix menos eficiente ou pressao de margem na operacao.",
        )