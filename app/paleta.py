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
