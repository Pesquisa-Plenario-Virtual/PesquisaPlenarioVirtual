"""Posição dos marcadores ER/ESPIN nas fronteiras entre anos.

ER 51/2016 já vale no próprio 2016 (fronteira 2015/2016); ER 52/2019 e
ER 53/2020 valem só no ano seguinte à edição (fronteiras 2018/2019 e
2019/2020), e a faixa ESPIN vai da fronteira 2019/2020 à 2022/2023. Num
eixo de anos absolutos a fronteira N/N+1 vale N + 0.5; num eixo categórico
vale (N − base) + 0.5.
"""
import plotly.graph_objects as go

from visual.base import (
    PRETO,
    VERMELHO,
    add_er_marker,
    add_espin_shade,
    remover_faixa_espin,
    remover_marcos_er,
)


def _lines(fig):
    return sorted(round(float(s.x0), 2) for s in fig.layout.shapes if s.type == "line")


def _vrect(fig):
    return [(round(float(s.x0), 2), round(float(s.x1), 2))
            for s in fig.layout.shapes if s.type == "rect"]


def test_marcadores_em_fronteiras_eixo_numerico():
    fig = go.Figure()
    for er in (51, 52, 53):
        add_er_marker(fig, 0, er, 0, 100, 110)
    add_espin_shade(fig, 0, 0, 100)
    assert _lines(fig) == [2015.5, 2018.5, 2019.5, 2019.56, 2022.5]
    assert _vrect(fig) == [(2019.5, 2022.5)]
    labels = {a.text: round(float(a.x), 1) for a in fig.layout.annotations}
    assert labels["<b>ER 51</b>"] == 2015.5
    assert labels["<b>ER 52</b>"] == 2018.5
    assert labels["<b>ER 53</b>"] == 2019.5
    assert labels["<b>ESPIN</b>"] == 2021.0
    # seta dupla percorre a faixa (da linha inicial à final), sobre as linhas vermelhas
    setas = [a for a in fig.layout.annotations if a.showarrow]
    assert len(setas) == 2
    for a in setas:
        assert round(float(a.ay), 1) == round(float(a.y), 1)  # seta na horizontal
    # linhas vermelhas (ESPIN) mais baixas que as pretas (ER)
    alturas = {s.line.color: {round(float(s.y1), 1)} for s in fig.layout.shapes if s.type == "line"}
    assert alturas[PRETO] == {100.0}
    assert alturas[VERMELHO] == {95.0}


def test_marcadores_em_fronteiras_eixo_categorico():
    fig = go.Figure()
    add_er_marker(fig, 2020, 53, 0, 100, 110)
    add_espin_shade(fig, 2020, 0, 100)
    assert _lines(fig) == [-0.5, -0.44, 2.5]
    assert _vrect(fig) == [(-0.5, 2.5)]
    labels = {a.text: round(float(a.x), 1) for a in fig.layout.annotations}
    assert labels["<b>ER 53</b>"] == -0.5
    assert labels["<b>ESPIN</b>"] == 1.0


def test_remocao_por_assinatura_nao_atinge_elementos_legitimos():
    fig = go.Figure()
    add_er_marker(fig, 0, 53, 0, 100, 110)
    add_espin_shade(fig, 0, 0, 100)
    fig.add_shape(type="line", x0=2000, x1=2001, y0=0, y1=50,
                  line=dict(color="#3498db", width=3))
    fig.add_annotation(x=2000, y=10, text="Rótulo comum", showarrow=False)

    remover_marcos_er(fig)
    assert all(not (s.type == "line"
                    and str(getattr(getattr(s, "line", None), "dash", None) or "").lower() == "dash"
                    and str(getattr(getattr(s, "line", None), "color", None) or "").upper()
                    in ("#000000", "BLACK")) for s in fig.layout.shapes)
    assert not any((a.text or "").startswith("<b>ER") for a in fig.layout.annotations)
    # elementos legítimos intactos
    assert any(s.type == "line" and not (s.line.dash or "")
               for s in fig.layout.shapes)
    assert any(a.text == "Rótulo comum" for a in fig.layout.annotations)

    remover_faixa_espin(fig)
    assert not any(s.type == "rect" and str(s.fillcolor or "").upper() == "#FCE7F3"
                   for s in fig.layout.shapes)
    assert not any(s.type == "line"
                   and str(getattr(getattr(s, "line", None), "dash", None) or "").lower() == "dash"
                   and str(getattr(getattr(s, "line", None), "color", None) or "").upper()
                   in ("#C00000", "RED") for s in fig.layout.shapes)
    assert not any("ESPIN" in (a.text or "") or (a.showarrow and str(a.arrowcolor or "").upper() == "#C00000")
                   for a in fig.layout.annotations)
    # ainda restam só o que não é marco
    assert len(fig.layout.shapes) == 1
    assert len(fig.layout.annotations) == 1


if __name__ == "__main__":
    for _nome, _fn in sorted(globals().items()):
        if _nome.startswith("test_"):
            _fn()
    print("ok")
