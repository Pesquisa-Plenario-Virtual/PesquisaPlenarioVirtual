"""Fonte única de rótulo e cor para as oito páginas não-empíricas.

Sem Plotly e sem Streamlit de propósito: é consumido por tema.py, pelos testes
e por qualquer notebook. Os Blocos Empíricos não usam este módulo.
"""

from __future__ import annotations

# Siglas que sobrevivem à normalização de caixa.
SIGLAS = frozenset({
    "ADI", "ADPF", "ADC", "ADO",
    "PV", "PP", "PR", "RC", "QI", "IJ",
    "ER", "ESPIN", "STF", "CC",
})

# Nome canônico -> apelidos aceitos (comparados em minúsculas).
_APELIDOS: dict[str, tuple[str, ...]] = {
    "Plenário Virtual":    ("plenário virtual", "plenario virtual", "pv"),
    "Plenário Presencial": ("plenário presencial", "plenário físico", "plenario fisico", "pp"),
    "Só Virtual":          ("só virtual", "so virtual", "virtual"),
    "Só Presencial":       ("só presencial", "só físico", "so fisico", "físico", "presencial"),
    "Ambos os ambientes":  ("ambos os ambientes", "ambos"),

    # Vocabulários derivados. As páginas rotulam as mesmas categorias de formas
    # diferentes ("1 - Unânime" em Inclusões, "Concluído - decisão unânime" no
    # dado). Sem estes apelidos o nome não casa com CORES e a cor antiga
    # sobrevive ao tema — foi assim que o dashboard acabou com dois azuis para
    # conceitos vizinhos. Estes mapeamentos são o que faz "mesma variável,
    # mesma cor" valer de verdade.
    "Concluído":     ("concluído", "concluídos", "concluido", "concluidos"),
    "Não concluído": ("não concluído", "não concluídos", "nao concluido",
                      "nao concluidos", "4 - não concluído (bloco)"),
    "Concluído - decisão unânime":                    ("1 - unânime",),
    "Concluído - decisão maioria com o relator":      ("2 - maioria (relator vencedor)",),
    "Concluído - decisão maioria, vencido o relator": ("3 - maioria (relator vencido)",),
    "Não concluído - pedido de vista":   ("1 - pedido de vista",),
    "Não concluído - destaque":          ("2 - destaque",),
    "Não concluído - retirado de pauta": ("3 - retirado de pauta",),
    "Não concluído - motivos diversos":  ("4 - motivos diversos",),
    "Com sustentação oral": ("com sustentação", "com sustentacao"),
    "Sem sustentação oral": ("sem sustentação", "sem sustentacao"),
    "Com reajuste de voto": ("com reajuste",),
    "Sem reajuste de voto": ("sem reajuste",),
    "1 sessão":    ("1 sessão", "1 sessao"),
    "2–3 sessões": ("2–3 sessões", "2-3 sessões", "2-3 sessoes"),
    "4–5 sessões": ("4–5 sessões", "4-5 sessões", "4-5 sessoes"),
    "6+ sessões":  ("6+ sessões", "6+ sessoes"),
    "Sessões virtuais":        ("sessões virtuais", "sessoes virtuais"),
    "Inclusões em pauta (PV)": ("inclusões em pauta (pv)", "inclusoes em pauta (pv)"),
}

# Rótulos que começam com "Total" são agregados de qualquer métrica
# ("Total geral (processos ativos)", "Total geral (processos baixados)", …).
# Todos recebem a cor de "Total" em vez de cada página inventar a sua.
_PREFIXO_AGREGADO = "total"

_MAPA_APELIDO = {ap: canon for canon, aps in _APELIDOS.items() for ap in aps}


def sentence_case(texto: str) -> str:
    """Caixa de frase preservando siglas: 'CONCLUÍDO' -> 'Concluído', 'ADI' -> 'ADI'."""
    if not texto:
        return texto
    palavras = [p if p.upper() in SIGLAS else p.lower() for p in texto.split(" ")]
    saida = " ".join(palavras)
    for i, ch in enumerate(saida):
        if ch.isalpha():
            return saida[:i] + ch.upper() + saida[i + 1:]
    return saida


def canonico(nome: str) -> str:
    """Rótulo de exibição de um valor. Apelido conhecido vira o canônico;
    o resto cai em sentence_case."""
    if nome is None:
        return ""
    texto = str(nome).strip()
    achado = _MAPA_APELIDO.get(texto.lower())
    if achado is not None:
        return achado
    return sentence_case(texto)


CINZA_OUTROS = "#898781"

# Rótulo canônico -> (cor no modo claro, cor no modo escuro).
# Validado com dataviz/scripts/validate_palette.js contra #ffffff e #0e1117.
# Não alterar sem revalidar — ver §4 da spec.
CORES: dict[str, tuple[str, str]] = {
    # Ambiente — a espinha da narrativa
    "Plenário Virtual":    ("#2a78d6", "#3987e5"),
    "Plenário Presencial": ("#eb6834", "#d95926"),
    # Tramitação — ecoa o par de ambiente
    "Só Virtual":         ("#2a78d6", "#3987e5"),
    "Ambos os ambientes": ("#1baf7a", "#199e70"),
    "Só Presencial":      ("#eb6834", "#d95926"),
    # Classe processual — aprovado na lista de pares adjacentes nos dois modos
    "ADI":  ("#2a78d6", "#3987e5"),
    "ADPF": ("#eb6834", "#d95926"),
    "ADC":  ("#1baf7a", "#199e70"),
    "ADO":  ("#eda100", "#c98500"),
    # Macro-desfecho — reusa o par de ambiente: azul decide, laranja trava
    "Concluído":     ("#2a78d6", "#3987e5"),
    "Não concluído": ("#eb6834", "#d95926"),
    # Desfecho detalhado — matiz é a família, tom é o degrau (ordenado por volume)
    "Concluído - decisão unânime":                   ("#184f95", "#184f95"),
    "Concluído - decisão maioria com o relator":     ("#2a78d6", "#3987e5"),
    "Concluído - decisão maioria, vencido o relator": ("#86b6ef", "#9ec5f4"),
    "Não concluído - motivos diversos":  ("#9c3d13", "#c9541d"),
    "Não concluído - retirado de pauta": ("#c9541d", "#eb6834"),
    "Não concluído - pedido de vista":   ("#eb6834", "#f5a184"),
    "Não concluído - destaque":          ("#f5a184", "#fac7b6"),
    # Tipo de questão
    "PR": ("#2a78d6", "#3987e5"),
    "RC": ("#eb6834", "#d95926"),
    "QI": ("#1baf7a", "#199e70"),
    # Binários — presença tem cor, ausência é cinza reservado
    "Com sustentação oral": ("#1baf7a", "#199e70"),
    "Com reajuste de voto": ("#1baf7a", "#199e70"),
    "Sem sustentação oral": (CINZA_OUTROS, CINZA_OUTROS),
    "Sem reajuste de voto": (CINZA_OUTROS, CINZA_OUTROS),
    # Série de decisão do item 6.b2 — agregação dos desfechos concluídos, na
    # família azul dos concluídos, contraste por tom: o consenso é o degrau
    # escuro, a divergência o claro. O item 6.b3 (Prevalência da
    # relatoria/divergência) usa cor local em inclusoes/plots.py
    # (CORES_MACRO_DESFECHO), fora da paleta validada — pedido explícito,
    # mesma cor do I12.
    "Julgamento por unanimidade":    ("#184f95", "#184f95"),
    "Julgamento com divergência(s)": ("#86b6ef", "#9ec5f4"),
    # Faixas de nº de sessões — rampa ordinal azul: são todas sessões virtuais,
    # então a família é a do Plenário Virtual e o tom cresce com a contagem.
    # Degraus da rampa sequencial azul documentada na §4 da spec, respeitando o
    # piso ordinal (nada mais claro que o degrau 250 no modo claro).
    # Revalidado como ordinal: luminância monotônica, contraste ≥ 2.11 com o
    # fundo e ordem mantida sob simulação de deuteranopia/protanopia/tritanopia
    # (distância adjacente ≥ 0.173, mesmo patamar dos pares aprovados).
    "1 sessão":     ("#184f95", "#184f95"),
    "2–3 sessões":  ("#256abf", "#3987e5"),
    "4–5 sessões":  ("#3987e5", "#6da7ec"),
    "6+ sessões":   ("#86b6ef", "#b7d3f6"),
    # Agregados. "Total" não é uma variável do domínio, é a soma das que são —
    # fica no azul da paleta para não introduzir um segundo azul no dashboard.
    "Total": ("#2a78d6", "#3987e5"),
    # Séries do G0, que contrapõe duas unidades de contagem no mesmo eixo.
    "Sessões virtuais":      ("#2a78d6", "#3987e5"),
    "Inclusões em pauta (PV)": ("#1baf7a", "#199e70"),
}

# Degraus de reserva para valores fora do vocabulário, atribuídos de forma
# determinística. Ordem validada como categórica na lista de pares adjacentes.
_RESERVA = (
    ("#4a3aa7", "#9085e9"),
    ("#e87ba4", "#d55181"),
    ("#008300", "#008300"),
    ("#e34948", "#e66767"),
)


def cor(nome: str, dark: bool = False) -> str:
    """Cor de um valor semântico. Desconhecido recebe um degrau de reserva fixo."""
    canon = canonico(nome)
    par = CORES.get(canon)
    if par is None and canon.lower().startswith(_PREFIXO_AGREGADO):
        par = CORES["Total"]
    if par is None:
        par = _RESERVA[sum(canon.encode("utf-8")) % len(_RESERVA)]
    return par[1] if dark else par[0]


def conhecido(nome: str) -> bool:
    """Se o nome tem cor própria na paleta — inclui apelidos e agregados.

    `tema.aplicar_tema` usa isto para decidir se recolore um trace: uma série
    fora do vocabulário mantém a cor que a função de gráfico escolheu.
    """
    canon = canonico(nome)
    return canon in CORES or canon.lower().startswith(_PREFIXO_AGREGADO)


def cores(nomes, dark: bool = False) -> dict[str, str]:
    """Mapa {rótulo canônico: cor} para uma lista de valores."""
    return {canonico(n): cor(n, dark) for n in nomes}
