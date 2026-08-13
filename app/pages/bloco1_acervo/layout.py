"""Renderização da página Bloco 1 — Narrativa do Acervo."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from visual.base import remover_marcos
from .plots import (
    fig_1a_variacao_trienal, fig_1a2_variacao_trienal,
    fig_1b_acervo_por_classe, fig_1b2_acervo_por_classe_vertical,
    fig_1b3_acervo_por_classe_vertical_extremos, fig_1b4_acervo_por_classe_vertical_sem_eixo,
    fig_1c_distribuicao_baixa,
    fig_1d_variacao_anual, fig_1d2_variacao_anual,
)

_CATALOGO = [
    ("1.a — Variação trienal", "Variação trienal do acervo (entradas − saídas) (1988–2025).", fig_1a_variacao_trienal),
    ("1.a.2 — Variação trienal (paleta azul)", "Variação trienal do acervo (entradas − saídas), decréscimo em azul (1988–2025).", fig_1a2_variacao_trienal),
    ("1.b — Acervo por classe", "Acervo ativo por classe processual e ano (apenas totais) (1988–2025).", fig_1b_acervo_por_classe),
    ("1.b2 — Acervo por classe (vertical)", "Acervo ativo por classe processual e ano (barras verticais empilhadas) (1988–2025).", fig_1b2_acervo_por_classe_vertical),
    ("1.b3 — Acervo por classe (vertical, extremos rotulados)", "Igual ao 1.b2, com os totais de 2017 e 2025 rotulados (1988–2025).", fig_1b3_acervo_por_classe_vertical_extremos),
    ("1.b4 — Acervo por classe (vertical, sem eixo esquerdo)", "Igual ao 1.b2, sem eixo esquerdo, com opção de rotular o total de cada ano (1988–2025).", fig_1b4_acervo_por_classe_vertical_sem_eixo),
    ("1.c — Entrada e saída espelhada", "Entradas e saídas anuais, escala espelhada (1988–2025).", fig_1c_distribuicao_baixa),
    ("1.d — Variação anual", "Variação anual do acervo (entradas − saídas) (1988–2025).", fig_1d_variacao_anual),
    ("1.d.2 — Variação anual (paleta azul)", "Variação anual do acervo (entradas − saídas), decréscimo em azul (1988–2025).", fig_1d2_variacao_anual),
]
_LABELS = [item[0] for item in _CATALOGO]


def render_graficos(df: pd.DataFrame) -> None:
    escolha = st.selectbox("Selecione a visualização", options=_LABELS, index=0, key="bloco1_selectbox")
    idx = _LABELS.index(escolha)
    _, descricao, fn = _CATALOGO[idx]

    st.caption(descricao)
    c1, c2 = st.columns(2)
    with c1:
        show_values = st.checkbox("Exibir valores", value=True, key=f"bloco1_sv_{idx}")
    with c2:
        marcos_er = st.checkbox("Marcos ER", value=True, key=f"bloco1_er_{idx}")
    faixa_espin = st.checkbox("Faixa ESPIN", value=True, key=f"bloco1_espin_{idx}")

    fig = fn(df, show_values=show_values)
    if not (marcos_er and faixa_espin):
        fig = remover_marcos(fig, er=marcos_er, espin=faixa_espin)
    st.plotly_chart(fig, width="stretch")

    with st.expander("📊 Dados agregados por ano"):
        tab = df.groupby("ano", as_index=False)[
            ["quantidade_ativos", "quantidade_distribuidos", "quantidade_baixas"]
        ].sum()
        st.dataframe(tab, width="stretch", height=280)
