"""Padrão visual único (PADRÃO GERAL) para todos os gráficos Plotly do dashboard.

Fonte: Especificacoes_graficos_Joao.md (briefing original da cliente).
Regras: fonte preta (#000000), sem grade de fundo, sem eixo secundário, sem
linha de total, sem rodapé de fonte, título afirma o achado, marcadores de
ER (emendas regimentais) e sombreamento ESPIN idênticos em todos os gráficos
que cruzam essas datas.
"""

from __future__ import annotations
import plotly.graph_objects as go

AZUL = "#2563EB"
AZUL_CLARO = "#93C5FD"
CINZA = "#9CA3AF"
VERDE = "#059669"
ROXO = "#7C3AED"
VERMELHO = "#C00000"
PRETO = "#000000"

COR_PV = AZUL
COR_PP = CINZA
COR_AMBOS = AZUL_CLARO

# Emendas Regimentais: data de edição, usada nas guardas de recorte de período.
ER_DATAS = {
    51: (2016, 6, 22),
    52: (2019, 6, 14),
    53: (2020, 3, 18),
}
# Fronteiras entre anos onde os marcadores ficam: a emenda marca o início do
# regime que passa a valer no ano seguinte à sua edição (ER 51/2016 vale de
# 2017; ER 52/2019 de 2019; ER 53/2020 de 2020). Cada valor é o ano `N` da
# fronteira N/N+1.
ER_FRONTEIRAS = {51: 2016, 52: 2018, 53: 2019}
# Faixa ESPIN: da fronteira 2019/2020 (final de 2019) à fronteira 2022/2023
# (final de 2022).
ESPIN_FRONTEIRAS = (2019, 2022)

AXIS_PADRAO = dict(
    showline=True, linewidth=1.5, linecolor=PRETO,
    showgrid=False, zeroline=False,
    title_font=dict(family="Arial, sans-serif", size=16, color=PRETO),
    tickfont=dict(family="Arial, sans-serif", size=15, color=PRETO, weight="bold"),
    ticks="outside", tickcolor=PRETO,
)

LAYOUT_PADRAO = dict(
    template="plotly_white",
    height=560,
    margin=dict(t=110, b=70, l=60, r=40),
    title_font=dict(family="Arial, sans-serif", size=22, color=PRETO),
    font=dict(family="Arial, sans-serif", color=PRETO),
    plot_bgcolor="white",
    paper_bgcolor="white",
    showlegend=False,
)

LEGENDA_PADRAO = dict(
    orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5,
    font=dict(family="Arial, sans-serif", size=14, color=PRETO),
)


def br(v: float, d: int = 0) -> str:
    """Formata número no padrão brasileiro (ponto de milhar, vírgula decimal)."""
    if d == 0:
        return f"{int(round(v)):,}".replace(",", ".")
    s = f"{v:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".")


# ── Pilha vertical do topo: título → gap → legenda → gap → gráfico ───────────
# O `margin.t` reserva altura para a pilha toda. O `max()` com o valor que o
# gráfico pediu preserva margens que existem por outro motivo (ex.: rótulos de
# valor altos acima das barras no bloco 2).
TOPO_PAD = 12
ALTURA_LINHA_TITULO = 36
GAP_TITULO_LEGENDA = 16
ALTURA_LINHA_LEGENDA = 26
GAP_LEGENDA_GRAFICO = 70


def _linhas_legenda(fig: go.Figure, tem_legenda: bool) -> int:
    if not tem_legenda:
        return 0
    n_series = len(fig.data)
    return max(1, -(-n_series // 4)) if n_series > 1 else 0


def _pilha_vertical_topo(fig: go.Figure, tem_subtitulo: bool, tem_legenda: bool, margin_t_atual) -> float:
    """margin.t mínimo para a pilha título → legenda → gráfico, nunca encolhe o valor do gráfico."""
    linhas_titulo = 2 if tem_subtitulo else 1
    linhas_legenda = _linhas_legenda(fig, tem_legenda)
    minimo = TOPO_PAD + ALTURA_LINHA_TITULO * linhas_titulo + GAP_LEGENDA_GRAFICO
    if linhas_legenda:
        minimo += GAP_TITULO_LEGENDA + ALTURA_LINHA_LEGENDA * linhas_legenda
    return max(margin_t_atual or LAYOUT_PADRAO["margin"]["t"], minimo)


def aplicar_padrao(fig: go.Figure, titulo: str, subtitulo: str | None = None, **layout_kwargs) -> go.Figure:
    """Aplica título/subtítulo em negrito preto e o layout base a `fig`, sem rodapé de fonte.

    A pilha vertical do topo é padronizada em todos os gráficos: o `margin.t`
    reserva altura para título + gap + legenda + gap, e legendas horizontais de
    topo ficam `GAP_LEGENDA_GRAFICO` px acima do topo do gráfico (gap uniforme,
    independente do tamanho da figura). Legendas dentro da área do gráfico (y<1)
    e abaixo dele (pizzas, y<0) ficam como o gráfico definiu.
    """
    title = f"<b>{titulo}</b>"
    if subtitulo:
        title += f"<br><sup>{subtitulo}</sup>"
    layout = {**LAYOUT_PADRAO, **layout_kwargs}
    legend = dict(layout.get("legend") or {})
    legenda_topo = (bool(layout.get("showlegend")) and legend.get("orientation", "v") == "h"
                    and legend.get("yanchor", "bottom") != "top")
    margin = dict(layout.get("margin") or {})
    margin["t"] = _pilha_vertical_topo(fig, bool(subtitulo), legenda_topo, margin.get("t"))
    layout["margin"] = margin
    # Legenda usa coordenadas "paper" (área do gráfico, y=1 no topo do plot,
    # pode passar de 1 para subir para a margem). Título usa "container" (y=1
    # no topo da figura inteira) ancorado no topo por `TOPO_PAD`: com subtítulo
    # (<br><sup>), o Plotly não estende a altura do bloco de título de forma
    # previsível a partir de um `yanchor="bottom"`, então ancorar pelo topo e
    # deixar o bloco crescer para baixo é o que não colide com a legenda logo
    # abaixo — o espaço para essa altura já está reservado em `margin.t`.
    altura_fig = float(layout.get("height") or LAYOUT_PADRAO["height"])
    altura_plot = max(1.0, altura_fig - margin["t"] - float(margin.get("b") or LAYOUT_PADRAO["margin"]["b"]))
    if legenda_topo:
        y_legenda = 1.0 + GAP_LEGENDA_GRAFICO / altura_plot
        legend.update(orientation="h", y=y_legenda, yanchor="bottom", x=0.5, xanchor="center")
        layout["legend"] = legend
    y_titulo = max(0.0, min(1.0, 1.0 - (TOPO_PAD + ALTURA_LINHA_TITULO * 0.6) / altura_fig))
    layout["title"] = dict(text=title, xref="container", yref="container",
                           x=0.5, xanchor="center", y=y_titulo, yanchor="top")
    fig.update_layout(**layout)
    fig.update_xaxes(**AXIS_PADRAO)
    fig.update_yaxes(**AXIS_PADRAO)
    return fig


def _fronteira(ano_base: int, ano: int) -> float:
    """Posição x da fronteira entre o ano `ano` e `ano+1` (início e fim de cada barra de ano)."""
    return (ano - ano_base) + 0.5


def add_er_marker(fig: go.Figure, ano_base: int, er: int, y0: float, y1: float, y_label: float) -> go.Figure:
    """Linha vertical preta tracejada + rótulo 'ER n' na fronteira do ano da emenda."""
    x = _fronteira(ano_base, ER_FRONTEIRAS[er])
    fig.add_shape(type="line", x0=x, x1=x, y0=y0, y1=y1,
                  line=dict(color=PRETO, width=1.5, dash="dash"), xref="x", yref="y")
    fig.add_annotation(x=x, y=y_label, text=f"<b>ER {er}</b>", showarrow=False,
                        font=dict(color=PRETO, size=12), xref="x", yref="y")
    # y0 é sempre 0 (base do eixo); sem isto o autorange do Plotly deixa um
    # piso negativo e a linha "flutua" acima do eixo X em vez de tocá-lo.
    fig.update_yaxes(rangemode="tozero")
    return fig


def add_espin_shade(fig: go.Figure, ano_base: int, y0: float, y1: float) -> go.Figure:
    """Sombreamento rosa claro + linhas vermelhas tracejadas + seta e rótulo 'ESPIN' na faixa da ESPIN.

    Réplica do padrão 1.b3 (bloco empírico): as linhas vermelhas são mais
    baixas que as linhas das ERs, a seta percorre a faixa da linha inicial à
    final, e o rótulo fica centralizado acima da seta. A faixa vai da fronteira
    2019/2020 (final de 2019) à fronteira 2022/2023 (final de 2022); a linha
    vermelha de início fica 0.06 à direita da fronteira para não sobrepor a
    linha preta do ER 53, que ocupa a mesma fronteira.
    """
    x0 = _fronteira(ano_base, ESPIN_FRONTEIRAS[0])
    x1 = _fronteira(ano_base, ESPIN_FRONTEIRAS[1])
    x0_linha = x0 + 0.06
    y_espin = y0 + (y1 - y0) * 0.95
    fig.add_vrect(x0=x0, x1=x1, fillcolor="#FCE7F3", opacity=0.55, line_width=0, layer="below")
    for x in (x0_linha, x1):
        fig.add_shape(type="line", x0=x, x1=x, y0=y0, y1=y_espin,
                      line=dict(color=VERMELHO, width=1.5, dash="dash"), xref="x", yref="y")
    fig.add_annotation(x=x0_linha, y=y_espin, ax=x1, ay=y_espin, axref="x", ayref="y",
                       xref="x", yref="y", showarrow=True, arrowhead=2, arrowsize=1.6,
                       arrowwidth=1.2, arrowcolor=VERMELHO, text="")
    fig.add_annotation(x=x1, y=y_espin, ax=x0_linha, ay=y_espin, axref="x", ayref="y",
                       xref="x", yref="y", showarrow=True, arrowhead=2, arrowsize=1.6,
                       arrowwidth=1.2, arrowcolor=VERMELHO, text="")
    fig.add_annotation(x=(x0 + x1) / 2, y=y_espin, yanchor="bottom", yshift=6,
                       text="<b>ESPIN</b>", showarrow=False,
                       font=dict(color=VERMELHO, size=13, weight="bold"),
                       xref="x", yref="y")
    # y0 é sempre 0 (base do eixo); sem isto o autorange do Plotly deixa um
    # piso negativo e a faixa "flutua" acima do eixo X em vez de tocá-lo.
    fig.update_yaxes(rangemode="tozero")
    return fig


# ── Remoção dos marcos (toggle do usuário) ───────────────────────────────────
# Identificação por assinatura: linhas tracejadas preto (ER) / vermelho (ESPIN),
# faixa rosa, setas vermelhas e anotações "ER..."/"...ESPIN...". Nenhuma outra
# shape tracejada existe nos gráficos (verificado no código), então a remoção
# não alcança elementos legítimos.

def remover_marcos_er(fig: go.Figure) -> go.Figure:
    """Remove os marcadores das Emendas Regimentais (linhas pretas tracejadas e rótulos 'ER n')."""
    fig.layout.shapes = [
        s for s in fig.layout.shapes
        if not (s.type == "line"
                and str(getattr(getattr(s, "line", None), "dash", None) or "").lower() == "dash"
                and str(getattr(getattr(s, "line", None), "color", None) or "").upper()
                in ("#000000", "BLACK"))
    ]
    fig.layout.annotations = [
        a for a in fig.layout.annotations
        if not (a.text or "").startswith("<b>ER")
    ]
    return fig


def remover_faixa_espin(fig: go.Figure) -> go.Figure:
    """Remove a faixa da ESPIN (sombreamento rosa, linhas vermelhas, setas e rótulo)."""
    fig.layout.shapes = [
        s for s in fig.layout.shapes
        if not (s.type == "rect" and str(s.fillcolor or "").upper() == "#FCE7F3")
        and not (s.type == "line"
                 and str(getattr(getattr(s, "line", None), "dash", None) or "").lower() == "dash"
                 and str(getattr(getattr(s, "line", None), "color", None) or "").upper()
                 in ("#C00000", "RED"))
    ]
    fig.layout.annotations = [
        a for a in fig.layout.annotations
        if not ("ESPIN" in (a.text or "")
                or (a.showarrow and str(a.arrowcolor or "").upper() in ("#C00000", "RED")))
    ]
    return fig


def remover_marcos(fig: go.Figure, er: bool = True, espin: bool = True) -> go.Figure:
    """Remove os marcos desligados: `er=False` tira as ERs, `espin=False` tira a faixa ESPIN."""
    if not er:
        remover_marcos_er(fig)
    if not espin:
        remover_faixa_espin(fig)
    return fig
