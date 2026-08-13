"""Renderização da página Bloco 3 — Persistência Pós-Pandêmica."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from visual.base import remover_marcos
from pages.bloco2_inclusoes.plots import fig_2a_participacao_ano, fig_2m_categoria_ano_pv


def render_graficos(df: pd.DataFrame) -> None:
    c1, c2 = st.columns(2)
    with c1:
        show_values = st.checkbox("Exibir valores", value=True, key="bloco3_sv")
    with c2:
        marcos_er = st.checkbox("Marcos ER", value=True, key="bloco3_er")
    faixa_espin = st.checkbox("Faixa ESPIN", value=True, key="bloco3_espin")

    def aplicar(fig):
        return remover_marcos(fig, er=marcos_er, espin=faixa_espin) if not (marcos_er and faixa_espin) else fig

    st.subheader("A ausência de inflexão no fim da ESPIN")
    st.caption(
        "O mesmo gráfico 2.a, agora lido sob a ótica da persistência: a participação do "
        "Plenário Virtual não recua após o fim da ESPIN (abril de 2022) — o patamar de "
        "universalização atingido durante a pandemia se sustenta como novo normal institucional."
    )
    st.plotly_chart(aplicar(fig_2a_participacao_ano(df, show_values=show_values)), width="stretch")

    st.markdown("---")

    st.subheader("O desfecho por categoria também se mantém estável")
    st.caption(
        "O mesmo gráfico 2.m: a composição do desfecho no Plenário Virtual (unanimidade "
        "dominante) não se altera estruturalmente entre o período ESPIN e o pós-ESPIN, "
        "reforçando a leitura de persistência institucional."
    )
    st.plotly_chart(aplicar(fig_2m_categoria_ano_pv(df, show_values=show_values)), width="stretch")
