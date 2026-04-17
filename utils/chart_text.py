import streamlit as st


def render_chart_description(title: str, what_is: str, how_to_read: str, insight: str) -> None:
    st.markdown(
        f"""
<div class="brida-chart-note">
    <div class="brida-chart-note-title">{title}</div>
    <div class="brida-chart-note-line">📌 {what_is}</div>
    <div class="brida-chart-note-line">🔍 {how_to_read}</div>
    <div class="brida-chart-note-line">🎯 {insight}</div>
</div>
"""
        ,
        unsafe_allow_html=True,
    )