"""Testes das partes puras de components/grafico.py."""
import plotly.graph_objects as go

from components.grafico import tabela_da_figura


def _fig_duas_series() -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["2020", "2021"], y=[10, 20], name="Plenário Virtual"))
    fig.add_trace(go.Bar(x=["2020", "2021"], y=[5, 8], name="Plenário Presencial"))
    fig.update_layout(xaxis_title="Ano")
    return fig


def test_uma_linha_por_categoria_do_eixo_x():
    tab = tabela_da_figura(_fig_duas_series())
    assert list(tab["Ano"]) == ["2020", "2021", "Total"]


def test_uma_coluna_por_serie_mais_total():
    tab = tabela_da_figura(_fig_duas_series())
    assert list(tab.columns) == ["Ano", "Plenário Virtual", "Plenário Presencial", "Total"]


def test_valores_batem_com_a_figura():
    tab = tabela_da_figura(_fig_duas_series())
    assert list(tab["Plenário Virtual"]) == [10, 20, 30]
    assert list(tab["Plenário Presencial"]) == [5, 8, 13]
    assert list(tab["Total"]) == [15, 28, 43]


def test_serie_unica_sem_nome_usa_rotulo_generico():
    fig = go.Figure(go.Bar(x=["A", "B"], y=[1, 2]))
    tab = tabela_da_figura(fig)
    assert "Valor" in tab.columns
    assert list(tab["Valor"]) == [1, 2, 3]


def test_barra_horizontal_le_a_categoria_do_eixo_y():
    fig = go.Figure(go.Bar(x=[70.0, 30.0], y=["Concluído", "Não concluído"],
                           orientation="h", name="Percentual"))
    tab = tabela_da_figura(fig)
    assert list(tab.iloc[:, 0])[:2] == ["Concluído", "Não concluído"]
    assert list(tab["Percentual"])[:2] == [70.0, 30.0]


def test_figura_vazia_devolve_dataframe_vazio():
    assert tabela_da_figura(go.Figure()).empty


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
