"""Testes das partes puras de pages/inclusoes/layout.py."""
from pages.inclusoes.layout import dimensoes_disponiveis

# Colunas reais de inclusoes_em_pauta.parquet (via dados.loader.load_inclusoes_em_pauta).
_COLUNAS_INCLUSOES = [
    "incidente", "nome_processo", "classe", "relator", "ano", "data_inclusao",
    "data_inclusao_dt", "ambiente", "tipo_questao", "tipo_questao_original",
    "sufixo_extraido", "desfecho", "macro_desfecho", "andamento_origem",
    "virou_sessao",
]


def test_exclui_dimensoes_que_a_base_de_inclusoes_nao_tem():
    dims = dimensoes_disponiveis(_COLUNAS_INCLUSOES)
    colunas = set(dims.values())
    assert "tramitacao" not in colunas
    assert "teve_reajuste" not in colunas
    assert "teve_sustentacao" not in colunas


def test_mantem_dimensoes_que_a_base_de_inclusoes_tem():
    dims = dimensoes_disponiveis(_COLUNAS_INCLUSOES)
    colunas = set(dims.values())
    assert {"ano", "classe", "ambiente", "tipo_questao"} <= colunas


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
