"""Testes da janela de casamento pauta -> decisão (`_classificar_desfechos`).

Motivo: para o Plenário Físico, a janela era curta (3-7 dias) e não sabia de
julgamento suspenso (`ANDAMENTOS_ADIAMENTO` existia mas nunca era consultada).
Decisão por maioria demora mais para sair que decisão unânime, então mais
maioria caía fora da janela — víes artificial para unanimidade em anos com
poucos casos concluídos (ex.: Plenário Físico, 2012-2015). Havia também um
off-by-one: decisão que cai exatamente no último dia da janela era descartada
(`<` em vez de `<=`).

Convenção igual aos outros arquivos de teste: `assert` puro, sem framework.

Rodar: `PYTHONPATH=. .venv/bin/python src/tests/test_janela_desfecho.py`
"""

from __future__ import annotations

import pandas as pd

from src.inclusao_pauta import (
    ANDAMENTOS_PAUTA,
    ANDAMENTOS_RETIRADA_FISICO,
    DESTAQUE_NOMES_FISICO,
    _classificar_desfechos,
)

RETIRADA = ANDAMENTOS_RETIRADA_FISICO
DESTAQUE = DESTAQUE_NOMES_FISICO


def _dt(s: str) -> pd.Timestamp:
    return pd.to_datetime(s, dayfirst=True)


def _pauta_df(incidente: int, and_data: str, fim_janela: str, dec_ref: str | None = None) -> pd.DataFrame:
    return pd.DataFrame([{
        "incidente": incidente,
        "and_data_dt": _dt(and_data),
        "and_index": 1,
        "fim_janela": _dt(fim_janela),
        "dec_ref": _dt(dec_ref or and_data),
    }])


_COLS_ANDAMENTOS = ["incidente", "and_data_dt", "and_index", "and_nome", "and_complemento"]
_COLS_DECISOES = ["incidente", "dec_data_dt", "dec_complemento"]


def _andamentos_df(rows: list[tuple[int, str, str, str]]) -> pd.DataFrame:
    """rows: (incidente, and_data, and_nome, and_complemento)."""
    if not rows:
        return pd.DataFrame(columns=_COLS_ANDAMENTOS)
    return pd.DataFrame([{
        "incidente": inc, "and_data_dt": _dt(data), "and_index": idx + 2,
        "and_nome": nome, "and_complemento": comp,
    } for idx, (inc, data, nome, comp) in enumerate(rows)])


def _decisoes_df(rows: list[tuple[int, str, str]]) -> pd.DataFrame:
    """rows: (incidente, dec_data, dec_complemento)."""
    if not rows:
        return pd.DataFrame(columns=_COLS_DECISOES)
    return pd.DataFrame([{
        "incidente": inc, "dec_data_dt": _dt(data), "dec_complemento": comp,
    } for inc, data, comp in rows])


def _classifica(pauta_df, and_df, dec_df) -> str:
    r = _classificar_desfechos(pauta_df, and_df, dec_df, RETIRADA, DESTAQUE)
    return r.iloc[0]["desfecho"]


# ── Off-by-one: decisão exatamente no fim da janela ────────────────────────
# Caso real: incidente 3927030, pauta 04/05/2015 ("Pleno em 04/05/2015" ->
# fim_janela = 07/05/2015), decisão "por maioria... vencido o Ministro Marco
# Aurélio" no próprio 07/05/2015 — perdida hoje por `<` estrito.


def test_decisao_no_ultimo_dia_da_janela_e_contada():
    pauta = _pauta_df(3927030, "04/05/2015", "07/05/2015")
    andamentos = _andamentos_df([])
    decisoes = _decisoes_df([
        (3927030, "07/05/2015",
         "Decisão: O Tribunal, por maioria e nos termos do voto da Relatora, "
         "conheceu e negou provimento ao agravo regimental, vencido o Ministro "
         "Marco Aurélio."),
    ])
    assert _classifica(pauta, andamentos, decisoes) == \
        "Concluído - decisão maioria com o relator"


# ── Adiamento estende a janela e pega a decisão por maioria ────────────────
# Caso real: incidente 4125637, pauta 30/01/2012 ("Apresentado em mesa para
# julgamento", sem data explícita -> fallback 7 dias, fim_janela 06/02/2012),
# "Suspenso o julgamento" em 02/02/2012 (dentro da janela original), decisão
# por maioria em 09/02/2012 (fora da janela original de 7 dias, hoje perdida).


def test_adiamento_estende_janela_e_pega_decisao_maioria():
    pauta = _pauta_df(4125637, "30/01/2012", "06/02/2012")
    andamentos = _andamentos_df([
        (4125637, "02/02/2012", "Suspenso o julgamento", ""),
    ])
    decisoes = _decisoes_df([
        (4125637, "09/02/2012",
         "NA SESSÃO DO PLENÁRIO DE 8.2.2012 - Decisão: Em continuidade ao "
         "julgamento, o Tribunal, por maioria, quanto aos parágrafos, negou "
         "provimento, vencido o Ministro Marco Aurélio."),
    ])
    assert _classifica(pauta, andamentos, decisoes) == \
        "Concluído - decisão maioria com o relator"


# ── Sem adiamento, a janela NÃO é estendida ─────────────────────────────────


def test_sem_adiamento_janela_nao_estende():
    pauta = _pauta_df(1, "01/01/2020", "08/01/2020")  # fallback 7d
    andamentos = _andamentos_df([])
    decisoes = _decisoes_df([
        (1, "21/01/2020",
         "Decisão: O Tribunal, por maioria e nos termos do voto do Relator, "
         "negou provimento, vencido o Ministro X."),
    ])
    assert _classifica(pauta, andamentos, decisoes) == "Não concluído - motivos diversos"


# ── Teto de 180 dias: adiamento não estica a janela indefinidamente ────────


def test_adiamento_respeita_teto_de_180_dias():
    pauta = _pauta_df(2, "01/01/2020", "08/01/2020")
    andamentos = _andamentos_df([
        (2, "05/01/2020", "Suspenso o julgamento", ""),
    ])
    decisoes = _decisoes_df([
        (2, "25/07/2020",  # > 180 dias da inclusão
         "Decisão: O Tribunal, por maioria, negou provimento, vencido o "
         "Ministro X."),
    ])
    assert _classifica(pauta, andamentos, decisoes) == "Não concluído - motivos diversos"


# ── Reentrada em pauta fecha a janela estendida ─────────────────────────────


def test_reentrada_em_pauta_fecha_janela_estendida():
    assert ANDAMENTOS_PAUTA, "lista de andamentos de pauta não pode estar vazia"
    nome_reentrada = ANDAMENTOS_PAUTA[0]
    pauta = _pauta_df(3, "01/01/2020", "08/01/2020")
    andamentos = _andamentos_df([
        (3, "05/01/2020", "Suspenso o julgamento", ""),
        (3, "01/02/2020", nome_reentrada, ""),  # novo ciclo de pauta
    ])
    decisoes = _decisoes_df([
        (3, "15/02/2020",  # depois da reentrada, não pertence a este ciclo
         "Decisão: O Tribunal, por maioria, negou provimento, vencido o "
         "Ministro X."),
    ])
    assert _classifica(pauta, andamentos, decisoes) == "Não concluído - motivos diversos"


if __name__ == "__main__":
    for _nome, _fn in sorted(globals().items()):
        if _nome.startswith("test_"):
            _fn()
    print("ok")
