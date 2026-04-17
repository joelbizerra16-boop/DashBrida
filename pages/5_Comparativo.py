import plotly.express as px
import streamlit as st

from utils.auth import guard_page_access, render_logout_button
from utils.chart_text import render_chart_description
from utils.formatters import (
    abreviar_valor,
    build_category_tooltip_dataframe,
    build_pie_tooltip_dataframe,
    format_dataframe_ptbr,
    format_percent,
)
from utils.load_data import get_dashboard_context, init_session_state
from utils.metrics import build_type_analysis
from utils.theme import apply_brand_theme, render_page_header, render_section_gap, style_plotly_figure

st.set_page_config(page_title="Comparativo", layout="wide", initial_sidebar_state="expanded")
guard_page_access()
init_session_state()
apply_brand_theme()
render_logout_button()

df, _, _ = get_dashboard_context()

render_page_header("Comparativo", "Comparacao executiva entre tipos para orientar alocacao e crescimento")

if df.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

type_df = build_type_analysis(df)
comparativo_receita_tooltip_df = build_category_tooltip_dataframe(
    type_df,
    label_column="TIPO",
    value_column="ValorTotal",
    weight_column="PesoTotal",
    ratio_column="R$/KG",
)
comparativo_peso_tooltip_df = build_category_tooltip_dataframe(
    type_df,
    label_column="TIPO",
    value_column="PesoTotal",
    value_mode="weight",
    weight_column="PesoTotal",
    ratio_column="R$/KG",
)
comparativo_eficiencia_tooltip_df = build_category_tooltip_dataframe(
    type_df,
    label_column="TIPO",
    value_column="R$/KG",
    value_mode="ratio",
    weight_column="PesoTotal",
    ratio_column="R$/KG",
)

render_section_gap()
col1, col2 = st.columns(2)
with col1:
    receita_peso_chart = px.bar(
        type_df,
        x="TIPO",
        y=["ValorTotal", "PesoTotal"],
        barmode="group",
        title="Receita x Peso",
    )
    receita_peso_chart.update_traces(
        texttemplate="%{y:.2s}",
        textposition="outside",
        textfont={"size": 10},
        cliponaxis=False,
    )
    receita_peso_chart.data[0].customdata = comparativo_receita_tooltip_df[["Label", "Valor_fmt", "Peso_fmt", "RKG_fmt", "Participacao_fmt", "Rank", "Vs_media_fmt", "Seta"]]
    receita_peso_chart.data[0].hovertemplate = "<b>🏷️ %{customdata[0]}</b><br><br>💰 Receita: %{customdata[1]}<br>⚖️ Peso: %{customdata[2]}<br>📊 R$/KG: %{customdata[3]}<br>🧩 Participação: %{customdata[4]}<br>🏁 Ranking: #%{customdata[5]}<br>📈 Vs. média: %{customdata[7]} %{customdata[6]}<extra></extra>"
    receita_peso_chart.data[1].customdata = comparativo_peso_tooltip_df[["Label", "Valor_fmt", "RKG_fmt", "Participacao_fmt", "Rank", "Vs_media_fmt", "Seta"]]
    receita_peso_chart.data[1].hovertemplate = "<b>🏷️ %{customdata[0]}</b><br><br>⚖️ Peso: %{customdata[1]}<br>📊 R$/KG: %{customdata[2]}<br>🧩 Participação: %{customdata[3]}<br>🏁 Ranking: #%{customdata[4]}<br>📈 Vs. média: %{customdata[6]} %{customdata[5]}<extra></extra>"
    style_plotly_figure(receita_peso_chart, color_sequence=["#1F2A5A", "#8A97B8"], abbreviate_y_axis=True)
    st.plotly_chart(receita_peso_chart, width="stretch", key="comparativo_receita_peso")
    top_revenue_type = type_df.sort_values("ValorTotal", ascending=False).iloc[0]["TIPO"]
    render_chart_description(
        "Receita x Peso",
        "Compara o tamanho financeiro e operacional de cada tipo.",
        f"Diferencas entre receita e peso mostram eficiencia relativa; hoje {top_revenue_type} lidera em receita.",
        "Ajuda a entender quais operacoes crescem com equilibrio e quais consomem muito peso para pouco retorno.",
    )

with col2:
    eficiencia_chart = px.bar(type_df, x="TIPO", y="R$/KG", title="Eficiencia por tipo")
    eficiencia_chart.update_traces(
        text=[abreviar_valor(v) for v in type_df["R$/KG"]],
        textposition="outside",
        textfont={"size": 10},
        cliponaxis=False,
        customdata=comparativo_eficiencia_tooltip_df[["Label", "Valor_fmt", "Peso_fmt", "Participacao_fmt", "Rank", "Vs_media_fmt", "Seta"]],
        hovertemplate="<b>🏷️ %{customdata[0]}</b><br><br>📊 R$/KG: %{customdata[1]}<br>⚖️ Peso: %{customdata[2]}<br>🧩 Participação: %{customdata[3]}<br>🏁 Ranking: #%{customdata[4]}<br>📈 Vs. média: %{customdata[6]} %{customdata[5]}<extra></extra>",
    )
    style_plotly_figure(eficiencia_chart, color_sequence=["#F25C05"])
    st.plotly_chart(eficiencia_chart, width="stretch", key="comparativo_eficiencia")
    render_chart_description(
        "Eficiencia por Tipo",
        "Mostra o retorno medio por quilo dentro de cada operacao.",
        "Barras maiores representam melhor aproveitamento economico do peso movimentado.",
        "Use para decidir onde expandir, ajustar preco ou revisar o mix transportado.",
    )

participacao_df = type_df.copy()
participacao_df["ParticipacaoLabel"] = participacao_df["Participacao"].apply(format_percent)
participacao_tooltip_df = build_pie_tooltip_dataframe(
    participacao_df,
    label_column="TIPO",
    value_column="ValorTotal",
)

render_section_gap()
st.subheader("Participacao percentual")
participacao_chart = px.pie(
    participacao_df,
    names="TIPO",
    values="ValorTotal",
    title="Participacao na receita",
)
participacao_chart.update_traces(
    customdata=participacao_tooltip_df[["Label", "Valor_fmt", "Participacao_fmt", "Rank"]],
    texttemplate="%{percent:.1%}<br>%{customdata[0]}",
    textfont={"size": 10},
    hovertemplate="<b>🥧 %{customdata[0]}</b><br><br>💰 Receita: %{customdata[1]}<br>🧩 Participação: %{customdata[2]}<br>🏁 Ranking: #%{customdata[3]}<extra></extra>",
)
style_plotly_figure(participacao_chart, color_sequence=["#1F2A5A", "#F25C05", "#8A97B8"])
st.plotly_chart(participacao_chart, width="stretch", key="comparativo_participacao")
main_share = participacao_df.sort_values("Participacao", ascending=False).iloc[0]
render_chart_description(
    "Participacao na Receita",
    "Mostra quanto cada tipo representa no faturamento total.",
    f"Fatias maiores indicam maior dependencia; hoje {main_share['TIPO']} responde por {format_percent(main_share['Participacao'])}.",
    "Ajuda a balancear risco comercial e definir onde diversificar a operacao.",
)
st.dataframe(
    format_dataframe_ptbr(
        participacao_df[["TIPO", "ValorTotal", "PesoTotal", "R$/KG", "ParticipacaoLabel"]].rename(
            columns={"ParticipacaoLabel": "Participacao %"}
        )
    ),
    width="stretch",
)