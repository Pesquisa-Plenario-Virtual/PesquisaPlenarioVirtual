"""Renderização da página Gráficos de Narrativa."""

from __future__ import annotations
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from .plots import plot_na, plot_nb, plot_nc, plot_nd, plot_ne, plot_nf

_CATALOGO = [
    GraficoSpec(
        id="N1",
        rotulo="N1 — Participação estável",
        subtitulo="Participação estável do PV ao ano",
        descricao="Barras anuais do percentual de inclusões em pauta destinadas ao PV, com marcador vertical no fim da ESPIN (abril de 2022).",
        fn=plot_na,
        tipos=("barra", "linha"),
        filtros=("periodo", "classe"),
    ),
    GraficoSpec(
        id="N2",
        rotulo="N2 — Pauta versus concluídos",
        subtitulo="Pauta versus concluídos (síntese do impacto)",
        descricao="Participação do PV na pauta (63,9%) e nos julgamentos concluídos (91,3%).",
        fn=plot_nb,
        tipos=("barra",),
        filtros=("periodo", "classe"),
    ),
    GraficoSpec(
        id="N3",
        rotulo="N3 — Tramitação por ambiente",
        subtitulo="Só o virtual concentra a maior parte dos processos",
        descricao="Três barras horizontais: processos que tramitaram somente PV, ambos, somente PP.",
        fn=plot_nc,
        tipos=("barra_h", "barra"),
        filtros=("periodo", "classe"),
    ),
    GraficoSpec(
        id="N4",
        rotulo="N4 — Recursos",
        subtitulo="Recursos tramitam quase inteiramente no virtual (94,3%)",
        descricao="Barra única empilhada com o destino das inclusões de recursos: PV (94,3%) vs PP (5,7%).",
        fn=plot_nd,
        tipos=("barra_h", "barra"),
        filtros=("periodo", "classe"),
    ),
    GraficoSpec(
        id="N5",
        rotulo="N5 — Inclusões por processo",
        subtitulo="Presencial concentra mais inclusões por processo que o virtual",
        descricao="Média de inclusões em pauta por processo em cada ambiente: PV (1,8) vs PP (4,3).",
        fn=plot_ne,
        tipos=("barra",),
        filtros=("periodo", "classe"),
    ),
    GraficoSpec(
        id="N6",
        rotulo="N6 — Conclusão por processo",
        subtitulo="Virtual conclui o que pauta em proporção muito maior que o presencial",
        descricao="Percentual de processos pautados que tiveram julgamento concluído: PV (86,0%) vs PP (39,2%).",
        fn=plot_nf,
        tipos=("barra",),
        filtros=("periodo", "classe"),
    ),
]


def render_graficos(df: pd.DataFrame) -> None:
    render_pagina(_CATALOGO, df, key_prefix="narr")
