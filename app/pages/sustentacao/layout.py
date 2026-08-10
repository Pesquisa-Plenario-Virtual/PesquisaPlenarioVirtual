"""Renderização da página de Sustentação Oral."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from .plots import (
    gs1_sust_filtravel, gs3_sust_anual_filtravel,
    gs5_sust_classe_filtravel, gs7_sust_tipo_filtravel, gs8_taxa_ambiente,
)
from pages.tramitacao.plots import gt10_tabulador
from dados.filters import dimensoes_disponiveis

_PREDEFINIDOS_SUST = [
    ("Ambiente × Classe (inclusões, agrupado)",           "ambiente",        "classe",            "inclusoes", "group"),
    ("Ambiente × Sustentação (inclusões, agrupado)",      "ambiente",        "teve_sustentacao",  "inclusoes", "group"),
    ("Ano × Sustentação (inclusões, empilhado 100%)",     "ano",             "teve_sustentacao",  "inclusoes", "100%"),
    ("Classe × Sustentação (inclusões, empilhado 100%)",  "classe",          "teve_sustentacao",  "inclusoes", "100%"),
    ("Tipo de Questão × Sustentação (inclusões)",         "tipo_questao",    "teve_sustentacao",  "inclusoes", "group"),
    ("Macro-Desfecho × Sustentação (inclusões)",          "macro_desfecho",  "teve_sustentacao",  "inclusoes", "group"),
]

# ── Catálogo S1–S8 (S9 é o tabulador livre, fora do catálogo) ──────────────────
_CATALOGO = [
    GraficoSpec(
        id="S1/S2",
        rotulo="S1/S2 — Proporção com/sem sustentação (Plenário Virtual e Plenário Presencial)",
        subtitulo="Sustentação Oral — período total",
        descricao="Pizza com a proporção de inclusões que tiveram sustentação oral. "
                  "Selecione o âmbito.",
        fn=gs1_sust_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="S3/S4",
        rotulo="S3/S4 — Sustentações por Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Sustentação Oral por Ano",
        descricao="Volume anual de inclusões com sustentação oral. "
                  "Anos sem ocorrência aparecem com valor zero. Selecione o âmbito.",
        fn=gs3_sust_anual_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="S5/S6",
        rotulo="S5/S6 — Sustentações por Ano e Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="Sustentação Oral por Ano e Classe",
        descricao="Barras agrupadas por classe (ADI, ADPF, ADC, ADO) mostrando o volume anual "
                  "de sustentações orais. Selecione o âmbito.",
        fn=gs5_sust_classe_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="S7",
        rotulo="S7 — Sustentações por Ano e Tipo de Questão",
        subtitulo="Sustentação Oral por Ano e Tipo de Questão",
        descricao="Barras agrupadas por tipo de questão (PR / RC / QI) mostrando o volume anual "
                  "de sustentações orais. IJ renomeado para QI. Selecione o âmbito.",
        fn=gs7_sust_tipo_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "classe", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="S8",
        rotulo="S8 — Taxa de Sustentação por Ano e Ambiente (%)",
        subtitulo="Taxa de Sustentação Oral por Ano e Ambiente (%)",
        descricao="Percentual de inclusões com sustentação oral em cada ano, comparando "
                  "Plenário Virtual e Plenário Presencial lado a lado.",
        fn=gs8_taxa_ambiente,
        tipos=("barra", "linha"),
        filtros=("classe", "tipo_questao", "periodo"),
    ),
]


def _render_interactive_tabulador(df: pd.DataFrame) -> None:

    dims = dimensoes_disponiveis(df.columns)
    dims_label = list(dims.keys())
    colunas_ok = set(dims.values())
    presets = [p for p in _PREDEFINIDOS_SUST if p[1] in colunas_ok and p[2] in colunas_ok]
    labels_pre = [p[0] for p in presets]

    col_pre, _ = st.columns([2, 1])
    with col_pre:
        pre_escolha = st.selectbox(
            "🔖 Pré-definidos",
            options=["— ou configure manualmente abaixo —"] + labels_pre,
            index=0,
            key="sust_predefinido",
        )

    escolha_dims = pre_escolha if not pre_escolha.startswith("—") else labels_pre[0]
    _, px, pg, pm, pbm = next(p for p in presets if p[0] == escolha_dims)
    def_x  = dims_label.index(next(k for k, v in dims.items() if v == px))
    def_g  = dims_label.index(next(k for k, v in dims.items() if v == pg))
    def_m  = ["inclusoes", "processos"].index(pm)
    def_bm = ["group", "stack", "100%"].index(pbm)

    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    with c1:
        eixo_x_lbl = st.selectbox("Eixo X", dims_label, index=def_x, key="sust_tab_x")
    with c2:
        eixo_y_lbl = st.selectbox("Eixo Y", dims_label, index=def_g, key="sust_tab_y")
    with c3:
        metrica = st.selectbox(
            "Métrica", ["inclusoes", "processos"], index=def_m, key="sust_tab_m",
            format_func=lambda v: "Inclusões em pauta" if v == "inclusoes" else "Processos distintos",
        )
    with c4:
        barmode = st.selectbox(
            "Modo", ["group", "stack", "100%"], index=def_bm, key="sust_tab_bm",
            format_func=lambda v: {"group": "Agrupado", "stack": "Empilhado", "100%": "Empilhado 100%"}[v],
        )
    with c5:
        show_values_tab = st.checkbox("Exibir valores", value=False, key="sust_tab_sv")

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



_CATALOGO.append(GraficoSpec(
    id="S9",
    rotulo="S9 — Tabulador interativo (eixos livres)",
    subtitulo="Tabulador interativo — eixos, agrupamento e métrica livres",
    descricao="Configure o eixo X, a cor/grupo, a métrica e o modo de barras. "
              "A tabela abaixo acompanha os mesmos eixos.",
    fn=None,
    renderer=lambda df, key: _render_interactive_tabulador(df),
))

def render_graficos(df: pd.DataFrame) -> None:
    render_pagina(_CATALOGO, df, key_prefix="sust")
