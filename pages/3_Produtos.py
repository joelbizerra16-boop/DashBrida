import plotly.express as px
import streamlit as st

from utils.auth import guard_page_access, render_logout_button
from utils.chart_text import render_chart_description
from utils.formatters import abreviar_valor, build_category_tooltip_dataframe, format_dataframe_ptbr
from utils.load_data import get_dashboard_context
from utils.metrics import build_product_analysis
from utils.theme import apply_brand_theme, render_page_header, render_section_gap, style_plotly_figure

st.set_page_config(page_title="Produtos", layout="wide", initial_sidebar_state="expanded")
guard_page_access()
apply_brand_theme()
render_logout_button()

df, _, _ = get_dashboard_context()

render_page_header("Produtos", "Acompanhamento dos itens com maior impacto comercial e operacional")

if df.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

product_df = build_product_analysis(df)
top10_tooltip_df = build_category_tooltip_dataframe(
    product_df.head(10),
    label_column="Produto",
    value_column="ValorTotal",
    weight_column="PesoTotal",
    ratio_column="R$/KG",
)

render_section_gap()
col1, col2 = st.columns(2)
with col1:
    st.subheader("Ranking por faturamento")
    st.dataframe(format_dataframe_ptbr(product_df[["Produto", "ValorTotal"]].head(20)), width="stretch")

with col2:
    st.subheader("Ranking por quantidade")
    st.dataframe(
        format_dataframe_ptbr(
            product_df.sort_values("QuantidadeTotal", ascending=False)[["Produto", "QuantidadeTotal"]].head(20)
        ),
        width="stretch",
    )

st.subheader("Top 20 produtos")
st.dataframe(format_dataframe_ptbr(product_df.head(20)), width="stretch")

render_section_gap()
top10_chart = px.bar(
    product_df.head(10),
    x="Produto",
    y="ValorTotal",
    title="Top 10 faturamento",
)
top10_chart.update_layout(xaxis_tickangle=-35)
top10_chart.update_traces(
    text=[abreviar_valor(v) for v in product_df.head(10)["ValorTotal"]],
    textposition="outside",
    textfont={"size": 10},
    cliponaxis=False,
    customdata=top10_tooltip_df[["Label", "Valor_fmt", "Peso_fmt", "RKG_fmt", "Participacao_fmt", "Rank", "Vs_media_fmt", "Seta"]],
    hovertemplate="<b>📦 %{customdata[0]}</b><br><br>💰 Receita: %{customdata[1]}<br>⚖️ Peso: %{customdata[2]}<br>📊 R$/KG: %{customdata[3]}<br>🧩 Participação: %{customdata[4]}<br>🏁 Ranking: #%{customdata[5]}<br>📈 Vs. média: %{customdata[7]} %{customdata[6]}<extra></extra>",
)
style_plotly_figure(top10_chart, color_sequence=["#1F2A5A"], abbreviate_y_axis=True)
st.plotly_chart(top10_chart, width="stretch", key="produtos_top10_faturamento")
top_product = product_df.iloc[0]["Produto"]
render_chart_description(
    "Top 10 Faturamento",
    "Mostra os produtos que mais geram receita no periodo selecionado.",
    f"Barras maiores representam maior impacto financeiro; o lider atual e {top_product}.",
    "Use para reforcar estoque, negociacao e foco comercial nos itens mais relevantes.",
)