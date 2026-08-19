"""Renderização da página de Tramitação por Ambiente."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from components.tabulador import render_tabulador
from dados.filters import dimensoes_disponiveis
from pages.bloco2_inclusoes.plots import (
    fig_2i_tramitacao_anual_2016, fig_31_tramitacao_2016,
    fig_31_tramitacao_alt, fig_32_tramitacao_alt,
)
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

# ── Catálogo T1–T17 (T17 é o tabulador livre, fora do catálogo) ────────────────
_CATALOGO = [
    GraficoSpec(
        id="T1",
        rotulo="T1 — Tramitação por ambiente (geral)",
        subtitulo="Quase 60% dos processos tramitam só no virtual (2.168 de 3.644) (2020–2025)",
        descricao="Distribuição dos processos distintos por ambiente: "
                  "só PV, só PP ou ambos.",
        fn=gt1_tramitacao,
        tipos=("barra",),
        filtros=("classe", "tipo_questao", "periodo"),
        periodo_padrao=(2020, 2025),
    ),
    GraficoSpec(
        id="T2",
        rotulo="T2 — Tramitação por ambiente e classe",
        subtitulo="ADI domina a tramitação em todos os ambientes (2020–2025)",
        descricao="Barras agrupadas por ambiente de tramitação (só PV / só PP / ambos) "
                  "para cada classe processual (ADI, ADPF, ADC, ADO).",
        fn=gt2_tram_por_classe,
        tipos=("barra",),
        filtros=("tipo_questao", "periodo"),
        periodo_padrao=(2020, 2025),
    ),
    GraficoSpec(
        id="T3",
        rotulo="T3 — Tramitação por ambiente e tipo de questão",
        subtitulo="PR domina a tramitação em todos os ambientes (2020–2025)",
        descricao="Barras agrupadas por ambiente de tramitação para cada tipo de questão "
                  "(PR / RC / QI). IJ renomeado para QI.",
        fn=gt3_tram_por_tipo,
        tipos=("barra",),
        filtros=("classe", "periodo"),
        periodo_padrao=(2020, 2025),
    ),
    GraficoSpec(
        id="T4",
        rotulo="T4 — Processos em ambos os ambientes por tipo de questão",
        subtitulo="PR também domina os processos que passaram pelos dois ambientes (2020–2025)",
        descricao="Recorte dos processos que tramitaram em ambos os ambientes, "
                  "distribuídos por tipo de questão (PR / RC / QI).",
        fn=gt4_ambos_por_tipo,
        tipos=("barra",),
        filtros=("classe", "periodo"),
        periodo_padrao=(2020, 2025),
    ),
    GraficoSpec(
        id="T5",
        rotulo="T5 — Macro-desfecho por ambiente de tramitação",
        subtitulo="Não conclusão domina os grupos presencial e misto; no virtual, concluídos levam (2020–2025)",
        descricao="Volume de inclusões concluídas e não concluídas em cada "
                  "grupo de tramitação (só PV / só PP / ambos).",
        fn=gt5_macro_por_tram,
        tipos=("barra",),
        filtros=("classe", "tipo_questao", "periodo"),
        periodo_padrao=(2020, 2025),
    ),
    GraficoSpec(
        id="T6",
        rotulo="T6 — Desfecho detalhado por ambiente de tramitação",
        subtitulo="Virtual conclui em unanimidade; presencial acumula 'motivos diversos' (2020–2025)",
        descricao="Os sete desfechos detalhados (unânime, maioria, pedido de vista "
                  "e os demais) em cada grupo de tramitação.",
        fn=gt6_desfecho_por_tram,
        tipos=("barra", "barra_h", "linha"),
        filtros=("classe", "tipo_questao", "periodo"),
        periodo_padrao=(2020, 2025),
        percentual=True,
    ),
    GraficoSpec(
        id="T7",
        rotulo="T7 — Distribuição por classe dentro de cada ambiente",
        subtitulo="ADI é a maioria esmagadora em qualquer ambiente de tramitação (2020–2025)",
        descricao="Barras 100% empilhadas mostrando a composição por classe processual "
                  "dentro de cada ambiente (só PV / só PP / ambos).",
        fn=gt7_classe_por_tram,
        tipos=("barra",),
        filtros=("tipo_questao", "periodo"),
        periodo_padrao=(2020, 2025),
    ),
    GraficoSpec(
        id="T8",
        rotulo="T8 — Distribuição por tipo de questão dentro de cada ambiente",
        subtitulo="QI pesa só no presencial (60%); virtual e misto são quase só PR (2020–2025)",
        descricao="Barras 100% empilhadas mostrando a composição por tipo de questão "
                  "dentro de cada ambiente (só PV / só PP / ambos).",
        fn=gt8_tipo_por_tram,
        tipos=("barra",),
        filtros=("classe", "periodo"),
        periodo_padrao=(2020, 2025),
    ),
    GraficoSpec(
        id="T9",
        rotulo="T9 — Taxa de conclusão por ambiente e classe (%)",
        subtitulo="Virtual conclui muito mais que o presencial em toda classe (2020–2025)",
        descricao="Percentual de inclusões concluídas para cada combinação de ambiente de "
                  "tramitação e classe processual.",
        fn=gt9_taxa_conclusao,
        tipos=("barra",),
        filtros=("tipo_questao", "periodo"),
        periodo_padrao=(2020, 2025),
    ),
    GraficoSpec(
        id="T10",
        rotulo="T10 — Processos por ano e ambiente",
        subtitulo="Presencial encolhe enquanto o virtual dispara a partir de 2019 (2020–2025)",
        descricao="Cada processo aparece uma vez por ano-ambiente onde foi pautado. "
                  "Barra por ambiente com total geral no eixo secundário.",
        fn=gt11_proc_ano_ambiente,
        tipos=("barra", "linha"),
        filtros=("classe", "tipo_questao", "periodo"),
        periodo_padrao=(2020, 2025),
    ),
    GraficoSpec(
        id="T11",
        rotulo="T11 — Processos por tipo de tramitação",
        subtitulo="Virtual substitui o presencial na tramitação de novos processos (2020–2025)",
        descricao="Cada processo conta uma única vez: ano da primeira inclusão, "
                  "categoria conforme todo o histórico (Virtual / Físico / Ambos).",
        fn=gt12_proc_tramitacao_primeiro_ano,
        tipos=("barra", "linha"),
        filtros=("classe", "tipo_questao", "periodo"),
        periodo_padrao=(2020, 2025),
    ),
    GraficoSpec(
        id="T12",
        rotulo="T12 — Processos por tipo de tramitação (período total)",
        subtitulo="Quase 60% dos processos tramitam exclusivamente no virtual (2009–2025)",
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
    render_tabulador(df, key_suffix, dimensoes_disponiveis(df.columns), _PREDEFINIDOS)


_TABULADOR = GraficoSpec(
    id="T17",
    rotulo="T17 — Tabulador interativo (eixos livres)",
    subtitulo="Tabulador interativo — eixos, agrupamento e métrica livres",
    descricao="Configure o eixo X, a cor/grupo, a métrica e o modo de barras. "
              "A tabela abaixo acompanha os mesmos eixos.",
    fn=None,
    renderer=lambda df, key: _render_tabulador(df, key_suffix=key),
)

# ── Portados do Bloco 2 (período fixo) ────────────────────────────────────────
# A página Tramitação trabalha com o dataset de tramitações; as figuras do
# Bloco 2 precisam das inclusões em pauta, capturadas por closure em
# _montar_catalogo. Entradas com filtros=(): período é identidade do gráfico.
def _montar_catalogo(df_inc: pd.DataFrame) -> list[GraficoSpec]:
    """Monta o catálogo fechando as figuras do Bloco 2 sobre `df_inc`.

    Aplica a convenção do chamador do Bloco 2 (tipo_questao já com IJ→QI) e
    ignora o dataframe da página — as figuras filtram o ano por dentro.
    """
    d_inc = df_inc.assign(tipo_questao=df_inc["tipo_questao"].replace({"IJ": "QI"}))

    def _portado(fn):
        def _wrap(_df, show_values: bool = True, **_kw):
            return fn(d_inc, show_values=show_values)
        return _wrap

    portados = [
        GraficoSpec(
            id="T13",
            rotulo="T13 — Tramitação por ano (2016–2025)",
            subtitulo="Virtual ultrapassa o presencial em 2020 e o substitui na tramitação (2016–2025)",
            descricao="Ambiente de tramitação de cada processo por ano, 2016–2025: o virtual ultrapassa "
                      "o presencial em 2020. Período fixo do dado, sem recorte.",
            fn=_portado(fig_2i_tramitacao_anual_2016),
            tipos=("barra",),
            filtros=(),
            portada=True,
        ),
        GraficoSpec(
            id="T14",
            rotulo="T14 — Tramitação por período (2016–2019)",
            subtitulo="2016–2019: quase dois terços dos processos só no presencial (63%)",
            descricao="Proporção de processos que tramitaram só no virtual, só no presencial ou em ambos, "
                      "2016–2019. Período fixo do dado, sem recorte.",
            fn=_portado(fig_31_tramitacao_2016),
            tipos=("barra",),
            filtros=(),
            portada=True,
        ),
        GraficoSpec(
            id="T15",
            rotulo="T15 — Tramitação por período, vertical (2016–2019)",
            subtitulo="2016–2019: quase dois terços dos processos só no presencial (63%)",
            descricao="Mesma leitura do T14 em barras verticais, 2016–2019. Período fixo do dado, sem recorte.",
            fn=_portado(fig_31_tramitacao_alt),
            tipos=("barra",),
            filtros=(),
            portada=True,
        ),
        GraficoSpec(
            id="T16",
            rotulo="T16 — Tramitação por período, vertical (2020–2025)",
            subtitulo="2020–2025: mais de três quartos dos processos só no virtual (78%)",
            descricao="Mesma leitura do 3.2 em barras verticais, 2020–2025. Período fixo do dado, sem recorte.",
            fn=_portado(fig_32_tramitacao_alt),
            tipos=("barra",),
            filtros=(),
            portada=True,
        ),
    ]
    # O tabulador fecha a página: entra por último, depois dos portados.
    return [*_CATALOGO, *portados, _TABULADOR]


def render_graficos(df: pd.DataFrame, df_inc: pd.DataFrame | None = None) -> None:
    if df_inc is not None:
        catalogo = _montar_catalogo(df_inc)
    else:
        catalogo = [*_CATALOGO, _TABULADOR]
    render_pagina(catalogo, df, key_prefix="tram")
