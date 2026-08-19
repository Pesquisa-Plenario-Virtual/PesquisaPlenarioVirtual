"""Testes das partes puras de pages/inclusoes/layout.py."""
from pages.inclusoes.layout import dimensoes_disponiveis, _CATALOGO

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


def test_i19_i20_recortam_2020_2025():
    """I19/I20 eram a única dupla de gráficos sem recorte temporal — o I19
    somava o período inteiro (2016–2025) e divergia do I3 (18,4% vs 16,9% de
    pedidos de vista). Ambos devem travar o padrão em 2020–2025 como I3."""
    for sid in ("I19", "I20"):
        spec = next(s for s in _CATALOGO if s.id == sid)
        assert spec.periodo_padrao == (2020, 2025)
        assert "periodo" in spec.filtros
        assert " (2020–2025)" in spec.subtitulo


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
