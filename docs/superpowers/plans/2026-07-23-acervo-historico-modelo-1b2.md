# Acervo Histórico — Padronização Visual (modelo 1.b2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refazer os gráficos da página "Acervo Histórico" (`app/pages/acervo/`) para usar exatamente o mesmo modelo visual de `fig_1b2_acervo_por_classe_vertical` (Bloco 1) — linhas ER/ESPIN, cores de classe, legenda, fontes de eixo — mantendo uma única função paramétrica, e dar a cada gráfico um título/subtítulo que conta a história dos dados (como no 1.b2).

**Architecture:** Um único arquivo (`app/pages/acervo/plots.py`) já concentra a função paramétrica `plotar_grafico_stf`. O trabalho é: (1) trocar a mecânica de ER/ESPIN/cores/legenda/fontes pela implementação bespoke do 1.b2 (copiada, não pelos helpers genéricos `add_er_marker`/`add_espin_shade` de `estilo.py`, que produzem posicionamento e texto diferentes), migrando o eixo X de numérico contínuo para categórico por ano (igual ao 1.b2); (2) adicionar uma tabela de títulos/subtítulos "história" por métrica para a visão TOTAL, e um título calculado dinamicamente (tendência real dos dados) para as visões por classe, para não inventar uma afirmação que não se sustente para toda classe.

**Tech Stack:** Python, pandas, Plotly (`go.Figure`), Streamlit. Sem novas dependências.

## Global Constraints

- Não mexer em `app/pages/bloco1_acervo/`, `bloco2_inclusoes/`, `bloco3_pandemia/` (ou qualquer coisa dos Blocos 1/2/3) — só `app/pages/acervo/`.
- Manter a assinatura pública `plotar_grafico_stf(df, classe_nome, coluna_metrica, label_metrica, show_values=False) -> go.Figure` — é chamada por `app/pages/acervo/layout.py:73` e `:80` sem outros parâmetros; não alterar `layout.py`.
- Cores de barra = `_CORES_CLASSE` do Bloco 1 (`app/pages/bloco1_acervo/plots.py:17`): `{"ADI": "#2563EB", "ADPF": "#93C5FD", "ADC": "#059669", "ADO": "#7C3AED"}`. TOTAL usa `AZUL` (`#2563EB`, de `estilo.py`).
- Fonte de eixo: `tickfont=dict(size=22)`, `title_font=dict(size=22)` nos dois eixos (igual `fig_1b2`, `app/pages/bloco1_acervo/plots.py:207`).
- Legenda: `orientation="h", yanchor="bottom", y=0.95, x=0.5, xanchor="center"` (igual `fig_1b2:203`).
- Layout: `height=650, margin=dict(t=150, b=70, l=60, r=40)` (igual `fig_1b2:204`).
- ER/ESPIN: eixo X passa a ser categórico (`x=anos` como strings), réplica exata da lógica de `fig_1b2_acervo_por_classe_vertical` (`app/pages/bloco1_acervo/plots.py:156-197`), usando `_frac_ano` e `ER_DATAS`/`ANO_MIN=1988` de `estilo.py`.
- Sem novos arquivos de dependência; sem framework de teste novo — usar `assert` simples num `test_plots.py` sem fixtures.

---

## Arquivos afetados

- Modificar: `app/pages/acervo/plots.py` — reescrever `plotar_grafico_stf`, remover `CORES_CLASSE` antigo e `_ER_Y_MULT` antigo, importar `_CORES_CLASSE`/`ANO_MIN`/`_frac_ano`/`ER_DATAS` como no Bloco 1.
- Criar: `app/pages/acervo/test_plots.py` — smoke test assert-based (sem pytest fixtures, roda com `python -m app.pages.acervo.test_plots` ou `pytest`).
- Não tocar: `app/pages/acervo/layout.py`, `app/pages/acervo/acervo.py`, `app/pages/bloco1_acervo/*`, `app/pages/bloco2_inclusoes/*`, `app/pages/bloco3_pandemia/*`.

---

### Task 1: Reescrever `plotar_grafico_stf` com o modelo visual do 1.b2

**Files:**
- Modify: `app/pages/acervo/plots.py` (arquivo inteiro, ~83 linhas atuais)
- Test: `app/pages/acervo/test_plots.py`

**Interfaces:**
- Consumes: de `estilo.py` — `aplicar_padrao(fig, titulo, subtitulo, **kwargs)`, `br(v, d=0)`, `_frac_ano(ano_base, ano, mes, dia)`, `ER_DATAS` (dict `{51:(2016,6,22), 52:(2019,6,14), 53:(2020,3,18)}`), `VERMELHO = "#C00000"`, `AZUL = "#2563EB"`.
- Produces: `plotar_grafico_stf(df: pd.DataFrame, classe_nome: str, coluna_metrica: str, label_metrica: str, show_values: bool = False) -> go.Figure` — mesma assinatura de hoje, comportamento visual novo. Constante módulo `_CORES_CLASSE: dict[str, str]`.

**Dados de referência (já verificados, usar nos títulos — não recalcular hipóteses):**
- `quantidade_ativos` total: pico em 2017 (2357), cai a cada ano até 2025 (1031). ADI é ~70% do acervo ativo em 2025.
- `quantidade_inativos` total: monótono crescente, 1988→2025 (3815 em 2016 → 8295 em 2025).
- `total_geral`: monótono crescente ano a ano (nunca cai, mesmo com ativos caindo).
- `quantidade_baixas`: dispara 2019–2020 (506→797, pico), cai depois (2025: 388).
- `quantidade_distribuidos`: pico em 2020–2021 (503, 572), cai depois (2025: 251).

- [ ] **Step 1: Escrever o smoke test (falha primeiro, função ainda não existe com o novo comportamento)**

```python
# app/pages/acervo/test_plots.py
"""Smoke test do modelo visual de plotar_grafico_stf (padrão 1.b2)."""
import pandas as pd

from pages.acervo.plots import plotar_grafico_stf, _CORES_CLASSE


def _df_fake() -> pd.DataFrame:
    anos = list(range(2016, 2026))
    rows = []
    for ano in anos:
        for classe, base in [("ADI", 100), ("ADPF", 40), ("ADC", 10), ("ADO", 5)]:
            rows.append({"ano": ano, "classe": classe, "quantidade_ativos": base + ano - 2016})
    return pd.DataFrame(rows)


def test_total_usa_azul_e_tem_er_espin():
    df = _df_fake()
    fig = plotar_grafico_stf(df, "TOTAL", "quantidade_ativos", "Processos Ativos", show_values=True)
    assert fig.layout.height == 650
    assert fig.layout.margin.t == 150 and fig.layout.margin.b == 70
    assert fig.data[0].marker.color == "#2563EB"
    # eixo categórico por ano (igual 1.b2), não numérico contínuo
    assert list(fig.data[0].x) == [str(a) for a in range(2016, 2026)]
    # linhas ER (51/52/53) + vrect ESPIN + anotações "ER" e "ESPIN"
    shape_colors = {s.line.color for s in fig.layout.shapes if s.type == "line"}
    assert "#000000" in shape_colors  # ER
    assert "#C00000" in shape_colors  # ESPIN
    ann_texts = " ".join(a.text for a in fig.layout.annotations)
    assert "ER" in ann_texts and "ESPIN" in ann_texts
    assert fig.layout.legend.y == 0.95
    assert fig.layout.xaxis.tickfont.size == 22


def test_classe_usa_cor_do_bloco1_e_titulo_dinamico():
    df = _df_fake()
    fig = plotar_grafico_stf(df, "ADPF", "quantidade_ativos", "Processos Ativos", show_values=False)
    assert fig.data[0].marker.color == _CORES_CLASSE["ADPF"]
    # título deve conter o nome da classe (história calculada a partir dos dados reais, não fixa)
    assert "ADPF" in fig.layout.title.text


if __name__ == "__main__":
    test_total_usa_azul_e_tem_er_espin()
    test_classe_usa_cor_do_bloco1_e_titulo_dinamico()
    print("ok")
```

- [ ] **Step 2: Rodar o teste para confirmar que falha**

Run: `cd /home/boscodeb/prog/plenario_virtual && PYTHONPATH=app python3 app/pages/acervo/test_plots.py`
Expected: `ImportError: cannot import name '_CORES_CLASSE'` (constante ainda não existe com esse nome/valores no arquivo atual).

- [ ] **Step 3: Reescrever `app/pages/acervo/plots.py`**

```python
"""Figuras Plotly para a página de Acervo — função única paramétrica.

Modelo visual idêntico ao 1.b2 (app/pages/bloco1_acervo/plots.py):
mesmas cores de classe, linhas ER/ESPIN, legenda e fontes de eixo.
"""

from __future__ import annotations
import plotly.graph_objects as go
import pandas as pd

from estilo import aplicar_padrao, br, AZUL, VERMELHO, ER_DATAS, _frac_ano

_CORES_CLASSE = {"ADI": "#2563EB", "ADPF": "#93C5FD", "ADC": "#059669", "ADO": "#7C3AED"}
ANO_MIN = 1988

# Título/subtítulo "história" por métrica, para a visão TOTAL (verificado contra os dados).
_HISTORIA_METRICA = {
    "quantidade_ativos": (
        "O acervo ativo encolhe ano a ano desde o pico de 2017",
        "Estoque de processos ativos ao final de cada ano",
    ),
    "quantidade_inativos": (
        "O acervo inativo cresce de forma ininterrupta desde 1988",
        "Estoque acumulado de processos encerrados",
    ),
    "total_geral": (
        "O acervo total nunca parou de crescer, mesmo com a queda dos ativos",
        "Soma de processos ativos e inativos ao final de cada ano",
    ),
    "quantidade_baixas": (
        "As baixas anuais dispararam com a ESPIN e a virtualização do julgamento",
        "Processos baixados por ano",
    ),
    "quantidade_distribuidos": (
        "As distribuições recuam após o pico da pandemia em 2020–2021",
        "Processos distribuídos por ano",
    ),
}


def _titulo_classe(d: pd.DataFrame, coluna_metrica: str, label_metrica: str, classe_nome: str) -> str:
    """Título calculado a partir da tendência real da classe (primeiro vs. último ano)."""
    d = d.sort_values("ano")
    v_ini, v_fim = float(d[coluna_metrica].iloc[0]), float(d[coluna_metrica].iloc[-1])
    ano_ini, ano_fim = int(d["ano"].iloc[0]), int(d["ano"].iloc[-1])
    if v_fim > v_ini:
        tendencia = "cresce"
    elif v_fim < v_ini:
        tendencia = "cai"
    else:
        tendencia = "se mantém estável"
    return (
        f"Classe {classe_nome}: {label_metrica.lower()} {tendencia} "
        f"de {br(v_ini)} ({ano_ini}) para {br(v_fim)} ({ano_fim})"
    )


def plotar_grafico_stf(
    df: pd.DataFrame,
    classe_nome: str,
    coluna_metrica: str,
    label_metrica: str,
    show_values: bool = False,
) -> go.Figure:
    """
    Função única de plotagem paramétrica — modelo visual do 1.b2.

    - classe_nome="TOTAL": barra do agregado geral, cor AZUL, título "história" fixo por métrica.
    - classe_nome=<classe>: barra da classe, cor de `_CORES_CLASSE`, título calculado pela tendência real.
    """
    is_total = classe_nome.upper() == "TOTAL"

    if is_total:
        d = df.groupby("ano", as_index=False)[coluna_metrica].sum()
        cor = AZUL
        nome = f"TOTAL GERAL ({label_metrica.upper()})"
    else:
        d = df[df["classe"] == classe_nome].sort_values("ano")
        cor = _CORES_CLASSE.get(classe_nome, AZUL)
        nome = f"CLASSE: {classe_nome.upper()}"

    anos_int = sorted(d["ano"].unique().tolist())
    anos = [str(a) for a in anos_int]
    ymax = float(d[coluna_metrica].max() or 1)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=[str(a) for a in d["ano"]],
        y=d[coluna_metrica],
        marker_color=cor,
        text=[br(v) for v in d[coluna_metrica]] if show_values else None,
        textposition="outside",
        textfont=dict(color="black", size=13, weight="bold"),
        cliponaxis=False,
        name=nome,
    ))

    y_er = ymax * 1.1
    y_espin = ymax * 1.1

    # ESPIN — réplica exata de fig_1b2_acervo_por_classe_vertical
    if 2020 in anos_int and 2022 in anos_int:
        idx_2020 = anos.index("2020")
        idx_2022 = anos.index("2022")
        x0_espin = idx_2020 - 0.5
        x1_espin = idx_2022 + 0.5
        x0_linha_espin = x0_espin + 0.06

        fig.add_vrect(x0=x0_espin, x1=x1_espin, fillcolor="#FCE7F3", opacity=0.7, line_width=0, layer="below")
        fig.add_shape(type="line", x0=x0_linha_espin, x1=x0_linha_espin, y0=0, y1=y_espin,
                      line=dict(color=VERMELHO, width=1.5, dash="dash"), xref="x", yref="y")
        fig.add_shape(type="line", x0=x1_espin, x1=x1_espin, y0=0, y1=y_espin,
                      line=dict(color=VERMELHO, width=1.5, dash="dash"), xref="x", yref="y")
        fig.add_annotation(x=x0_linha_espin, y=y_espin, ax=x1_espin, ay=y_espin, axref="x", ayref="y",
                           xref="x", yref="y", showarrow=True, arrowhead=2, arrowsize=1.6,
                           arrowwidth=1.2, arrowcolor=VERMELHO, text="")
        fig.add_annotation(x=x1_espin, y=y_espin, ax=x0_linha_espin, ay=y_espin, axref="x", ayref="y",
                           xref="x", yref="y", showarrow=True, arrowhead=2, arrowsize=1.6,
                           arrowwidth=1.2, arrowcolor=VERMELHO, text="")
        fig.add_annotation(x=(x0_linha_espin + x1_espin) / 2, y=y_espin, yanchor="bottom", yshift=6,
                           text="<b>ESPIN</b>", showarrow=False,
                           font=dict(color=VERMELHO, size=13, weight="bold"),
                           xref="x", yref="y")

    # ER — réplica exata de fig_1b2_acervo_por_classe_vertical
    for er in (51, 52, 53):
        if er in (52, 53):
            ano_er, _, _ = ER_DATAS[er]
            if str(ano_er) not in anos:
                continue
            x = anos.index(str(ano_er)) - 0.5
        else:
            ano_er, mes, dia = ER_DATAS[er]
            x = _frac_ano(ANO_MIN, ano_er, mes, dia)
        fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=y_er,
                      line=dict(color="black", width=1.5, dash="dash"), xref="x", yref="y")
        fig.add_annotation(x=x, y=y_er, yanchor="bottom", text=f"<b>ER<br>{er}</b>", showarrow=False,
                           font=dict(color="black", size=11), bgcolor="white", borderpad=1,
                           xref="x", yref="y")

    if is_total:
        titulo, subtitulo_base = _HISTORIA_METRICA[coluna_metrica]
    else:
        titulo = _titulo_classe(d, coluna_metrica, label_metrica, classe_nome)
        subtitulo_base = label_metrica

    titulo_peca = "Total Geral" if is_total else f"Classe {classe_nome}"
    ano_min, ano_max = anos_int[0], anos_int[-1]
    subtitulo = f"{subtitulo_base} — {titulo_peca} ({ano_min}–{ano_max})"

    fig = aplicar_padrao(
        fig, titulo, subtitulo,
        xaxis=dict(title=""), yaxis=dict(title="", range=[0, ymax * 1.2]),
        showlegend=True, legend=dict(orientation="h", yanchor="bottom", y=0.95, x=0.5, xanchor="center"),
        height=650, margin=dict(t=150, b=70, l=60, r=40),
    )
    fig.update_yaxes(showline=True)
    fig.update_xaxes(tickfont=dict(size=22), title_font=dict(size=22))
    return fig
```

- [ ] **Step 4: Rodar o teste para confirmar que passa**

Run: `cd /home/boscodeb/prog/plenario_virtual && PYTHONPATH=app python3 app/pages/acervo/test_plots.py`
Expected: `ok`

- [ ] **Step 5: Rodar manualmente contra os dados reais (checagem visual rápida, sem servidor)**

```bash
PYTHONPATH=app python3 -c "
import pandas as pd
from pages.acervo.plots import plotar_grafico_stf
df = pd.read_parquet('data/processed/acervo/evolucao_acervo.parquet')
fig = plotar_grafico_stf(df, 'TOTAL', 'quantidade_ativos', 'Processos Ativos', show_values=True)
print(fig.layout.title.text)
fig2 = plotar_grafico_stf(df, 'ADPF', 'quantidade_ativos', 'Processos Ativos', show_values=True)
print(fig2.layout.title.text)
"
```

Expected: dois títulos diferentes, o segundo citando "ADPF" e a tendência real (cresce/cai) dessa classe.

- [ ] **Step 6: Subir o app localmente e conferir visualmente a aba Acervo (comparar com 1.b2)**

Run: `streamlit run app/main.py` (ou o entrypoint existente do projeto) e abrir a página "Acervo" → aba "Processos Ativos" → sub-abas Total/ADI/ADPF/ADC/ADO.
Expected: mesmas linhas ER (pretas, tracejadas, rótulo "ER\n51" com fundo branco), mesma faixa rosa + setas vermelhas ESPIN, legenda horizontal embaixo do título, fonte do eixo X grande (tamanho 22), altura visualmente igual ao gráfico 1.b2 do Bloco 1.

- [ ] **Step 7: Commit**

```bash
git add app/pages/acervo/plots.py app/pages/acervo/test_plots.py
git commit -m "refactor(acervo): unify visual model with fig_1b2 (ER/ESPIN, colors, legend, fonts) and add data-driven titles"
```

---

## Self-Review

**1. Spec coverage:**
- Mesmas linhas ER/ESPIN (posição e formatação) → Step 3, réplica literal do bloco de código do 1.b2.
- Mesmas cores de barra → `_CORES_CLASSE` idêntico ao Bloco 1.
- Mesma legenda → `legend=dict(orientation="h", yanchor="bottom", y=0.95, ...)` idêntico.
- Mesmos tamanhos de fonte de eixo → `tickfont`/`title_font` size 22 aplicados.
- Função única generalizada → `plotar_grafico_stf` continua sendo a única função, assinatura preservada, nenhuma duplicação por classe/métrica.
- Título/subtítulo próprios por gráfico, que contam a história → `_HISTORIA_METRICA` (TOTAL) + `_titulo_classe` (por classe, calculado dos dados reais, nunca falso).
- Bloco 1/2/3 intocados → nenhuma task toca esses diretórios.

**2. Placeholder scan:** nenhum "TODO"/"implementar depois" — todo código é completo e roda.

**3. Type consistency:** `plotar_grafico_stf` mantém a assinatura `(df, classe_nome, coluna_metrica, label_metrica, show_values=False) -> go.Figure` usada em `layout.py:73,80`; `_CORES_CLASSE` é o nome importado no teste e definido no módulo.
