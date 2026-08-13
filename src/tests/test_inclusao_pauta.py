"""Testes do extrator de tipo de questão do pipeline.

Primeira cobertura de `src/`. O pipeline produz todos os números do dashboard e
até aqui não tinha teste nenhum — foi por isso que um bug de regex no extrator
de sufixo virou uma tabela de 72 linhas remendada dentro do app em vez de uma
correção na origem.

Convenção igual à dos treze arquivos de teste do app: `assert` puro, sem
framework, bloco `__main__` com descoberta automática.

Rodar: `PYTHONPATH=. .venv/bin/python src/tests/test_inclusao_pauta.py`
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

from src.inclusao_pauta import classificar_tipo_questao, extrair_sufixo

CASOS = Path(__file__).with_name("casos_sufixo_nao_extraido.csv")


def _classifica(complemento: str) -> str:
    return classificar_tipo_questao(extrair_sufixo(complemento))


# ── Comportamento já conhecido, para provar que o arranjo roda ────────────────


def test_sufixo_recursal_vira_rc():
    assert classificar_tipo_questao("ADI-ED") == "RC"
    assert classificar_tipo_questao("ADPF-AgR") == "RC"
    assert classificar_tipo_questao("ADI-ED-segundos") == "RC"


def test_sem_sufixo_e_principal():
    assert classificar_tipo_questao("ADI") == "PR"
    assert classificar_tipo_questao("ADPF") == "PR"


def test_sufixo_incidental_vira_ij():
    assert classificar_tipo_questao("ADI-MC") == "IJ"
    assert classificar_tipo_questao("ADI-MC-Ref") == "IJ"
    assert classificar_tipo_questao("ADI-QO") == "IJ"


def test_entrada_invalida_nao_levanta():
    for v in (None, 123, [], ""):
        assert isinstance(classificar_tipo_questao(v), str)


def test_complemento_terminado_em_ponto_ja_funcionava():
    """Formato que o regex original reconhecia — não pode regredir."""
    assert _classifica("Julgamento Virtual: ADI-ED.") == "RC"
    assert _classifica("Julgamento Virtual: ADI.") == "PR"


# ── Os 72 casos que motivaram o remendo ───────────────────────────────────────


def test_casos_reais_de_sufixo_nao_extraido():
    """As 72 linhas que viviam num CSV dentro do app, agora como corpus.

    Todas têm o sufixo recursal presente no texto do andamento e seguido de
    " - " em vez de ponto. O regex original exigia `.` ou `{` como terminador,
    então devolvia None e o recurso era contado como processo principal.
    """
    with CASOS.open(encoding="utf-8") as f:
        linhas = list(csv.DictReader(f))

    assert len(linhas) == 72, f"esperado 72 casos, veio {len(linhas)}"

    erros = []
    for linha in linhas:
        obtido = _classifica(linha["and_complemento"])
        esperado = linha["tipo_questao_corrigido"]
        if obtido != esperado:
            erros.append(f'{linha["and_complemento"][:60]!r}: {obtido} != {esperado}')
    assert not erros, f"{len(erros)} de {len(linhas)} classificados errado:\n  " + "\n  ".join(erros[:10])


# ── Alcance da correção sobre o dado real ─────────────────────────────────────

_ANDAMENTOS = Path(__file__).resolve().parents[2] / "data" / "interim" / "dim_andamentos.parquet"


_REGEX_ANTIGO = re.compile(
    r'Julgamento Virtual:\s*([A-Z]{2,5})([\-\s][A-Za-z][\w\-]*)?\s*[\.{]'
)


def _classifica_com_regex_antigo(complemento: str) -> str:
    """Reproduz o extrator antes da correção, para medir o ganho."""
    m = _REGEX_ANTIGO.search(complemento or "")
    if not m:
        return "Não identificado"
    classe, sufixo = m.group(1), (m.group(2) or "").strip(" -")
    return classificar_tipo_questao(f"{classe}-{sufixo}" if sufixo else classe)


def test_alcance_da_correcao_no_dado_real():
    """Mede o ganho contra o extrator antigo, na mesma população.

    Afirma a relação, não um total absoluto: toda mudança tem que partir de
    "Não identificado". O extrator preenche lacuna; se passar a *alterar* uma
    resposta que já tinha, virou outra coisa e precisa de revisão humana.

    Um limiar absoluto não serve aqui — a maioria dos eventos com o texto
    "Julgamento Virtual" em dim_andamentos não é inclusão em pauta com sufixo
    de classe, então a taxa de "Não identificado" é alta por natureza.
    """
    if not _ANDAMENTOS.exists():
        print(f"  (pulado: {_ANDAMENTOS.name} não disponível)")
        return

    import pandas as pd

    a = pd.read_parquet(_ANDAMENTOS, columns=["and_complemento"])
    textos = a.loc[
        a["and_complemento"].astype(str).str.contains("Julgamento Virtual", na=False),
        "and_complemento",
    ]
    assert len(textos) > 10_000, f"amostra menor que o esperado: {len(textos)}"

    antes = textos.map(_classifica_com_regex_antigo)
    depois = textos.map(_classifica)
    mudaram = antes != depois

    assert mudaram.sum() > 0, "a correção do regex deixou de ter efeito"

    partiram_de_outra_coisa = antes[mudaram][antes[mudaram] != "Não identificado"]
    assert partiram_de_outra_coisa.empty, (
        "o extrator passou a ALTERAR classificações que já existiam, não só a "
        f"preencher lacuna: {partiram_de_outra_coisa.value_counts().to_dict()}"
    )


def test_extrator_nunca_muda_uma_resposta_que_ja_tinha():
    """Um sufixo já reconhecido não pode mudar de classificação.

    Guarda contra um regex mais permissivo capturar texto a mais e transformar,
    por exemplo, um PR legítimo em RC.
    """
    fixos = {
        "Julgamento Virtual: ADI.": "PR",
        "Julgamento Virtual: ADPF.": "PR",
        "Julgamento Virtual: ADI-ED.": "RC",
        "Julgamento Virtual: ADI-MC.": "IJ",
        "Julgamento Virtual: ADI - Agendado para: 01/01/2020.": "PR",
        "Julgamento Virtual: ADI-AgR - Agendado para: 01/01/2020.": "RC",
    }
    for texto, esperado in fixos.items():
        assert _classifica(texto) == esperado, f"{texto!r} -> {_classifica(texto)}, esperado {esperado}"


if __name__ == "__main__":
    for _nome, _fn in sorted(globals().items()):
        if _nome.startswith("test_"):
            _fn()
    print("ok")
