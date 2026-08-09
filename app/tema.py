"""Pós-processamento de figura para as oito páginas não-empíricas.

As funções de gráfico continuam produzindo go.Figure como sempre; este módulo
percorre a figura pronta e impõe o padrão da Pessoa 2. É o que permite aplicar
as regras em ~90 gráficos sem editar ~90 funções.

Com tema="empirico" a figura volta intocada — é assim que o alternador de tema
funciona sem duplicar código de gráfico.
"""

from __future__ import annotations

import plotly.graph_objects as go

from paleta import canonico

FONTE = "Times New Roman, Times, serif"

TAMANHOS = {
    "titulo": 22,
    "subtitulo": 14,
    "eixo_titulo": 16,
    "tick": 14,
    "legenda": 14,
    "valor": 13,
    "anotacao": 12,
}

TINTA_CLARA = "#0b0b0b"
TINTA_ESCURA = "#fafafa"
FUNDO_CLARO = "#ffffff"
FUNDO_ESCURO = "#0e1117"


def _fonte(size_key: str, dark: bool) -> dict:
    return dict(
        family=FONTE,
        size=TAMANHOS[size_key],
        color=TINTA_ESCURA if dark else TINTA_CLARA,
    )


def _normalizar_eixos(fig: go.Figure, dark: bool) -> None:
    """Tipografia, tamanho e tickangle=0 em todo eixo, inclusive subplots."""
    eixo_tick = _fonte("tick", dark)
    eixo_titulo = _fonte("eixo_titulo", dark)
    for chave in fig.layout:
        if not (chave.startswith("xaxis") or chave.startswith("yaxis")):
            continue
        eixo = fig.layout[chave]
        eixo.tickfont = eixo_tick
        eixo.title.font = eixo_titulo
        if chave.startswith("xaxis"):
            eixo.tickangle = 0


def _normalizar_traces(fig: go.Figure, dark: bool) -> None:
    """Nome de série em rótulo canônico e textfont padronizado."""
    valor = _fonte("valor", dark)
    for tr in fig.data:
        if getattr(tr, "name", None):
            tr.name = canonico(tr.name)
        if hasattr(tr, "textfont"):
            tr.textfont = valor


def _normalizar_anotacoes(fig: go.Figure, dark: bool) -> None:
    anotacao = _fonte("anotacao", dark)
    for ann in fig.layout.annotations:
        # a cor da anotação é semântica (ER preto, ESPIN vermelho) — preservar
        cor_original = ann.font.color
        ann.font = dict(family=FONTE, size=TAMANHOS["anotacao"],
                        color=cor_original or anotacao["color"])


def aplicar_tema(fig: go.Figure, tema: str = "novo", dark: bool = False) -> go.Figure:
    """Impõe o padrão visual da Pessoa 2 a uma figura já construída.

    tema="empirico" devolve a figura sem tocar em nada.
    """
    if tema == "empirico":
        return fig

    tinta = TINTA_ESCURA if dark else TINTA_CLARA
    fundo = FUNDO_ESCURO if dark else FUNDO_CLARO

    fig.update_layout(
        font=dict(family=FONTE, color=tinta),
        title_font=_fonte("titulo", dark),
        legend_font=_fonte("legenda", dark),
        paper_bgcolor=fundo,
        plot_bgcolor=fundo,
    )
    _normalizar_eixos(fig, dark)
    _normalizar_traces(fig, dark)
    _normalizar_anotacoes(fig, dark)
    return fig
