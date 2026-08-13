"""Testes de pages/sessoes_virtuais/plots.py.

prep_duracao usa o âmbito para filtrar df_final (a primeira pauta) — troca de
âmbito muda o resultado de verdade (ver task-15-report.md). Isso só é visível
na UI porque GraficoSpec.opcoes_filtro (components/grafico.py) e o pulo do
pré-filtro por "ambiente" em render_grafico deixam o seletor alcançar
"Plenário Presencial" mesmo com df_s (sessões) só tendo "Plenário Virtual".
Este teste roda contra os parquets reais (via dados.loader, como a própria
página faz) e afirma só a relação qualitativa — PP com mediana bem maior e
menos processos que PV — não os números de hoje, para não quebrar numa
atualização normal da base.
"""
import pandas as pd

from dados.loader import load_sessoes_virtuais, load_inclusoes_em_pauta
from pages.sessoes_virtuais.plots import prep_duracao


def _dados():
    df_s = load_sessoes_virtuais().copy()
    df_s["tipo_questao"] = df_s["tipo_questao"].replace({"IJ": "QI"})
    df_s["data_sessao_dt"] = pd.to_datetime(df_s["data_sessao_dt"])
    df_final = load_inclusoes_em_pauta()
    return df_s, df_final


def test_ambiente_muda_o_resultado_de_prep_duracao():
    df_s, df_final = _dados()
    pv = prep_duracao(df_s, df_final, "Plenário Virtual")
    pp = prep_duracao(df_s, df_final, "Plenário Presencial")

    assert not pv.empty and not pp.empty
    # PP soma processos que já tramitavam fisicamente antes de ir a virtual —
    # bem menos frequente do que já nascer no PV.
    assert len(pp) < len(pv)
    # A distância entre a primeira pauta física e a conclusão virtual é
    # sistematicamente maior do que quando as duas etapas já ocorrem no PV.
    assert pp["dias"].median() > pv["dias"].median() * 5


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
