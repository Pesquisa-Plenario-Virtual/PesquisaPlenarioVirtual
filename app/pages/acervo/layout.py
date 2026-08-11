"""Renderização da página de Acervo."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from components.tabulador import render_tabulador
from .plots import plotar_grafico_stf
from pages.tramitacao.plots import gt10_tabulador
from dados.filters import dimensoes_disponiveis

_PREDEFINIDOS_ACERVO = [
    ("Ano × Classe (total geral, empilhado)",         "ano", "classe",        "inclusoes", "stack"),
    ("Ano × Classe (total geral, empilhado 100%)",    "ano", "classe",        "inclusoes", "100%"),
    ("Classe × Macro-Desfecho (inclusões, agrupado)", "classe", "macro_desfecho", "inclusoes", "group"),
    ("Ano × Ambiente (inclusões, empilhado)",         "ano", "ambiente",      "inclusoes", "stack"),
]

# Métricas disponíveis no dataset
_METRICAS = [
    (
        "quantidade_ativos",
        "Processos Ativos",
        "Acervo Ativo",
        "Estoque de processos **sem baixa definitiva** ao final de cada ano (31/12). "
        "Mede o volume pendente de julgamento e é o principal indicador de pressão sobre a pauta do tribunal.",
    ),
    (
        "quantidade_inativos",
        "Processos Inativos",
        "Acervo Inativo",
        "Estoque **acumulado** de processos já encerrados até o final de cada ano. "
        "Representa o histórico total de casos resolvidos desde 1988.",
    ),
    (
        "total_geral",
        "Total de Processos",
        "Total Geral",
        "Soma dos processos ativos e inativos ao final de cada ano. "
        "Reflete o volume total de ações já distribuídas no tribunal desde sua criação.",
    ),
    (
        "quantidade_baixas",
        "Processos Baixados",
        "Baixas Anuais",
        "**Fluxo anual** de processos encerrados em cada ano. Diferente do acervo inativo (estoque), "
        "as baixas medem a produtividade do tribunal ano a ano — picos indicam o impacto das Emendas Regimentais e do Plenário Virtual.",
    ),
    (
        "quantidade_distribuidos",
        "Processos Distribuídos",
        "Distribuições (Entrada)",
        "**Fluxo anual** de novos processos distribuídos ao relator em cada ano. "
        "Mede a pressão de entrada no tribunal e permite comparar a taxa de entrada com a taxa de baixas.",
    ),
]


def _wrapper_metrica(col: str, label: str):
    """Fecha sobre a coluna/rótulo da métrica; decide TOTAL vs. classe única a
    partir de quantas classes sobraram no recorte que a casca entrega.

    plotar_grafico_stf("TOTAL", ...) soma o dataframe que recebe via
    groupby("ano").sum() — não assume a base inteira — então agregar um
    subconjunto de 2-3 classes é uma leitura honesta (verificado).
    """
    def _plot(df: pd.DataFrame, show_values: bool = True, **_kw):
        classes = df["classe"].dropna().unique().tolist()
        classe = classes[0] if len(classes) == 1 else "TOTAL"
        return plotar_grafico_stf(df, classe, col, label, show_values)
    return _plot


_CATALOGO = [
    GraficoSpec(
        id=f"A{i + 1}",
        rotulo=f"A{i + 1} — {titulo}",
        subtitulo=f"Evolução — {titulo}",
        descricao=descricao,
        fn=_wrapper_metrica(col, label),
        tipos=("barra", "linha"),
        filtros=("classe", "periodo"),
    )
    for i, (col, label, titulo, descricao) in enumerate(_METRICAS)
]


def _render_interactive_tabulador(_df=None, key: str = "acervo_tab") -> None:
    # O acervo histórico não tem as dimensões do tabulador (é ano x classe x
    # métrica agregada), então este bloco trabalha sobre as inclusões em pauta.
    from dados.loader import load_inclusoes_em_pauta
    df_inc = load_inclusoes_em_pauta()
    st.caption(
        "Sobre o dataset de inclusões em pauta — diferente dos gráficos de "
        "evolução acima, que usam o acervo histórico."
    )
    render_tabulador(df_inc, key, dimensoes_disponiveis(df_inc.columns), _PREDEFINIDOS_ACERVO)


_CATALOGO.append(GraficoSpec(
    id="A6",
    rotulo="A6 — Tabulador interativo (eixos livres)",
    subtitulo="Tabulador interativo — eixos, agrupamento e métrica livres",
    descricao="Configure o eixo X, a cor/grupo, a métrica e o modo de barras. "
              "A tabela abaixo acompanha os mesmos eixos.",
    fn=None,
    renderer=lambda df, key: _render_interactive_tabulador(),
))

def render_graficos(df: pd.DataFrame) -> None:
    """Ponto de entrada: catálogo A1-A5 + Tabulador Gráfico livre (A6)."""
    render_pagina(_CATALOGO, df, key_prefix="acervo")
