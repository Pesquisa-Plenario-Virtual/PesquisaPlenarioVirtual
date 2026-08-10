"""Renderização da página de Reajuste de Voto."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from .plots import (
    gr1_reajuste_pct, gr3_anual_filtravel, gr5_classe_filtravel,
    gr7_tipo_vs_reajuste, gr8_desfecho_vs_reajuste,
)
from pages.tramitacao.plots import gt10_tabulador
from dados.filters import dimensoes_disponiveis

_PREDEFINIDOS_TAB = [
    ("Ano × Reajuste (inclusões, empilhado 100%)",    "ano",          "teve_reajuste",  "inclusoes", "100%"),
    ("Ambiente × Reajuste (inclusões, agrupado)",     "ambiente",     "teve_reajuste",  "inclusoes", "group"),
    ("Classe × Reajuste (inclusões, empilhado 100%)", "classe",       "teve_reajuste",  "inclusoes", "100%"),
    ("Tipo de Questão × Reajuste (inclusões)",        "tipo_questao", "teve_reajuste",  "inclusoes", "group"),
    ("Macro-Desfecho × Reajuste (inclusões)",         "macro_desfecho", "teve_reajuste", "inclusoes", "group"),
    ("Desfecho Detalhado × Reajuste (inclusões)",     "desfecho",       "teve_reajuste",  "inclusoes", "group"),
]

# ── Catálogo R1–R8 (R9 é o tabulador livre, fora do catálogo) ──────────────────
_CATALOGO = [
    GraficoSpec(
        id="R1/R2",
        rotulo="R1/R2 — % com reajuste (Plenário Virtual e Plenário Presencial)",
        subtitulo="Reajuste de Voto — período total",
        descricao="Percentual de inclusões que tiveram ao menos um reajuste de voto, por ambiente.",
        fn=gr1_reajuste_pct,
        tipos=("barra",),
        filtros=("classe", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="R3/R4",
        rotulo="R3/R4 — Reajustes por Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Reajuste de Voto por Ano",
        descricao="Volume anual de inclusões que registraram reajuste de voto. "
                  "Anos sem ocorrência aparecem com valor zero. Selecione o âmbito.",
        fn=gr3_anual_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="R5/R6",
        rotulo="R5/R6 — Reajustes por Ano e Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="Reajuste de Voto por Ano e Classe",
        descricao="Barras agrupadas por classe (ADI, ADPF, ADC, ADO) mostrando o volume anual "
                  "de reajustes de voto. Selecione o âmbito.",
        fn=gr5_classe_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="R7",
        rotulo="R7 — Tipo de Questão × Reajuste",
        subtitulo="Tipo de Questão × Reajuste (inclusões)",
        descricao="Distribuição das inclusões com/sem reajuste por tipo de questão (PR/RC/QI).",
        fn=gr7_tipo_vs_reajuste,
        tipos=("barra",),
        filtros=("ambiente", "classe", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="R8",
        rotulo="R8 — Desfecho Detalhado × Reajuste",
        subtitulo="Desfecho Detalhado × Reajuste (inclusões)",
        descricao="Distribuição das inclusões com/sem reajuste por desfecho detalhado.",
        fn=gr8_desfecho_vs_reajuste,
        tipos=("barra", "barra_h"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
]


def _render_interactive_tabulador(df: pd.DataFrame) -> None:
    st.subheader("Tabulador Gráfico Interativo")
    st.caption("Configure livremente os eixos, agrupamento e modo de barras.")

    dims = dimensoes_disponiveis(df.columns)
    dims_label = list(dims.keys())
    colunas_ok = set(dims.values())
    presets = [p for p in _PREDEFINIDOS_TAB if p[1] in colunas_ok and p[2] in colunas_ok]
    labels_pre = [p[0] for p in presets]

    col_pre, _ = st.columns([2, 1])
    with col_pre:
        pre_escolha = st.selectbox(
            "🔖 Pré-definidos",
            options=["— ou configure manualmente abaixo —"] + labels_pre,
            index=0,
            key="reaj_predefinido",
        )

    escolha_dims = pre_escolha if not pre_escolha.startswith("—") else labels_pre[0]
    _, px, pg, pm, pbm = next(p for p in presets if p[0] == escolha_dims)
    def_x  = dims_label.index(next(k for k, v in dims.items() if v == px))
    def_g  = dims_label.index(next(k for k, v in dims.items() if v == pg))
    def_m  = ["inclusoes", "processos"].index(pm)
    def_bm = ["group", "stack", "100%"].index(pbm)

    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    with c1:
        eixo_x_lbl = st.selectbox("Eixo X", dims_label, index=def_x, key="reaj_tab_x")
    with c2:
        eixo_y_lbl = st.selectbox("Eixo Y", dims_label, index=def_g, key="reaj_tab_y")
    with c3:
        metrica = st.selectbox(
            "Métrica", ["inclusoes", "processos"], index=def_m, key="reaj_tab_m",
            format_func=lambda v: "Inclusões em pauta" if v == "inclusoes" else "Processos distintos",
        )
    with c4:
        barmode = st.selectbox(
            "Modo", ["group", "stack", "100%"], index=def_bm, key="reaj_tab_bm",
            format_func=lambda v: {"group": "Agrupado", "stack": "Empilhado", "100%": "Empilhado 100%"}[v],
        )
    with c5:
        show_values_tab = st.checkbox("Exibir valores", value=False, key="reaj_tab_sv")

    eixo_x = dims[eixo_x_lbl]
    eixo_y = dims[eixo_y_lbl]

    if eixo_x == eixo_y:
        st.warning("Eixo X e Eixo Y não podem ser a mesma dimensão.")
        return

    st.plotly_chart(
        gt10_tabulador(df, eixo_x, eixo_y, metrica, barmode, show_values_tab),
        width="stretch",
    )

    st.markdown("---")
    st.subheader("Tabela — mesmos eixos")
    d = df.copy()
    d["tipo_questao"] = d["tipo_questao"].replace({"IJ": "QI"})
    if metrica == "processos":
        d = d.drop_duplicates("incidente")
    tab = d.groupby([eixo_x, eixo_y], observed=True).size().reset_index(name="n")
    if barmode == "100%":
        totais = tab.groupby(eixo_x)["n"].transform("sum")
        tab["n"] = (tab["n"] / totais * 100).round(1)
    pvt = tab.pivot_table(index=eixo_x, columns=eixo_y, values="n", fill_value=0)
    pvt["Total"] = pvt.sum(axis=1)
    pvt.loc["Total"] = pvt.sum()
    pvt = pvt.reset_index()
    pvt[pvt.columns[0]] = pvt[pvt.columns[0]].astype(str)
    fmt = {c: "{:,.0f}" for c in pvt.columns if pvt[c].dtype.kind in "iuf"}
    st.dataframe(pvt.style.format(fmt, na_rep="—"), width="stretch", height=280)


def render_graficos(df: pd.DataFrame) -> None:
    render_pagina(_CATALOGO, df, key_prefix="reaj")

    st.markdown("---")
    with st.expander("🔧 Tabulador Interativo — eixos livres (R9)"):
        _render_interactive_tabulador(df)
