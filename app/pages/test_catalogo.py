"""Testes das partes puras de components/catalogo.py."""
from components.catalogo import (
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


def test_nome_param_url_isola_por_prefixo():
    assert nome_param_url("g") != nome_param_url("t")
    assert nome_param_url("g") == "g_g"


def test_apptest_cliques_consecutivos_no_selectbox_registram_na_hora():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_pagina_de_teste)
    at.run()
    assert at.selectbox[0].value == "G1"

    at.selectbox[0].select("G5 rótulo")
    at.run()
    assert at.session_state["pageA_selecionado"] == "G5"
    assert at.selectbox[0].value == "G5"

    # o clique seguinte, pra um valor diferente, também tem que valer de cara
    # — sem precisar repetir o clique.
    at.selectbox[0].select("G10 rótulo")
    at.run()
    assert at.session_state["pageA_selecionado"] == "G10"
    assert at.selectbox[0].value == "G10"


def test_apptest_botao_do_sumario_move_o_selectbox_e_clique_seguinte_registra():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_pagina_de_teste)
    at.run()

    at.button(key="pageA_ir_G24").click()
    at.run()
    assert at.session_state["pageA_selecionado"] == "G24"
    assert at.selectbox[0].value == "G24"

    # depois da navegação pelo botão, um clique direto no selectbox também
    # tem que valer na primeira tentativa.
    at.selectbox[0].select("G5 rótulo")
    at.run()
    assert at.session_state["pageA_selecionado"] == "G5"
    assert at.selectbox[0].value == "G5"


def test_apptest_busca_filtra_sumario_mas_nao_o_selectbox():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_pagina_de_teste)
    at.run()

    at.selectbox[0].select("G5 rótulo")
    at.run()
    assert at.session_state["pageA_selecionado"] == "G5"
    opcoes_antes = list(at.selectbox[0].options)

    at.text_input(key="pageA_busca").set_value("G10")
    at.run()

    # sumário só mostra quem bate com a busca — o botão de G5 sumiu.
    assert not any(b.key == "pageA_ir_G5" for b in at.button)
    assert any(b.key == "pageA_ir_G10" for b in at.button)
    # mas o selectbox continua com o catálogo inteiro e a seleção intacta.
    assert at.selectbox[0].options == opcoes_antes
    assert at.selectbox[0].value == "G5"
    assert at.session_state["pageA_selecionado"] == "G5"


def test_apptest_busca_sem_resultado_nao_quebra_nem_muda_selecao():
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_function(_pagina_de_teste)
    at.run()
    at.selectbox[0].select("G5 rótulo")
    at.run()

    at.text_input(key="pageA_busca").set_value("sustentação oral")
    at.run()

    assert not at.exception
    assert any("Nenhum gráfico corresponde" in w.value for w in at.warning)
    assert at.selectbox[0].value == "G5"
    assert at.session_state["pageA_selecionado"] == "G5"


def test_apptest_link_compartilhado_ida_e_volta_semeia_uma_vez_so():
    from streamlit.testing.v1 import AppTest

    param = nome_param_url("pageA")
    at = AppTest.from_function(_pagina_de_teste)
    at.query_params[param] = "G24"
    at.run()
    assert at.session_state["pageA_selecionado"] == "G24"
    assert at.selectbox[0].value == "G24"

    # o seed só roda uma vez: uma escolha nova do usuário não é revertida
    # pelo query param, mesmo que ele continue presente na sessão.
    at.selectbox[0].select("G5 rótulo")
    at.run()
    assert at.session_state["pageA_selecionado"] == "G5"


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
