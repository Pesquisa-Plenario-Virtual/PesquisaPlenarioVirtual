"""Renderização da página Gráficos de Narrativa."""

from __future__ import annotations
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from .plots import plot_na, plot_nb, plot_nc, plot_nd, plot_ne, plot_nf

_CATALOGO = [
    GraficoSpec(
        id="NA",
        rotulo="NA — Participação estável",
        subtitulo="Participação estável do PV ao ano",
        descricao="Barras anuais do percentual de inclusões em pauta destinadas ao PV, com marcador vertical no fim da ESPIN (abril de 2022).",
        fn=plot_na,
        tipos=("barra", "linha"),
        filtros=("periodo", "classe"),
    ),
    GraficoSpec(
        id="NB",
        rotulo="NB — Pauta versus concluídos",
        subtitulo="Pauta versus concluídos (síntese do impacto)",
        descricao="Participação do PV na pauta (63,9%) e nos julgamentos concluídos (91,3%).",
        fn=plot_nb,
        tipos=("barra",),
        filtros=("periodo", "classe"),
    ),
    GraficoSpec(
        id="NC",
        rotulo="NC — Tramitação por ambiente",
        subtitulo="Tramitação por ambiente",
        descricao="Três barras horizontais: processos que tramitaram somente PV, ambos, somente PP.",
        fn=plot_nc,
        tipos=("barra_h", "barra"),
        filtros=("periodo", "classe"),
    ),
    GraficoSpec(
        id="ND",
        rotulo="ND — Recursos",
        subtitulo="Recursos",
        descricao="Barra única empilhada com o destino das inclusões de recursos: PV (94,3%) vs PP (5,7%).",
        fn=plot_nd,
        tipos=("barra_h", "barra"),
        filtros=("periodo", "classe"),
    ),
    GraficoSpec(
        id="NE",
        rotulo="NE — Inclusões por processo",
        subtitulo="Inclusões por processo",
        descricao="Média de inclusões em pauta por processo em cada ambiente: PV (1,8) vs PP (4,3).",
        fn=plot_ne,
        tipos=("barra",),
        filtros=("periodo", "classe"),
    ),
    GraficoSpec(
        id="NF",
        rotulo="NF — Conclusão por processo",
        subtitulo="Conclusão por processo",
        descricao="Percentual de processos pautados que tiveram julgamento concluído: PV (86,0%) vs PP (39,2%).",
        fn=plot_nf,
        tipos=("barra",),
        filtros=("periodo", "classe"),
    ),
]


def render_graficos(df: pd.DataFrame) -> None:
    render_pagina(_CATALOGO, df, key_prefix="narr")
