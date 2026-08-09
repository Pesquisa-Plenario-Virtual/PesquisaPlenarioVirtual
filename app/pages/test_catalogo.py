"""Testes das partes puras de components/catalogo.py."""
from components.catalogo import filtrar_por_busca, sumario_por_bloco
from components.grafico import GraficoSpec


def _cat() -> list[GraficoSpec]:
    def _f(df):
        return None
    return [
        GraficoSpec(id="T5", rotulo="T5 — Macro-desfecho por ambiente",
                    subtitulo="s", descricao="Volume de inclusões concluídas", fn=_f),
        GraficoSpec(id="T6", rotulo="T6 — Desfecho detalhado por ambiente",
                    subtitulo="s", descricao="Os sete desfechos detalhados", fn=_f),
        GraficoSpec(id="T7", rotulo="T7 — Classe dentro de cada ambiente",
                    subtitulo="s", descricao="Composição por classe processual", fn=_f),
    ]


def test_busca_vazia_devolve_tudo():
    assert len(filtrar_por_busca(_cat(), "")) == 3
    assert len(filtrar_por_busca(_cat(), "   ")) == 3


def test_busca_por_id():
    assert [s.id for s in filtrar_por_busca(_cat(), "T6")] == ["T6"]
    assert [s.id for s in filtrar_por_busca(_cat(), "t6")] == ["T6"]


def test_busca_por_palavra_do_rotulo():
    assert [s.id for s in filtrar_por_busca(_cat(), "desfecho")] == ["T5", "T6"]


def test_busca_por_palavra_da_descricao():
    assert [s.id for s in filtrar_por_busca(_cat(), "processual")] == ["T7"]


def test_busca_ignora_acento():
    assert [s.id for s in filtrar_por_busca(_cat(), "composicao")] == ["T7"]


def test_busca_sem_resultado_devolve_lista_vazia():
    assert filtrar_por_busca(_cat(), "sustentação") == []


def test_sumario_agrupa_pelo_prefixo_do_id():
    blocos = sumario_por_bloco(_cat())
    assert list(blocos.keys()) == ["T"]
    assert [s.id for s in blocos["T"]] == ["T5", "T6", "T7"]


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
