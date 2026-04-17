import pandas as pd
import plotly.express as px
import streamlit as st

from utils.auth import guard_page_access, render_logout_button
from utils.chart_text import render_chart_description
from utils.formatters import abreviar_valor, format_currency, format_integer
from utils.load_data import get_dashboard_context
from utils.theme import apply_brand_theme, render_page_header, render_section_gap, style_plotly_figure

st.set_page_config(page_title="Inteligencia", layout="wide", initial_sidebar_state="expanded")
guard_page_access()
apply_brand_theme()
render_logout_button()

df, _, _ = get_dashboard_context()

render_page_header("Inteligencia", "Leitura visual para identificar concentracao de peso, receita e oportunidades")

if df.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

modo = st.radio(
    "Modo de visualizacao",
    ["Detalhado", "Consolidado"],
    horizontal=True,
)

if modo == "Detalhado":
    df_plot = df.copy()
else:
    df_plot = (
        df.groupby(["Produto", "TIPO"], as_index=False)
        .agg(
            {
                "ValorTotal": "sum",
                "PesoTotal": "sum",
                "QuantidadeTotal": "sum",
            }
        )
    )

df_plot = df_plot.copy()
df_plot["Produto"] = df_plot["Produto"].astype(str)
df_plot["TIPO"] = df_plot["TIPO"].fillna("NAO INFORMADO").astype(str)
df_plot["ValorTotal"] = pd.to_numeric(df_plot["ValorTotal"], errors="coerce").fillna(0)
df_plot["PesoTotal"] = pd.to_numeric(df_plot["PesoTotal"], errors="coerce").fillna(0)
df_plot["QuantidadeTotal"] = pd.to_numeric(df_plot["QuantidadeTotal"], errors="coerce").fillna(0)
df_plot["R$/KG"] = df_plot["ValorTotal"] / df_plot["PesoTotal"].replace(0, pd.NA)
df_plot["Quadrante"] = "Outros"

peso_medio = df_plot["PesoTotal"].mean()
valor_medio = df_plot["ValorTotal"].mean()
high_weight_mask = df_plot["PesoTotal"] > df_plot["PesoTotal"].median()
high_value_mask = df_plot["ValorTotal"] > df_plot["ValorTotal"].median()
df_plot.loc[high_weight_mask & high_value_mask, "Quadrante"] = "Alto valor / Alto peso"

df_plot["label"] = ""
top_points = df_plot["ValorTotal"].nlargest(min(8, len(df_plot))).index
df_plot.loc[top_points, "label"] = df_plot.loc[top_points, "ValorTotal"].apply(abreviar_valor)

print(df_plot[["TIPO"]].value_counts())
st.write("Linhas filtradas:", len(df))
st.write("Linhas no grafico:", len(df_plot))

fig = px.scatter(
    df_plot,
    x="PesoTotal",
    y="ValorTotal",
    color="TIPO",
    text="label",
    hover_name="Produto",
    opacity=0.75,
    hover_data={
        "Produto": True,
        "TIPO": True,
        "ValorTotal": ":,.2f",
        "PesoTotal": ":,.0f",
        "QuantidadeTotal": ":,.0f",
        "R$/KG": ":,.2f",
        "Quadrante": True,
        "label": False,
    },
    title="Peso x Valor por produto",
    color_discrete_map={
        "ARLA": "#FF4B4B",
        "AGREGADO": "#4B8BFF",
        "MOBIL": "#1f77b4",
    },
    labels={
        "TIPO": "🏷️ Tipo",
        "ValorTotal": "💰 Receita",
        "PesoTotal": "⚖️ Peso",
        "QuantidadeTotal": "📦 Quantidade",
        "R$/KG": "📊 R$/KG",
        "Quadrante": "🧠 Quadrante",
    },
)
fig.add_vline(x=peso_medio, line_dash="dash", line_color="gray")
fig.add_hline(y=valor_medio, line_dash="dash", line_color="gray")
fig.add_annotation(x=peso_medio, y=valor_medio, text="Centro dos quadrantes", showarrow=True)
fig.update_traces(
    marker={"size": 8},
    textposition="top center",
    textfont={"size": 10},
)
style_plotly_figure(fig, abbreviate_x_axis=True, abbreviate_y_axis=True)

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