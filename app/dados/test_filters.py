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


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
