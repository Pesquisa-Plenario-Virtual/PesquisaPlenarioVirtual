"""Página: Gráficos de Narrativa."""

import sys
from pathlib import Path

import streamlit as st

_here = Path(__file__).resolve()
_root = _here.parent.parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from dados.loader import load_inclusoes_em_pauta
from pages.narrativa.layout import render_graficos

try:
    df = load_inclusoes_em_pauta()
except Exception as e:
    st.error(f"Erro ao carregar dataset: {e}")
    st.stop()

if df.empty:
    st.warning("O dataframe retornou vazio.")
    st.stop()

# A "narrativa" é sobre o período pós-universalização — os 6 achados (NA–NF)
# são todos referenciados a 2020–2025 (ver task-18-brief.md, Passo 1).
df = df[df["ano"].between(2020, 2025)]

st.title("Gráficos de Narrativa")
st.markdown("""
Seis gráficos que sintetizam os principais achados sobre a relação entre o **Plenário Virtual**
e o **Plenário Presencial** no STF (2020–2025). Dados do portal de transparência do STF,
elaboração própria.
""")

st.markdown("---")
render_graficos(df)
