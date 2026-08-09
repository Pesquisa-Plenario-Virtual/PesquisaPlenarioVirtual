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
}

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
    if par is None:
        par = _RESERVA[sum(canon.encode("utf-8")) % len(_RESERVA)]
    return par[1] if dark else par[0]


def cores(nomes, dark: bool = False) -> dict[str, str]:
    """Mapa {rótulo canônico: cor} para uma lista de valores."""
    return {canonico(n): cor(n, dark) for n in nomes}
