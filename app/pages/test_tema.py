"""Testes de tema.py — pós-processamento de figura."""
import plotly.graph_objects as go

from tema import FONTE, TAMANHOS, aplicar_tema


def _fig_suja() -> go.Figure:
    """Figura no estado em que as páginas produzem hoje: Arial, tamanhos
    avulsos, ano na diagonal, nome de série em caixa alta."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["2020", "2021"], y=[10, 20], name="PLENÁRIO VIRTUAL",
        textfont=dict(family="Arial, sans-serif", size=17, color="black"),
    ))
    fig.add_trace(go.Bar(
        x=["2020", "2021"], y=[5, 8], name="PLENÁRIO FÍSICO",
        textfont=dict(family="Arial, sans-serif", size=17, color="black"),
    ))
    fig.update_layout(
        title="<b>Um achado qualquer</b>",
        font=dict(family="Arial, sans-serif", color="#000000"),
        title_font=dict(family="Arial, sans-serif", size=22),
        legend=dict(font=dict(family="Arial, sans-serif", size=14)),
        xaxis=dict(title="Ano", tickangle=-45,
                   tickfont=dict(family="Arial, sans-serif", size=22),
                   title_font=dict(family="Arial, sans-serif", size=22)),
        yaxis=dict(title="Inclusões em pauta",
                   tickfont=dict(family="Arial, sans-serif", size=15)),
    )
    fig.add_annotation(x=0, y=25, text="<b>ER 53</b>",
                       font=dict(family="Arial, sans-serif", size=11))
    return fig


def test_fonte_times_em_layout_eixos_legenda_e_traces():
    fig = aplicar_tema(_fig_suja())
    assert fig.layout.font.family == FONTE
    assert fig.layout.title.font.family == FONTE
    assert fig.layout.legend.font.family == FONTE
    assert fig.layout.xaxis.tickfont.family == FONTE
    assert fig.layout.xaxis.title.font.family == FONTE
    assert fig.layout.yaxis.tickfont.family == FONTE
    assert fig.layout.annotations[0].font.family == FONTE
    for tr in fig.data:
        assert tr.textfont.family == FONTE


def test_tamanhos_normalizados():
    fig = aplicar_tema(_fig_suja())
    assert fig.layout.title.font.size == TAMANHOS["titulo"]
    assert fig.layout.xaxis.tickfont.size == TAMANHOS["tick"]
    assert fig.layout.yaxis.tickfont.size == TAMANHOS["tick"]
    assert fig.layout.xaxis.title.font.size == TAMANHOS["eixo_titulo"]
    assert fig.layout.legend.font.size == TAMANHOS["legenda"]
    assert fig.layout.annotations[0].font.size == TAMANHOS["anotacao"]
    for tr in fig.data:
        assert tr.textfont.size == TAMANHOS["valor"]


def test_ano_fica_na_horizontal():
    fig = aplicar_tema(_fig_suja())
    assert fig.layout.xaxis.tickangle == 0


def test_legenda_em_caixa_de_frase_e_sem_plenario_fisico():
    fig = aplicar_tema(_fig_suja())
    nomes = [tr.name for tr in fig.data]
    assert nomes == ["Plenário Virtual", "Plenário Presencial"]


def test_tema_empirico_nao_toca_na_figura():
    original = _fig_suja()
    devolvida = aplicar_tema(original, tema="empirico")
    assert devolvida.layout.font.family == "Arial, sans-serif"
    assert devolvida.layout.xaxis.tickangle == -45
    assert devolvida.data[0].name == "PLENÁRIO VIRTUAL"


def test_modo_escuro_troca_fundo_e_tinta():
    fig = aplicar_tema(_fig_suja(), dark=True)
    assert fig.layout.paper_bgcolor == "#0e1117"
    assert fig.layout.plot_bgcolor == "#0e1117"
    assert fig.layout.font.color == "#fafafa"


def _fig_com_plenario_fisico_por_toda_parte() -> go.Figure:
    """'Plenário Físico' vazando em título, eixo (inclusive subplot),
    anotação e valor categórico — o cenário do replace() em plots.py."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["Plenário Físico", "Plenário Virtual"], y=[5, 10]))
    fig.update_layout(
        title="Inclusões no Plenário Físico por ano",
        xaxis=dict(title="Ambiente"),
        xaxis2=dict(title="Comparativo Plenário Físico x Virtual"),
    )
    fig.add_annotation(x=0, y=12, text="Predomínio do Plenário Físico em 2020")
    return fig


def test_titulo_com_plenario_fisico_no_meio_da_frase_e_corrigido():
    fig = aplicar_tema(_fig_com_plenario_fisico_por_toda_parte())
    assert fig.layout.title.text == "Inclusões no Plenário Presencial por ano"


def test_titulo_de_eixo_x_com_plenario_fisico_e_corrigido():
    fig = aplicar_tema(_fig_com_plenario_fisico_por_toda_parte())
    assert "Plenário Físico" not in fig.layout.xaxis2.title.text
    assert "Plenário Presencial" in fig.layout.xaxis2.title.text


def test_anotacao_com_plenario_fisico_e_corrigida():
    fig = aplicar_tema(_fig_com_plenario_fisico_por_toda_parte())
    assert fig.layout.annotations[0].text == "Predomínio do Plenário Presencial em 2020"


def test_valor_categorico_plenario_fisico_vira_presencial():
    fig = aplicar_tema(_fig_com_plenario_fisico_por_toda_parte())
    assert fig.data[0].x == ("Plenário Presencial", "Plenário Virtual")


def test_tema_empirico_e_byte_identico_mesmo_com_plenario_fisico():
    original = _fig_com_plenario_fisico_por_toda_parte()
    antes = original.to_json()
    devolvida = aplicar_tema(original, tema="empirico")
    assert devolvida.to_json() == antes
    assert "Plenário Físico" in devolvida.to_json()


from paleta import cor as cor_paleta


def test_recolore_serie_conhecida_pelo_nome():
    fig = aplicar_tema(_fig_suja())
    assert fig.data[0].marker.color == cor_paleta("Plenário Virtual")
    assert fig.data[1].marker.color == cor_paleta("Plenário Presencial")


def test_recolore_no_modo_escuro_com_o_degrau_escuro():
    fig = aplicar_tema(_fig_suja(), dark=True)
    assert fig.data[0].marker.color == cor_paleta("Plenário Virtual", dark=True)


def test_nao_recolore_serie_fora_do_vocabulario_com_cor_explicita():
    fig = go.Figure(go.Bar(x=[1], y=[2], name="Série sem vocabulário",
                           marker_color="#123456"))
    aplicar_tema(fig)
    assert fig.data[0].marker.color == "#123456"


def test_recolore_linha_alem_de_barra():
    fig = go.Figure(go.Scatter(x=[1, 2], y=[3, 4], mode="lines",
                               name="Plenário Virtual"))
    aplicar_tema(fig)
    assert fig.data[0].line.color == cor_paleta("Plenário Virtual")


def test_nao_quebra_com_marker_color_vetorial():
    """acervo/plots.py e bloco1 passam uma lista de cores por barra."""
    fig = go.Figure(go.Bar(x=[1, 2], y=[3, 4], name="Variação",
                           marker_color=["#aaaaaa", "#bbbbbb"]))
    aplicar_tema(fig)
    assert list(fig.data[0].marker.color) == ["#aaaaaa", "#bbbbbb"]


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
