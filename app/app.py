import sys
import streamlit as st

from pathlib import Path

st.set_page_config(layout="wide")

# ── Path setup ───────────────────────────────────────────────────────────────
_root = Path(__file__).resolve().parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

# ── Preferências globais (valem só para as páginas não-empíricas) ────────────
CSS_NOTURNO = """
<style>
  [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: #0e1117; }
  [data-testid="stSidebar"] { background: #161a23; }
  .stMarkdown, .stCaption, h1, h2, h3, h4, label, p { color: #fafafa !important; }
</style>
"""


def _preferencias_globais() -> None:
    """Seletor de tema visual e modo noturno.

    Os Blocos Empíricos não passam por render_grafico, então não respondem ao
    tema — é isso que protege a validação da Pessoa 1.
    """
    with st.sidebar:
        st.header("Aparência")
        st.session_state["tema_visual"] = st.radio(
            "Tema dos gráficos",
            options=["novo", "empirico"],
            index=0,
            format_func=lambda t: "Novo padrão" if t == "novo" else "Visual empírico",
            help="O visual empírico reproduz os gráficos como estão nos Blocos "
                 "Empíricos. Não afeta as páginas dos Blocos Empíricos, que "
                 "sempre usam o visual original.",
            key="pref_tema",
        )
        st.session_state["modo_noturno"] = st.toggle(
            "Modo noturno", value=False, key="pref_noturno",
            help="Escurece o app e troca os degraus de cor dos gráficos.",
        )
        st.divider()

    if st.session_state["modo_noturno"]:
        st.markdown(CSS_NOTURNO, unsafe_allow_html=True)


_preferencias_globais()

# ── Navegação ────────────────────────────────────────────────────────────────
pg = st.navigation(
    {
        "Início": [
            st.Page("pages/home/home.py", title="Início", icon="🏛️", default=True),
        ],
        "Acervo": [
            st.Page("pages/acervo/acervo.py", title="Acervo Histórico", icon="📦"),
        ],
        "Inclusões em Pauta": [
            st.Page("pages/inclusoes/inclusoes.py", title="Inclusões em Pauta", icon="📅"),
        ],
        "Reajuste de Voto": [
            st.Page("pages/reajuste/reajuste.py", title="Reajuste de Voto", icon="🔄"),
        ],
        "Tramitação": [
            st.Page("pages/tramitacao/tramitacao.py", title="Tramitação por Ambiente", icon="🔀"),
        ],
        "Sustentação Oral": [
            st.Page("pages/sustentacao/sustentacao.py", title="Sustentação Oral", icon="🎤"),
        ],
        "Sessões Virtuais": [
            st.Page("pages/sessoes_virtuais/sessoes_virtuais.py", title="Sessões Virtuais", icon="🖥️"),
        ],
        "Visão Geral": [
            st.Page("pages/geral/geral.py", title="Visão Geral", icon="📊"),
        ],
        "Narrativa": [
            st.Page("pages/narrativa/narrativa.py", title="Gráficos Narrativa", icon="📈"),
        ],
        "Blocos Empíricos": [
            st.Page("pages/bloco1_acervo/bloco1_acervo.py", title="Bloco 1 — Acervo", icon="🗂️"),
            st.Page("pages/bloco2_inclusoes/bloco2_inclusoes.py", title="Bloco 2 — Inclusões Estendidas", icon="🧮"),
            st.Page("pages/bloco3_pandemia/bloco3_pandemia.py", title="Bloco 3 — Pós-Pandemia", icon="🦠"),
        ],
    }
)

pg.run()
