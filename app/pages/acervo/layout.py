"""Renderização da página de Acervo."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from .plots import plotar_grafico_stf
from pages.tramitacao.plots import gt10_tabulador
from dados.filters import dimensoes_disponiveis

_PREDEFINIDOS_ACERVO = [
    ("Ano × Classe (total geral, empilhado)",         "ano", "classe",        "inclusoes", "stack"),
    ("Ano × Classe (total geral, empilhado 100%)",    "ano", "classe",        "inclusoes", "100%"),
    ("Classe × Macro-Desfecho (inclusões, agrupado)", "classe", "macro_desfecho", "inclusoes", "group"),
    ("Ano × Ambiente (inclusões, empilhado)",         "ano", "ambiente",      "inclusoes", "stack"),
]

# Métricas disponíveis no dataset
_METRICAS = [
    (
        "quantidade_ativos",
        "Processos Ativos",
        "Acervo Ativo",
        "Estoque de processos **sem baixa definitiva** ao final de cada ano (31/12). "
        "Mede o volume pendente de julgamento e é o principal indicador de pressão sobre a pauta do tribunal.",
    ),
    (
        "quantidade_inativos",
        "Processos Inativos",
        "Acervo Inativo",
        "Estoque **acumulado** de processos já encerrados até o final de cada ano. "
        "Representa o histórico total de casos resolvidos desde 1988.",
    ),
    (
        "total_geral",
        "Total de Processos",
        "Total Geral",
        "Soma dos processos ativos e inativos ao final de cada ano. "
        "Reflete o volume total de ações já distribuídas no tribunal desde sua criação.",
    ),
    (
        "quantidade_baixas",
        "Processos Baixados",
        "Baixas Anuais",
        "**Fluxo anual** de processos encerrados em cada ano. Diferente do acervo inativo (estoque), "
        "as baixas medem a produtividade do tribunal ano a ano — picos indicam o impacto das Emendas Regimentais e do Plenário Virtual.",
    ),
    (
        "quantidade_distribuidos",
        "Processos Distribuídos",
        "Distribuições (Entrada)",
        "**Fluxo anual** de novos processos distribuídos ao relator em cada ano. "
        "Mede a pressão de entrada no tribunal e permite comparar a taxa de entrada com a taxa de baixas.",
    ),
]


def _wrapper_metrica(col: str, label: str):
    """Fecha sobre a coluna/rótulo da métrica; decide TOTAL vs. classe única a
    partir de quantas classes sobraram no recorte que a casca entrega.

    plotar_grafico_stf("TOTAL", ...) soma o dataframe que recebe via
    groupby("ano").sum() — não assume a base inteira — então agregar um
    subconjunto de 2-3 classes é uma leitura honesta (verificado).
    """
    def _plot(df: pd.DataFrame, show_values: bool = True, **_kw):
        classes = df["classe"].dropna().unique().tolist()
        classe = classes[0] if len(classes) == 1 else "TOTAL"
        return plotar_grafico_stf(df, classe, col, label, show_values)
    return _plot


_CATALOGO = [
    GraficoSpec(
        id=f"A{i + 1}",
        rotulo=f"A{i + 1} — {titulo}",
        subtitulo=f"Evolução — {titulo}",
        descricao=descricao,
        fn=_wrapper_metrica(col, label),
        tipos=("barra", "linha"),
        filtros=("classe", "periodo"),
    )
    for i, (col, label, titulo, descricao) in enumerate(_METRICAS)
]


def _render_interactive_tabulador() -> None:
    from dados.loader import load_inclusoes_em_pauta
    df_inc = load_inclusoes_em_pauta()

    st.subheader("Tabulador Gráfico Interativo")
    st.caption(
        "Configure livremente os eixos, agrupamento e modo de barras sobre o dataset "
        "de inclusões em pauta — diferente dos gráficos de evolução acima, que usam o acervo histórico."
    )

    dims = dimensoes_disponiveis(df_inc.columns)
    dims_label = list(dims.keys())
    colunas_ok = set(dims.values())
    presets = [p for p in _PREDEFINIDOS_ACERVO if p[1] in colunas_ok and p[2] in colunas_ok]
    labels_pre = [p[0] for p in presets]

    col_pre, _ = st.columns([2, 1])
    with col_pre:
        pre_escolha = st.selectbox(
            "🔖 Pré-definidos",
            options=["— ou configure manualmente abaixo —"] + labels_pre,
            index=0,
            key="acervo_predefinido",
        )

    escolha_dims = pre_escolha if not pre_escolha.startswith("—") else labels_pre[0]
    _, px, pg, pm, pbm = next(p for p in presets if p[0] == escolha_dims)
    def_x  = dims_label.index(next(k for k, v in dims.items() if v == px))
    def_g  = dims_label.index(next(k for k, v in dims.items() if v == pg))
    def_m  = ["inclusoes", "processos"].index(pm)
    def_bm = ["group", "stack", "100%"].index(pbm)

    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    with c1:
        eixo_x_lbl = st.selectbox("Eixo X",    dims_label, index=def_x, key="acervo_tab_x_v2")
    with c2:
        grupo_lbl  = st.selectbox("Cor/Grupo", dims_label, index=def_g, key="acervo_tab_g_v2")
    with c3:
        metrica = st.selectbox(
            "Métrica", ["inclusoes", "processos"], index=def_m, key="acervo_tab_m",
            format_func=lambda v: "Inclusões em pauta" if v == "inclusoes" else "Processos distintos",
        )
    with c4:
        barmode = st.selectbox(
            "Modo", ["group", "stack", "100%"], index=def_bm, key="acervo_tab_bm",
            format_func=lambda v: {"group": "Agrupado", "stack": "Empilhado", "100%": "Empilhado 100%"}[v],
        )
    with c5:
        show_values = st.checkbox("Exibir valores", value=False, key="acervo_tab_sv")

    eixo_x = dims[eixo_x_lbl]
    grupo  = dims[grupo_lbl]

    if eixo_x == grupo:
        st.warning("Eixo X e Cor/Grupo não podem ser a mesma dimensão.")
        return

    st.plotly_chart(
        gt10_tabulador(df_inc, eixo_x, grupo, metrica, barmode, show_values),
        width="stretch",
    )


def render_graficos(df: pd.DataFrame) -> None:
    """Ponto de entrada: catálogo A1-A5 + Tabulador Gráfico livre (A6)."""
    render_pagina(_CATALOGO, df, key_prefix="acervo")

    st.markdown("---")
    with st.expander("🔧 Tabulador Gráfico Interativo — eixos livres (A6)"):
        _render_interactive_tabulador()
