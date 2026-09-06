"""Trava a extração de vencidos e a reclassificação "sem Marco Aurélio".

Textos são recortes reais de `dim_decisoes.dec_complemento`.

Convenção igual a test_filters.py: assert puro, sem framework, bloco __main__.
Rodar: PYTHONPATH=app .venv/bin/python app/dados/test_divergencia.py
"""

from __future__ import annotations

import pandas as pd

from dados.divergencia import (
    anexar_desfecho_sem_ministro,
    extrair_vencidos,
    reclassificar_desfecho,
    relator_no_texto,
)

MAIORIA_REL = "Concluído - decisão maioria com o relator"
MAIORIA_VENC = "Concluído - decisão maioria, vencido o relator"
UNANIME = "Concluído - decisão unânime"


# ── extrair_vencidos ─────────────────────────────────────────────────────────

def test_um_vencido_singular():
    t = ("Decisão: O Tribunal, por maioria, conheceu da ação para julgá-la "
         "procedente, nos termos do voto do Relator, vencido o Ministro Marco "
         "Aurélio. Não participou deste julgamento o Ministro Celso de Mello. "
         "Plenário, Sessão Virtual de 16.8.2019 a 22.8.2019.")
    assert extrair_vencidos(t) == {"Marco Aurélio"}


def test_um_vencido_senhor_ministro():
    t = ("Decisão: O Tribunal, por maioria e nos termos do voto do Relator, "
         "resolveu questão de ordem, vencido o Senhor Ministro Marco Aurélio. "
         "Votou o Presidente, Ministro Gilmar Mendes. Plenário, 26.08.2009.")
    assert extrair_vencidos(t) == {"Marco Aurélio"}


def test_dois_vencidos():
    t = ("nos termos do voto do Relator, vencidos os Senhores Ministros Menezes "
         "Direito e Marco Aurélio. Decisão dotada de efeito vinculante.")
    assert extrair_vencidos(t) == {"Menezes Direito", "Marco Aurélio"}


def test_vencidos_com_relator_e_lista():
    t = ("O Tribunal, por maioria, julgou procedente a ação, nos termos do voto "
         "do Ministro Edson Fachin, Redator para o acórdão, vencidos os Ministros "
         "Marco Aurélio (Relator), Cármen Lúcia e Celso de Mello. Falou o "
         "advogado. Plenário, Sessão Virtual de 2.10.2020 a 9.10.2020.")
    assert extrair_vencidos(t) == {"Marco Aurélio", "Cármen Lúcia", "Celso de Mello"}


def test_vencidos_em_parte_sem_marco_aurelio():
    t = ("julgou procedente o pedido, nos termos do voto do Relator, vencidos, "
         "em parte, os Ministros Edson Fachin (Relator), Alexandre de Moraes, "
         "Rosa Weber, Dias Toffoli e Celso de Mello. Presidiu o julgamento a "
         "Ministra Cármen Lúcia. Plenário, 1º.8.2018.")
    v = extrair_vencidos(t)
    assert "Marco Aurélio" not in v
    assert {"Edson Fachin", "Alexandre de Moraes", "Rosa Weber"} <= v


def test_vencido_o_relator_sem_nome():
    t = ("Decisão: O Tribunal, por maioria, negou provimento ao agravo "
         "regimental, vencido o relator. Plenário, 11.9.2019.")
    assert extrair_vencidos(t) == set()


def test_caixa_alta_dois_vencidos():
    t = ("O TRIBUNAL, POR MAIORIA, JULGOU PROCEDENTE A AÇÃO, VENCIDOS, O SENHOR "
         "MINISTRO MARCO AURÉLIO, QUE DECLARAVA A INCONSTITUCIONALIDADE DO CAPUT "
         "DO ART. 15, E O SENHOR MINISTRO SEPÚLVEDA PERTENCE, QUE DECLARAVA A "
         "INCONSTITUCIONALIDADE. VOTOU O PRESIDENTE.")
    v = extrair_vencidos(t)
    assert "Marco Aurélio" in {n.title() for n in v} or "MARCO AURÉLIO" in v


def test_texto_ausente():
    assert extrair_vencidos(None) == set()
    assert extrair_vencidos("") == set()


# ── relator_no_texto ─────────────────────────────────────────────────────────

def test_relator_detectado():
    assert relator_no_texto("vencidos os Ministros Marco Aurélio (Relator), Cármen Lúcia.")
    assert not relator_no_texto("vencido o Ministro Marco Aurélio, que indeferia.")


# ── reclassificar_desfecho ───────────────────────────────────────────────────

def test_marco_aurelio_sozinho_vira_unanime():
    assert reclassificar_desfecho(MAIORIA_REL, {"Marco Aurélio"}, False) == UNANIME


def test_marco_aurelio_com_outros_fica_maioria():
    assert reclassificar_desfecho(
        MAIORIA_REL, {"Marco Aurélio", "Dias Toffoli"}, False) == MAIORIA_REL


def test_sem_marco_aurelio_inalterado():
    assert reclassificar_desfecho(MAIORIA_REL, {"Dias Toffoli"}, False) == MAIORIA_REL


def test_marco_aurelio_relator_inalterado():
    assert reclassificar_desfecho(MAIORIA_VENC, {"Marco Aurélio"}, True) == MAIORIA_VENC


def test_nao_maioria_inalterado():
    assert reclassificar_desfecho(UNANIME, {"Marco Aurélio"}, False) == UNANIME
    assert reclassificar_desfecho(
        "Não concluído - pedido de vista", {"Marco Aurélio"}, False
    ) == "Não concluído - pedido de vista"


# ── anexar_desfecho_sem_ministro ─────────────────────────────────────────────

def test_anexa_coluna_e_reclassifica():
    df = pd.DataFrame({
        "incidente": [1, 2, 3],
        "data_inclusao_dt": pd.to_datetime(["2020-03-01", "2020-03-01", "2020-03-01"]),
        "desfecho": [MAIORIA_REL, MAIORIA_REL, UNANIME],
        "macro_desfecho": ["Concluído", "Concluído", "Concluído"],
    })
    dec = pd.DataFrame({
        "incidente": [1, 2],
        "dec_data": ["10/03/2020", "10/03/2020"],
        "dec_complemento": [
            "O Tribunal, por maioria, julgou procedente, vencido o Ministro Marco Aurélio.",
            "O Tribunal, por maioria, julgou procedente, vencidos os Ministros Marco Aurélio e Rosa Weber.",
        ],
    })
    out = anexar_desfecho_sem_ministro(df, dec)
    assert list(out["desfecho_sem_ma"]) == [UNANIME, MAIORIA_REL, UNANIME]
    assert list(out["desfecho"]) == [MAIORIA_REL, MAIORIA_REL, UNANIME]  # bruto intocado


def test_sem_decisoes_coluna_espelha_desfecho():
    df = pd.DataFrame({
        "incidente": [1],
        "data_inclusao_dt": pd.to_datetime(["2020-03-01"]),
        "desfecho": [MAIORIA_REL],
        "macro_desfecho": ["Concluído"],
    })
    out = anexar_desfecho_sem_ministro(df, pd.DataFrame())
    assert list(out["desfecho_sem_ma"]) == [MAIORIA_REL]


if __name__ == "__main__":
    for _nome, _fn in sorted(globals().items()):
        if _nome.startswith("test_"):
            _fn()
    print("ok")
