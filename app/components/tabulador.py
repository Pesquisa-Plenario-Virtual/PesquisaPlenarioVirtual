"""Tabulador de eixos livres, compartilhado pelas seis páginas que o oferecem.

Existia uma cópia por página, quase idênticas — divergiam só no dicionário de
dimensões, na lista de pré-definidos, no rótulo da métrica e no prefixo de key.
Seis cópias significam seis lugares para corrigir, e foi por isso que o tema
nunca chegou aqui: `aplicar_tema` não aparecia em nenhuma delas, então o
tabulador era o único gráfico do dashboard fora do padrão visual.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from estilo import br
from pages.tramitacao.plots import gt10_tabulador
from tema import aplicar_tema

METRICAS_PADRAO = {
    "inclusoes": "Inclusões em pauta",
    "processos": "Processos distintos",
}

_MODOS = {"group": "Agrupado", "stack": "Empilhado", "100%": "Empilhado 100%"}
_SEM_PRESET = "— ou configure manualmente abaixo —"


def _tabela_dos_mesmos_eixos(df, eixo_x: str, grupo: str, metrica: str,
                             barmode: str) -> pd.DataFrame:
    """Mesma agregação que alimenta o gráfico, em forma de tabela."""
    d = df.copy()
    if "tipo_questao" in d.columns:
        d["tipo_questao"] = d["tipo_questao"].replace({"IJ": "QI"})
    if metrica == "processos" and "incidente" in d.columns:
        d = d.drop_duplicates("incidente")
    tab = d.groupby([eixo_x, grupo], observed=True).size().reset_index(name="n")
    if barmode == "100%":
        totais = tab.groupby(eixo_x)["n"].transform("sum")
        tab["n"] = (tab["n"] / totais * 100).round(1)
    pvt = tab.pivot_table(index=eixo_x, columns=grupo, values="n", fill_value=0)
    pvt["Total"] = pvt.sum(axis=1)
    pvt.loc["Total"] = pvt.sum()
    pvt = pvt.reset_index()
    pvt[pvt.columns[0]] = pvt[pvt.columns[0]].astype(str)
    return pvt


def figura_tabulador(df, eixo_x: str, grupo: str, metrica: str, barmode: str,
                     show_values: bool, titulo_y: str | None = None,
                     tema: str = "novo", dark: bool = False):
    """Figura do tabulador, já tematizada. Puro: sem Streamlit, testável.

    O tema mora aqui e não em `render_tabulador` justamente para poder ser
    verificado pelo portão de conformidade — enquanto a aplicação do tema
    estava dentro do renderizador de UI, o tabulador ficou fora do padrão
    visual sem que nenhum teste percebesse.
    """
    metrica_gt = "processos" if metrica == "processos" else "inclusoes"
    fig = gt10_tabulador(df, eixo_x, grupo, metrica_gt, barmode, show_values)
    if titulo_y:
        fig.update_yaxes(title_text=titulo_y)
    return aplicar_tema(fig, tema=tema, dark=dark)


def render_tabulador(df, key: str, dims: dict[str, str], presets: list[tuple],
                     metricas: dict[str, str] | None = None,
                     titulo_y: dict[str, str] | None = None) -> None:
    """Renderiza o tabulador: controles, gráfico tematizado e tabela espelhada.

    `dims`   — {rótulo visível: coluna}, já filtrado pelas colunas de `df`.
    `presets`— tuplas (rótulo, eixo_x, grupo, métrica, barmode).
    `metricas`— {valor: rótulo}; o valor vira "inclusoes" ou "processos" ao
                chamar gt10_tabulador, que só conhece esses dois.
    `titulo_y`— sobrescreve o título do eixo y por métrica escolhida.
    """
    metricas = metricas or METRICAS_PADRAO
    titulo_y = titulo_y or {}

    if len(dims) < 2:
        st.info("Este conjunto de dados não tem dimensões suficientes para o tabulador.")
        return

    dims_label = list(dims.keys())
    colunas_ok = set(dims.values())
    disponiveis = [p for p in presets if p[1] in colunas_ok and p[2] in colunas_ok]
    labels_pre = [p[0] for p in disponiveis]
    valores_metrica = list(metricas.keys())

    col_pre, _ = st.columns([2, 1])
    with col_pre:
        escolha_pre = st.selectbox("🔖 Pré-definidos", [_SEM_PRESET] + labels_pre,
                                   index=0, key=f"{key}_pre")

    if escolha_pre == _SEM_PRESET or not disponiveis:
        def_x, def_g, def_m, def_bm = 0, min(1, len(dims_label) - 1), 0, 0
    else:
        _, px, pg, pm, pbm = next(p for p in disponiveis if p[0] == escolha_pre)
        def_x = dims_label.index(next(k for k, v in dims.items() if v == px))
        def_g = dims_label.index(next(k for k, v in dims.items() if v == pg))
        def_m = valores_metrica.index(pm) if pm in valores_metrica else 0
        def_bm = list(_MODOS).index(pbm)

    c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 1])
    with c1:
        eixo_x_lbl = st.selectbox("Eixo X", dims_label, index=def_x, key=f"{key}_x")
    with c2:
        grupo_lbl = st.selectbox("Cor/Grupo", dims_label, index=def_g, key=f"{key}_g")
    with c3:
        metrica = st.selectbox("Métrica", valores_metrica, index=def_m, key=f"{key}_m",
                               format_func=lambda v: metricas[v])
    with c4:
        barmode = st.selectbox("Modo", list(_MODOS), index=def_bm, key=f"{key}_bm",
                               format_func=lambda v: _MODOS[v])
    with c5:
        show_values = st.checkbox("Exibir valores", value=False, key=f"{key}_sv")

    eixo_x, grupo = dims[eixo_x_lbl], dims[grupo_lbl]
    if eixo_x == grupo:
        st.warning("Eixo X e Cor/Grupo não podem ser a mesma dimensão.")
        return

    fig = figura_tabulador(
        df, eixo_x, grupo, metrica, barmode, show_values,
        titulo_y=titulo_y.get(metrica),
        tema=st.session_state.get("tema_visual", "novo"),
        dark=st.session_state.get("modo_noturno", False),
    )
    # sem key: só há um gráfico aqui, e uma key transformaria o plotly_chart em
    # widget com estado, o que não é o que se quer para exibição pura.
    st.plotly_chart(fig, width="stretch")

    st.markdown("---")
    st.subheader("Tabela — mesmos eixos")
    pvt = _tabela_dos_mesmos_eixos(df, eixo_x, grupo, metrica, barmode)
    casas = 1 if barmode == "100%" else 0
    fmt = {c: (lambda v, d=casas: br(v, d)) for c in pvt.columns if pvt[c].dtype.kind in "iuf"}
    st.dataframe(pvt.style.format(fmt, na_rep="—"), width="stretch", height=280)
