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

# ── Catálogo S1–S5 (S6 é o tabulador livre, fora do catálogo) ──────────────────
_CATALOGO = [
    GraficoSpec(
        id="S1",
        rotulo="S1 — Proporção com/sem sustentação (Plenário Virtual e Plenário Presencial)",
        subtitulo="Sustentação oral ocorre em cerca de um quarto das inclusões (25%)",
        descricao="Barra horizontal com a proporção de inclusões que tiveram sustentação oral, percentual na ponta. "
                  "Selecione o âmbito.",
        fn=gs1_sust_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="S2",
        rotulo="S2 — Sustentações por Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Sustentações crescem com a universalização e atingem o pico em 2020",
        descricao="Volume anual de inclusões com sustentação oral. "
                  "Anos sem ocorrência aparecem com valor zero. Selecione o âmbito.",
        fn=gs3_sust_anual_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="S3",
        rotulo="S3 — Sustentações por Ano e Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="ADI concentra as sustentações em todos os anos",
        descricao="Barras agrupadas por classe (ADI, ADPF, ADC, ADO) mostrando o volume anual "
                  "de sustentações orais. Selecione o âmbito.",
        fn=gs5_sust_classe_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="S4",
        rotulo="S4 — Sustentações por Ano e Tipo de Questão",
        subtitulo="PR responde pela grande maioria das sustentações",
        descricao="Barras agrupadas por tipo de questão (PR / RC / QI) mostrando o volume anual "
                  "de sustentações orais. IJ renomeado para QI. Selecione o âmbito.",
        fn=gs7_sust_tipo_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "classe", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="S5",
        rotulo="S5 — Taxa de Sustentação por Ano e Ambiente (%)",
        subtitulo="Taxas dos dois âmbitos se aproximam após a universalização",
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
    id="S6",
    rotulo="S6 — Tabulador interativo (eixos livres)",
    subtitulo="Tabulador interativo — eixos, agrupamento e métrica livres",
    descricao="Configure o eixo X, a cor/grupo, a métrica e o modo de barras. "
              "A tabela abaixo acompanha os mesmos eixos.",
    fn=None,
    renderer=lambda df, key: _render_interactive_tabulador(df),
))

def render_graficos(df: pd.DataFrame) -> None:
    render_pagina(_CATALOGO, df, key_prefix="sust")
