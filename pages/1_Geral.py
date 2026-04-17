import pandas as pd
import plotly.express as px
import streamlit as st

from utils.auth import guard_page_access, render_logout_button
from utils.chart_text import render_chart_description
from utils.formatters import (
    abreviar_valor,
    build_category_tooltip_dataframe,
    build_daily_tooltip_dataframe,
    format_currency,
    format_dataframe_ptbr,
    format_date,
    format_integer,
    format_ratio,
)
from utils.load_data import get_dashboard_context, init_session_state
from utils.metrics import build_daily_analysis, calculate_kpis, get_daily_highlights
from utils.theme import (
    apply_brand_theme,
    render_insight_cards,
    render_kpi_card,
    render_page_header,
    render_section_gap,
    style_plotly_figure,
)


def configure_daily_chart(fig, daily_df: pd.DataFrame, *, y_tickformat: str | None = None):
    fig.update_traces(mode="lines+markers", marker={"size": 7})
    fig.update_xaxes(tickformat="%d/%m", dtick="D1")
    if y_tickformat:
        fig.update_yaxes(tickformat=y_tickformat)

    if len(daily_df) == 1:
        single_day = pd.to_datetime(daily_df["Data"].iloc[0]).normalize()
        fig.update_xaxes(range=[single_day - pd.Timedelta(hours=12), single_day + pd.Timedelta(hours=12)])

    return fig


def render_single_chart_section(title: str, figure, chart_key: str, description_args: tuple[str, str, str, str]) -> None:
    st.markdown(f"## {title}")
    st.plotly_chart(figure, use_container_width=True, key=chart_key)
    render_chart_description(*description_args)
    st.divider()


st.set_page_config(page_title="Geral", layout="wide", initial_sidebar_state="expanded")
guard_page_access()
init_session_state()
apply_brand_theme()
render_logout_button()
st.markdown(
    """
    <style>
    .brida-chart-note {
        background: #ffffff;
        padding: 16px 18px;
        border-radius: 12px;
        border-left: 4px solid #ff6b00;
        margin-top: 10px;
        margin-bottom: 30px;
        font-size: 14px;
        color: #2c3e50;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05);
    }

    h2 {
        margin-top: 30px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

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
daily_tooltip_df = build_daily_tooltip_dataframe(daily_df)
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

receita_chart = px.line(daily_df, x="Data", y="ValorTotal", title="Receita por dia")
receita_chart.update_traces(
    line={"color": "#1F2A5A", "width": 2.6},
    customdata=daily_tooltip_df[["Data_str", "Valor_fmt", "Peso_fmt", "RKG_fmt", "Var_fmt", "Seta", "Status"]],
    hovertemplate="<b>📅 %{customdata[0]}</b><br><br>💰 Receita: %{customdata[1]}<br>⚖️ Peso: %{customdata[2]}<br>📊 R$/KG: %{customdata[3]}<br><br>📈 Variação: %{customdata[5]} %{customdata[4]}<br>🧠 Status: %{customdata[6]}<extra></extra>",
)
style_plotly_figure(receita_chart, abbreviate_y_axis=True)
configure_daily_chart(receita_chart, daily_df, y_tickformat="~s")
render_single_chart_section(
    "📈 Receita por dia",
    receita_chart,
    "geral_receita_dia",
    (
        "Receita por Dia",
        "Mostra a evolucao do faturamento ao longo do periodo filtrado.",
        f"Picos indicam dias mais fortes; o melhor dia atual foi {format_date(best_day['Data']) if best_day is not None else '-'}.",
        "Use para identificar sazonalidade e reforcar a operacao comercial nos dias mais rentaveis.",
    ),
)

mix_df = df.groupby("TIPO", as_index=False)["ValorTotal"].sum()
mix_tooltip_df = build_category_tooltip_dataframe(
    mix_df,
    label_column="TIPO",
    value_column="ValorTotal",
)
mix_chart = px.bar(mix_df, x="TIPO", y="ValorTotal", title="Mix por tipo")
mix_chart.update_traces(
    text=[abreviar_valor(v) for v in mix_df["ValorTotal"]],
    textposition="outside",
    textfont={"size": 10},
    cliponaxis=False,
    customdata=mix_tooltip_df[["Label", "Valor_fmt", "Participacao_fmt", "Rank", "Vs_media_fmt", "Seta"]],
    hovertemplate="<b>🏷️ %{customdata[0]}</b><br><br>💰 Receita: %{customdata[1]}<br>🧩 Participação: %{customdata[2]}<br>🏁 Ranking: #%{customdata[3]}<br>📈 Vs. média: %{customdata[5]} %{customdata[4]}<extra></extra>",
)
style_plotly_figure(mix_chart, color_sequence=["#1F2A5A", "#F25C05", "#8A97B8"], abbreviate_y_axis=True)
dominant_type = mix_df.sort_values("ValorTotal", ascending=False).iloc[0]["TIPO"]
render_single_chart_section(
    "📊 Mix por tipo",
    mix_chart,
    "geral_mix_tipo",
    (
        "Mix por Tipo",
        "Mostra a participacao de cada operacao na receita total.",
        f"Barras maiores indicam maior dependencia; hoje o tipo lider e {dominant_type}.",
        "Ajuda a reduzir concentracao excessiva e orientar prioridades comerciais.",
    ),
)

peso_chart = px.line(daily_df, x="Data", y="PesoTotal", title="Peso por dia")
peso_chart.update_traces(
    line={"color": "#8A97B8", "width": 2.6},
    customdata=daily_tooltip_df[["Data_str", "Peso_fmt", "Valor_fmt", "RKG_fmt", "Var_fmt", "Seta", "Status"]],
    hovertemplate="<b>📅 %{customdata[0]}</b><br><br>⚖️ Peso: %{customdata[1]}<br>💰 Receita: %{customdata[2]}<br>📊 R$/KG: %{customdata[3]}<br><br>📈 Variação da receita: %{customdata[5]} %{customdata[4]}<br>🧠 Status: %{customdata[6]}<extra></extra>",
)
style_plotly_figure(peso_chart, abbreviate_y_axis=True)
configure_daily_chart(peso_chart, daily_df, y_tickformat="~s")
render_single_chart_section(
    "⚖️ Peso por dia",
    peso_chart,
    "geral_peso_dia",
    (
        "Peso por Dia",
        "Representa o volume logistico movimentado no periodo.",
        "Altas indicam maior esforco operacional e necessidade de capacidade.",
        "Compare com a receita para avaliar se o crescimento operacional gera retorno suficiente.",
    ),
)

rkg_chart = px.line(daily_df, x="Data", y="R$/KG", title="R$/KG por dia")
rkg_chart.update_traces(
    line={"color": "#F25C05", "width": 2.6},
    customdata=daily_tooltip_df[["Data_str", "RKG_fmt", "Valor_fmt", "Peso_fmt", "Var_fmt", "Seta", "Status"]],
    hovertemplate="<b>📅 %{customdata[0]}</b><br><br>📊 R$/KG: %{customdata[1]}<br>💰 Receita: %{customdata[2]}<br>⚖️ Peso: %{customdata[3]}<br><br>📈 Variação da receita: %{customdata[5]} %{customdata[4]}<br>🧠 Status: %{customdata[6]}<extra></extra>",
)
style_plotly_figure(rkg_chart)
configure_daily_chart(rkg_chart, daily_df, y_tickformat=".2f")
render_single_chart_section(
    "💰 R$/KG por dia",
    rkg_chart,
    "geral_rkg_dia",
    (
        "R$/KG por Dia",
        f"Mede a eficiencia da operacao em receita por peso; a media atual e {format_ratio(kpis['r_kg'])}.",
        "Quanto maior a linha, melhor o retorno por quilo transportado.",
        "Quedas recorrentes indicam mix menos eficiente ou pressao de margem na operacao.",
    ),
)