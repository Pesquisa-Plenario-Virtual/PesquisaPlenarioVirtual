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

from visual.base import br
from visual.paleta import canonico, conhecido, cor

FONTE = "Times New Roman, Times, serif"

TAMANHOS = {
    "titulo": 22,
    "subtitulo": 16,
    "eixo_titulo": 18,
    "tick": 16,
    "legenda": 16,
    "valor": 15,
    "anotacao": 14,
}

# Hex da paleta antiga (estilo.py) -> equivalente na paleta validada.
# estilo.py continua como está porque os Blocos Empíricos o importam e mantêm o
# visual original; a troca acontece só aqui, na camada que as oito páginas usam.
_EQUIVALENTE_LEGADO = {
    "#2563EB": "#2a78d6",  # AZUL
    "#93C5FD": "#86b6ef",  # AZUL_CLARO
    "#9CA3AF": "#898781",  # CINZA
    "#059669": "#1baf7a",  # VERDE
    "#7C3AED": "#4a3aa7",  # ROXO
    "#C00000": "#e34948",  # VERMELHO
}
_EQUIVALENTE_LEGADO_ESCURO = {
    "#2A78D6": "#3987e5",
    "#86B6EF": "#9ec5f4",
    "#1BAF7A": "#199e70",
    "#4A3AA7": "#9085e9",
    "#E34948": "#e66767",
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


def _fonte(size_key: str, dark: bool, escala: float = 1.0) -> dict:
    return dict(
        family=FONTE,
        size=round(TAMANHOS[size_key] * escala),
        color=TINTA_ESCURA if dark else TINTA_CLARA,
    )


def _normalizar_eixos(fig: go.Figure, dark: bool, escala: float = 1.0) -> None:
    """Tipografia, tamanho e tickangle=0 em todo eixo, inclusive subplots."""
    eixo_tick = _fonte("tick", dark, escala)
    eixo_titulo = _fonte("eixo_titulo", dark, escala)
    for chave in fig.layout:
        if not (chave.startswith("xaxis") or chave.startswith("yaxis")):
            continue
        eixo = fig.layout[chave]
        eixo.tickfont = eixo_tick
        eixo.title.font = eixo_titulo
        if chave.startswith("xaxis"):
            eixo.tickangle = 0


def _normalizar_traces(fig: go.Figure, dark: bool, escala: float = 1.0) -> None:
    """Nome canônico, textfont padronizado e cor semântica por nome de série.

    Só recolore o que está no vocabulário da paleta: uma série fora dele mantém
    a cor que a função de gráfico escolheu. Cor vetorial (uma por barra, como em
    acervo/plots.py) é preservada — recolorir destruiria a codificação.
    """
    valor = _fonte("valor", dark, escala)
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
        marker = getattr(tr, "marker", None)
        cor_atual = getattr(marker, "color", None) if marker is not None else None
        vetorial = hasattr(cor_atual, "__len__") and not isinstance(cor_atual, str)

        if nome and conhecido(nome):
            nova = cor(nome, dark)
        else:
            # Série sem nome, ou fora do vocabulário: não dá para recolorir pelo
            # significado. Ainda assim, se ela carrega um hex da paleta antiga de
            # estilo.py, trocar pelo equivalente novo — senão o dashboard fica com
            # dois azuis para o mesmo papel. estilo.py não pode mudar: os Blocos
            # Empíricos o importam e mantêm o visual original de propósito.
            nova = _EQUIVALENTE_LEGADO.get(str(cor_atual).upper()) if not vetorial else None
            if nova is None:
                linha = getattr(tr, "line", None)
                cor_linha = getattr(linha, "color", None) if linha is not None else None
                nova = _EQUIVALENTE_LEGADO.get(str(cor_linha).upper())
            if nova is not None and dark:
                nova = _EQUIVALENTE_LEGADO_ESCURO.get(str(nova).upper(), nova)
        if nova is None:
            continue

        if marker is not None and hasattr(marker, "color") and not vetorial:
            tr.marker.color = nova
        if hasattr(tr, "line") and tr.type in ("scatter", "scattergl") and not vetorial:
            tr.line.color = nova


# Só dígitos: uma string com ponto ou vírgula já foi formatada por quem a
# produziu, e "2.168" (milhar) é indistinguível de "2.168" (decimal) pela
# forma — reinterpretar viraria 2,2. Número cru chega como int/float.
_SO_NUMERO = re.compile(r"^-?\d+$")

# "63.9%" — percentual com ponto decimal. Aqui não há ambiguidade: antes do "%"
# o ponto só pode ser decimal, porque ninguém escreve milhar em percentual de
# um dígito. Uns gráficos produziam "63.9%" e outros "63,9%".
_PERCENTUAL_PONTO = re.compile(r"^(-?\d+)\.(\d+)(\s*%)$")


def texto_numerico_br(valor):
    """Rótulo de valor no padrão brasileiro, deixando o resto intacto.

    As páginas montam esse rótulo de três jeitos: já formatado com `estilo.br`
    (Acervo, T1), como `str(int(v))` sem separador (R7, R8) e como float cru
    para o Plotly formatar (a maioria). Daí uns gráficos mostrarem 2.168 e
    outros 4230. Aqui tudo converge para o mesmo padrão.

    Só toca no que é número puro: `"5,6%  (159 processos)"` e
    `"Plenário Virtual: 94,3% (1.048 recursos)"` passam batido.
    """
    if isinstance(valor, bool) or valor is None:
        return valor
    if isinstance(valor, str):
        texto = valor.strip()
        pct = _PERCENTUAL_PONTO.match(texto)
        if pct:
            inteiro, decimal, sufixo = pct.groups()
            return f"{br(float(inteiro), 0)},{decimal}{sufixo}"
        if not _SO_NUMERO.match(texto):
            return valor
        numero = float(texto)
    elif isinstance(valor, (int, float)):
        numero = float(valor)
    else:
        try:
            numero = float(valor)
        except (TypeError, ValueError):
            return valor
    if numero != numero:  # NaN
        return valor
    return br(numero, 0) if numero == int(numero) else br(numero, 1)


def _normalizar_texto_de_valor(fig: go.Figure) -> None:
    """Aplica o padrão brasileiro aos rótulos de valor de cada trace."""
    for tr in fig.data:
        texto = getattr(tr, "text", None)
        if texto is None:
            continue
        if isinstance(texto, str):
            tr.text = texto_numerico_br(texto)
        else:
            try:
                tr.text = [texto_numerico_br(v) for v in texto]
            except TypeError:
                continue


def _valores_numericos(fig: go.Figure, campo: str) -> list[float]:
    """Valores numéricos plotados num eixo. Dado categórico (strings) fica fora."""
    valores: list[float] = []
    for tr in fig.data:
        dados = getattr(tr, campo, None)
        if dados is None:
            continue
        for v in dados:
            if isinstance(v, bool) or isinstance(v, str):
                continue
            try:
                f = float(v)
            except (TypeError, ValueError):
                continue
            if f == f:  # descarta NaN
                valores.append(f)
    return valores


def _parece_ano(valores: list[float]) -> bool:
    """Eixo de ano, não de contagem: inteiros dentro de uma faixa plausível.

    Sem isso, agrupar milhar transformaria 2025 em '2.025'. Um eixo de contagem
    que por acaso caia todo entre 1900 e 2100 perderia o separador — perda
    pequena e reversível, muito melhor que estragar toda série anual.
    """
    return bool(valores) and all(1900 <= v <= 2100 and v == int(v) for v in valores)


def _normalizar_numeros(fig: go.Figure) -> None:
    """Milhar com ponto e decimal com vírgula, no padrão brasileiro.

    Sem isto o Plotly abrevia em SI e o eixo mostra '6k' e '8k' no lugar de
    6.000 e 8.000. `separators` também acerta o hover; `tickformat=","` liga o
    agrupamento sem forçar inteiro, então um eixo percentual continua com a
    casa decimal.
    """
    fig.update_layout(separators=",.")
    for chave in fig.layout:
        if not (chave.startswith("xaxis") or chave.startswith("yaxis")):
            continue
        eixo = fig.layout[chave]
        if eixo.tickformat:  # formato escolhido pelo gráfico manda
            continue
        valores = _valores_numericos(fig, "y" if chave.startswith("yaxis") else "x")
        if _parece_ano(valores):
            eixo.tickformat = "d"
            continue
        if valores and max(abs(v) for v in valores) >= 1000:
            eixo.tickformat = ","


def _normalizar_anotacoes(fig: go.Figure, dark: bool, escala: float = 1.0) -> None:
    anotacao = _fonte("anotacao", dark, escala)
    for ann in fig.layout.annotations:
        if ann.text:
            ann.text = limpar_html_de_fonte(ann.text)
        # a cor da anotação é semântica (ER preto, ESPIN vermelho) — preservar
        cor_original = ann.font.color
        ann.font = dict(family=FONTE, size=round(TAMANHOS["anotacao"] * escala),
                        color=cor_original or anotacao["color"])


# Rótulos de eixo que só repetem a dimensão que o próprio eixo já mostra
# (Ano no x, contagem no y). Removidos para plotagem minimalista; rótulos com
# "%" ou que nomeiam a categoria (Classe, Tipo de questão, Período) ficam.
_ROTULOS_CONTAGEM = {
    "Ano", "Processos", "Processos distintos", "Processos (incidentes distintos)",
    "Inclusões em pauta", "Inclusões", "Inclusões concluídas", "Inclusões por processo",
    "Inclusões com sustentação", "Inclusões com sustentação oral",
    "Inclusões com reajuste de voto", "Nº de processos", "Nº de processos concluídos",
    "Nº de sessões", "Nº de sessões por processo", "Quantidade",
}


def remover_tracinho_e_rotulos(fig: go.Figure) -> go.Figure:
    """Tira o tracinho do eixo x e rótulos de eixo redundantes.

    Aplica-se no ponto de render (não dentro de aplicar_tema) justamente para
    valer nos dois temas das páginas não-empíricas: o toggle "Visual empírico"
    devolve a figura intocada, e é lá que o usuário não quer ver o tracinho
    nem o "Ano"/"Processos distintos" repetidos.
    """
    for chave in fig.layout:
        if chave.startswith("xaxis"):
            fig.layout[chave].ticks = ""
        if not (chave.startswith("xaxis") or chave.startswith("yaxis")):
            continue
        if fig.layout[chave].title.text in _ROTULOS_CONTAGEM:
            fig.layout[chave].title.text = ""
    return fig


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


def aplicar_tema(fig: go.Figure, tema: str = "novo", dark: bool = False,
                 escala_fonte: float = 1.0) -> go.Figure:
    """Impõe o padrão visual da Pessoa 2 a uma figura já construída.

    tema="empirico" devolve a figura sem tocar em nada. `escala_fonte`
    multiplica TAMANHOS inteiro — opt-in por GraficoSpec.fonte_grande, não
    muda o padrão dos outros gráficos.
    """
    if tema == "empirico":
        return fig

    tinta = TINTA_ESCURA if dark else TINTA_CLARA
    fundo = FUNDO_ESCURO if dark else FUNDO_CLARO

    fig.update_layout(
        font=dict(family=FONTE, color=tinta),
        title_font=_fonte("titulo", dark, escala_fonte),
        legend_font=_fonte("legenda", dark, escala_fonte),
        paper_bgcolor=fundo,
        plot_bgcolor=fundo,
    )
    if fig.layout.title.text:
        fig.layout.title.text = limpar_html_de_fonte(fig.layout.title.text)
    _normalizar_eixos(fig, dark, escala_fonte)
    _normalizar_traces(fig, dark, escala_fonte)
    _normalizar_anotacoes(fig, dark, escala_fonte)
    _normalizar_texto_livre(fig)
    _normalizar_numeros(fig)
    _normalizar_texto_de_valor(fig)
    return fig


TIPOS = ("barra", "linha", "area", "barra_h")


def _e_vetor(c) -> bool:
    """Mesmo critério de _normalizar_traces: lista/tupla/array/Series é vetor,
    string não é."""
    return c is not None and not isinstance(c, str) and hasattr(c, "__len__")


def _cor_marker_bruta(tr):
    marker = getattr(tr, "marker", None)
    return getattr(marker, "color", None) if marker is not None else None


def _cor_vetor_uniforme(c) -> str | None:
    """Se `c` é vetor com um único valor distinto, devolve esse valor.

    Uma cor por barra onde todas as barras têm a mesma cor (ex.: I1, blindado
    contra o recolore de `_normalizar_traces` via cor vetorial) não perde nada
    virando linha/área — só cor por barra *diferente por barra* não converte.
    """
    if not _e_vetor(c):
        return None
    valores = {v for v in c if v is not None}
    return next(iter(valores)) if len(valores) == 1 else None


def _cor_do_trace(tr) -> str | None:
    c = _cor_marker_bruta(tr)
    if _e_vetor(c):
        return _cor_vetor_uniforme(c)
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
    forma de barra/linha/área) ou cor vetorial *não uniforme* (cor diferente
    por barra) pedida como linha/área, onde uma única linha não tem como
    carregar várias cores.
    """
    if tipo not in TIPOS or tipo == "barra" or not fig.data:
        return fig
    if any(not hasattr(tr, "x") or not hasattr(tr, "y") for tr in fig.data):
        return fig
    if tipo in ("linha", "area") and any(
        _e_vetor(_cor_marker_bruta(tr)) and _cor_vetor_uniforme(_cor_marker_bruta(tr)) is None
        for tr in fig.data
    ):
        return fig

    novos = []
    for i, tr in enumerate(fig.data):
        c = _cor_do_trace(tr)
        base = dict(x=tr.x, y=tr.y, name=tr.name, text=tr.text,
                    hovertemplate=tr.hovertemplate, legendgroup=tr.legendgroup,
                    showlegend=tr.showlegend)
        if tipo == "linha":
            # A linha em si só aceita uma cor (`c`, escalar); o marcador de
            # cada ponto pode manter a cor vetorial original — mesma regra do
            # barra_h logo abaixo, protege séries como I1 do recolore.
            bruta = _cor_marker_bruta(tr)
            marker_cor = bruta if _e_vetor(bruta) else c
            modo = "lines+markers+text" if tr.text is not None else "lines+markers"
            # Alterna posição do rótulo por série (top/bottom) pra não
            # sobrepor texto quando duas linhas passam perto uma da outra.
            posicao = "top center" if i % 2 == 0 else "bottom center"
            novos.append(go.Scatter(mode=modo,
                                    line=dict(color=c, width=2),
                                    marker=dict(color=marker_cor, size=8),
                                    textposition=posicao, **base))
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
