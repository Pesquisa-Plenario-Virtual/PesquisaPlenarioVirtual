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
from pages.bloco1_acervo.plots import (
    fig_1a_variacao_trienal, fig_1a2_variacao_trienal, fig_1b_acervo_por_classe,
    fig_1b2_acervo_por_classe_vertical, fig_1b3_acervo_por_classe_vertical_extremos,
    fig_1b4_acervo_por_classe_vertical_sem_eixo, fig_1c_distribuicao_baixa,
    fig_1d_variacao_anual, fig_1d2_variacao_anual,
)

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


# ── Narrativa do Acervo (Bloco 1) — portadas por import, período fixo 1988–2025 ──
# Entradas com filtros=(): a função filtra o ano por dentro e o período é parte
# da identidade do gráfico. O dataframe chega completo por closure da página.
_NARRATIVA_ACERVO = [
    GraficoSpec(
        id="A6",
        rotulo="A6 — Variação trienal do acervo (1988–2025)",
        subtitulo="Acervo ativo encolhe mais de 500 processos por triênio desde 2018",
        descricao="Variação do acervo ativo (distribuição − baixa) agrupada em triênios, "
                  "positivo cinza e negativo vermelho. Período fixo da série, sem recorte.",
        fn=fig_1a_variacao_trienal,
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="A7",
        rotulo="A7 — Variação trienal do acervo, negativo azul (1988–2025)",
        subtitulo="Acervo ativo encolhe mais de 500 processos por triênio desde 2018",
        descricao="Mesma variação trienal do A6, com o negativo em azul em vez de vermelho. "
                  "Período fixo da série, sem recorte.",
        fn=fig_1a2_variacao_trienal,
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="A8",
        rotulo="A8 — Acervo por classe, horizontal (1988–2025)",
        subtitulo="ADI concentra o acervo ativo em todo o período",
        descricao="Barras horizontais empilhadas por classe, 1988 no topo, com os totais anuais na ponta. "
                  "Período fixo da série, sem recorte.",
        fn=fig_1b_acervo_por_classe,
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="A9",
        rotulo="A9 — Acervo por classe, vertical (1988–2025)",
        subtitulo="ADI concentra o acervo ativo em todo o período",
        descricao="Barras verticais empilhadas por classe, com marcadores ER e faixa ESPIN. "
                  "Período fixo da série, sem recorte.",
        fn=fig_1b2_acervo_por_classe_vertical,
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="A10",
        rotulo="A10 — Acervo por classe, totais de 2017 e 2025 rotulados (1988–2025)",
        subtitulo="ADI concentra o acervo ativo em todo o período",
        descricao="Mesmo A9, com os totais de 2017 e 2025 rotulados no topo das barras. "
                  "Período fixo da série, sem recorte.",
        fn=fig_1b3_acervo_por_classe_vertical_extremos,
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="A11",
        rotulo="A11 — Acervo por classe, sem eixo (1988–2025)",
        subtitulo="ADI concentra o acervo ativo em todo o período",
        descricao="Mesmo A9 sem o eixo esquerdo; 'Exibir valores' rotula o total de cada ano. "
                  "Período fixo da série, sem recorte.",
        fn=fig_1b4_acervo_por_classe_vertical_sem_eixo,
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="A12",
        rotulo="A12 — Distribuição e baixa espelhados (1988–2025)",
        subtitulo="Baixas disparam após 2019 e superam as distribuições",
        descricao="Colunas espelhadas: distribuições (entrada) para cima e baixas (saída) para baixo, "
                  "com marcadores ER e faixa ESPIN. Período fixo da série, sem recorte.",
        fn=fig_1c_distribuicao_baixa,
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="A13",
        rotulo="A13 — Variação anual do acervo (1988–2025)",
        subtitulo="Acervo ativo em queda contínua desde 2019",
        descricao="Variação anual (entradas − saídas), acréscimo cinza e decréscimo vermelho, "
                  "com marcadores ER e faixa ESPIN. Período fixo da série, sem recorte.",
        fn=fig_1d_variacao_anual,
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="A14",
        rotulo="A14 — Variação anual do acervo, decréscimo azul (1988–2025)",
        subtitulo="Acervo ativo em queda contínua desde 2019",
        descricao="Mesma variação anual do A13, com o decréscimo em azul em vez de vermelho. "
                  "Período fixo da série, sem recorte.",
        fn=fig_1d2_variacao_anual,
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
]

_CATALOGO.extend(_NARRATIVA_ACERVO)

_CATALOGO.append(GraficoSpec(
    id="A15",
    rotulo="A15 — Tabulador interativo (eixos livres)",
    subtitulo="Tabulador interativo — eixos, agrupamento e métrica livres",
    descricao="Configure o eixo X, a cor/grupo, a métrica e o modo de barras. "
              "A tabela abaixo acompanha os mesmos eixos.",
    fn=None,
    renderer=lambda df, key: _render_interactive_tabulador(),
))

def render_graficos(df: pd.DataFrame) -> None:
    """Ponto de entrada: catálogo A1-A5 + Tabulador Gráfico livre (A6)."""
    render_pagina(_CATALOGO, df, key_prefix="acervo")
