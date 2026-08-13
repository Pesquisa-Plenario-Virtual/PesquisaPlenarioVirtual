"""Trava o parâmetro morto de voltar (P1) e a regra do balde não concluído (P2).

P1: `proporcao` era aceito e ignorado em g22/g26 — o toggle de escala do
catálogo (percentual=True) não fazia nada. Aqui alternar `proporcao` TEM que
mudar os valores dos traces.
P2: `excluir_nc` remove o balde "4 - Não concluído (bloco)" produzido por
`_categoria_desfecho`, nunca filtrando a string de desfecho.
"""
import pandas as pd

from pages.inclusoes.plots import g22_cat_periodo_filtravel, g26_cat_tipo_periodo_filtravel
from pages.inclusoes.plots import _prep_cat, _sem_nao_concluido


def _df_fake() -> pd.DataFrame:
    desfechos = [
        "Concluído - decisão unânime",
        "Concluído - decisão maioria com o relator",
        "Concluído - decisão maioria, vencido o relator",
        "Não concluído - motivos diversos",
    ]
    return pd.DataFrame({
        "ano": 2016,
        "ambiente": "Plenário Virtual",
        "tipo_questao": ["PR", "RC", "PR", "RC"],
        "desfecho": desfechos,
    })


def _xs(fig):
    return [round(float(t.x[0]), 1) for t in fig.data if hasattr(t, "x")]


def test_proporcao_alterna_eixo_x_em_g22():
    df = _df_fake()
    absoluto = g22_cat_periodo_filtravel(df, show_values=False, proporcao=False)
    percentual = g22_cat_periodo_filtravel(df, show_values=False, proporcao=True)
    xs_abs = _xs(absoluto)
    xs_pct = _xs(percentual)
    assert xs_abs == [1.0]
    assert xs_pct == [25.0]
    assert xs_abs != xs_pct


def test_proporcao_alterna_eixo_x_em_g26():
    df = _df_fake()
    absoluto = g26_cat_tipo_periodo_filtravel(df, show_values=False, proporcao=False)
    percentual = g26_cat_tipo_periodo_filtravel(df, show_values=False, proporcao=True)
    assert len(absoluto) == len(percentual) == 2
    for fig_abs, fig_pct in zip(absoluto, percentual):
        assert _xs(fig_abs) != _xs(fig_pct)


def test_excluir_nc_tira_balde_mas_nao_filtra_por_string():
    df = _df_fake()
    prep = _prep_cat(df)
    sem = _sem_nao_concluido(prep)
    assert "4 - Não concluído (bloco)" not in set(sem["categoria"])
    assert "Não concluído - motivos diversos" in set(df["desfecho"])  # dado bruto intocado

    fig = g22_cat_periodo_filtravel(df, excluir_nc=True, show_values=False)
    rotulos = [lbl for t in fig.data if hasattr(t, "y") for lbl in (t.y or [])]
    assert len(rotulos) == 3
    assert "4 - Não concluído (bloco)" not in rotulos

    figuras = g26_cat_tipo_periodo_filtravel(df, excluir_nc=True, show_values=False)
    assert len(figuras) == 2
    for f in figuras:
        assert "4 - Não concluído (bloco)" not in [lbl for t in f.data if hasattr(t, "y") for lbl in (t.y or [])]


from pages.inclusoes.plots import g7a_desfechos_pp_2009_2019

def test_7a_recorta_pp_2009_2019_e_sai_em_percentual():
    """7.a — só Plenário Presencial, só 2009–2019, só concluído, eixo X em %.

    O recorte do período e do âmbito acontece por dentro da função (período
    fixo), então o teste usa o dado real recortado na própria chamada — o mesmo
    recorte que o catálogo declararia se pudesse.

    A fixture usa "Plenário Presencial" porque é o que `load_inclusoes_em_pauta`
    entrega: o loader renomeia "Plenário Físico" na carga. Antes esta fixture
    usava o nome cru e por isso passava enquanto o gráfico saía vazio no app —
    o teste validava um dado que a produção nunca vê.
    """
    df = pd.DataFrame({
        "ano": [2009, 2009, 2009, 2009, 2010, 2010, 2010, 2010,
                2011, 2011, 2011, 2011, 2012, 2012, 2012, 2012],
        "ambiente": "Plenário Presencial",
        "tipo_questao": ["PR"] * 16,
        "desfecho": [
            "Concluído - decisão unânime",
            "Concluído - decisão maioria com o relator",
            "Concluído - decisão maioria, vencido o relator",
            "Não concluído - motivos diversos",
        ] * 4,
    })

    fig = g7a_desfechos_pp_2009_2019(df, show_values=False)
    series = {t.name: t for t in fig.data if hasattr(t, "name")}

    # uma série por categoria concluída; anos dentro do recorte fixo
    assert set(series) == {"1 - Unânime", "2 - Maioria (relator vencedor)", "3 - Maioria (relator vencido)"}
    anos = {int(v) for t in fig.data for v in (list(t.x) if t.x is not None else [])}
    assert anos <= {2009, 2010, 2011, 2012}

    # em percentual: cada ano soma ~100 nas três categorias concluídas
    por_ano: dict[int, float] = {}
    for c, t in series.items():
        for a, v in zip(t.x, t.y):
            por_ano[int(a)] = por_ano.get(int(a), 0.0) + float(v)
    assert set(por_ano) == {2009, 2010, 2011, 2012}
    for v in por_ano.values():
        assert abs(v - 100.0) < 0.2, v


from pages.inclusoes.plots import g7b_unanimidade_vs_divergencia_2010_2025


def test_7b_recorta_2010_2025_ambos_e_exclui_er_53():
    """7.b — 2010–2025, PP+PV juntos, e marcos ER 51/52 sem o ER 53.

    Os marcos só aparecem se o ano da ER cair no intervalo plotado, então o
    fake cobre 2016–2021 (ER 51=2016, ER 52=2019, ER 53=2020).
    """
    anos = [2016, 2017, 2018, 2019, 2020, 2021]
    df = pd.DataFrame({
        "ano": anos,
        "ambiente": "Plenário Virtual",
        "tipo_questao": ["PR"] * len(anos),
        "desfecho": [
            "Concluído - decisão unânime",
            "Concluído - decisão maioria com o relator",
            "Concluído - decisão maioria, vencido o relator",
            "Concluído - decisão unânime",
            "Concluído - decisão maioria, vencido o relator",
            "Não concluído - motivos diversos",
        ],
    })

    fig = g7b_unanimidade_vs_divergencia_2010_2025(df, show_values=False)
    series = {t.name for t in fig.data if hasattr(t, "name")}
    assert series == {"Unânime", "Divergência"}

    textos = [a.text or "" for a in fig.layout.annotations]
    assert any("ER 51" in t for t in textos)
    assert any("ER 52" in t for t in textos)
    assert not any("ER 53" in t for t in textos)


if __name__ == "__main__":
    for _nome, _fn in sorted(globals().items()):
        if _nome.startswith("test_"):
            _fn()
    print("ok")
