"""Figuras Plotly para a página de Sustentação Oral."""

from __future__ import annotations
import plotly.graph_objects as go
import pandas as pd

from estilo import aplicar_padrao, add_er_marker, add_espin_shade, br, AZUL, AZUL_CLARO, CINZA, VERDE, ROXO, VERMELHO

CORES_SUST = {
    "Com sustentação oral": "#0891b2",
    "Sem sustentação oral": "#e5e7eb",
}
CORES_CLASSE = {
    "ADI":  "#2563eb",
    "ADPF": "#f59e0b",
    "ADC":  "#16a34a",
    "ADO":  "#ef4444",
}
CORES_TIPO  = {"PR": "#2563eb", "RC": "#f59e0b", "QI": "#16a34a"}
CORES_AMB   = {"Plenário Virtual": "#2563eb", "Plenário Presencial": "#94a3b8"}
_CLASSES    = ["ADI", "ADPF", "ADC", "ADO"]
_TIPOS      = ["PR", "RC", "QI"]

# Legenda horizontal acima do gráfico (barras com múltiplas séries).
_LEGEND_BARRAS = dict(
    orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5,
    font=dict(family="Arial, sans-serif", size=14, color="black"),
)
# Legenda horizontal abaixo do gráfico (pizzas).
_LEGEND_PIZZA = dict(
    orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5,
    font=dict(family="Arial, sans-serif", size=14, color="black"),
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _periodo(df: pd.DataFrame) -> str:
    """Trecho ' (ano_min–ano_max)' derivado do próprio df; vazio se não houver 'ano'.

    Mesmo padrão de gt10_tabulador (pages/tramitacao/plots.py) e de
    pages/reajuste/plots.py: o df recebido já pode vir recortado pelo filtro
    de período da casca, então o intervalo exibido no título reflete o
    recorte atual em vez de um texto fixo que mentiria sempre que o dataset
    ou o recorte mudassem.
    """
    anos = pd.to_numeric(df.get("ano"), errors="coerce").dropna() if "ano" in df.columns else pd.Series(dtype="float")
    return f" ({int(anos.min())}–{int(anos.max())})" if not anos.empty else ""


def _marcos_temporais(fig: go.Figure, y_max: float) -> go.Figure:
    """ER 53 e sombreamento ESPIN — o dataset de sustentação oral cobre 2020–2025,
    então ER 51/52 (2016/2019) nunca entram no eixo e ficam de fora."""
    if y_max <= 0:
        return fig
    y1 = y_max * 1.15
    y_label = y_max * 1.22
    add_er_marker(fig, 0, 53, 0, y1, y_label)
    add_espin_shade(fig, 0, 0, y1, y_label)
    return fig


def _pizza(serie: pd.Series, titulo: str, cores: list, show_values: bool = True) -> go.Figure:
    fig = go.Figure(go.Pie(
        labels=[str(l).upper() for l in serie.index], values=serie.values,
        hole=0.4,
        marker=dict(colors=cores, line=dict(color="white", width=2)),
        textinfo="percent" if show_values else "none",
        textfont=dict(family="Arial, sans-serif", size=14, color="black"),
        textposition="inside",
        insidetextorientation="radial",
        showlegend=True,
    ))
    aplicar_padrao(fig, titulo, height=500, margin=dict(t=110, b=100, l=60, r=60),
                   showlegend=True, legend=_LEGEND_PIZZA)
    return fig


def _serie_sust(df_amb: pd.DataFrame) -> pd.Series:
    return df_amb["teve_sustentacao"].map(
        {True: "Com sustentação oral", False: "Sem sustentação oral"}
    ).value_counts()


def _pizza_sust(df_amb: pd.DataFrame, titulo: str, show_values: bool = True) -> go.Figure:
    return _pizza(_serie_sust(df_amb), titulo,
                  [CORES_SUST.get(l, "#999") for l in _serie_sust(df_amb).index],
                  show_values=show_values)


def _barras_anuais(df_amb: pd.DataFrame, titulo: str, show_values: bool = True,
                   proporcao: bool = False) -> go.Figure:
    anos = list(range(int(df_amb["ano"].min()), int(df_amb["ano"].max()) + 1))
    tab = (df_amb[df_amb["teve_sustentacao"]]
           .groupby("ano").size().reset_index(name="n"))
    tab = tab.set_index("ano").reindex(anos, fill_value=0).reset_index()

    if proporcao:
        total_ano = df_amb.groupby("ano").size().reindex(anos, fill_value=0)
        tab["y"] = (tab["n"] / tab["ano"].map(total_ano) * 100).round(1)
        texto = tab["y"].apply(lambda v: f"{v:.1f}%") if show_values else None
        y_title = "% de inclusões com sustentação oral"
    else:
        tab["y"] = tab["n"]
        texto = tab["y"] if show_values else None
        y_title = "Inclusões com sustentação oral"

    fig = go.Figure(go.Bar(
        x=tab["ano"], y=tab["y"],
        marker_color="#0891b2",
        text=texto,
        textposition="outside", cliponaxis=False,
        textfont=dict(family="Arial, sans-serif", size=17, color="black"),
        name="COM SUSTENTAÇÃO",
    ))
    aplicar_padrao(fig, titulo, height=700, margin=dict(t=130, b=140, l=120, r=60),
                   xaxis=dict(dtick=1, title="Ano"),
                   yaxis_title=y_title)
    _marcos_temporais(fig, tab["y"].max())
    return fig


def _barras_grupo(df_sub: pd.DataFrame, col_grupo: str,
                  cores: dict, titulo: str, x_title: str = "Ano",
                  show_values: bool = True, proporcao: bool = False) -> go.Figure:
    tab = df_sub.groupby(["ano", col_grupo], observed=True).size().reset_index(name="n")

    if proporcao:
        totais = tab.groupby("ano")["n"].transform("sum")
        tab["y"] = (tab["n"] / totais * 100).round(1)
        y_title = "% do total do ano"
    else:
        tab["y"] = tab["n"]
        y_title = "Inclusões com sustentação"

    fig = go.Figure()
    grupos = [g for g in cores if g in tab[col_grupo].unique()]
    for g in grupos:
        d = tab[tab[col_grupo] == g]
        texto = d["y"].apply(lambda v: f"{v:.1f}%") if proporcao else d["y"]
        fig.add_trace(go.Bar(
            x=d["ano"], y=d["y"], name=g.upper(),
            marker_color=cores[g],
            text=texto if show_values else None,
            textposition="outside", cliponaxis=False,
            textfont=dict(family="Arial, sans-serif", size=17, color="black"),
        ))
    aplicar_padrao(fig, titulo, height=700, margin=dict(t=130, b=140, l=120, r=60),
                   barmode="group", showlegend=True, legend=_LEGEND_BARRAS,
                   xaxis=dict(dtick=1, title=x_title),
                   yaxis_title=y_title)
    if not tab.empty:
        _marcos_temporais(fig, tab["y"].max())
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# S1/S2 — Pizza período total (PV/PP selecionável)
# ═══════════════════════════════════════════════════════════════════════════════

def gs1_sust_filtravel(df: pd.DataFrame, show_values: bool = True,
                       ambiente: str = "Plenário Virtual") -> go.Figure:
    d = df[df["ambiente"] == ambiente]
    return _pizza_sust(
        d,
        f"Sustentação oral — {ambiente}{_periodo(d)}",
        show_values=show_values,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# S3/S4 — Barras anuais (PV/PP selecionável)
# ═══════════════════════════════════════════════════════════════════════════════

def gs3_sust_anual_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                             ambiente: str = "Plenário Virtual") -> go.Figure:
    d = df[df["ambiente"] == ambiente]
    return _barras_anuais(
        d,
        f"Sustentação oral por ano — {ambiente}{_periodo(d)}",
        show_values=show_values,
        proporcao=proporcao,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# S5/S6 — Por ano e classe (PV/PP selecionável)
# ═══════════════════════════════════════════════════════════════════════════════

def gs5_sust_classe_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                              ambiente: str = "Plenário Virtual") -> go.Figure:
    sub = df[(df["ambiente"] == ambiente) & df["teve_sustentacao"]]
    return _barras_grupo(sub, "classe", CORES_CLASSE,
                         f"Sustentação oral por ano e classe — {ambiente}{_periodo(sub)}",
                         show_values=show_values, proporcao=proporcao)


# ═══════════════════════════════════════════════════════════════════════════════
# S7 — Por ano e tipo de questão (PV/PP selecionável)
# ═══════════════════════════════════════════════════════════════════════════════

def gs7_sust_tipo_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                            ambiente: str = "Plenário Virtual") -> go.Figure:
    sub = df[(df["ambiente"] == ambiente) & df["teve_sustentacao"]].copy()
    sub["tipo_questao"] = sub["tipo_questao"].replace({"IJ": "QI"})
    return _barras_grupo(sub, "tipo_questao", CORES_TIPO,
                         f"Sustentação oral por ano e tipo de questão — {ambiente}{_periodo(sub)}",
                         show_values=show_values, proporcao=proporcao)


# ═══════════════════════════════════════════════════════════════════════════════
# S8 — Taxa de sustentação por ano e ambiente (%)
# ═══════════════════════════════════════════════════════════════════════════════

def gs8_taxa_ambiente(df: pd.DataFrame, show_values: bool = True) -> go.Figure:
    tab = (df.groupby(["ano", "ambiente"], observed=True)["teve_sustentacao"]
           .mean().mul(100).reset_index(name="n"))
    fig = go.Figure()
    for amb, cor in CORES_AMB.items():
        d = tab[tab["ambiente"] == amb]
        vals = d["n"].round(1)
        fig.add_trace(go.Bar(
            x=d["ano"], y=vals, name=amb.upper(),
            marker_color=cor,
            text=(vals.astype(str) + "%") if show_values else None,
            textposition="outside", cliponaxis=False,
            textfont=dict(family="Arial, sans-serif", size=17, color="black"),
        ))
    aplicar_padrao(fig, "Taxa de sustentação oral por ano e ambiente",
                   f"% de inclusões com sustentação oral, Plenário Virtual vs Plenário Presencial{_periodo(df)}",
                   height=700, margin=dict(t=130, b=140, l=120, r=60),
                   barmode="group", showlegend=True, legend=_LEGEND_BARRAS,
                   xaxis=dict(dtick=1, title="Ano"),
                   yaxis_title="% de inclusões com sustentação")
    if not tab.empty:
        _marcos_temporais(fig, tab["n"].max())
    return fig
