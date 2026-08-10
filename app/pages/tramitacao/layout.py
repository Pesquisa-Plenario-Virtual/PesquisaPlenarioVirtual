"""Renderização da página de Tramitação por Ambiente."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from .plots import (
    gt1_tramitacao,
    gt2_tram_por_classe,
    gt3_tram_por_tipo,
    gt4_ambos_por_tipo,
    gt5_macro_por_tram,
    gt6_desfecho_por_tram,
    gt7_classe_por_tram,
    gt8_tipo_por_tram,
    gt9_taxa_conclusao,
    gt10_tabulador,
    gt11_proc_ano_ambiente,
    gt12_proc_tramitacao_primeiro_ano,
    gt13_tramitacao_periodo,
    DIMENSOES,
)

# ── Catálogo T1–T9, T11–T13 (T10 é o tabulador livre, fora do catálogo) ────────
_CATALOGO = [
    GraficoSpec(
        id="T1",
        rotulo="T1 — Tramitação por ambiente (geral)",
        subtitulo="Tramitação por Ambiente — Processos CC (2016–2025)",
        descricao="Distribuição dos processos distintos por ambiente: "
                  "só PV, só PP ou ambos.",
        fn=gt1_tramitacao,
        tipos=("barra",),
        filtros=("classe", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="T2",
        rotulo="T2 — Tramitação por ambiente e classe",
        subtitulo="Tramitação por Ambiente e Classe — Processos CC (2016–2025)",
        descricao="Barras agrupadas por ambiente de tramitação (só PV / só PP / ambos) "
                  "para cada classe processual (ADI, ADPF, ADC, ADO).",
        fn=gt2_tram_por_classe,
        tipos=("barra",),
        filtros=("tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="T3",
        rotulo="T3 — Tramitação por ambiente e tipo de questão",
        subtitulo="Tramitação por Ambiente e Tipo de Questão — Processos CC (2016–2025)",
        descricao="Barras agrupadas por ambiente de tramitação para cada tipo de questão "
                  "(PR / RC / QI). IJ renomeado para QI.",
        fn=gt3_tram_por_tipo,
        tipos=("barra",),
        filtros=("classe", "periodo"),
    ),
    GraficoSpec(
        id="T4",
        rotulo="T4 — Processos em ambos os ambientes por tipo de questão",
        subtitulo="Processos em Ambos os Ambientes por Tipo de Questão (2016–2025)",
        descricao="Recorte dos processos que tramitaram em ambos os ambientes, "
                  "distribuídos por tipo de questão (PR / RC / QI).",
        fn=gt4_ambos_por_tipo,
        tipos=("barra",),
        filtros=("classe", "periodo"),
    ),
    GraficoSpec(
        id="T5",
        rotulo="T5 — Macro-desfecho por ambiente de tramitação",
        subtitulo="Macro-Desfecho por Ambiente de Tramitação — Inclusões (2016–2025)",
        descricao="Volume de inclusões concluídas e não concluídas em cada "
                  "grupo de tramitação (só PV / só PP / ambos).",
        fn=gt5_macro_por_tram,
        tipos=("barra",),
        filtros=("classe", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="T6",
        rotulo="T6 — Desfecho detalhado por ambiente de tramitação",
        subtitulo="Desfecho detalhado por ambiente de tramitação — Inclusões (2016–2025)",
        descricao="Os sete desfechos detalhados (unânime, maioria, pedido de vista "
                  "e os demais) em cada grupo de tramitação.",
        fn=gt6_desfecho_por_tram,
        tipos=("barra", "barra_h", "linha"),
        filtros=("classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="T7",
        rotulo="T7 — Distribuição por classe dentro de cada ambiente",
        subtitulo="Distribuição por Classe — por Ambiente de Tramitação (2016–2025)",
        descricao="Barras 100% empilhadas mostrando a composição por classe processual "
                  "dentro de cada ambiente (só PV / só PP / ambos).",
        fn=gt7_classe_por_tram,
        tipos=("barra",),
        filtros=("tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="T8",
        rotulo="T8 — Distribuição por tipo de questão dentro de cada ambiente",
        subtitulo="Distribuição por Tipo de Questão — por Ambiente de Tramitação (2016–2025)",
        descricao="Barras 100% empilhadas mostrando a composição por tipo de questão "
                  "dentro de cada ambiente (só PV / só PP / ambos).",
        fn=gt8_tipo_por_tram,
        tipos=("barra",),
        filtros=("classe", "periodo"),
    ),
    GraficoSpec(
        id="T9",
        rotulo="T9 — Taxa de conclusão por ambiente e classe (%)",
        subtitulo="Taxa de Conclusão (%) por Ambiente de Tramitação e Classe (2016–2025)",
        descricao="Percentual de inclusões concluídas para cada combinação de ambiente de "
                  "tramitação e classe processual.",
        fn=gt9_taxa_conclusao,
        tipos=("barra",),
        filtros=("tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="T11",
        rotulo="T11 — Processos por ano e ambiente",
        subtitulo="Processos distintos por ano e ambiente (2016–2025)",
        descricao="Cada processo aparece uma vez por ano-ambiente onde foi pautado. "
                  "Barra por ambiente com total geral no eixo secundário.",
        fn=gt11_proc_ano_ambiente,
        tipos=("barra", "linha"),
        filtros=("classe", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="T12",
        rotulo="T12 — Processos por tipo de tramitação",
        subtitulo="Processos por tipo de tramitação, por ano sem repetição (2016–2025)",
        descricao="Cada processo conta uma única vez: ano da primeira inclusão, "
                  "categoria conforme todo o histórico (Virtual / Físico / Ambos).",
        fn=gt12_proc_tramitacao_primeiro_ano,
        tipos=("barra", "linha"),
        filtros=("classe", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="T13",
        rotulo="T13 — Processos por tipo de tramitação (período total)",
        subtitulo="Processos por tipo de tramitação — 2016–2025",
        descricao="Cada processo aparece uma única vez, classificado pelo(s) ambiente(s) "
                  "em que tramitou ao longo de todo o período.",
        fn=gt13_tramitacao_periodo,
        tipos=("barra",),
        filtros=("classe", "tipo_questao"),
    ),
]

_PREDEFINIDOS = [
    ("Ambiente × Classe (inclusões, agrupado)",          "tramitacao",   "classe",         "inclusoes", "group"),
    ("Ambiente × Macro-Desfecho (inclusões, agrupado)",  "tramitacao",   "macro_desfecho", "inclusoes", "group"),
    ("Ambiente × Tipo de Questão (processos, agrupado)", "tramitacao",   "tipo_questao",   "processos", "group"),
    ("Classe × Ambiente (inclusões, empilhado 100%)",    "classe",       "tramitacao",     "inclusoes", "100%"),
    ("Classe × Macro-Desfecho (inclusões, empilhado)",   "classe",       "macro_desfecho", "inclusoes", "stack"),
    ("Ano × Ambiente (inclusões, empilhado)",            "ano",          "tramitacao",     "inclusoes", "stack"),
    ("Ano × Macro-Desfecho (inclusões, empilhado 100%)", "ano",          "macro_desfecho", "inclusoes", "100%"),
    ("Tipo de Questão × Desfecho (inclusões, agrupado)", "tipo_questao", "macro_desfecho", "inclusoes", "group"),
]
_LABELS_PRE = [p[0] for p in _PREDEFINIDOS]
_DIMS_LABEL = list(DIMENSOES.keys())


def _render_tabulador(df: pd.DataFrame, key_suffix: str) -> None:
    col_pre, _ = st.columns([2, 1])
    with col_pre:
        pre_escolha = st.selectbox(
            "🔖 Pré-definidos",
            options=["— ou configure manualmente abaixo —"] + _LABELS_PRE,
            index=0,
            key=f"tab_predefinido_{key_suffix}",
        )

    if pre_escolha.startswith("—"):
        def_x, def_g, def_m, def_bm = 0, 1, 0, 0
    else:
        _, px, pg, pm, pbm = next(p for p in _PREDEFINIDOS if p[0] == pre_escolha)
        def_x  = _DIMS_LABEL.index(next(k for k, v in DIMENSOES.items() if v == px))
        def_g  = _DIMS_LABEL.index(next(k for k, v in DIMENSOES.items() if v == pg))
        def_m  = ["inclusoes", "processos"].index(pm)
        def_bm = ["group", "stack", "100%"].index(pbm)

    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    with c1:
        eixo_x_lbl = st.selectbox("Eixo X",    _DIMS_LABEL, index=def_x, key=f"tab_x_{key_suffix}")
    with c2:
        grupo_lbl  = st.selectbox("Cor/Grupo", _DIMS_LABEL, index=def_g, key=f"tab_g_{key_suffix}")
    with c3:
        metrica = st.selectbox(
            "Métrica", ["inclusoes", "processos"], index=def_m, key=f"tab_m_{key_suffix}",
            format_func=lambda v: "Inclusões em pauta" if v == "inclusoes" else "Processos distintos",
        )
    with c4:
        barmode = st.selectbox(
            "Modo", ["group", "stack", "100%"], index=def_bm, key=f"tab_bm_{key_suffix}",
            format_func=lambda v: {"group": "Agrupado", "stack": "Empilhado", "100%": "Empilhado 100%"}[v],
        )
    with c5:
        show_values = st.checkbox("Exibir valores", value=False, key=f"tab_sv_{key_suffix}")

    eixo_x = DIMENSOES[eixo_x_lbl]
    grupo  = DIMENSOES[grupo_lbl]

    if eixo_x == grupo:
        st.warning("Eixo X e Cor/Grupo não podem ser a mesma dimensão.")
        return

    st.plotly_chart(gt10_tabulador(df, eixo_x, grupo, metrica, barmode, show_values), width="stretch")

    st.markdown("---")
    st.subheader("Tabela — mesmos eixos")
    d = df.copy()
    d["tipo_questao"] = d["tipo_questao"].replace({"IJ": "QI"})
    if metrica == "processos":
        d = d.drop_duplicates("incidente")
    tab = d.groupby([eixo_x, grupo], observed=True).size().reset_index(name="n")
    if barmode == "100%":
        totais = tab.groupby(eixo_x)["n"].transform("sum")
        tab["n"] = (tab["n"] / totais * 100).round(1)
    pvt = tab.pivot_table(index=eixo_x, columns=grupo, values="n", fill_value=0)
    pvt["Total"] = pvt.sum(axis=1)
    pvt.loc["Total"] = pvt.sum()
    pvt = pvt.reset_index()
    pvt[pvt.columns[0]] = pvt[pvt.columns[0]].astype(str)
    fmt = {c: "{:,.0f}" for c in pvt.columns if pvt[c].dtype.kind in "iuf"}
    st.dataframe(pvt.style.format(fmt, na_rep="—"), width="stretch", height=280)


_CATALOGO.append(GraficoSpec(
    id="T10",
    rotulo="T10 — Tabulador interativo (eixos livres)",
    subtitulo="Tabulador interativo — eixos, agrupamento e métrica livres",
    descricao="Configure o eixo X, a cor/grupo, a métrica e o modo de barras. "
              "A tabela abaixo acompanha os mesmos eixos.",
    fn=None,
    renderer=lambda df, key: _render_tabulador(df, key_suffix=key),
))


def render_graficos(df: pd.DataFrame) -> None:
    render_pagina(_CATALOGO, df, key_prefix="tram")
