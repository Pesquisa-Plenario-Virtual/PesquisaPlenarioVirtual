"""Renderização da página de Sessões Virtuais."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from .plots import (
    g0_sessoes_vs_inclusoes,
    g3_1_distribuicao_sessoes, g3_2_faixa_sessoes_classe,
    g3_3_taxa_conclusao_primeira, g3_4_taxa_conclusao_posicao,
    g4_2_sessoes_classe_tipo, g4_3_macro_ano_tipo,
    g4_4_macro_ano_classe, g4_5_taxa_conclusao_classe_tipo,
    g5_1_distribuicao_duracao, g5_2_duracao_mediana_classe,
    g5_3_duracao_mediana_tipo,
    prep_duracao,
)
from pages.tramitacao.plots import gt10_tabulador

_DIMS_SV = {
    "Classe":           "classe",
    "Tipo de questão":  "tipo_questao",
    "Macro-desfecho":   "macro_desfecho",
    "Desfecho detalhado": "desfecho",
    "Ano":              "ano",
    "Relator":          "relator",
}

_PREDEFINIDOS = [
    ("Ano × Classe (sessões, agrupado)",              "ano",      "classe",         "sessoes", "group"),
    ("Ano × Tipo (sessões, agrupado)",                "ano",      "tipo_questao",   "sessoes", "group"),
    ("Ano × Macro-desfecho (sessões, empilhado)",     "ano",      "macro_desfecho", "sessoes", "stack"),
    ("Classe × Tipo (sessões, agrupado)",             "classe",   "tipo_questao",   "sessoes", "group"),
    ("Classe × Macro-desfecho (sessões, 100%)",       "classe",   "macro_desfecho", "sessoes", "100%"),
    ("Classe × Desfecho (sessões, agrupado)",         "classe",   "desfecho",       "sessoes", "group"),
    ("Relator × Classe (sessões, agrupado)",          "relator",  "classe",         "sessoes", "group"),
    ("Relator × Macro-desfecho (sessões, agrupado)",  "relator",  "macro_desfecho", "sessoes", "group"),
]


def _dims_disponiveis(colunas) -> dict[str, str]:
    """Subconjunto de _DIMS_SV cujas colunas existem em `colunas`.

    Mesmo raciocínio de dados.filters.dimensoes_disponiveis, mas aplicado a
    _DIMS_SV — o dicionário de dimensões desta página, não ao DIMENSOES
    compartilhado com Tramitação/Inclusões/Reajuste/Sustentação (que tem
    colunas, como "tramitacao", que sessoes_virtuais.parquet não tem).
    """
    disponiveis = set(colunas)
    return {label: col for label, col in _DIMS_SV.items() if col in disponiveis}


def _montar_catalogo(df_final: pd.DataFrame) -> list[GraficoSpec]:
    """Monta o catálogo com `df_final` (inclusões em pauta) capturado por closure.

    A casca chama spec.fn(df, **kwargs) com um único dataframe (df_s). G0 e o
    Bloco 5 (G5.1-G5.3) precisam também de df_final — G0 para comparar sessões
    com inclusões, o Bloco 5 para prep_duracao calcular a data da primeira
    pauta. Os wrappers do Bloco 5 declaram `ambiente` na assinatura para a
    casca oferecer o seletor de âmbito (ver GraficoSpec.filtros abaixo).
    """

    def _g0(df_s, show_values=True, **kw):
        return g0_sessoes_vs_inclusoes(df_s, df_final, show_values=show_values)

    def _g5_1(df_s, show_values=True, ambiente="Plenário Virtual", **kw):
        return g5_1_distribuicao_duracao(prep_duracao(df_s, df_final, ambiente), show_values)

    def _g5_2(df_s, show_values=True, ambiente="Plenário Virtual", **kw):
        return g5_2_duracao_mediana_classe(prep_duracao(df_s, df_final, ambiente), show_values)

    def _g5_3(df_s, show_values=True, ambiente="Plenário Virtual", **kw):
        return g5_3_duracao_mediana_tipo(prep_duracao(df_s, df_final, ambiente), show_values)

    return [
        GraficoSpec(
            id="G0",
            rotulo="G0 — Sessões virtuais vs Inclusões em pauta (PV)",
            subtitulo="Sessões Virtuais vs Inclusões em Pauta (PV)",
            descricao="Comparação anual entre o volume de sessões virtuais iniciadas e o total de "
                      "inclusões em pauta no Plenário Virtual.",
            fn=_g0,
            tipos=("barra", "linha"),
        ),
        GraficoSpec(
            id="G3.1",
            rotulo="G3.1 — Distribuição de sessões por processo",
            subtitulo="Distribuição de Sessões por Processo",
            descricao="Quantos processos tiveram 1, 2–3, 4–5 ou 6+ sessões virtuais.",
            fn=g3_1_distribuicao_sessoes,
            tipos=("barra", "linha"),
            filtros=("classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G3.2",
            rotulo="G3.2 — Faixa de sessões por classe",
            subtitulo="Número de Sessões por Processo e Classe",
            descricao="Distribuição das faixas de sessões por classe processual.",
            fn=g3_2_faixa_sessoes_classe,
            tipos=("barra",),
            filtros=("tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G3.3",
            rotulo="G3.3 — Taxa de conclusão: 1ª vs posteriores",
            subtitulo="Taxa de Conclusão: 1ª Sessão vs Sessões Posteriores",
            descricao="Comparação da taxa de conclusão entre a primeira sessão e as sessões seguintes.",
            fn=g3_3_taxa_conclusao_primeira,
            tipos=("barra",),
            filtros=("classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G3.4",
            rotulo="G3.4 — Taxa de conclusão por posição da sessão",
            subtitulo="Taxa de Conclusão por Posição da Sessão",
            descricao="Taxa de conclusão para a 1ª, 2ª, 3ª e 4ª+ sessão no histórico do processo.",
            fn=g3_4_taxa_conclusao_posicao,
            tipos=("barra", "linha"),
            filtros=("classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G4.1",
            rotulo="G4.1 — Classe × Tipo de Questão (quadro de referência)",
            subtitulo="Classe × Tipo de Questão",
            descricao="Barras agrupadas por tipo de questão (PR/RC/QI) com o volume de sessões por "
                      "classe — mesma leitura do G4.2, útil como quadro de referência com totais na tabela.",
            fn=g4_2_sessoes_classe_tipo,
            tipos=("barra",),
            filtros=("periodo",),
        ),
        GraficoSpec(
            id="G4.2",
            rotulo="G4.2 — Sessões por classe e tipo de questão",
            subtitulo="Sessões por Classe e Tipo de Questão",
            descricao="Barras agrupadas por tipo de questão (PR/RC/QI) com o volume de sessões por classe.",
            fn=g4_2_sessoes_classe_tipo,
            tipos=("barra",),
            filtros=("periodo",),
        ),
        GraficoSpec(
            id="G4.3",
            rotulo="G4.3 — Macro-desfecho por ano e tipo de questão",
            subtitulo="Macro-Desfecho por Ano e Tipo de Questão",
            descricao="Barras empilhadas (Concluído/Não concluído) por ano. "
                      "Uma aba por tipo: PR, RC e QI.",
            fn=g4_3_macro_ano_tipo,
            tipos=("barra", "linha"),
            filtros=("classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G4.4",
            rotulo="G4.4 — Macro-desfecho por ano e classe",
            subtitulo="Macro-Desfecho por Ano e Classe (ADI e ADPF)",
            descricao="Barras empilhadas por ano para ADI e ADPF. ADC e ADO omitidos por base pequena.",
            fn=g4_4_macro_ano_classe,
            tipos=("barra", "linha"),
            filtros=("classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G4.5",
            rotulo="G4.5 — Taxa de conclusão: classe × tipo de questão",
            subtitulo="Taxa de Conclusão por Classe e Tipo de Questão",
            descricao="Percentual de sessões concluídas, agrupado por classe e tipo de questão.",
            fn=g4_5_taxa_conclusao_classe_tipo,
            tipos=("barra",),
            filtros=("periodo",),
        ),
        GraficoSpec(
            id="G5.1",
            rotulo="G5.1 — Distribuição de duração até conclusão",
            subtitulo="Tempo até Conclusão",
            descricao="Distribuição do tempo decorrido entre a primeira inclusão em pauta e a sessão de "
                      "conclusão, em faixas. Selecione o âmbito da primeira pauta.",
            fn=_g5_1,
            tipos=("barra", "linha"),
            filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G5.2",
            rotulo="G5.2 — Duração mediana por classe",
            subtitulo="Tempo Mediano até Conclusão por Classe (dias)",
            descricao="Mediana de dias entre a primeira pauta e a conclusão, por classe. "
                      "Selecione o âmbito da primeira pauta.",
            fn=_g5_2,
            tipos=("barra",),
            filtros=("ambiente", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G5.3",
            rotulo="G5.3 — Duração mediana por tipo de questão",
            subtitulo="Tempo Mediano até Conclusão por Tipo de Questão (dias)",
            descricao="Mediana de dias entre a primeira pauta e a conclusão, por tipo. "
                      "Selecione o âmbito da primeira pauta.",
            fn=_g5_3,
            tipos=("barra",),
            filtros=("ambiente", "classe", "periodo"),
        ),
    ]


# ── Tabulador interativo ──────────────────────────────────────────────────────

def _render_interactive_tabulador(df_s: pd.DataFrame) -> None:
    st.subheader("Tabulador Interativo")
    st.caption("Configure livremente os eixos, agrupamento e modo de barras.")

    dims = _dims_disponiveis(df_s.columns)
    dims_label = list(dims.keys())
    colunas_ok = set(dims.values())
    presets = [p for p in _PREDEFINIDOS if p[1] in colunas_ok and p[2] in colunas_ok]
    labels_pre = [p[0] for p in presets]

    col_pre, _ = st.columns([2, 1])
    with col_pre:
        pre_escolha = st.selectbox(
            "🔖 Pré-definidos",
            options=["— ou configure manualmente abaixo —"] + labels_pre,
            index=0,
            key="sv_predefinido",
        )

    if pre_escolha.startswith("—"):
        def_x, def_g, def_m, def_bm = 0, 1, 0, 0
    else:
        _, px, pg, pm, pbm = next(p for p in presets if p[0] == pre_escolha)
        def_x  = dims_label.index(next(k for k, v in dims.items() if v == px))
        def_g  = dims_label.index(next(k for k, v in dims.items() if v == pg))
        def_m  = ["sessoes", "processos"].index(pm)
        def_bm = ["group", "stack", "100%"].index(pbm)

    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    with c1:
        eixo_x_lbl = st.selectbox("Eixo X",    dims_label, index=def_x, key="sv_tab_x")
    with c2:
        grupo_lbl  = st.selectbox("Cor/Grupo", dims_label, index=def_g, key="sv_tab_g")
    with c3:
        metrica = st.selectbox(
            "Métrica", ["sessoes", "processos"], index=def_m, key="sv_tab_m",
            format_func=lambda v: "Sessões" if v == "sessoes" else "Processos distintos",
        )
    with c4:
        barmode = st.selectbox(
            "Modo", ["group", "stack", "100%"], index=def_bm, key="sv_tab_bm",
            format_func=lambda v: {"group": "Agrupado", "stack": "Empilhado", "100%": "Empilhado 100%"}[v],
        )
    with c5:
        show_values = st.checkbox("Exibir valores", value=False, key="sv_tab_sv")

    eixo_x = dims[eixo_x_lbl]
    grupo  = dims[grupo_lbl]

    if eixo_x == grupo:
        st.warning("Eixo X e Cor/Grupo não podem ser a mesma dimensão.")
        return

    gt_metrica = "processos" if metrica == "processos" else "inclusoes"
    fig = gt10_tabulador(df_s, eixo_x, grupo, gt_metrica, barmode, show_values)
    if metrica == "sessoes":
        fig.update_yaxes(title_text="Nº de sessões")
    st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    st.subheader("Tabela — mesmos eixos")
    d = df_s.copy()
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


# ── Renderização principal ────────────────────────────────────────────────────

def render_graficos(df_s: pd.DataFrame, df_final: pd.DataFrame) -> None:
    render_pagina(_montar_catalogo(df_final), df_s, key_prefix="sv")

    st.markdown("---")
    with st.expander("🔧 Tabulador Interativo — eixos livres (G6)"):
        _render_interactive_tabulador(df_s)
