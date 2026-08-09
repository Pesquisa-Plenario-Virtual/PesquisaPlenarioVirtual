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
