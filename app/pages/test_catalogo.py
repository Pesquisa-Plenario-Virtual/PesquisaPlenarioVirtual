"""Testes das partes puras de components/catalogo.py."""
from components.catalogo import (
    deve_persistir_selecao,
    filtrar_por_busca,
    nome_param_url,
    sumario_por_bloco,
)
from components.grafico import GraficoSpec

# ponytail: pandas 3.0.5 + pyarrow segfoca dentro do AppTest ao renderizar
# gráfico de verdade — stubar render_grafico como no-op e passar df=None é
# válido porque render_pagina nunca usa df, só repassa. Sem isso não dá pra
# testar render_pagina fim a fim nesse venv.
def _pagina_de_teste():
    import streamlit as st  # noqa: F401
    from components import catalogo
    from components.grafico import GraficoSpec as _Spec

    catalogo.render_grafico = lambda spec, df, key: None

    def _f(df):
        return None

    catalogo_completo = [
        _Spec(id=f"G{i}", rotulo=f"G{i} rótulo", subtitulo="s", descricao="d", fn=_f)
        for i in range(1, 17)
    ] + [_Spec(id="G24", rotulo="G24 rótulo", subtitulo="s", descricao="d", fn=_f)]

    catalogo.render_pagina(catalogo_completo, None, "pageA")


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


def test_nao_persiste_quando_busca_exclui_id_selecionado():
    assert deve_persistir_selecao(["T5", "T6"], "T7") is False


def test_persiste_quando_id_selecionado_segue_visivel():
    assert deve_persistir_selecao(["T5", "T6"], "T5") is True


def test_nome_param_url_isola_por_prefixo():
    assert nome_param_url("g") != nome_param_url("t")
    assert nome_param_url("g") == "g_g"


def test_apptest_busca_exclui_e_restaura_selecao_ao_limpar():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_pagina_de_teste)
    at.run()

    at.selectbox[0].select("G24 rótulo")
    at.run()
    assert at.session_state["pageA_selecionado"] == "G24"

    at.text_input(key="pageA_busca").set_value("G10")
    at.run()
    assert at.session_state["pageA_selecionado"] == "G24"  # busca não sobrescreve
    assert at.selectbox[0].value == "G10"  # tela mostra o fallback, não persiste

    at.text_input(key="pageA_busca").set_value("")
    at.run()
    assert at.session_state["pageA_selecionado"] == "G24"
    assert at.selectbox[0].value == "G24"  # G24 volta, na tela e persistido


def test_apptest_botao_do_sumario_move_o_selectbox():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_pagina_de_teste)
    at.run()
    assert at.selectbox[0].value == "G1"

    at.button(key="pageA_ir_G24").click()
    at.run()
    assert at.session_state["pageA_selecionado"] == "G24"
    assert at.selectbox[0].value == "G24"


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
