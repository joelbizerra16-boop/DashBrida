import plotly.express as px
import streamlit as st

from utils.auth import ensure_authenticated, render_logout_button
from utils.chart_text import render_chart_description
from utils.formatters import abreviar_valor, format_dataframe_ptbr, format_percent
from utils.load_data import get_dashboard_context
from utils.metrics import build_type_analysis
from utils.theme import apply_brand_theme, render_page_header, render_section_gap, style_plotly_figure

st.set_page_config(page_title="Comparativo", layout="wide", initial_sidebar_state="expanded")
apply_brand_theme()
ensure_authenticated()
render_logout_button()

df, _, _ = get_dashboard_context()

render_page_header("Comparativo", "Comparacao executiva entre tipos para orientar alocacao e crescimento")

if df.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

type_df = build_type_analysis(df)

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
    receita_peso_chart.data[0].hovertemplate = "R$ %{y:,.2f}<extra></extra>"
    receita_peso_chart.data[1].hovertemplate = "%{y:,.2f} KG<extra></extra>"
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
        hovertemplate="%{y:,.2f}<extra></extra>",
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

render_section_gap()
st.subheader("Participacao percentual")
participacao_chart = px.pie(
    participacao_df,
    names="TIPO",
    values="ValorTotal",
    title="Participacao na receita",
)
participacao_chart.update_traces(
    customdata=[[abreviar_valor(v)] for v in participacao_df["ValorTotal"]],
    texttemplate="%{percent:.1%}<br>%{customdata[0]}",
    textfont={"size": 10},
    hovertemplate="R$ %{value:,.2f}<extra></extra>",
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