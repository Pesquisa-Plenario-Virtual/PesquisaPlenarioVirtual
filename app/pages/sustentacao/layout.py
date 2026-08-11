"""Renderização da página de Sustentação Oral."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from components.tabulador import render_tabulador
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


def _render_interactive_tabulador(df: pd.DataFrame, key: str = "sust_tab") -> None:
    render_tabulador(df, key, dimensoes_disponiveis(df.columns), _PREDEFINIDOS_SUST)


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
