"""Teste do seletor de tema/modo noturno em app.py.

app.py não é importável direto (roda st.navigation + pg.run() no import,
que dependem de arquivos de página reais e cwd). Por isso o teste replica
aqui só o corpo de _preferencias_globais, como test_catalogo.py já faz com
_pagina_de_teste para render_pagina.
"""
from streamlit.testing.v1 import AppTest


def _pagina_de_teste():
    import streamlit as st

    CSS_NOTURNO = "<style></style>"

    def _preferencias_globais() -> None:
        with st.sidebar:
            st.header("Aparência")
            st.session_state["tema_visual"] = st.radio(
                "Tema dos gráficos",
                options=["novo", "empirico"],
                index=0,
                format_func=lambda t: "Novo padrão" if t == "novo" else "Visual empírico",
                key="pref_tema",
            )
            st.session_state["modo_noturno"] = st.toggle(
                "Modo noturno", value=False, key="pref_noturno",
            )
            st.divider()

        if st.session_state["modo_noturno"]:
            st.markdown(CSS_NOTURNO, unsafe_allow_html=True)

    _preferencias_globais()


def test_defaults_apos_rodar():
    at = AppTest.from_function(_pagina_de_teste)
    at.run()
    assert at.session_state["tema_visual"] == "novo"
    assert at.session_state["modo_noturno"] is False


def test_toggle_liga_modo_noturno():
    at = AppTest.from_function(_pagina_de_teste)
    at.run()
    at.toggle(key="pref_noturno").set_value(True)
    at.run()
    assert at.session_state["modo_noturno"] is True


def test_radio_troca_para_empirico():
    at = AppTest.from_function(_pagina_de_teste)
    at.run()
    at.radio(key="pref_tema").set_value("empirico")
    at.run()
    assert at.session_state["tema_visual"] == "empirico"


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
