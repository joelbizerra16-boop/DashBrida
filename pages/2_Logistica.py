import plotly.express as px
import streamlit as st

from utils.auth import guard_page_access, render_logout_button
from utils.chart_text import render_chart_description
from utils.formatters import (
    abreviar_valor,
    build_category_tooltip_dataframe,
    format_currency,
    format_dataframe_ptbr,
    format_integer,
    format_ratio,
)
from utils.load_data import get_dashboard_context
from utils.metrics import build_product_analysis, build_type_analysis
from utils.theme import apply_brand_theme, render_kpi_card, render_page_header, render_section_gap, style_plotly_figure

st.set_page_config(page_title="Logistica", layout="wide", initial_sidebar_state="expanded")
guard_page_access()
apply_brand_theme()
render_logout_button()

df, _, _ = get_dashboard_context()

render_page_header("Logistica", "Monitoramento de peso, eficiencia e pressao operacional por tipo")

if df.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

type_df = build_type_analysis(df)
product_df = build_product_analysis(df)
type_weight_tooltip_df = build_category_tooltip_dataframe(
    type_df,
    label_column="TIPO",
    value_column="PesoTotal",
    value_mode="weight",
    weight_column="PesoTotal",
    ratio_column="R$/KG",
)
type_efficiency_tooltip_df = build_category_tooltip_dataframe(
    type_df,
    label_column="TIPO",
    value_column="R$/KG",
    value_mode="ratio",
    weight_column="PesoTotal",
    ratio_column="R$/KG",
)

col1, col2, col3 = st.columns(3)
with col1:
    render_kpi_card("Peso total", format_integer(type_df["PesoTotal"].sum()), tone="muted")
with col2:
    render_kpi_card("Receita total", format_currency(type_df["ValorTotal"].sum()), tone="blue")
with col3:
    render_kpi_card(
        "R$/KG medio",
        format_ratio(type_df["ValorTotal"].sum() / type_df["PesoTotal"].sum() if type_df["PesoTotal"].sum() > 0 else 0),
        tone="orange",
    )

render_section_gap()

chart_col1, chart_col2 = st.columns(2)
with chart_col1:
    with st.container():
        peso_chart = px.bar(type_df, x="TIPO", y="PesoTotal", title="Peso por tipo")
        peso_chart.update_traces(
            text=[abreviar_valor(v) for v in type_df["PesoTotal"]],
            textposition="outside",
            textfont={"size": 10},
            cliponaxis=False,
            customdata=type_weight_tooltip_df[["Label", "Valor_fmt", "RKG_fmt", "Participacao_fmt", "Rank", "Vs_media_fmt", "Seta"]],
            hovertemplate="<b>🏷️ %{customdata[0]}</b><br><br>⚖️ Peso: %{customdata[1]}<br>📊 R$/KG: %{customdata[2]}<br>🧩 Participação: %{customdata[3]}<br>🏁 Ranking: #%{customdata[4]}<br>📈 Vs. média: %{customdata[6]} %{customdata[5]}<extra></extra>",
        )
        style_plotly_figure(peso_chart, color_sequence=["#8A97B8"], abbreviate_y_axis=True)
        st.plotly_chart(peso_chart, width="stretch", key="logistica_peso_tipo")
        top_weight_type = type_df.sort_values("PesoTotal", ascending=False).iloc[0]["TIPO"]
        render_chart_description(
            "Peso por Tipo",
            "Mostra onde esta concentrado o maior volume logistico da operacao.",
            f"Barras mais altas exigem mais estrutura; hoje o maior peso esta em {top_weight_type}.",
            "Use para ajustar capacidade, frota e prioridade operacional por tipo.",
        )

with chart_col2:
    with st.container():
        eficiencia_chart = px.bar(type_df, x="TIPO", y="R$/KG", title="Eficiencia por tipo")
        eficiencia_chart.update_traces(
            text=[abreviar_valor(v) for v in type_df["R$/KG"]],
            textposition="outside",
            textfont={"size": 10},
            cliponaxis=False,
            customdata=type_efficiency_tooltip_df[["Label", "Valor_fmt", "Peso_fmt", "Participacao_fmt", "Rank", "Vs_media_fmt", "Seta"]],
            hovertemplate="<b>🏷️ %{customdata[0]}</b><br><br>📊 R$/KG: %{customdata[1]}<br>⚖️ Peso: %{customdata[2]}<br>🧩 Participação: %{customdata[3]}<br>🏁 Ranking: #%{customdata[4]}<br>📈 Vs. média: %{customdata[6]} %{customdata[5]}<extra></extra>",
        )
        style_plotly_figure(eficiencia_chart, color_sequence=["#F25C05"])
        st.plotly_chart(eficiencia_chart, width="stretch", key="logistica_eficiencia_tipo")
        best_efficiency_type = type_df.sort_values("R$/KG", ascending=False).iloc[0]["TIPO"]
        render_chart_description(
            "Eficiencia por Tipo",
            "Compara o retorno financeiro por quilo entre os tipos de operacao.",
            f"Barras mais altas entregam melhor retorno; o melhor desempenho atual e {best_efficiency_type}.",
            "Ajuda a priorizar linhas mais eficientes e revisar operacoes com menor rentabilidade.",
        )

render_section_gap()
st.subheader("Ranking de produtos mais pesados")
ranking_peso = product_df.sort_values("PesoTotal", ascending=False).head(20)
ranking_tooltip_df = build_category_tooltip_dataframe(
    ranking_peso.head(10),
    label_column="Produto",
    value_column="PesoTotal",
    value_mode="weight",
    weight_column="PesoTotal",
    ratio_column="R$/KG",
)
ranking_chart = px.bar(
    ranking_peso.head(10),
    x="PesoTotal",
    y="Produto",
    orientation="h",
    title="Top 10 produtos por peso",
)
ranking_chart.update_layout(yaxis={"categoryorder": "total ascending"})
ranking_chart.update_traces(
    text=[abreviar_valor(v) for v in ranking_peso.head(10)["PesoTotal"]],
    textposition="outside",
    textfont={"size": 10},
    cliponaxis=False,
    customdata=ranking_tooltip_df[["Label", "Valor_fmt", "RKG_fmt", "Participacao_fmt", "Rank", "Vs_media_fmt", "Seta"]],
    hovertemplate="<b>📦 %{customdata[0]}</b><br><br>⚖️ Peso: %{customdata[1]}<br>📊 R$/KG: %{customdata[2]}<br>🧩 Participação: %{customdata[3]}<br>🏁 Ranking: #%{customdata[4]}<br>📈 Vs. média: %{customdata[6]} %{customdata[5]}<extra></extra>",
)
style_plotly_figure(ranking_chart, color_sequence=["#1F2A5A"], abbreviate_x_axis=True)
st.plotly_chart(ranking_chart, width="stretch", key="logistica_ranking_peso")
heaviest_product = ranking_peso.iloc[0]["Produto"]
render_chart_description(
    "Ranking de Produtos Mais Pesados",
    "Lista os produtos que mais pressionam a operacao em volume transportado.",
    f"Os primeiros colocados concentram o maior peso; o lider atual e {heaviest_product}.",
    "Use para revisar armazenagem, frete e negociacao dos itens que mais consomem capacidade.",
)
st.dataframe(format_dataframe_ptbr(ranking_peso), width="stretch")