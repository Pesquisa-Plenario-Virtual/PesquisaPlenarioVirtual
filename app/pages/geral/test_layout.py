"""Testes de pages/geral/layout.py — linha do tempo normativa.

_build_timeline_figure não toca em Streamlit (ao contrário de render_timeline,
que chama st.plotly_chart), então dá pra testar aplicar_tema em cima dela sem
depender de AppTest.
"""
from pages.geral.layout import _build_timeline_figure
from visual.tema import FONTE, aplicar_tema


def test_apos_aplicar_tema_usa_fonte_padrao_e_nao_menciona_plenario_fisico():
    fig = aplicar_tema(_build_timeline_figure(), tema="novo", dark=False)
    assert fig.layout.font.family == FONTE

    textos = [fig.layout.title.text or ""]
    textos += [a.text or "" for a in fig.layout.annotations]
    assert not any("Plenário Físico" in t for t in textos)


def test_apos_aplicar_tema_modo_noturno_anotacoes_de_evento_ficam_legiveis():
    fig = aplicar_tema(_build_timeline_figure(), tema="novo", dark=True)
    # anotações de evento (sem cor própria, só <span> inline de font-size+cor)
    # herdam a cor de tinta clara do tema depois que limpar_html_de_fonte
    # remove o <span> inteiro (cor embutida junto com o font-size).
    anotacoes_evento = [a for a in fig.layout.annotations if "ER " in (a.text or "")]
    assert anotacoes_evento
    for a in anotacoes_evento:
        assert "color:" not in a.text
        assert a.font.color == "#fafafa"


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
