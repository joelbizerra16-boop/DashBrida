import plotly.express as px
import streamlit as st

from utils.auth import ensure_authenticated, render_logout_button
from utils.chart_text import render_chart_description
from utils.formatters import abreviar_valor, format_currency, format_integer
from utils.load_data import get_dashboard_context
from utils.theme import apply_brand_theme, render_page_header, render_section_gap, style_plotly_figure

st.set_page_config(page_title="Inteligencia", layout="wide", initial_sidebar_state="expanded")
apply_brand_theme()
ensure_authenticated()
render_logout_button()

df, _, _ = get_dashboard_context()

render_page_header("Inteligencia", "Leitura visual para identificar concentracao de peso, receita e oportunidades")

if df.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

peso_medio = df["PesoTotal"].mean()
valor_medio = df["ValorTotal"].mean()
scatter_df = df.copy()
scatter_df["label"] = ""
top_points = scatter_df["ValorTotal"].nlargest(min(8, len(scatter_df))).index
scatter_df.loc[top_points, "label"] = scatter_df.loc[top_points, "ValorTotal"].apply(abreviar_valor)

fig = px.scatter(
    scatter_df,
    x="PesoTotal",
    y="ValorTotal",
    color="TIPO",
    text="label",
    hover_data=["Produto", "QuantidadeTotal"],
    title="Peso x Valor por produto",
)
fig.add_vline(x=peso_medio, line_dash="dash", line_color="gray")
fig.add_hline(y=valor_medio, line_dash="dash", line_color="gray")
fig.add_annotation(x=peso_medio, y=valor_medio, text="Centro dos quadrantes", showarrow=True)
fig.update_traces(
    textposition="top center",
    textfont={"size": 10},
    hovertemplate="Peso: %{x:,.2f} KG<br>Valor: R$ %{y:,.2f}<extra></extra>",
)
style_plotly_figure(fig, color_sequence=["#1F2A5A", "#F25C05", "#8A97B8"], abbreviate_x_axis=True, abbreviate_y_axis=True)

render_section_gap()
st.plotly_chart(fig, width="stretch", key="inteligencia_scatter")
render_chart_description(
    "Peso x Receita",
    "Relaciona peso transportado com faturamento de cada produto.",
    f"Pontos acima e a direita tendem a ser mais fortes; o centro atual esta em {format_integer(peso_medio)} KG e {format_currency(valor_medio)}.",
    "Use os quadrantes para separar produtos promissores, ineficientes e candidatos a revisao.",
)

render_section_gap()
col1, col2 = st.columns(2)
with col1:
    st.caption("Quadrante superior direito: alto peso e alto valor.")
with col2:
    st.caption("Quadrante inferior esquerdo: baixo peso e baixo valor.")