"""Plotly figures for narrative graphics NA–NF.

Calculadas a partir de inclusoes_em_pauta (2020–2025); ver pages/narrativa/test_plots.py
para o portão de regressão que reproduz os 12 números publicados a partir do parquet.
NB, NE e NF reproduzem a lógica validada de bloco2_inclusoes/plots.py
(fig_2l_pauta_vs_concluidos, fig_2q_media_por_processo, fig_2r_pct_concluidos).
"""

from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

from visual.base import aplicar_padrao, add_espin_shade, br, COR_PV, COR_PP, COR_AMBOS

_LAYOUT_EXTRA = dict(height=650, margin=dict(t=130, b=80, l=60, r=60), hovermode="x unified")


def plot_na(df: pd.DataFrame, show_values: bool = True) -> go.Figure:
    tab = df.groupby(["ano", "ambiente"]).size().unstack(fill_value=0)
    pct = 100 * tab["Plenário Virtual"] / tab.sum(axis=1)
    anos = [str(a) for a in pct.index]
    anos_int = list(pct.index)

    fig = go.Figure(data=[
        go.Bar(x=anos, y=pct.values, marker_color=COR_PV,
               text=[f'{br(v, 1)}%' for v in pct.values] if show_values else None,
               textposition='outside',
               cliponaxis=False, showlegend=False)
    ])

    if anos_int:
        add_espin_shade(fig, anos_int[0], y0=0, y1=85)

    aplicar_padrao(
        fig,
        "A participação do Plenário Virtual mantém-se entre 59% e 68% ao ano",
        "Percentual das inclusões em pauta destinadas ao ambiente virtual (2020–2025)",
        yaxis=dict(range=[0, 85]),
        xaxis=dict(title="Ano"),
        **_LAYOUT_EXTRA,
    )
    return fig


def plot_nb(df: pd.DataFrame, show_values: bool = True) -> go.Figure:
    pauta_pv = (df["ambiente"] == "Plenário Virtual").sum()
    pauta_total = len(df)
    pct_pauta = 100 * pauta_pv / pauta_total
    concl = df[df["desfecho"].str.startswith("Concluído")]
    concl_pv = (concl["ambiente"] == "Plenário Virtual").sum()
    concl_total = len(concl)
    pct_concl = 100 * concl_pv / concl_total

    categorias = ['Participação na pauta', 'Participação nos julgamentos concluídos']
    valores = [pct_pauta, pct_concl]

    fig = go.Figure(data=[
        go.Bar(x=categorias, y=valores, marker_color=COR_PV,
               text=[f'{br(v, 1)}%' for v in valores] if show_values else None,
               textposition='outside',
               cliponaxis=False, showlegend=False)
    ])

    aplicar_padrao(
        fig,
        "O Plenário Virtual concentra os julgamentos concluídos",
        "Participação do ambiente virtual na pauta e nos julgamentos concluídos (2020–2025)",
        yaxis=dict(range=[0, 110]),
        xaxis=dict(title=""),
        **_LAYOUT_EXTRA,
    )
    return fig


def plot_nc(df: pd.DataFrame, show_values: bool = True) -> go.Figure:
    amb = df.groupby("incidente")["ambiente"].apply(set)

    def classif(s):
        pv, pp = "Plenário Virtual" in s, "Plenário Presencial" in s
        if pv and pp:
            return "Ambos"
        return "Somente Virtual" if pv else "Somente Presencial"

    tram = amb.apply(classif)
    vc = tram.value_counts().reindex(["Somente Presencial", "Ambos", "Somente Virtual"], fill_value=0)
    total = vc.sum()
    pct = 100 * vc / total

    # Construída como barra vertical canônica: o toggle "Tipo de gráfico" (tipos=
    # ("barra_h", "barra")) converte para horizontal por padrão via converter_tipo,
    # que espera x=categorias / y=valores em qualquer figura de entrada.
    categorias = ['Somente Plenário Presencial', 'Ambos os ambientes', 'Somente Plenário Virtual']
    cores = [COR_PP, COR_AMBOS, COR_PV]
    textos = [f'{br(v, 1)}%  ({br(p)} processos)' for v, p in zip(pct.values, vc.values)]

    fig = go.Figure(data=[
        go.Bar(x=categorias, y=pct.values, marker_color=cores,
               text=textos if show_values else None,
               textposition='outside', cliponaxis=False, showlegend=False)
    ])

    aplicar_padrao(
        fig,
        "Três de cada quatro processos nunca passam pelo Plenário Presencial",
        "Tramitação em pauta dos processos de controle concentrado (2020–2025)",
        yaxis=dict(range=[0, 110], title="%"),
        xaxis=dict(title=""),
        **_LAYOUT_EXTRA,
    )
    return fig


def plot_nd(df: pd.DataFrame, show_values: bool = True) -> go.Figure:
    rc = df[df["tipo_questao"] == "RC"]
    vc = rc["ambiente"].value_counts()
    total = vc.sum()
    pv_n, pp_n = int(vc.get("Plenário Virtual", 0)), int(vc.get("Plenário Presencial", 0))
    pv_pct, pp_pct = 100 * pv_n / total, 100 * pp_n / total

    # Barra vertical canônica (ver nota em plot_nc) — tipos=("barra_h", "barra").
    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=['Recursos'], y=[pv_pct], name='Plenário Virtual',
        marker_color=COR_PV,
        text=f"Plenário Virtual: {br(pv_pct, 1)}% ({br(pv_n)} recursos)" if show_values else None,
        textposition='inside', insidetextanchor='middle',
    ))

    fig.add_trace(go.Bar(
        x=['Recursos'], y=[pp_pct], name='Plenário Presencial',
        marker_color=COR_PP,
        text=f"PP: {br(pp_pct, 1)}% ({br(pp_n)})" if show_values else None,
        textposition='outside',
    ))

    aplicar_padrao(
        fig,
        "A atividade recursal migrou quase integralmente para o ambiente virtual",
        "Destino das inclusões em pauta de recursos (AgR, ED e afins) (2020–2025)",
        barmode='stack',
        yaxis=dict(title="%"),
        xaxis=dict(title=""),
        showlegend=False,
        **_LAYOUT_EXTRA,
    )
    return fig


def plot_ne(df: pd.DataFrame, show_values: bool = True) -> go.Figure:
    medias = df.groupby("ambiente").apply(lambda d: len(d) / d["incidente"].nunique())
    categorias = ['Plenário Virtual', 'Plenário Presencial']
    valores = [medias.get(c, 0) for c in categorias]
    cores = [COR_PV, COR_PP]

    fig = go.Figure(data=[
        go.Bar(x=categorias, y=valores, marker_color=cores,
               text=[br(v, 1) for v in valores] if show_values else None,
               textposition='outside', cliponaxis=False, showlegend=False)
    ])

    aplicar_padrao(
        fig,
        "Cada julgamento presencial consome mais que o dobro de inclusões em pauta",
        "Média de inclusões em pauta por processo em cada ambiente (2020–2025)",
        yaxis=dict(range=[0, 5.5], title="Inclusões por processo"),
        xaxis=dict(title=""),
        **_LAYOUT_EXTRA,
    )
    return fig


def plot_nf(df: pd.DataFrame, show_values: bool = True) -> go.Figure:
    def pct_por_processo(d):
        return d.groupby("incidente")["desfecho"].apply(lambda s: s.str.startswith("Concluído").any())

    categorias = ['Plenário Virtual', 'Plenário Presencial']
    cores = [COR_PV, COR_PP]
    valores = []
    for amb in categorias:
        concl = pct_por_processo(df[df["ambiente"] == amb])
        valores.append(100 * concl.mean() if len(concl) else 0)

    fig = go.Figure(data=[
        go.Bar(x=categorias, y=valores, marker_color=cores,
               text=[f'{br(v, 1)}%' for v in valores] if show_values else None,
               textposition='outside', cliponaxis=False, showlegend=False)
    ])

    aplicar_padrao(
        fig,
        "Considerado o processo, o ambiente virtual conclui 86% do que pauta",
        "Percentual de processos pautados que tiveram julgamento concluído (2020–2025)",
        yaxis=dict(range=[0, 105]),
        xaxis=dict(title=""),
        **_LAYOUT_EXTRA,
    )
    return fig
