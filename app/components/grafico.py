"""Casca de renderização de gráfico: controles, filtros e tabela espelhada.

tabela_da_figura é puro (sem Streamlit) para poder ser testado; render_grafico
usa st.* e é exercido pela execução do app.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def tabela_da_figura(fig: go.Figure) -> pd.DataFrame:
    """Reconstrói a tabela a partir dos traces da figura.

    A tabela não pode divergir do gráfico porque lê a mesma fonte. Uma coluna
    por série, uma linha por categoria do eixo categórico, mais linha e coluna
    de total. Nunca lança: traces sem x/y, sem nome, categorias divergentes
    entre séries, categorias duplicadas dentro de uma série, valores não
    numéricos e figuras sem traces (ex.: go.Pie) resultam em DataFrame vazio
    ou em colunas parciais, nunca em exceção.
    """
    if not fig.data:
        return pd.DataFrame()

    try:
        horizontal = getattr(fig.data[0], "orientation", None) == "h"
        nome_eixo = (fig.layout.yaxis.title.text if horizontal
                     else fig.layout.xaxis.title.text) or "Categoria"

        colunas: dict[str, pd.Series] = {}
        for i, tr in enumerate(fig.data):
            cats = getattr(tr, "y", None) if horizontal else getattr(tr, "x", None)
            vals = getattr(tr, "x", None) if horizontal else getattr(tr, "y", None)
            if cats is None or vals is None:
                continue
            nome = tr.name or ("Valor" if len(fig.data) == 1 else f"Série {i + 1}")
            serie = pd.Series(list(vals), index=[str(c) for c in cats], name=nome)
            serie = pd.to_numeric(serie, errors="coerce")
            if serie.index.has_duplicates:
                serie = serie.groupby(level=0, sort=False).sum()
            # nome repetido entre traces (ex.: mesma série em subplots): soma
            if nome in colunas:
                colunas[nome] = colunas[nome].add(serie, fill_value=0)
            else:
                colunas[nome] = serie

        if not colunas:
            return pd.DataFrame()

        tab = pd.DataFrame(colunas).fillna(0)
        numericas = tab.select_dtypes("number").columns
        if len(numericas) > 1:
            tab["Total"] = tab[numericas].sum(axis=1)
        tab.loc["Total"] = tab.sum(numeric_only=True)
        tab.index.name = nome_eixo
        return tab.reset_index()
    except Exception:
        return pd.DataFrame()
