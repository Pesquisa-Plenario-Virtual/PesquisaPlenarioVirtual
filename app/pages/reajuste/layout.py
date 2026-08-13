"""Renderização da página de Reajuste de Voto."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from components.tabulador import render_tabulador
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

# ── Catálogo R1–R5 (R6 é o tabulador livre, fora do catálogo) ──────────────────
_CATALOGO = [
    GraficoSpec(
        id="R1",
        rotulo="R1 — % com reajuste (Plenário Virtual e Plenário Presencial)",
        subtitulo="Reajuste de voto é raro e na mesma proporção nos dois âmbitos (≈1,5%)",
        descricao="Percentual de inclusões que tiveram ao menos um reajuste de voto, por ambiente.",
        fn=gr1_reajuste_pct,
        tipos=("barra",),
        filtros=("classe", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="R2",
        rotulo="R2 — Reajustes por Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Reajustes aparecem só a partir de 2020 e seguem em volume baixo",
        descricao="Volume anual de inclusões que registraram reajuste de voto. "
                  "Anos sem ocorrência aparecem com valor zero. Selecione o âmbito.",
        fn=gr3_anual_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="R3",
        rotulo="R3 — Reajustes por Ano e Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="ADI concentra os reajustes desde o início",
        descricao="Barras agrupadas por classe (ADI, ADPF, ADC, ADO) mostrando o volume anual "
                  "de reajustes de voto. Selecione o âmbito.",
        fn=gr5_classe_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="R4",
        rotulo="R4 — Tipo de Questão × Reajuste",
        subtitulo="PR responde pela quase totalidade dos reajustes",
        descricao="Distribuição das inclusões com/sem reajuste por tipo de questão (PR/RC/QI).",
        fn=gr7_tipo_vs_reajuste,
        tipos=("barra",),
        filtros=("ambiente", "classe", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="R5",
        rotulo="R5 — Desfecho Detalhado × Reajuste",
        subtitulo="Unanimidade lidera entre as inclusões com reajuste",
        descricao="Distribuição das inclusões com/sem reajuste por desfecho detalhado.",
        fn=gr8_desfecho_vs_reajuste,
        tipos=("barra", "barra_h"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
]


def _render_interactive_tabulador(df: pd.DataFrame, key: str = "reaj_tab") -> None:
    render_tabulador(df, key, dimensoes_disponiveis(df.columns), _PREDEFINIDOS_TAB)


_CATALOGO.append(GraficoSpec(
    id="R6",
    rotulo="R6 — Tabulador interativo (eixos livres)",
    subtitulo="Tabulador interativo — eixos, agrupamento e métrica livres",
    descricao="Configure o eixo X, a cor/grupo, a métrica e o modo de barras. "
              "A tabela abaixo acompanha os mesmos eixos.",
    fn=None,
    renderer=lambda df, key: _render_interactive_tabulador(df),
))

def render_graficos(df: pd.DataFrame) -> None:
    render_pagina(_CATALOGO, df, key_prefix="reaj")
