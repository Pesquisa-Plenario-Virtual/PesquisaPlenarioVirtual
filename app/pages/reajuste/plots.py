"""Figuras Plotly para a página de Reajuste de Voto."""

from __future__ import annotations
import plotly.graph_objects as go
import pandas as pd

from visual.base import aplicar_padrao, add_er_marker, add_espin_shade, AZUL, CINZA, VERDE, ROXO, VERMELHO
from pages.tramitacao.plots import gt10_tabulador

CORES_CLASSE = {
    "ADI":  AZUL,
    "ADPF": "#f59e0b",
    "ADC":  VERDE,
    "ADO":  "#ef4444",
}
CORES_TRAM = {
    "Ambos os ambientes": ROXO,
    "Virtual":            AZUL,
    "Físico":             "#f59e0b",
}
CORES_TIPO = {"PR": AZUL, "RC": "#f59e0b", "QI": VERDE}
_CLASSES = ["ADI", "ADPF", "ADC", "ADO"]


def _periodo(df: pd.DataFrame) -> str:
    """Trecho ' (ano_min–ano_max)' derivado do próprio df; vazio se não houver 'ano'.

    Mesmo padrão de gt10_tabulador (pages/tramitacao/plots.py): o df recebido
    pode já vir recortado pelo filtro de período da casca, então o intervalo
    exibido no título reflete o recorte atual em vez de um texto fixo que
    mentiria sempre que o dataset ou o recorte mudassem.
    """
    anos = pd.to_numeric(df.get("ano"), errors="coerce").dropna() if "ano" in df.columns else pd.Series(dtype="float")
    return f" ({int(anos.min())}–{int(anos.max())})" if not anos.empty else ""


# ── G-R1 — % de inclusões com reajuste de voto, por ambiente ───────────────────

def gr1_reajuste_pct(df: pd.DataFrame, show_values: bool = True) -> go.Figure:
    ambientes = ["Plenário Virtual", "Plenário Presencial"]
    pcts = [100 * df[df["ambiente"] == a]["teve_reajuste"].mean() for a in ambientes]
    maior = "Plenário Presencial" if pcts[1] > pcts[0] else "Plenário Virtual"
    fig = go.Figure(go.Bar(
        x=[a.upper() for a in ambientes], y=pcts,
        marker_color=VERMELHO,
        text=[f"{v:.1f}%".replace(".", ",") for v in pcts] if show_values else None,
        textposition="outside", textfont=dict(family="Arial, sans-serif", size=20, color="black", weight="bold"),
        cliponaxis=False,
    ))
    aplicar_padrao(
        fig,
        f"Reajuste de voto é mais comum no {maior}",
        f"% de inclusões com ao menos um reajuste de voto, por ambiente{_periodo(df)}",
        xaxis=dict(title=""), yaxis=dict(title="", range=[0, max(pcts) * 1.3]),
    )
    fig.update_yaxes(showline=False, showticklabels=False, ticks="")
    return fig
# ── G-R3 — Barras anuais por ambiente (selecionável) ───────────────────────────

def gr3_anual_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                        ambiente: str = "Plenário Virtual") -> go.Figure:
    d = df[df["ambiente"] == ambiente]
    return _barras_anuais(
        d,
        f"Reajuste de voto por ano — {ambiente}{_periodo(d)}",
        show_values=show_values,
        proporcao=proporcao,
    )
def _barras_anuais(df_amb: pd.DataFrame, titulo: str, show_values: bool = True,
                   proporcao: bool = False) -> go.Figure:
    anos = list(range(int(df_amb["ano"].min()), int(df_amb["ano"].max()) + 1))
    tab = (df_amb[df_amb["teve_reajuste"]]
           .groupby("ano").size().reset_index(name="n"))
    tab = (tab.set_index("ano")
              .reindex(anos, fill_value=0)
              .reset_index())

    if proporcao:
        total_ano = df_amb.groupby("ano").size().reindex(anos, fill_value=0)
        tab["y"] = (tab["n"] / tab["ano"].map(total_ano) * 100).round(1)
        texto = tab["y"].apply(lambda v: f"{v:.1f}%") if show_values else None
        y_title = "% de inclusões com reajuste de voto"
        subtitulo = "Percentual anual de inclusões com reajuste de voto, sobre o total do ano"
    else:
        tab["y"] = tab["n"]
        texto = tab["y"] if show_values else None
        y_title = "Inclusões com reajuste de voto"
        subtitulo = "Volume anual de inclusões com reajuste de voto"

    y_max = float(tab["y"].max() or 1)
    fig = go.Figure(go.Bar(
        x=tab["ano"], y=tab["y"],
        marker_color=VERMELHO,
        text=texto,
        textposition="outside",
        textfont=dict(family="Arial, sans-serif", size=17, color="black", weight="bold"),
        cliponaxis=False,
        name="COM REAJUSTE",
    ))
    aplicar_padrao(
        fig, titulo, subtitulo,
        xaxis=dict(dtick=1, title="Ano"),
        yaxis=dict(title=y_title, range=[0, y_max * 1.3]),
    )
    add_espin_shade(fig, ano_base=0, y0=0, y1=y_max * 1.25)
    add_er_marker(fig, ano_base=0, er=53, y0=0, y1=y_max * 1.25, y_label=y_max * 1.05)
    return fig
# ── G-R5 — Barras anuais por classe por ambiente (selecionável) ────────────────

def gr5_classe_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                         ambiente: str = "Plenário Virtual") -> go.Figure:
    d = df[df["ambiente"] == ambiente]
    return _barras_classe(
        d,
        f"Reajuste de voto por ano e classe — {ambiente}{_periodo(d)}",
        show_values=show_values,
        proporcao=proporcao,
    )
def _barras_classe(df_amb: pd.DataFrame, titulo: str, show_values: bool = True,
                   proporcao: bool = False) -> go.Figure:
    sub = df_amb[df_amb["teve_reajuste"]]
    tab = sub.groupby(["ano", "classe"], observed=True).size().reset_index(name="n")

    if proporcao:
        totais = tab.groupby("ano")["n"].transform("sum")
        tab["y"] = (tab["n"] / totais * 100).round(1)
        y_title = "% dos reajustes do ano"
        subtitulo = "Composição por classe processual dos reajustes de voto, por ano"
    else:
        tab["y"] = tab["n"]
        y_title = "Inclusões com reajuste de voto"
        subtitulo = "Distribuição por classe processual (ADI, ADPF, ADC, ADO)"

    y_max = float(tab["y"].max() or 1)
    fig = go.Figure()
    for cls in _CLASSES:
        d = tab[tab["classe"] == cls]
        if d.empty:
            continue
        texto = d["y"].apply(lambda v: f"{v:.1f}%") if proporcao else d["y"]
        fig.add_trace(go.Bar(
            x=d["ano"], y=d["y"], name=cls.upper(),
            marker_color=CORES_CLASSE[cls],
            text=texto if show_values else None,
            textposition="outside",
            textfont=dict(family="Arial, sans-serif", size=17, color="black", weight="bold"),
            cliponaxis=False,
        ))
    aplicar_padrao(
        fig, titulo, subtitulo,
        barmode="group", showlegend=True,
        xaxis=dict(dtick=1, title="Ano"),
        yaxis=dict(title=y_title, range=[0, y_max * 1.3]),
    )
    add_espin_shade(fig, ano_base=0, y0=0, y1=y_max * 1.25)
    add_er_marker(fig, ano_base=0, er=53, y0=0, y1=y_max * 1.25, y_label=y_max * 1.05)
    return fig
# ── G-R7 — Tipo de questão × reajuste (delega ao tabulador T10) ────────────────

def gr7_tipo_vs_reajuste(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False):
    barmode = "100%" if proporcao else "group"
    return gt10_tabulador(df, "tipo_questao", "teve_reajuste", "inclusoes", barmode, show_values)
# ── G-R8 — Desfecho detalhado × reajuste (delega ao tabulador T10) ─────────────

def gr8_desfecho_vs_reajuste(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False):
    """R8: desfecho vs reajuste — labels e título como annotations."""
    import re
    barmode = "100%" if proporcao else "group"
    fig = gt10_tabulador(df, "desfecho", "teve_reajuste", "inclusoes", barmode, show_values)
    fig.update_xaxes(showticklabels=False, tickangle=0, title="")
    seen: set = set()
    vals: list[str] = []
    for tr in fig.data:
        for v in tr.x:
            if isinstance(v, str) and v not in seen:
                seen.add(v)
                vals.append(v)
    for i, v in enumerate(vals):
        s = str(v)
        if "decisão " in s and s.startswith("Concluído"):
            s = s.replace("decisão ", "decisão<br>", 1)
        else:
            s = re.sub(r"\s*-\s*", "<br>", s, count=1)
        fig.add_annotation(
            x=i, y=0, xref="x", yref="paper", yshift=-25,
            text=s, showarrow=False,
            font=dict(family="Arial, sans-serif", size=17, color="black"),
            xanchor="center", yanchor="top",
        )
    fig.add_annotation(
        x=0.5, y=-0.2, xref="paper", yref="paper",
        text="Desfecho detalhado", showarrow=False,
        font=dict(family="Arial, sans-serif", size=18, color="black"),
        xanchor="center", yanchor="top",
    )
    fig.update_layout(margin=dict(b=240), legend=dict(y=-0.28))
    return fig
