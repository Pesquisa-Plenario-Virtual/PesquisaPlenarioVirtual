"""Testes das partes puras de dados/filters.py."""
from dados.filters import dimensoes_disponiveis
from pages.tramitacao.plots import DIMENSOES


def test_mantem_so_dimensoes_cuja_coluna_existe():
    dims = dimensoes_disponiveis(["classe", "ano", "outra_coluna"])
    assert set(dims.values()) == {"classe", "ano"}


def test_sem_colunas_devolve_vazio():
    assert dimensoes_disponiveis([]) == {}


def test_todas_as_nove_quando_todas_as_colunas_existem():
    dims = dimensoes_disponiveis(DIMENSOES.values())
    assert dims == DIMENSOES



def test_filter_by_values_distingue_none_de_lista_vazia():
    """None = sem filtro; [] = usuário desmarcou tudo.

    Tratar os dois igual fazia o dashboard mostrar tudo quando o usuário pediu
    nada. Mesma classe de bug já corrigida na casca de gráfico.
    """
    import pandas as pd
    from dados.filters import filter_by_values
    df = pd.DataFrame({"classe": ["ADI", "ADPF", "ADI"]})
    assert len(filter_by_values(df, "classe", None)) == 3
    assert len(filter_by_values(df, "classe", [])) == 0
    assert len(filter_by_values(df, "classe", ["ADI"])) == 2
    # coluna inexistente continua sendo no-op
    assert len(filter_by_values(df, "nao_existe", [])) == 3


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
