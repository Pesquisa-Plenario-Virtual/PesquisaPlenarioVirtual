"""Renderização da página de Inclusões em Pauta."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from .plots import (
    g5_anual_ambiente, g6_classe_filtravel, g8_desfecho_filtravel,
    g10_macro_anual_filtravel, g12_concluidos_filtravel,
    g14_nao_concluidos_classe_filtravel, g16_concluidos_classe_filtravel,
    g18_nc_tipo_filtravel, g20_c_tipo_filtravel,
    g22_cat_periodo_filtravel, g24_cat_anual_filtravel,
    g26_cat_tipo_periodo_filtravel, g28_cat_tipo_anual_filtravel,
    g30_nc_cat_anual_filtravel, g32_nc_cat_classe_filtravel,
    g34_nc_cat_tipo_filtravel,
    _refinar_motivos_diversos,
    g_pauta_concluidos,
)
from pages.tramitacao.plots import gt10_tabulador, DIMENSOES

_DIMS_LABEL = list(DIMENSOES.keys())

_PREDEFINIDOS_TAB = [
    ("Ano × Ambiente (inclusões, agrupado)",           "ano",      "ambiente",       "inclusoes", "group"),
    ("Ano × Classe (inclusões, empilhado)",            "ano",      "classe",         "inclusoes", "stack"),
    ("Ano × Tipo de Questão (inclusões, agrupado)",    "ano",      "tipo_questao",   "inclusoes", "group"),
    ("Ambiente × Classe (inclusões, agrupado)",         "ambiente", "classe",         "inclusoes", "group"),
    ("Ambiente × Macro-Desfecho (inclusões, 100%)",    "ambiente", "macro_desfecho", "inclusoes", "100%"),
    ("Classe × Macro-Desfecho (inclusões, agrupado)",   "classe",   "macro_desfecho", "inclusoes", "group"),
    ("Classe × Desfecho Detalhado (inclusões)",         "classe",   "desfecho",       "inclusoes", "group"),
    ("Tipo de Questão × Macro-Desfecho (inclusões)",    "tipo_questao", "macro_desfecho", "inclusoes", "group"),
    ("Tipo de Questão × Desfecho Detalhado (inclusões)","tipo_questao", "desfecho",     "inclusoes", "group"),
]
_LABELS_PRE_TAB = [p[0] for p in _PREDEFINIDOS_TAB]

# ── Catálogo G5–G36 ──────────────────────────────────────────────────────────
_CATALOGO: list[GraficoSpec] = [
    # ── Inclusões em Pauta ────────────────────────────────────────────────────
    GraficoSpec(
        id="G5",
        rotulo="G5 — Inclusões por Ano e Ambiente (Plenário Virtual vs Plenário Presencial)",
        subtitulo="Inclusões em Pauta por Ano e Ambiente",
        descricao="Comparação anual do volume de inclusões em pauta entre o Plenário Virtual e o Plenário Presencial. "
                  "Inclui pizza com a proporção acumulada no período.",
        fn=g5_anual_ambiente,
        tipos=("barra", "linha"),
        filtros=("classe", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="G6/G7",
        rotulo="G6/G7 — Inclusões por Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="Inclusões por Classe",
        descricao="Barras agrupadas por classe (ADI, ADPF, ADC, ADO) com linha do total geral no eixo secundário. "
                  "Selecione o âmbito (Plenário Virtual / Plenário Presencial) e filtre as classes desejadas. "
                  "Inclui pizza com a distribuição por classe no período.",
        fn=g6_classe_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "tipo_questao", "periodo"),
        kwargs_fixos={"pizza_textinfo": "percent+value"},
    ),
    GraficoSpec(
        id="G8/G9",
        rotulo="G8/G9 — Desfecho Geral (Plenário Virtual e Plenário Presencial)",
        subtitulo="Desfecho Geral",
        descricao="Pizza com a proporção de concluídos e não concluídos, mais desfecho detalhado (PV) "
                  "ou apenas macro (Plenário Presencial). Selecione o âmbito.",
        fn=g8_desfecho_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao"),
        kwargs_fixos={"pizza_textinfo": "percent+value"},
    ),
    GraficoSpec(
        id="G10/G11",
        rotulo="G10/G11 — Macro-Desfecho Anual (Plenário Virtual e Plenário Presencial)",
        subtitulo="Macro-Desfecho Anual",
        descricao="Evolução anual do volume de inclusões concluídas e não concluídas. Selecione o âmbito.",
        fn=g10_macro_anual_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="G12/G13",
        rotulo="G12/G13 — Concluídos por Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Inclusões Concluídas por Ano",
        descricao="Fluxo anual de inclusões com desfecho concluído. Selecione o âmbito.",
        fn=g12_concluidos_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="G12/G13-seg",
        rotulo="G12/G13 — Concluídos por Ano, segmentado por desfecho (Plenário Virtual e Plenário Presencial)",
        subtitulo="Inclusões Concluídas por Ano, por Tipo de Desfecho",
        descricao="Fluxo anual de inclusões concluídas, segmentado por unânime, maioria com o relator "
                  "ou maioria vencido o relator. Selecione o âmbito.",
        fn=g12_concluidos_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
        kwargs_fixos={"segmentar": True},
    ),
    GraficoSpec(
        id="G14/G15",
        rotulo="G14/G15 — Não Concluídos por Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="Não Concluídos por Classe",
        descricao="Barras por classe com linha do total de não concluídos. Selecione o âmbito.",
        fn=g14_nao_concluidos_classe_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="G16/G17",
        rotulo="G16/G17 — Concluídos por Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="Concluídos por Classe",
        descricao="Barras por classe com linha do total de concluídos. Selecione o âmbito.",
        fn=g16_concluidos_classe_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "tipo_questao", "periodo"),
        percentual=True,
    ),
    # ── Tipo de Questão ───────────────────────────────────────────────────────
    GraficoSpec(
        id="G18/G19",
        rotulo="G18/G19 — Não Concluídos por Tipo de Questão (Plenário Virtual e Plenário Presencial)",
        subtitulo="Não Concluídos por Tipo de Questão",
        descricao="Barras por tipo de questão (PR / RC / QI) com linha do total de não concluídos. "
                  "IJ renomeado para QI na exibição. Selecione o âmbito.",
        fn=g18_nc_tipo_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="G20/G21",
        rotulo="G20/G21 — Concluídos por Tipo de Questão (Plenário Virtual e Plenário Presencial)",
        subtitulo="Concluídos por Tipo de Questão",
        descricao="Barras por tipo de questão (PR / RC / QI) com linha do total de concluídos. Selecione o âmbito.",
        fn=g20_c_tipo_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "periodo"),
        percentual=True,
    ),
    # ── Desfecho Concluído por Categoria ─────────────────────────────────────
    GraficoSpec(
        id="G22/G23",
        rotulo="G22/G23 — Categoria de Desfecho (Plenário Virtual e Plenário Presencial)",
        subtitulo="Categoria de Desfecho",
        descricao="Pizza com as 4 categorias: Unânime, Maioria (relator vencedor), Maioria (relator vencido) "
                  "e Não concluído (bloco agregado). Selecione o âmbito.",
        fn=g22_cat_periodo_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao"),
    ),
    GraficoSpec(
        id="G24/G25",
        rotulo="G24/G25 — Categoria de Desfecho por Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Categoria de Desfecho por Ano",
        descricao="Evolução anual das 4 categorias de desfecho. Selecione o âmbito.",
        fn=g24_cat_anual_filtravel,
        tipos=("barra", "barra_h", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="G26/G27",
        rotulo="G26/G27 — Categoria × Tipo de Questão (Plenário Virtual e Plenário Presencial)",
        subtitulo="Categoria de Desfecho por Tipo de Questão",
        descricao="Uma pizza por tipo de questão (PR/RC/QI) com as 4 categorias de desfecho. Período total. "
                  "Processos sem tipo de questão classificados como PR. Selecione o âmbito.",
        fn=g26_cat_tipo_periodo_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao"),
    ),
    GraficoSpec(
        id="G28/G29",
        rotulo="G28/G29 — Categoria × Tipo de Questão por Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Categoria de Desfecho por Tipo de Questão e Ano",
        descricao="Um gráfico por tipo de questão (PR, RC, QI) mostrando a evolução anual das categorias. "
                  "Selecione o âmbito e o tipo na aba.",
        fn=g28_cat_tipo_anual_filtravel,
        tipos=("barra", "barra_h", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    # ── Desfecho Não Concluído por Categoria ──────────────────────────────────
    GraficoSpec(
        id="G30/G31",
        rotulo="G30/G31 — Não Concluídos por Categoria e Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Não Concluídos por Categoria e Ano",
        descricao="Evolução anual das 4 categorias de não conclusão: Pedido de vista, Destaque, "
                  "Retirado de pauta e Motivos diversos. Selecione o âmbito.",
        fn=g30_nc_cat_anual_filtravel,
        tipos=("barra", "barra_h", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="G32/G33",
        rotulo="G32/G33 — Não Concluídos por Categoria e Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="Não Concluídos por Categoria e Classe",
        descricao="Um gráfico por classe (ADI, ADPF, ADC, ADO) com as categorias de não conclusão. "
                  "Selecione o âmbito e a classe na aba.",
        fn=g32_nc_cat_classe_filtravel,
        tipos=("barra", "barra_h"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="G34/G35",
        rotulo="G34/G35 — Não Concluídos por Categoria e Tipo (Plenário Virtual e Plenário Presencial)",
        subtitulo="Não Concluídos por Categoria e Tipo de Questão",
        descricao="Um gráfico por tipo de questão (PR, RC, QI) com as categorias de não conclusão. "
                  "Selecione o âmbito e o tipo na aba.",
        fn=g34_nc_cat_tipo_filtravel,
        tipos=("barra", "barra_h"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    # ── Pauta vs Concluídos ──────────────────────────────────────────────────
    GraficoSpec(
        id="G_PV",
        rotulo="G_PV — Pauta vs Julgamentos Concluídos (PV, período total)",
        subtitulo="PV: Pauta vs Julgamentos Concluídos",
        descricao="Duas barras do PV no período: participação na pauta (63,9%) e participação nos "
                  "julgamentos concluídos (91,3%). Contraste que mostra a concentração do PV nas conclusões.",
        fn=g_pauta_concluidos,
        tipos=("barra",),
        filtros=(),
    ),
]


def _render_interactive_tabulador(df: pd.DataFrame) -> None:
    st.subheader("Tabulador Gráfico Interativo")
    st.caption("Configure livremente os eixos, agrupamento e modo de barras.")

    col_pre, _ = st.columns([2, 1])
    with col_pre:
        pre_escolha = st.selectbox(
            "🔖 Pré-definidos",
            options=["— ou configure manualmente abaixo —"] + _LABELS_PRE_TAB,
            index=0,
            key="inc_tab_predef",
        )

    # Sem pré-definido escolhido, cai no primeiro item de _PREDEFINIDOS_TAB
    # (Ano × Ambiente) em vez de índice 0 fixo: DIMENSOES é compartilhado com a
    # página de Tramitação e seu índice 0 ("tramitacao") não existe nesta base.
    escolha_dims = pre_escolha if not pre_escolha.startswith("—") else _LABELS_PRE_TAB[0]
    _, px, pg, pm, pbm = next(p for p in _PREDEFINIDOS_TAB if p[0] == escolha_dims)
    def_x  = _DIMS_LABEL.index(next(k for k, v in DIMENSOES.items() if v == px))
    def_g  = _DIMS_LABEL.index(next(k for k, v in DIMENSOES.items() if v == pg))
    def_m  = ["inclusoes", "processos"].index(pm)
    def_bm = ["group", "stack", "100%"].index(pbm)

    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    with c1:
        eixo_x_lbl = st.selectbox("Eixo X", _DIMS_LABEL, index=def_x, key="inc_tab_x")
    with c2:
        eixo_y_lbl = st.selectbox("Eixo Y (cor/grupo)", _DIMS_LABEL, index=def_g, key="inc_tab_y")
    with c3:
        metrica = st.selectbox(
            "Métrica", ["inclusoes", "processos"], index=def_m, key="inc_tab_m",
            format_func=lambda v: "Inclusões em pauta" if v == "inclusoes" else "Processos distintos",
        )
    with c4:
        barmode = st.selectbox(
            "Modo", ["group", "stack", "100%"], index=def_bm, key="inc_tab_bm",
            format_func=lambda v: {"group": "Agrupado", "stack": "Empilhado", "100%": "Empilhado 100%"}[v],
        )
    with c5:
        show_values_tab = st.checkbox("Exibir valores", value=False, key="inc_tab_sv")

    eixo_x = DIMENSOES[eixo_x_lbl]
    eixo_y = DIMENSOES[eixo_y_lbl]

    if eixo_x == eixo_y:
        st.warning("Eixo X e Eixo Y não podem ser a mesma dimensão.")
        return

    fig = gt10_tabulador(df, eixo_x, eixo_y, metrica, barmode, show_values_tab)
    st.plotly_chart(fig, width="stretch")

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


def render_graficos(df: pd.DataFrame, df_dec: pd.DataFrame | None = None) -> None:
    df = _refinar_motivos_diversos(df, df_dec if df_dec is not None else pd.DataFrame())

    render_pagina(_CATALOGO, df, key_prefix="inc")

    st.markdown("---")
    with st.expander("🔧 Tabulador Interativo — eixos livres (G36)"):
        _render_interactive_tabulador(df)
