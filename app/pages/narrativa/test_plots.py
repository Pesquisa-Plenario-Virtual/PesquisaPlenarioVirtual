"""Testes de pages/narrativa/plots.py — portão de regressão dos 12 números publicados.

Os 6 gráficos de Narrativa (NA-NF) recalculam, a partir de inclusoes_em_pauta.parquet
(via dados.loader, como a página faz), achados já publicados — ver
.superpowers/sdd/2026-08-09-fase1-motor-estilo-casca-grafico/task-18-brief.md, Passo 1.

Ao contrário do smoke test usual, aqui os valores exatos IMPORTAM: o objetivo deste
teste é justamente detectar se uma mudança na base desloca algum dos 12 números
além de 0,1 ponto percentual — isso é regressão real, não ruído a ser tolerado.
"""
import pandas as pd

from dados.loader import load_inclusoes_em_pauta
from pages.narrativa.plots import plot_na, plot_nb, plot_nc, plot_nd, plot_ne, plot_nf

TOL = 0.1  # ponto percentual


def _df() -> pd.DataFrame:
    df = load_inclusoes_em_pauta()
    return df[df["ano"].between(2020, 2025)]


def _valores(fig, trace_idx=0):
    return list(fig.data[trace_idx].y)


def test_na_participacao_anual():
    fig = plot_na(_df())
    publicado = [59.8, 68.0, 64.1, 66.8, 59.0, 66.6]
    calculado = _valores(fig)
    assert len(calculado) == len(publicado)
    for pub, calc in zip(publicado, calculado):
        assert abs(pub - calc) <= TOL


def test_nb_pauta_vs_concluidos():
    fig = plot_nb(_df())
    pauta, concluidos = _valores(fig)
    assert abs(pauta - 63.9) <= TOL
    assert abs(concluidos - 91.3) <= TOL


def test_nc_tramitacao_por_ambiente():
    fig = plot_nc(_df())
    pp, ambos, pv = _valores(fig)
    assert abs(pp - 5.6) <= TOL
    assert abs(ambos - 16.9) <= TOL
    assert abs(pv - 77.5) <= TOL


def test_nd_destino_recursos():
    fig = plot_nd(_df())
    pv_pct = fig.data[0].y[0]
    pp_pct = fig.data[1].y[0]
    assert abs(pv_pct - 94.3) <= TOL
    assert abs(pp_pct - 5.7) <= TOL


def test_ne_media_inclusoes_por_processo():
    fig = plot_ne(_df())
    pv, pp = _valores(fig)
    assert abs(pv - 1.8) <= TOL
    assert abs(pp - 4.3) <= TOL


def test_nf_pct_concluidos_por_processo():
    fig = plot_nf(_df())
    pv, pp = _valores(fig)
    assert abs(pv - 86.0) <= TOL
    assert abs(pp - 39.2) <= TOL


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
