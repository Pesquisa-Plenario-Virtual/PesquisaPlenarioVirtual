"""Testes de pages/sustentacao/plots.py — marcos temporais (ER 51/52/53).

_marcos_temporais só deve desenhar cada marcador ER quando a data da emenda
cai dentro do intervalo de anos efetivamente plotado — não sob a suposição
fixa (e falsa) de que o dataset cobre só 2020–2025.
"""
import pandas as pd

from pages.sustentacao.plots import gs3_sust_anual_filtravel


def _df_fake(anos: list[int]) -> pd.DataFrame:
    rows = []
    for ano in anos:
        for teve in (True, False):
            rows.append({"ano": ano, "ambiente": "Plenário Virtual", "teve_sustentacao": teve})
    return pd.DataFrame(rows)


def test_periodo_2016_2025_carrega_er_51_52_53():
    fig = gs3_sust_anual_filtravel(_df_fake(list(range(2016, 2026))))
    ann_texts = " ".join(a.text for a in fig.layout.annotations)
    assert "ER 51" in ann_texts
    assert "ER 52" in ann_texts
    assert "ER 53" in ann_texts


def test_recorte_2021_2022_nao_carrega_nenhum_er():
    fig = gs3_sust_anual_filtravel(_df_fake([2021, 2022]))
    ann_texts = " ".join(a.text for a in fig.layout.annotations)
    assert "ER 51" not in ann_texts
    assert "ER 52" not in ann_texts
    assert "ER 53" not in ann_texts


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
