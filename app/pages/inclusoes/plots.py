"""Figuras Plotly para a página de Inclusões em Pauta."""

from __future__ import annotations
import plotly.graph_objects as go
import pandas as pd

from visual.base import (
    aplicar_padrao, add_er_marker, add_espin_shade, br,
    AZUL, AZUL_CLARO, CINZA, VERDE, ROXO, VERMELHO, ER_DATAS,
)
from visual.paleta import canonico, cor

CORES_CLASSE = {
    "ADI":  "#2563eb",
    "ADPF": "#f59e0b",
    "ADC":  "#16a34a",
    "ADO":  "#ef4444",
}
CORES_MACRO = {
    "Concluído":     "#2a78d6",
    "Não concluído": "#eb6834",
}
# Macrocategorias de I12 (Prevalência da relatoria/divergência) — cor pedida
# explicitamente fora da paleta validada, só usada nesse gráfico (vetorial,
# não passa pelo recolore central de visual/tema.py).
CORES_MACRO_DESFECHO = {
    "Prevalência da relatoria":   "#a2eb98",
    "Prevalência da divergência": "#d64e45",
}
CORES_TIPO = {
    "PR": "#2563eb",
    "RC": "#f59e0b",
    "QI": "#16a34a",
}
CORES_CATEGORIA = {
    "1 - Unânime":                    "#16a34a",
    "2 - Maioria (relator vencedor)": "#2563eb",
    "3 - Maioria (relator vencido)":  "#f59e0b",
    "4 - Não concluído (bloco)":      "#9ca3af",
}
CORES_NC = {
    "1 - Pedido de vista":   "#8b5cf6",
    "2 - Destaque":          "#ec4899",
    "3 - Retirado de pauta": "#f59e0b",
    "4 - Motivos diversos":  "#9ca3af",
}
CORES_DESFECHO_CONCLUIDO = {
    "Concluído - decisão unânime":                    "#184f95",
    "Concluído - decisão maioria com o relator":      "#2a78d6",
    "Concluído - decisão maioria, vencido o relator": "#86b6ef",
}
CORES_SUST = {
    "Com sustentação oral": "#0891b2",
    "Sem sustentação oral": "#e5e7eb",
}
CORES_REAJUSTE = {
    "Com reajuste de voto": "#dc2626",
    "Sem reajuste de voto": "#e5e7eb",
}
COR_PV    = "#2563eb"
COR_PP    = "#94a3b8"
# Exceção só para I1 (pedido explícito, diverge da paleta central de
# "Plenário Virtual"/"Plenário Presencial" usada nos outros ~90 gráficos).
COR_PV_I1 = "#b8136f"
COR_PP_I1 = "#5c5c5c"

_CLASSES = ["ADI", "ADPF", "ADC", "ADO"]
_TIPOS   = ["PR", "RC", "QI"]

# Legenda horizontal acima do gráfico (barras com múltiplas séries).
_LEGEND_BARRAS = dict(
    orientation="h", yanchor="bottom", y=1.1, xanchor="center", x=0.5,
    font=dict(family="Arial, sans-serif", size=14, color="black"),
)
# Legenda horizontal abaixo do gráfico (pizzas).
_LEGEND_PIZZA = dict(
    orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5,
    font=dict(family="Arial, sans-serif", size=14, color="black"),
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _bar_fig(barmode: str = "group") -> go.Figure:
    fig = go.Figure()
    fig.update_layout(barmode=barmode)
    return fig


def _marcos_temporais(fig: go.Figure, y_max: float, ano_min: int = 2016, ano_max: int = 2025,
                      excluir_ers: tuple = ()) -> go.Figure:
    """ER 51/52/53 e sombreamento ESPIN em gráficos anuais, só quando a data cai
    dentro do intervalo de anos efetivamente plotado (eixo x = ano, ano_base=0)."""
    if y_max <= 0:
        return fig
    y1 = y_max * 1.15
    y_label = y_max * 1.22
    for er, (ano, _mes, _dia) in ER_DATAS.items():
        if er in excluir_ers:
            continue
        if ano_min <= ano <= ano_max:
            add_er_marker(fig, 0, er, 0, y1, y_label)
    if ano_min <= 2022 and ano_max >= 2020:
        add_espin_shade(fig, 0, 0, y1)
    return fig


def _composicao(series: pd.Series, titulo: str, cores: list | None = None,
                show_values: bool = True, proporcao: bool = False,
                **_ignorado) -> go.Figure:
    """Composição parte-de-um-todo como barra horizontal, com o % na ponta.

    Substitui as pizzas. A Pessoa 2 pediu zero gráficos de pizza, e para
    composição sem eixo temporal a barra horizontal é o substituto correto —
    linha responderia outra pergunta. Categoria à esquerda, maior no topo, e o
    percentual na ponta da barra, que é o formato que ela indicou no G22/G23.

    `proporcao` alterna o eixo x entre contagem e percentual, mantendo o rótulo
    (que já mostra os dois). Sem isto o parâmetro seria aceito e ignorado — o
    toggle de escala que não faz nada, a classe de bug já vista neste projeto.

    `**_ignorado` absorve `buraco`, que só fazia sentido em pizza.
    """
    s = series.sort_values(ascending=False)         # menor no topo, maior na base (1ª categoria = base no plotly)
    total = float(s.sum()) or 1.0
    pct = s / total * 100

    rotulos = [canonico(str(i)) for i in s.index]
    if cores is not None:
        # `cores` vinha na ordem original da série; reordenar junto com ela
        ordem = {str(i): c for i, c in zip(series.index, cores)}
        marker_cor = [ordem.get(str(i)) for i in s.index]
    else:
        marker_cor = [cor(r) for r in rotulos]

    fig = go.Figure(go.Bar(
        x=pct.values if proporcao else s.values, y=rotulos, orientation="h",
        marker_color=marker_cor,
        text=[f"{p:.1f}%  ({br(v)})" for p, v in zip(pct, s.values)] if show_values else None,
        textposition="outside", cliponaxis=False,
    ))
    aplicar_padrao(
        fig, titulo,
        height=max(320, 90 + 46 * len(s)),
        margin=dict(t=110, b=60, l=220, r=120),
        showlegend=False,                            # o rótulo já está no eixo
        xaxis=dict(title="Percentual de desfechos (%)" if proporcao else "Inclusões em pauta",
                   range=[0, 100] if proporcao else None),
        yaxis=dict(title=""),
    )
    return fig


# Nome antigo mantido enquanto os chamadores migram; a função não faz mais pizza.
_pizza = _composicao


def _categoria_desfecho(d: str) -> str:
    if d == "Concluído - decisão unânime":
        return "1 - Unânime"
    if d == "Concluído - decisão maioria com o relator":
        return "2 - Maioria (relator vencedor)"
    if d == "Concluído - decisão maioria, vencido o relator":
        return "3 - Maioria (relator vencido)"
    return "4 - Não concluído (bloco)"


def _sem_nao_concluido(d: pd.DataFrame) -> pd.DataFrame:
    """Só as três categorias de desfecho concluído — remove o balde de não concluído.

    A fonte da verdade é `_categoria_desfecho`, que produz
    "4 - Não concluído (bloco)" como fallback para todo desfecho não concluído.
    Excluir é remover essa categoria produzida, nunca filtrar a string de
    desfecho — assim a regra fica num lugar só e as variantes "sem não
    concluído" (6.b–6.e) não podem divergir do G22/G24/G26/G28.
    """
    return d[d["categoria"] != "4 - Não concluído (bloco)"]


def _categoria_nc(d: str) -> str:
    if d == "Não concluído - pedido de vista":
        return "1 - Pedido de vista"
    if d == "Não concluído - destaque":
        return "2 - Destaque"
    if d == "Não concluído - retirado de pauta":
        return "3 - Retirado de pauta"
    return "4 - Motivos diversos"


def _barras_grupo(df_amb: pd.DataFrame, col_x: str, col_grupo: str,
                  cores: dict, titulo: str, label_y: str,
                  label_total: str, x_title: str = "Ano",
                  show_values: bool = True, proporcao: bool = False,
                  proporcao_global: bool = False, excluir_ers: tuple = (),
                  label_y_proporcao: str | None = None) -> go.Figure:
    # label_total: mantido por compatibilidade de assinatura; a linha de total
    # foi removida (PADRÃO GERAL não permite linha de tendência de total).
    tab = df_amb.groupby([col_x, col_grupo], observed=True).size().reset_index(name="n")
    grupos = list(cores.keys())

    if proporcao:
        if proporcao_global:
            # % do total geral (6.f: cada desfecho como fração de todos os
            # desfechos do âmbito). Sem isto o % seria por grupo-x (100% por
            # desfecho), o que responderia outra pergunta.
            total_geral = float(tab["n"].sum())
            tab["y"] = (tab["n"] / total_geral * 100).round(1)
        else:
            totais_x = tab.groupby(col_x)["n"].transform("sum")
            tab["y"] = (tab["n"] / totais_x * 100).round(1)
        # item 6.f pede o rótulo "Quantidade de desfechos" mesmo com o dado em
        # percentual — label_y_proporcao existe só para esse caso pedir um
        # texto de eixo diferente do "% do total" padrão.
        y_label = label_y_proporcao or "% do total"
        texto = tab["y"].apply(lambda v: f"{v:.1f}%") if show_values else None
    else:
        tab["y"] = tab["n"]
        y_label = label_y
        texto = tab["y"] if show_values else None

    fig = _bar_fig()
    for g in grupos:
        d = tab[tab[col_grupo] == g]
        if d.empty:
            continue
        fig.add_trace(go.Bar(
            x=d[col_x], y=d["y"], name=g,
            marker_color=cores[g],
            text=texto[d.index] if isinstance(texto, pd.Series) else texto,
            textposition="outside", cliponaxis=False,
            textfont=dict(size=20, color="black", weight="bold"),
        ))
    aplicar_padrao(fig, titulo, showlegend=True, legend=_LEGEND_BARRAS,
                    xaxis=dict(title=x_title, dtick=1),
                    yaxis_title=y_label)
    if col_x == "ano" and not tab.empty:
        _marcos_temporais(fig, tab["y"].max(), tab[col_x].min(), tab[col_x].max(),
                          excluir_ers=excluir_ers)
    return fig


# ═══════════════════════════════════════════════════════════════════════════════
# GRÁFICOS 5–17  (bloco INCLUSÕES EM PAUTA)
# ═══════════════════════════════════════════════════════════════════════════════

def g5_anual_ambiente(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False) -> tuple[go.Figure, go.Figure]:
    tab = df.groupby(["ano", "ambiente"], observed=True).size().reset_index(name="n")
    fig = _bar_fig()
    for amb, cor_ in [("Plenário Virtual", COR_PV_I1), ("Plenário Presencial", COR_PP_I1)]:
        d = tab[tab["ambiente"] == amb]
        texto = d["n"] if show_values else None
        fig.add_trace(go.Bar(
            # Cor vetorial (uma por barra) sobrevive ao recolore de
            # visual/tema.py — escalar seria trocado pelo azul/laranja da
            # paleta central por causa do name reconhecido.
            x=d["ano"], y=d["n"], name=amb.upper(), marker_color=[cor_] * len(d),
            text=texto, textposition="outside", cliponaxis=False,
        ))
    aplicar_padrao(fig, "Plenário Virtual concentra a maior parte das inclusões em pauta",
                   "Inclusões por ano e ambiente (Plenário Virtual vs Plenário Presencial)",
                   showlegend=True, legend=_LEGEND_BARRAS,
                   xaxis=dict(title="Ano", dtick=1),
                   yaxis_title="Inclusões")
    if not tab.empty:
        _marcos_temporais(fig, tab["n"].max(), tab["ano"].min(), tab["ano"].max())

    pizza = df["ambiente"].value_counts()
    cores_pizza = [COR_PV_I1 if l == "Plenário Virtual" else COR_PP_I1
                   for l in pizza.index]
    fig_p = _pizza(pizza, "Proporção PV vs PP (período total)", cores=cores_pizza,
                   show_values=show_values)
    return fig, fig_p


def g6_classe_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                        ambiente: str = "Plenário Virtual",
                        classes: list[str] | None = None) -> tuple[go.Figure, go.Figure]:
    d = df[df["ambiente"] == ambiente]
    if classes:
        d = d[d["classe"].isin(classes)]
    fig = _barras_grupo(d, "ano", "classe", CORES_CLASSE,
                        f"Inclusões por classe e ano — {ambiente}",
                        "Inclusões por classe", f"Total (linha)",
                        show_values=show_values, proporcao=proporcao)
    fig_p = _pizza(d["classe"].value_counts(),
                   f"Proporção por classe — {ambiente} (período total)",
                   cores=[CORES_CLASSE.get(l, "#999") for l in d["classe"].value_counts().index],
                   show_values=show_values)
    return fig, fig_p


def g8_desfecho_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                          ambiente: str = "Plenário Virtual") -> tuple[go.Figure, go.Figure]:
    d = df[df["ambiente"] == ambiente]
    vc = d["macro_desfecho"].value_counts()
    fig_macro = _pizza(vc, f"Concluídos e não concluídos — {ambiente} (período total)",
                       cores=[CORES_MACRO.get(l, "#94a3b8") for l in vc.index],
                       show_values=show_values, proporcao=proporcao)
    fig_det = _pizza(d["desfecho"].value_counts(),
                     f"Desfecho detalhado — {ambiente} (período total)", buraco=0.3,
                     show_values=show_values, proporcao=proporcao)
    return fig_macro, fig_det


def g6f_desfecho_percentual_ambiente(df: pd.DataFrame, ambiente: str = "Plenário Virtual",
                                     show_values: bool = True) -> go.Figure:
    """Item 6.f — desfecho em percentual por ambiente.

    X = os sete desfechos, Y = "Percentual de desfechos (%)", cada barra como
    fração do total de desfechos do âmbito. Recorte por `ambiente` da inclusão,
    não por `tramitacao` — T6 continua sendo o por tramitação. Um ambiente por
    entrada, duas entradas no catálogo.
    """
    sub = df[df["ambiente"] == ambiente]
    return _barras_grupo(sub, "desfecho", "ambiente", {ambiente: AZUL},
                         f"Desfechos por percentual — {ambiente}",
                         "Quantidade de desfechos", "Total (linha)",
                         x_title="Tipo de desfechos", show_values=show_values,
                         proporcao=True, proporcao_global=True,
                         label_y_proporcao="Quantidade de desfechos")


# Agrupamentos do item 6.b2/6.b3: nomes de série -> desfechos agregados.
# Strings verbatim do dado ("decisão maioria", sem "por", e a vírgula em
# "maioria, vencido o relator").
_AGRUPAMENTOS_DECISAO: dict[str, dict[str, tuple[str, ...]]] = {
    "unânime_vs_divergência": {
        "Julgamento por unanimidade":   ("Concluído - decisão unânime",),
        "Julgamento com divergência(s)": ("Concluído - decisão maioria com o relator",
                                          "Concluído - decisão maioria, vencido o relator"),
    },
    # Mesmos dois grupos e mesmo nome do macro do I12 (item 6.b) — I24/25/26
    # são a mesma análise em série temporal, precisam da mesma legenda e cor.
    "relator_vs_divergência": {
        "Prevalência da relatoria":   ("Concluído - decisão unânime",
                                       "Concluído - decisão maioria com o relator"),
        "Prevalência da divergência": ("Concluído - decisão maioria, vencido o relator",),
    },
}

# Macrocategoria de I12: as 3 categorias de desfecho concluído (chaves de
# `_categoria_desfecho`) agrupadas em 2 — quem prevalece é o relator ou a
# divergência.
_AGRUPAMENTO_MACRO_I12: dict[str, tuple[str, ...]] = {
    "Prevalência da relatoria":   ("1 - Unânime", "2 - Maioria (relator vencedor)"),
    "Prevalência da divergência": ("3 - Maioria (relator vencido)",),
}

# Mesmo esquema do I12, mas agrupando pelo critério de I21-23 (unânime vs
# divergência, sem distinguir se a divergência venceu ou perdeu o relator).
_AGRUPAMENTO_MACRO_UNANIME: dict[str, tuple[str, ...]] = {
    "Julgamento por unanimidade":    ("1 - Unânime",),
    "Julgamento com divergência(s)": ("2 - Maioria (relator vencedor)", "3 - Maioria (relator vencido)"),
}


def linha_decisao(df: pd.DataFrame, agrupamento: str = "unânime_vs_divergência",
                  ambiente: str = "Plenário Virtual",
                  show_values: bool = True, proporcao: bool = False,
                  excluir_ers: tuple = ()) -> go.Figure:
    """Item 6.b2/6.b3 — série temporal de unanimidade contra divergência.

    Monta como barras agrupadas por ano (não linha à mão); o catálogo declara
    `tipos=("linha", "barra")` e `visual.tema.converter_tipo` faz a conversão,
    o mesmo mecanismo das outras páginas. "Ambos os ambientes" não filtra.
    """
    grupos = _AGRUPAMENTOS_DECISAO[agrupamento]
    sub = df if ambiente == "Ambos os ambientes" else df[df["ambiente"] == ambiente]
    mapa = {d: nome for nome, ds in grupos.items() for d in ds}
    sub = sub.assign(serie=sub["desfecho"].map(mapa)).dropna(subset=["serie"])
    # Prevalência da relatoria/divergência usa a cor local do I12 (fora da
    # paleta validada, pedido explícito) — paleta.cor() só entra pro grupo
    # unânime_vs_divergência, que continua nos tons de azul de sempre.
    cores = {nome: CORES_MACRO_DESFECHO.get(nome) or cor(nome) for nome in grupos}
    fig = _barras_grupo(sub, "ano", "serie", cores,
                        f"Unanimidade contra divergência — {ambiente}",
                        "Quantidade de processos incluídos em pauta", "Total (linha)",
                        show_values=show_values, proporcao=proporcao, excluir_ers=excluir_ers)
    # Cor vetorial só pra Prevalência da relatoria/divergência — protege o
    # hex fora da paleta do recolore de visual/tema.py, mesmo mecanismo do
    # I1. As séries de unânime_vs_divergência continuam escalares, seguindo
    # a paleta normalmente (inclusive variante escura).
    for tr in fig.data:
        if tr.name in CORES_MACRO_DESFECHO:
            tr.marker.color = [CORES_MACRO_DESFECHO[tr.name]] * len(tr.x)
    return fig


def g7b_unanimidade_vs_divergencia_2010_2025(df: pd.DataFrame, show_values: bool = True) -> go.Figure:
    """7.b — linha temporal unânime vs divergência, PP+PV, 2010–2025.

    Destravado pela #5 (pipeline estendido a 2009). Período fixo recortado aqui
    dentro; sem `periodo` em `filtros`. Marcos ER 51/52 — o pedido original
    exclui o ER 53 ("marcos ER exceto ER 53"); o ESPIN permanece.
    """
    sub = df[(df["ano"] >= 2010) & (df["ano"] <= 2025)]
    return linha_decisao(sub, ambiente="Ambos os ambientes", show_values=show_values,
                         excluir_ers=(53,))


def g10_macro_anual_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                              ambiente: str = "Plenário Virtual") -> go.Figure:
    return _macro_anual(df[df["ambiente"] == ambiente],
                        f"Concluídos e não concluídos por ano — {ambiente}",
                        show_values=show_values, proporcao=proporcao)


def g12_concluidos_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                             ambiente: str = "Plenário Virtual", segmentar: bool = False) -> go.Figure:
    return _concluidos_anual(df[df["ambiente"] == ambiente],
                             f"Concluídos por ano — {ambiente}",
                             show_values=show_values, proporcao=proporcao, segmentar=segmentar)


def g14_nao_concluidos_classe_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                                        ambiente: str = "Plenário Virtual") -> go.Figure:
    return _por_classe_com_total(df[df["ambiente"] == ambiente],
                                 "Não concluído",
                                 f"Não concluídos por classe e ano — {ambiente}",
                                 f"Total não concluídos",
                                 show_values=show_values, proporcao=proporcao)


def g16_concluidos_classe_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                                    ambiente: str = "Plenário Virtual") -> go.Figure:
    return _por_classe_com_total(df[df["ambiente"] == ambiente],
                                 "Concluído",
                                 f"Concluídos por classe e ano — {ambiente}",
                                 f"Total concluídos",
                                 show_values=show_values, proporcao=proporcao)


def _macro_anual(df_amb: pd.DataFrame, titulo: str,
                 show_values: bool = True, proporcao: bool = False) -> go.Figure:
    tab = df_amb.groupby(["ano", "macro_desfecho"], observed=True).size().reset_index(name="n")
    if proporcao:
        totais = tab.groupby("ano")["n"].transform("sum")
        tab["y"] = (tab["n"] / totais * 100).round(1)
        texto = tab["y"].apply(lambda v: f"{v:.1f}%") if show_values else None
        y_title = "% do total"
    else:
        tab["y"] = tab["n"]
        texto = tab["y"] if show_values else None
        y_title = "Inclusões em pauta"

    fig = _bar_fig()
    for macro in ["Concluído", "Não concluído"]:
        d = tab[tab["macro_desfecho"] == macro]
        if d.empty:
            continue
        fig.add_trace(go.Bar(
            x=d["ano"], y=d["y"], name=macro.upper(),
            marker_color=CORES_MACRO[macro],
            text=texto[d.index] if isinstance(texto, pd.Series) else texto,
            textposition="outside", cliponaxis=False,
        ))
    aplicar_padrao(fig, titulo, showlegend=True, legend=_LEGEND_BARRAS,
                   xaxis=dict(title="Ano", dtick=1),
                   yaxis_title=y_title)
    if not tab.empty:
        _marcos_temporais(fig, tab["y"].max(), tab["ano"].min(), tab["ano"].max())
    return fig


def _concluidos_anual(df_amb: pd.DataFrame, titulo: str,
                      show_values: bool = True, proporcao: bool = False,
                      segmentar: bool = False) -> go.Figure:
    sub = df_amb[df_amb["macro_desfecho"] == "Concluído"]
    if segmentar:
        return _barras_grupo(sub, "ano", "desfecho", CORES_DESFECHO_CONCLUIDO,
                             titulo, "Inclusões concluídas", "Total (linha)",
                             show_values=show_values, proporcao=proporcao)

    tab = sub.groupby("ano").size().reset_index(name="n")
    if proporcao:
        total_ano = df_amb.groupby("ano").size().reset_index(name="t")
        tab = tab.merge(total_ano, on="ano")
        tab["y"] = (tab["n"] / tab["t"] * 100).round(1)
        texto = tab["y"].apply(lambda v: f"{v:.1f}%") if show_values else None
        y_title = "% de concluídos"
    else:
        tab["y"] = tab["n"]
        texto = tab["y"] if show_values else None
        y_title = "Inclusões concluídas"

    fig = _bar_fig()
    fig.add_trace(go.Bar(
        x=tab["ano"], y=tab["y"], name="CONCLUÍDOS",
        marker_color=CORES_MACRO["Concluído"],
        text=texto, textposition="outside", cliponaxis=False,
    ))
    aplicar_padrao(fig, titulo, xaxis=dict(title="Ano", dtick=1),
                   yaxis_title=y_title)
    if not tab.empty:
        _marcos_temporais(fig, tab["y"].max(), tab["ano"].min(), tab["ano"].max())
    return fig


def _por_classe_com_total(df_amb: pd.DataFrame, filtro_macro: str,
                           titulo: str, label_total: str,
                           show_values: bool = True, proporcao: bool = False) -> go.Figure:
    df_f = df_amb[df_amb["macro_desfecho"] == filtro_macro]
    return _barras_grupo(df_f, "ano", "classe", CORES_CLASSE,
                         titulo, "Inclusões por classe", label_total,
                         show_values=show_values, proporcao=proporcao)


# ═══════════════════════════════════════════════════════════════════════════════
# GRUPO 1 — Tipo de questão por ano  (gráficos 18–21)
# ═══════════════════════════════════════════════════════════════════════════════

def _prep_tipo(df: pd.DataFrame) -> pd.DataFrame:
    """IJ->QI é rótulo. "Não identificado"->PR já vem de `layout.render_graficos`
    (fonte única da página, vale pra I9/I10/I11/I12/I15-I18/I29 igual)."""
    d = df.copy()
    d["tipo_questao"] = d["tipo_questao"].replace({"IJ": "QI"})
    return d


RE_EXCLUSAO = (
    r'Incluído na Lista|Agendado para|Julgamento Presencial|'
    r'Sess[ãa]o (?:Ordinária|Extraordinária|Ordinaria|Extraordinaria) Virtual'
)


def _classificar_desfecho_texto(texto: str) -> str | None:
    if not isinstance(texto, str) or not texto.strip():
        return None
    t = texto.strip().lower()
    if 'unânime' in t or 'unanimidade' in t:
        return 'concluido_unanime'
    if 'por maioria' in t or 'vencido' in t:
        return 'concluido_maioria'
    if 'procedente' in t or 'improcedente' in t or 'parcialmente' in t:
        return 'concluido_merito'
    if 'indeferiu' in t or 'não conheceu' in t:
        return 'concluido_sem_merito'
    return None


def _refinar_motivos_diversos(df: pd.DataFrame, df_dec: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    mask_div = (d["ambiente"] == "Plenário Presencial") & (d["desfecho"] == "Não concluído - motivos diversos")
    if not mask_div.any():
        return d

    dec_pleno = pd.DataFrame()
    if not df_dec.empty and 'dec_julgador' in df_dec.columns:
        dec_pleno = df_dec[
            (df_dec['dec_julgador'].str.strip().str.upper() == 'TRIBUNAL PLENO') &
            (~df_dec['dec_complemento'].str.contains(RE_EXCLUSAO, case=False, na=False, regex=True))
        ].copy()
        if not dec_pleno.empty:
            dec_pleno['dec_data_dt'] = pd.to_datetime(dec_pleno['dec_data'], dayfirst=True, errors='coerce')

    indices_div = d.index[mask_div]
    novos = []
    for idx in indices_div:
        row = d.loc[idx]
        inc = row['incidente']
        inicio = row['data_inclusao_dt']

        proximas = d[(d['incidente'] == inc) & (d['data_inclusao_dt'] > inicio)]['data_inclusao_dt']
        fim = proximas.min() if not proximas.empty else pd.Timestamp('2026-12-31')

        if dec_pleno.empty:
            novos.append('Não concluído - sem decisão registrada')
            continue

        dec_janela = dec_pleno[
            (dec_pleno['incidente'] == inc) &
            (dec_pleno['dec_data_dt'] >= inicio) &
            (dec_pleno['dec_data_dt'] < fim)
        ]

        if dec_janela.empty:
            novos.append('Não concluído - sem decisão registrada')
        else:
            classificaveis = [
                t for t in dec_janela['dec_complemento']
                if _classificar_desfecho_texto(t) is not None
            ]
            if classificaveis:
                novos.append('Não concluído - decisão não capturada')
            else:
                novos.append('Não concluído - registro sem fórmula de votação')

    d.loc[mask_div, 'desfecho'] = novos
    return d


def g18_nc_tipo_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                          ambiente: str = "Plenário Virtual") -> go.Figure:
    sub = _prep_tipo(df[(df["ambiente"] == ambiente) &
                        (df["macro_desfecho"] == "Não concluído")])
    return _barras_grupo(sub, "ano", "tipo_questao", CORES_TIPO,
                         f"Não concluídos por tipo de questão — {ambiente}",
                         "Inclusões em pauta", "Total não concluídos",
                         show_values=show_values, proporcao=proporcao)


def g20_c_tipo_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                         ambiente: str = "Plenário Virtual") -> go.Figure:
    sub = _prep_tipo(df[(df["ambiente"] == ambiente) &
                        (df["macro_desfecho"] == "Concluído")])
    return _barras_grupo(sub, "ano", "tipo_questao", CORES_TIPO,
                         f"Concluídos por tipo de questão — {ambiente}",
                         "Inclusões em pauta", "Total concluídos",
                         show_values=show_values, proporcao=proporcao)


def _prep_cat(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["categoria"] = d["desfecho"].apply(_categoria_desfecho)
    return d


# I12/I16 pediram a legenda sem o prefixo "Concluído – ". `canonico()` faria o
# caminho inverso (código curto -> nome canônico completo), então o rótulo
# curto é resolvido aqui e a cor é buscada pelo nome canônico original, antes
# da troca — senão cai no degrau de reserva por não bater com a paleta.
_ROTULO_CATEGORIA_CURTO = {
    "1 - Unânime":                    "Decisão unânime",
    "2 - Maioria (relator vencedor)": "Decisão maioria com o relator",
    "3 - Maioria (relator vencido)":  "Decisão maioria, vencido o relator",
}


def _pizza_categoria(t: str, vc: pd.Series, titulo: str, show_values: bool,
                     proporcao: bool = False) -> go.Figure:
    """Composição das categorias de desfecho para um tipo de questão.

    Era pizza; virou barra horizontal pelo mesmo motivo das demais.
    """
    cores = [cor(canonico(l)) for l in vc.index]
    vc_curto = vc.rename(index=_ROTULO_CATEGORIA_CURTO)
    return _composicao(vc_curto, titulo, cores=cores, show_values=show_values, proporcao=proporcao)


def _pizzas_categoria_por_tipo(sub: pd.DataFrame, ambiente_label: str,
                               show_values: bool = True, proporcao: bool = False) -> list[go.Figure]:
    tipos = [t for t in _TIPOS if t in sub["tipo_questao"].unique()]
    return [
        _pizza_categoria(
            t,
            sub[sub["tipo_questao"] == t]["categoria"].value_counts().sort_index(),
            f"{t} — {ambiente_label}",
            show_values,
            proporcao=proporcao,
        )
        for t in tipos
    ]


def g22_cat_periodo_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                              ambiente: str = "Plenário Virtual",
                              excluir_nc: bool = False, macro: bool = False,
                              macro_unanime: bool = False) -> go.Figure:
    sub = _prep_cat(df[df["ambiente"] == ambiente])
    if excluir_nc or macro or macro_unanime:
        sub = _sem_nao_concluido(sub)
    if macro_unanime:
        mapa = {c: nome for nome, cs in _AGRUPAMENTO_MACRO_UNANIME.items() for c in cs}
        vc = sub["categoria"].map(mapa).value_counts()
        return _pizza(vc, f"Julgamento por unanimidade vs divergência — {ambiente} (período total)",
                      cores=[cor(l) for l in vc.index],
                      show_values=show_values, proporcao=proporcao)
    if macro:
        mapa = {c: nome for nome, cs in _AGRUPAMENTO_MACRO_I12.items() for c in cs}
        vc = sub["categoria"].map(mapa).value_counts()
        return _pizza(vc, f"Prevalência da relatoria vs divergência — {ambiente} (período total)",
                      cores=[CORES_MACRO_DESFECHO.get(l, "#999") for l in vc.index],
                      show_values=show_values, proporcao=proporcao)
    # Sem `cores=`: cai no fallback de paleta (mesmo caminho de I16), que já
    # resolve as 3 categorias concluídas em tons de azul validados — não
    # duplicar hex num dict local que pode divergir da paleta central.
    vc = sub["categoria"].value_counts().sort_index()
    return _pizza(vc, f"Desfecho por categoria — {ambiente} (período total)",
                  show_values=show_values, proporcao=proporcao)


def g24_cat_anual_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                            ambiente: str = "Plenário Virtual",
                            excluir_nc: bool = False) -> go.Figure:
    sub = _prep_cat(df[df["ambiente"] == ambiente])
    if excluir_nc:
        sub = _sem_nao_concluido(sub)
    return _barras_grupo(sub, "ano", "categoria", CORES_CATEGORIA,
                         f"Desfecho por categoria e ano — {ambiente}",
                         "Quantidade de processos incluídos em pauta", "Total (linha)",
                         show_values=show_values, proporcao=proporcao)


def g7a_desfechos_pp_2009_2019(df: pd.DataFrame, show_values: bool = True) -> go.Figure:
    """7.a — Desfechos do Plenário Presencial 2009–2019, só concluídos, em %.

    Estilo G24/25 (desfecho por categoria e ano) sobre o ambiente presencial
    antes da universalização do PV, período fixo recortado aqui dentro — como
    toda entrada de período fixo, não declara `periodo` em `filtros`.

    O filtro é por "Plenário Presencial", não "Plenário Físico": o loader
    renomeia o valor na carga, então comparar com o nome antigo nunca casa e o
    gráfico sai vazio. Mesma armadilha que já derrubou _classificar_tramitacao.
    """
    sub = _prep_cat(df[df["ambiente"] == "Plenário Presencial"])
    sub = sub[(sub["ano"] >= 2009) & (sub["ano"] <= 2019)]
    sub = _sem_nao_concluido(sub)
    return _barras_grupo(sub, "ano", "categoria", CORES_CATEGORIA,
                         "Desfecho por categoria e ano — Plenário Presencial (2009–2019)",
                         "Quantidade de processos incluídos em pauta", "Total (linha)",
                         show_values=show_values, proporcao=True)


def g26_cat_tipo_periodo_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                                   ambiente: str = "Plenário Virtual",
                                   excluir_nc: bool = False) -> list[go.Figure]:
    sub = _prep_cat(_prep_tipo(df[df["ambiente"] == ambiente]))
    if excluir_nc:
        sub = _sem_nao_concluido(sub)
    return _pizzas_categoria_por_tipo(sub, ambiente, show_values=show_values, proporcao=proporcao)


def g28_cat_tipo_anual_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                                 ambiente: str = "Plenário Virtual",
                                 excluir_nc: bool = False) -> dict[str, go.Figure]:
    sub = _prep_cat(_prep_tipo(df[df["ambiente"] == ambiente]))
    if excluir_nc:
        sub = _sem_nao_concluido(sub)
    return {t: _barras_grupo(sub[sub["tipo_questao"] == t],
                              "ano", "categoria", CORES_CATEGORIA,
                              f"Desfecho por categoria — {t} — {ambiente}",
                              "Inclusões em pauta", f"Total {t} (linha)",
                              show_values=show_values, proporcao=proporcao)
            for t in _TIPOS if not sub[sub["tipo_questao"] == t].empty}


def g30_nc_cat_anual_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                               ambiente: str = "Plenário Virtual") -> go.Figure:
    sub = _prep_nc(df[df["ambiente"] == ambiente])
    return _barras_grupo(sub, "ano", "categoria_nc", CORES_NC,
                         f"Não concluídos por categoria e ano — {ambiente}",
                         "Inclusões em pauta", "Total não concluídos",
                         show_values=show_values, proporcao=proporcao)


def g32_nc_cat_classe_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                                ambiente: str = "Plenário Virtual") -> dict[str, go.Figure]:
    sub = _prep_nc(df[df["ambiente"] == ambiente])
    return {c: _barras_grupo(sub[sub["classe"] == c],
                              "ano", "categoria_nc", CORES_NC,
                              f"Não concluídos por categoria — {c} — {ambiente}",
                              "Inclusões em pauta", f"Total {c} (linha)",
                              show_values=show_values, proporcao=proporcao)
            for c in _CLASSES if not sub[sub["classe"] == c].empty}


def g34_nc_cat_tipo_filtravel(df: pd.DataFrame, show_values: bool = True, proporcao: bool = False,
                              ambiente: str = "Plenário Virtual") -> dict[str, go.Figure]:
    sub = _prep_nc(_prep_tipo(df[df["ambiente"] == ambiente]))
    return {t: _barras_grupo(sub[sub["tipo_questao"] == t],
                              "ano", "categoria_nc", CORES_NC,
                              f"Não concluídos por categoria — {t} — {ambiente}",
                              "Inclusões em pauta", f"Total {t} (linha)",
                              show_values=show_values, proporcao=proporcao)
            for t in _TIPOS if not sub[sub["tipo_questao"] == t].empty}


# ═══════════════════════════════════════════════════════════════════════════════
# GRUPO 4 — Desfecho não concluído por categoria  (gráficos 30–35)
# ═══════════════════════════════════════════════════════════════════════════════

def _prep_nc(df: pd.DataFrame) -> pd.DataFrame:
    d = df[df["macro_desfecho"] == "Não concluído"].copy()
    d["categoria_nc"] = d["desfecho"].apply(_categoria_nc)
    return d


# ═══════════════════════════════════════════════════════════════════════════════
# GRUPO 5 — Pauta vs concluídos (PV, período total)
# ═══════════════════════════════════════════════════════════════════════════════

def g_pauta_concluidos(df: pd.DataFrame, show_values: bool = True, **kwargs) -> go.Figure:
    pv = df[df["ambiente"] == "Plenário Virtual"]
    pct_pauta = 100 * len(pv) / len(df)
    concluidos = df[df["macro_desfecho"] == "Concluído"]
    pct_concluidos = 100 * len(pv[pv["macro_desfecho"] == "Concluído"]) / len(concluidos)
    categorias = ['Participação<br>na pauta', 'Participação nos<br>julgamentos concluídos']
    valores = [pct_pauta, pct_concluidos]

    fig = _bar_fig()
    fig.add_trace(go.Bar(
        x=categorias, y=valores, marker_color=COR_PV,
        text=[f'{v:.1f}%' for v in valores] if show_values else None,
        textposition='outside', cliponaxis=False, showlegend=False,
    ))
    aplicar_padrao(fig, "Plenário Virtual concentra julgamentos concluídos muito além de sua participação na pauta",
                   f"Participação na pauta ({pct_pauta:.1f}%) vs. participação nos julgamentos concluídos ({pct_concluidos:.1f}%) — período total",
                   height=650, yaxis=dict(range=[0, 110]), xaxis=dict(title="", tickangle=0))
    return fig

