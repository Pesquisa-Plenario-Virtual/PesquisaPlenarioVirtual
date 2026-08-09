"""Pós-processamento de figura para as oito páginas não-empíricas.

As funções de gráfico continuam produzindo go.Figure como sempre; este módulo
percorre a figura pronta e impõe o padrão da Pessoa 2. É o que permite aplicar
as regras em ~90 gráficos sem editar ~90 funções.

Com tema="empirico" a figura volta intocada — é assim que o alternador de tema
funciona sem duplicar código de gráfico.
"""

from __future__ import annotations

import re

import plotly.graph_objects as go

from paleta import CORES, canonico, cor

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

_PLENARIO_FISICO = "Plenário Físico"
_PLENARIO_PRESENCIAL = "Plenário Presencial"


_SPAN_FONTE = re.compile(r"<span[^>]*font-size[^>]*>(.*?)</span>", re.IGNORECASE | re.DOTALL)


def limpar_html_de_fonte(texto: str) -> str:
    """Remove <span style='font-size:...'> preservando o conteúdo.

    Os Blocos Empíricos embutem tamanho no próprio rótulo; sem isso o valor
    embutido vence o textfont padronizado quando essas figuras são importadas
    pelas páginas temáticas.
    """
    if not texto or "<span" not in texto.lower():
        return texto
    anterior = None
    while anterior != texto:
        anterior = texto
        texto = _SPAN_FONTE.sub(r"\1", texto)
    return texto


def _sem_plenario_fisico(texto):
    """"Plenário Físico" não pode sobreviver em nenhum texto renderizado —
    troca a substring onde quer que apareça, sozinha ou dentro de uma frase."""
    if not isinstance(texto, str) or _PLENARIO_FISICO not in texto:
        return texto
    return texto.replace(_PLENARIO_FISICO, _PLENARIO_PRESENCIAL)


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
    """Nome canônico, textfont padronizado e cor semântica por nome de série.

    Só recolore o que está no vocabulário da paleta: uma série fora dele mantém
    a cor que a função de gráfico escolheu. Cor vetorial (uma por barra, como em
    acervo/plots.py) é preservada — recolorir destruiria a codificação.
    """
    valor = _fonte("valor", dark)
    for tr in fig.data:
        nome = getattr(tr, "name", None)
        if nome:
            tr.name = canonico(nome)
        if hasattr(tr, "textfont"):
            tr.textfont = valor
        texto = getattr(tr, "text", None)
        if isinstance(texto, str):
            tr.text = limpar_html_de_fonte(texto)
        elif isinstance(texto, (list, tuple)):
            tr.text = [limpar_html_de_fonte(t) if isinstance(t, str) else t for t in texto]
        if not nome or canonico(nome) not in CORES:
            continue
        nova = cor(nome, dark)
        marker = getattr(tr, "marker", None)
        cor_atual = getattr(marker, "color", None) if marker is not None else None
        vetorial = hasattr(cor_atual, "__len__") and not isinstance(cor_atual, str)
        if marker is not None and hasattr(marker, "color") and not vetorial:
            tr.marker.color = nova
        if hasattr(tr, "line") and tr.type in ("scatter", "scattergl"):
            tr.line.color = nova


def _normalizar_anotacoes(fig: go.Figure, dark: bool) -> None:
    anotacao = _fonte("anotacao", dark)
    for ann in fig.layout.annotations:
        if ann.text:
            ann.text = limpar_html_de_fonte(ann.text)
        # a cor da anotação é semântica (ER preto, ESPIN vermelho) — preservar
        cor_original = ann.font.color
        ann.font = dict(family=FONTE, size=TAMANHOS["anotacao"],
                        color=cor_original or anotacao["color"])


def _normalizar_texto_livre(fig: go.Figure) -> None:
    """Título, título de eixo (inclusive subplots), anotação e tick categórico:
    "Plenário Físico" não pode aparecer em nenhum desses lugares."""
    if fig.layout.title.text:
        fig.layout.title.text = _sem_plenario_fisico(fig.layout.title.text)

    for chave in fig.layout:
        if not (chave.startswith("xaxis") or chave.startswith("yaxis")):
            continue
        eixo = fig.layout[chave]
        if eixo.title.text:
            eixo.title.text = _sem_plenario_fisico(eixo.title.text)
        if eixo.ticktext:
            eixo.ticktext = tuple(_sem_plenario_fisico(t) for t in eixo.ticktext)

    for ann in fig.layout.annotations:
        if ann.text:
            ann.text = _sem_plenario_fisico(ann.text)

    for tr in fig.data:
        if getattr(tr, "x", None) is not None:
            tr.x = tuple(_sem_plenario_fisico(v) for v in tr.x)
        if getattr(tr, "y", None) is not None:
            tr.y = tuple(_sem_plenario_fisico(v) for v in tr.y)


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
    if fig.layout.title.text:
        fig.layout.title.text = limpar_html_de_fonte(fig.layout.title.text)
    _normalizar_eixos(fig, dark)
    _normalizar_traces(fig, dark)
    _normalizar_anotacoes(fig, dark)
    _normalizar_texto_livre(fig)
    return fig


TIPOS = ("barra", "linha", "area", "barra_h")


def _e_vetor(c) -> bool:
    """Mesmo critério de _normalizar_traces: lista/tupla/array/Series é vetor,
    string não é."""
    return c is not None and not isinstance(c, str) and hasattr(c, "__len__")


def _cor_marker_bruta(tr):
    marker = getattr(tr, "marker", None)
    return getattr(marker, "color", None) if marker is not None else None


def _cor_do_trace(tr) -> str | None:
    c = _cor_marker_bruta(tr)
    if _e_vetor(c):
        return None
    if c:
        return c
    linha = getattr(tr, "line", None)
    return getattr(linha, "color", None) if linha is not None else None


def converter_tipo(fig: go.Figure, tipo: str = "barra") -> go.Figure:
    """Reconstrói os traces na forma pedida preservando x, y, nome, cor e texto.

    Tipo desconhecido devolve a figura como está — o seletor da casca só oferece
    as formas declaradas em GraficoSpec.tipos, então isso é rede de segurança.

    Também devolve a figura intocada quando a reconstrução não tem como
    preservar o essencial: trace sem x/y (Pie, Sunburst, Treemap — não têm
    forma de barra/linha/área) ou cor vetorial (uma cor por barra) pedida como
    linha/área, onde uma única linha não tem como carregar várias cores.
    """
    if tipo not in TIPOS or tipo == "barra" or not fig.data:
        return fig
    if any(not hasattr(tr, "x") or not hasattr(tr, "y") for tr in fig.data):
        return fig
    if tipo in ("linha", "area") and any(_e_vetor(_cor_marker_bruta(tr)) for tr in fig.data):
        return fig

    novos = []
    for tr in fig.data:
        c = _cor_do_trace(tr)
        base = dict(x=tr.x, y=tr.y, name=tr.name, text=tr.text,
                    hovertemplate=tr.hovertemplate, legendgroup=tr.legendgroup,
                    showlegend=tr.showlegend)
        if tipo == "linha":
            novos.append(go.Scatter(mode="lines+markers",
                                    line=dict(color=c, width=2),
                                    marker=dict(color=c, size=8),
                                    textposition="top center", **base))
        elif tipo == "area":
            novos.append(go.Scatter(mode="lines", stackgroup="um", fill="tonexty",
                                    line=dict(color=c, width=2), **base))
        elif tipo == "barra_h":
            bruta = _cor_marker_bruta(tr)
            cor_barra = bruta if _e_vetor(bruta) else c
            trocado = dict(base, x=tr.y, y=tr.x)
            novos.append(go.Bar(orientation="h", marker=dict(color=cor_barra), **trocado))

    layout = fig.layout
    nova = go.Figure(data=novos, layout=layout)
    if tipo == "barra_h":
        titulo_x = layout.xaxis.title.text
        titulo_y = layout.yaxis.title.text
        nova.update_layout(xaxis_title=titulo_y, yaxis_title=titulo_x)
    return nova
