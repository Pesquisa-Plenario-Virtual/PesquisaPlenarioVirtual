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


def test_trace_com_x_y_de_tamanhos_diferentes_e_ignorado():
    # Contrato: um trace com x e y desalinhados é um bug de quem montou a
    # figura. tabela_da_figura não inventa um valor para ele — ignora o
    # trace e segue com os demais, em vez de lançar ou de fabricar um número.
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["2020", "2021"], y=[10, 20], name="A"))
    fig.add_trace(go.Bar(x=["2020", "2021", "2022"], y=[1, 2], name="B"))
    tab = tabela_da_figura(fig)
    assert "B" not in tab.columns
    assert list(tab["A"]) == [10, 20, 30]


def test_valor_nao_numerico_nao_vira_zero():
    # Categoria acidentalmente ligada ao eixo de valor (y de texto) deve
    # aparecer como está, nunca como 0.0 — 0.0 seria indistinguível de uma
    # série legitimamente zerada.
    fig = go.Figure(go.Bar(x=["A", "B"], y=["cat1", "cat2"], name="X"))
    tab = tabela_da_figura(fig)
    assert list(tab["X"])[:2] == ["cat1", "cat2"]
    assert 0.0 not in list(tab["X"])[:2]


def test_categoria_real_chamada_total_nao_e_sobrescrita():
    fig = go.Figure(go.Bar(x=["2020", "Total"], y=[10, 20], name="A"))
    tab = tabela_da_figura(fig)
    linhas_total = tab[tab.iloc[:, 0] == "Total"]
    # a categoria real "Total" (valor 20) e a linha de soma (30) coexistem
    assert list(linhas_total["A"]) == [20, 30]


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
