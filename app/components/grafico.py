"""Casca de renderização de gráfico: controles, filtros e tabela espelhada.

tabela_da_figura, _aplicar_filtros e _kwargs_aceitos são puros (sem Streamlit)
para poder ser testados sem contexto de execução; render_grafico e _controles
usam st.* e são exercidos pela execução do app.
"""

from __future__ import annotations

import inspect
from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from tema import TIPOS, aplicar_tema, converter_tipo

FILTROS_VALIDOS = ("ambiente", "classe", "tipo_questao", "desfecho", "periodo")

_ROTULO_TIPO = {
    "barra": "Barra", "linha": "Linha", "area": "Área", "barra_h": "Barra horizontal",
}
_COLUNA_DO_FILTRO = {
    "ambiente": "ambiente", "classe": "classe",
    "tipo_questao": "tipo_questao", "desfecho": "desfecho",
}


@dataclass
class GraficoSpec:
    """Uma entrada de catálogo de página."""
    id: str
    rotulo: str
    subtitulo: str
    descricao: str
    fn: Callable
    tipos: tuple[str, ...] = ("barra",)
    filtros: tuple[str, ...] = ()
    percentual: bool = False
    kwargs_fixos: dict = field(default_factory=dict)


def tabela_da_figura(fig: go.Figure) -> pd.DataFrame:
    """Reconstrói a tabela a partir dos traces da figura.

    A tabela não pode divergir do gráfico porque lê a mesma fonte. Uma coluna
    por série, uma linha por categoria do eixo categórico, mais linha e coluna
    de total.

    Guardas explícitas (deliberadas, não um catch-all): trace sem x/y é
    ignorado; trace cujo x e y têm tamanhos diferentes é ignorado (array
    desalinhado é bug de quem montou a figura — não vira número plausível);
    categorias duplicadas dentro de uma série são somadas. Fora isso, um
    defeito real (ex.: tipo inesperado) deve propagar como exceção, não virar
    um DataFrame vazio que a UI mostra como "sem dados".

    Série não numérica não é forçada a número: fica com dtype object e fica
    de fora da coluna/linha de Total (soma NaN, não fabrica zero). O
    `fillna(0)` só cobre o caso legítimo de uma categoria sem barra numa
    série (ausência real = zero), nunca uma falha de conversão de tipo.

    A linha de Total é anexada (concat), não atribuída por rótulo — uma
    categoria real do eixo chamada "Total" não é sobrescrita.
    """
    if not fig.data:
        return pd.DataFrame()

    horizontal = getattr(fig.data[0], "orientation", None) == "h"
    nome_eixo = (fig.layout.yaxis.title.text if horizontal
                 else fig.layout.xaxis.title.text) or "Categoria"

    colunas: dict[str, pd.Series] = {}
    for i, tr in enumerate(fig.data):
        cats = getattr(tr, "y", None) if horizontal else getattr(tr, "x", None)
        vals = getattr(tr, "x", None) if horizontal else getattr(tr, "y", None)
        if cats is None or vals is None:
            continue
        cats, vals = list(cats), list(vals)
        if len(cats) != len(vals):
            continue  # x/y desalinhados: trace malformado, ignora em vez de inventar valor
        nome = tr.name or ("Valor" if len(fig.data) == 1 else f"Série {i + 1}")
        serie = pd.Series(vals, index=[str(c) for c in cats], name=nome)
        if serie.index.has_duplicates:
            serie = serie.groupby(level=0, sort=False).sum()
        colunas[nome] = serie

    if not colunas:
        return pd.DataFrame()

    tab = pd.DataFrame(colunas).fillna(0)
    numericas = tab.select_dtypes("number").columns
    if len(numericas) > 1:
        tab["Total"] = tab[numericas].sum(axis=1)
    total = pd.DataFrame([tab.sum(numeric_only=True)], index=["Total"])
    tab = pd.concat([tab, total])
    tab.index.name = nome_eixo
    return tab.reset_index()


def _aplicar_filtros(df, escolhas: dict):
    """Recorta o dataframe pelas escolhas. Filtro sem coluna correspondente é ignorado.

    `None` (chave ausente) significa "filtro não oferecido" — mantém o
    dataframe intacto. `[]` significa "oferecido, nada selecionado" — deve
    zerar o resultado (isin([]) já faz isso), em vez de ser tratado como
    "sem filtro" e devolver tudo.
    """
    out = df
    periodo = escolhas.get("periodo")
    if periodo and "ano" in out.columns:
        out = out[out["ano"].between(periodo[0], periodo[1])]
    for nome, coluna in _COLUNA_DO_FILTRO.items():
        valores = escolhas.get(nome)
        if valores is not None and coluna in out.columns:
            out = out[out[coluna].isin(valores)]
    return out


def _kwargs_aceitos(fn: Callable, candidatos: dict) -> dict:
    """Só entrega à função os kwargs que ela declara — as ~90 funções de gráfico
    têm assinaturas diferentes e nem todas aceitam show_values ou proporcao."""
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return {}
    if any(p.kind is inspect.Parameter.VAR_KEYWORD for p in params.values()):
        return dict(candidatos)
    return {k: v for k, v in candidatos.items() if k in params}


def _fn_aceita_ambiente(fn: Callable) -> bool:
    """True se fn declara um parâmetro `ambiente` — nesse caso ela filtra
    internamente por um único ambiente (ex.: g12_concluidos_filtravel), e o
    controle correspondente precisa ser seleção única, não multiseleção,
    senão marcar os dois ambientes e o gráfico mostrar só um vira possível."""
    try:
        return "ambiente" in inspect.signature(fn).parameters
    except (TypeError, ValueError):
        return False


def _controles(spec: GraficoSpec, df, key: str) -> dict:
    """Linha de controles acima da figura. Devolve o estado escolhido."""
    estado: dict = {}
    cols = st.columns([1, 1, 1.4, 1.2])
    with cols[0]:
        estado["show_values"] = st.checkbox("Exibir valores", value=True, key=f"{key}_sv")
    with cols[1]:
        estado["legenda"] = st.checkbox("Exibir legenda", value=True, key=f"{key}_lg")
    with cols[2]:
        tipos = [t for t in spec.tipos if t in TIPOS] or ["barra"]
        estado["tipo"] = st.selectbox(
            "Tipo de gráfico", tipos, index=0, key=f"{key}_tipo",
            format_func=lambda t: _ROTULO_TIPO[t],
            disabled=len(tipos) == 1,
        )
    with cols[3]:
        estado["proporcao"] = spec.percentual and st.selectbox(
            "Escala", ["Absoluto", "Percentual"], index=0, key=f"{key}_esc",
        ) == "Percentual"

    escolhas: dict = {}
    ativos = [f for f in spec.filtros if f in FILTROS_VALIDOS]
    if ativos:
        fcols = st.columns(len(ativos))
        for col, nome in zip(fcols, ativos):
            with col:
                if nome == "periodo":
                    if "ano" not in df.columns or df["ano"].dropna().empty:
                        continue
                    lo, hi = int(df["ano"].min()), int(df["ano"].max())
                    if lo < hi:
                        escolhas["periodo"] = st.slider(
                            "Período", lo, hi, (lo, hi), step=1, key=f"{key}_per")
                    continue
                coluna = _COLUNA_DO_FILTRO[nome]
                if coluna not in df.columns:
                    continue
                opcoes = sorted(str(v) for v in df[coluna].dropna().unique())
                if nome == "ambiente" and _fn_aceita_ambiente(spec.fn):
                    opcoes = sorted(opcoes, key=lambda v: v != "Plenário Virtual")
                    escolhas[nome] = [st.selectbox(
                        "Âmbito", opcoes, index=0, key=f"{key}_{nome}")]
                    continue
                escolhas[nome] = st.multiselect(
                    coluna.replace("_", " ").capitalize(), opcoes,
                    default=opcoes, key=f"{key}_{nome}")
    estado["escolhas"] = escolhas
    return estado


def render_grafico(spec: GraficoSpec, df, key: str) -> None:
    """Renderiza um gráfico do catálogo com controles, tema e tabela espelhada."""
    estado = _controles(spec, df, key)
    recortado = _aplicar_filtros(df, estado["escolhas"])
    if recortado.empty:
        st.info("Sem dados para o recorte selecionado.")
        return

    candidatos = dict(spec.kwargs_fixos,
                      show_values=estado["show_values"],
                      proporcao=estado["proporcao"])
    for nome in ("ambiente",):
        valores = estado["escolhas"].get(nome)
        if valores and len(valores) == 1:
            candidatos[nome] = valores[0]

    figuras = spec.fn(recortado, **_kwargs_aceitos(spec.fn, candidatos))
    if isinstance(figuras, dict):
        abas = st.tabs(list(figuras.keys()))
        pares = [(aba, fig) for aba, fig in zip(abas, figuras.values())]
    elif isinstance(figuras, (tuple, list)):
        pares = [(None, fig) for fig in figuras]
    else:
        pares = [(None, figuras)]

    tema_atual = st.session_state.get("tema_visual", "novo")
    dark = st.session_state.get("modo_noturno", False)

    for i, (aba, fig) in enumerate(pares):
        contexto = aba if aba is not None else st.container()
        with contexto:
            fig = converter_tipo(fig, estado["tipo"])
            fig = aplicar_tema(fig, tema=tema_atual, dark=dark)
            fig.update_layout(showlegend=estado["legenda"] and len(fig.data) > 1)
            if not estado["show_values"]:
                fig.update_traces(text=None, texttemplate=None)
            st.plotly_chart(fig, width="stretch", key=f"{key}_fig_{i}")
            with st.expander("📊 Dados da visualização"):
                tab = tabela_da_figura(fig)
                if tab.empty:
                    st.caption("Esta visualização não produz tabela.")
                else:
                    st.dataframe(tab, width="stretch", height=280)
