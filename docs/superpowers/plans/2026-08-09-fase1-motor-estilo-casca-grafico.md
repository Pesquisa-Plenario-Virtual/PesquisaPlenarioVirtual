# Fase 1 — Motor de estilo e casca de gráfico

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir os quatro módulos compartilhados que fazem as regras de formatação e de montagem da Pessoa 2 valerem nas oito páginas não-empíricas sem editar as ~90 funções de gráfico existentes.

**Architecture:** Uma camada de pós-processamento. As funções de gráfico continuam produzindo `go.Figure` como hoje; `tema.aplicar_tema` percorre a figura pronta e reescreve tipografia, tamanhos, ângulo de tick, rótulos e cores. `components/grafico.render_grafico` envolve cada figura com os controles (valores, legenda, tipo de plotagem, período, classe) e deriva a tabela da própria figura. `components/catalogo.render_pagina` substitui os seis `render_graficos` duplicados.

**Tech Stack:** Python 3.13, Streamlit 1.59.1, Plotly 6.9.0, pandas. Sem dependências novas.

## Global Constraints

- **Nunca editar `app/pages/bloco1_acervo/`, `app/pages/bloco2_inclusoes/`, `app/pages/bloco3_pandemia/`.** `git diff --stat -- app/pages/bloco*/` tem que vir vazio ao fim de cada task.
- **Nenhuma dependência nova.** Não instalar pytest. Testes são scripts com `assert` e bloco `if __name__ == "__main__"`, seguindo `app/pages/acervo/test_plots.py`.
- **Comando de teste:** `cd app && PYTHONPATH=. ../.venv/bin/python <caminho/do/teste.py>`. Saída de sucesso: `ok`.
- **Fonte:** `"Times New Roman, Times, serif"` — string exata, em toda figura das oito páginas.
- **Tamanhos de fonte (px):** título 22, subtítulo 14, título de eixo 16, tick 14, legenda 14, valor de dado 13, anotação 12. Nenhum outro valor é permitido nas oito páginas.
- **Ângulo de tick:** `0` em todo eixo x. Nunca −45, nunca −90.
- **Rótulo de ambiente:** `"Plenário Presencial"`. A string `"Plenário Físico"` não pode aparecer em nenhum texto renderizado.
- **Superfícies para validação de cor:** clara `#ffffff`, escura `#0e1117`.
- **Commits:** um por task, sem trailer `Co-Authored-By`. Push após cada commit.
- **Strings exatas de `desfecho`** (copiar verbatim, note "decisão maioria" sem "por", e a vírgula antes de "vencido"):
  - `Concluído - decisão unânime`
  - `Concluído - decisão maioria com o relator`
  - `Concluído - decisão maioria, vencido o relator`
  - `Não concluído - motivos diversos`
  - `Não concluído - retirado de pauta`
  - `Não concluído - pedido de vista`
  - `Não concluído - destaque`

---

## Estrutura de arquivos

| Arquivo | Responsabilidade | Task |
|---|---|---|
| `app/paleta.py` (criar) | Rótulo canônico e cor por valor semântico. Sem Plotly, sem Streamlit. | 1, 2 |
| `app/pages/test_paleta.py` (criar) | Testes de `paleta.py` | 1, 2 |
| `app/tema.py` (criar) | Pós-processamento de `go.Figure`: tipografia, tamanhos, tick, rótulos, cor, modo escuro, conversão de tipo. Sem Streamlit. | 3–6 |
| `app/pages/test_tema.py` (criar) | Testes de `tema.py` | 3–6 |
| `app/components/grafico.py` (criar) | `GraficoSpec`, `tabela_da_figura`, `render_grafico`. Único módulo da fase que usa Streamlit para gráfico. | 7, 8 |
| `app/pages/test_grafico.py` (criar) | Testes das partes puras de `grafico.py` | 7 |
| `app/components/catalogo.py` (criar) | `render_pagina`: busca, sumário navegável, seletor, compartilhamento. | 9 |
| `app/app.py` (modificar) | Sidebar com seletor de tema e toggle de modo noturno. | 10 |
| `app/pages/<pagina>/layout.py` (modificar, 8 arquivos) | Catálogo passa a ser lista de `GraficoSpec`; `render_graficos` delega para `render_pagina`. | 11–18 |
| `app/pages/test_conformidade.py` (criar) | Portão de estilo: percorre as figuras das oito páginas e afirma fonte, tamanhos, tick, ausência de `go.Pie`. | 19 |

---

### Task 1: Rótulos canônicos e sentence case

**Files:**
- Create: `app/paleta.py`
- Test: `app/pages/test_paleta.py`

**Interfaces:**
- Consumes: nada.
- Produces: `paleta.SIGLAS: frozenset[str]`, `paleta.sentence_case(texto: str) -> str`, `paleta.canonico(nome: str) -> str`.

`canonico` resolve três problemas de uma vez: o `.upper()` que `inclusoes/plots.py:96` e `:152` aplicam nos nomes de série, o `"Plenário Físico"` que sobrevive em `tramitacao/plots.py`, e os apelidos de tramitação (`Só Virtual`, `Virtual`, `Só Físico`, `Físico`, `Presencial`).

- [ ] **Step 1: Escrever o teste que falha**

Criar `app/pages/test_paleta.py`:

```python
"""Testes de paleta.py — rótulos canônicos, sentence case e cor semântica."""
from paleta import sentence_case, canonico


def test_sentence_case_desfaz_upper_preservando_acentos():
    assert sentence_case("CONCLUÍDO") == "Concluído"
    assert sentence_case("NÃO CONCLUÍDO - MOTIVOS DIVERSOS") == "Não concluído - motivos diversos"


def test_sentence_case_preserva_siglas():
    assert sentence_case("ADI") == "ADI"
    assert sentence_case("ADPF") == "ADPF"
    assert sentence_case("TOTAL ADI E ADPF") == "Total ADI e ADPF"
    assert sentence_case("PR") == "PR"


def test_sentence_case_ja_correto_nao_muda():
    assert sentence_case("Não concluído - motivos diversos") == "Não concluído - motivos diversos"
    assert sentence_case("1 - Maioria (relator vencedor)") == "1 - Maioria (relator vencedor)"


def test_canonico_traduz_plenario_fisico():
    assert canonico("Plenário Físico") == "Plenário Presencial"
    assert canonico("PLENÁRIO FÍSICO") == "Plenário Presencial"
    assert canonico("Plenário Presencial") == "Plenário Presencial"


def test_canonico_preserva_nome_proprio_de_ambiente():
    assert canonico("PLENÁRIO VIRTUAL") == "Plenário Virtual"
    assert canonico("plenário virtual") == "Plenário Virtual"


def test_canonico_normaliza_apelidos_de_tramitacao():
    assert canonico("Só Virtual") == "Só Virtual"
    assert canonico("Virtual") == "Só Virtual"
    assert canonico("Só Físico") == "Só Presencial"
    assert canonico("Físico") == "Só Presencial"
    assert canonico("Presencial") == "Só Presencial"
    assert canonico("Ambos os ambientes") == "Ambos os ambientes"


def test_canonico_desconhecido_cai_em_sentence_case():
    assert canonico("ALGUMA COISA NOVA") == "Alguma coisa nova"


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_paleta.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'paleta'`

- [ ] **Step 3: Implementar o mínimo**

Criar `app/paleta.py`:

```python
"""Fonte única de rótulo e cor para as oito páginas não-empíricas.

Sem Plotly e sem Streamlit de propósito: é consumido por tema.py, pelos testes
e por qualquer notebook. Os Blocos Empíricos não usam este módulo.
"""

from __future__ import annotations

# Siglas que sobrevivem à normalização de caixa.
SIGLAS = frozenset({
    "ADI", "ADPF", "ADC", "ADO",
    "PV", "PP", "PR", "RC", "QI", "IJ",
    "ER", "ESPIN", "STF", "CC",
})

# Nome canônico -> apelidos aceitos (comparados em minúsculas).
_APELIDOS: dict[str, tuple[str, ...]] = {
    "Plenário Virtual":    ("plenário virtual", "plenario virtual", "pv"),
    "Plenário Presencial": ("plenário presencial", "plenário físico", "plenario fisico", "pp"),
    "Só Virtual":          ("só virtual", "so virtual", "virtual"),
    "Só Presencial":       ("só presencial", "só físico", "so fisico", "físico", "presencial"),
    "Ambos os ambientes":  ("ambos os ambientes", "ambos"),
}

_MAPA_APELIDO = {ap: canon for canon, aps in _APELIDOS.items() for ap in aps}


def sentence_case(texto: str) -> str:
    """Caixa de frase preservando siglas: 'CONCLUÍDO' -> 'Concluído', 'ADI' -> 'ADI'."""
    if not texto:
        return texto
    palavras = [p if p.upper() in SIGLAS else p.lower() for p in texto.split(" ")]
    saida = " ".join(palavras)
    for i, ch in enumerate(saida):
        if ch.isalpha():
            return saida[:i] + ch.upper() + saida[i + 1:]
    return saida


def canonico(nome: str) -> str:
    """Rótulo de exibição de um valor. Apelido conhecido vira o canônico;
    o resto cai em sentence_case."""
    if nome is None:
        return ""
    texto = str(nome).strip()
    achado = _MAPA_APELIDO.get(texto.lower())
    if achado is not None:
        return achado
    return sentence_case(texto)
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_paleta.py`
Expected: `ok`

Se `test_sentence_case_ja_correto_nao_muda` falhar em `"1 - Maioria (relator vencedor)"`: a palavra `"-"` não tem letra e o laço de capitalização precisa varrer a string inteira, não só a primeira palavra. O código acima já faz isso.

- [ ] **Step 5: Commit**

```bash
git add app/paleta.py app/pages/test_paleta.py
git commit -m "feat: paleta.py com rótulo canônico e sentence case preservando siglas"
git push
```

---

### Task 2: Cor semântica validada

**Files:**
- Modify: `app/paleta.py`
- Modify: `app/pages/test_paleta.py`

**Interfaces:**
- Consumes: `paleta.canonico` (Task 1).
- Produces: `paleta.cor(nome: str, dark: bool = False) -> str`, `paleta.cores(nomes: list[str], dark: bool = False) -> dict[str, str]`, `paleta.CINZA_OUTROS: str`.

Valores retirados da §4 da spec. Foram validados com `scripts/validate_palette.js` da skill `dataviz` contra `#ffffff` e `#0e1117` — **não alterar hex sem revalidar**.

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `app/pages/test_paleta.py`, antes do bloco `__main__`:

```python
from paleta import cor, cores, CINZA_OUTROS


def test_ambiente_tem_cor_fixa_nos_dois_modos():
    assert cor("Plenário Virtual") == "#2a78d6"
    assert cor("Plenário Virtual", dark=True) == "#3987e5"
    assert cor("Plenário Presencial") == "#eb6834"
    assert cor("Plenário Presencial", dark=True) == "#d95926"


def test_plenario_fisico_recebe_a_cor_de_presencial():
    assert cor("Plenário Físico") == cor("Plenário Presencial")


def test_cor_ignora_caixa():
    assert cor("PLENÁRIO VIRTUAL") == cor("Plenário Virtual")


def test_familia_de_desfecho_separa_concluido_de_nao_concluido():
    concluidos = [
        cor("Concluído - decisão unânime"),
        cor("Concluído - decisão maioria com o relator"),
        cor("Concluído - decisão maioria, vencido o relator"),
    ]
    nao = [
        cor("Não concluído - motivos diversos"),
        cor("Não concluído - retirado de pauta"),
        cor("Não concluído - pedido de vista"),
        cor("Não concluído - destaque"),
    ]
    assert len(set(concluidos)) == 3
    assert len(set(nao)) == 4
    assert not (set(concluidos) & set(nao))
    # o par que a Pessoa 2 reclamou tem que estar em famílias diferentes
    assert cor("Concluído - decisão maioria, vencido o relator") == "#86b6ef"
    assert cor("Não concluído - retirado de pauta") == "#c9541d"


def test_classes_tem_as_quatro_cores_validadas():
    assert cores(["ADI", "ADPF", "ADC", "ADO"]) == {
        "ADI": "#2a78d6", "ADPF": "#eb6834", "ADC": "#1baf7a", "ADO": "#eda100",
    }


def test_desconhecido_cai_em_cinza_deterministico():
    a = cor("categoria inexistente")
    b = cor("categoria inexistente")
    assert a == b
    assert a != cor("outra categoria inexistente")


def test_ausencia_usa_cinza_reservado():
    assert cor("Sem sustentação oral") == CINZA_OUTROS
    assert cor("Sem reajuste de voto") == CINZA_OUTROS
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_paleta.py`
Expected: FAIL com `ImportError: cannot import name 'cor' from 'paleta'`

- [ ] **Step 3: Implementar o mínimo**

Acrescentar a `app/paleta.py`:

```python
CINZA_OUTROS = "#898781"

# Rótulo canônico -> (cor no modo claro, cor no modo escuro).
# Validado com dataviz/scripts/validate_palette.js contra #ffffff e #0e1117.
# Não alterar sem revalidar — ver §4 da spec.
CORES: dict[str, tuple[str, str]] = {
    # Ambiente — a espinha da narrativa
    "Plenário Virtual":    ("#2a78d6", "#3987e5"),
    "Plenário Presencial": ("#eb6834", "#d95926"),
    # Tramitação — ecoa o par de ambiente
    "Só Virtual":         ("#2a78d6", "#3987e5"),
    "Ambos os ambientes": ("#1baf7a", "#199e70"),
    "Só Presencial":      ("#eb6834", "#d95926"),
    # Classe processual — aprovado na lista de pares adjacentes nos dois modos
    "ADI":  ("#2a78d6", "#3987e5"),
    "ADPF": ("#eb6834", "#d95926"),
    "ADC":  ("#1baf7a", "#199e70"),
    "ADO":  ("#eda100", "#c98500"),
    # Macro-desfecho — reusa o par de ambiente: azul decide, laranja trava
    "Concluído":     ("#2a78d6", "#3987e5"),
    "Não concluído": ("#eb6834", "#d95926"),
    # Desfecho detalhado — matiz é a família, tom é o degrau (ordenado por volume)
    "Concluído - decisão unânime":                   ("#184f95", "#184f95"),
    "Concluído - decisão maioria com o relator":     ("#2a78d6", "#3987e5"),
    "Concluído - decisão maioria, vencido o relator": ("#86b6ef", "#9ec5f4"),
    "Não concluído - motivos diversos":  ("#9c3d13", "#c9541d"),
    "Não concluído - retirado de pauta": ("#c9541d", "#eb6834"),
    "Não concluído - pedido de vista":   ("#eb6834", "#f5a184"),
    "Não concluído - destaque":          ("#f5a184", "#fac7b6"),
    # Tipo de questão
    "PR": ("#2a78d6", "#3987e5"),
    "RC": ("#eb6834", "#d95926"),
    "QI": ("#1baf7a", "#199e70"),
    # Binários — presença tem cor, ausência é cinza reservado
    "Com sustentação oral": ("#1baf7a", "#199e70"),
    "Com reajuste de voto": ("#1baf7a", "#199e70"),
    "Sem sustentação oral": (CINZA_OUTROS, CINZA_OUTROS),
    "Sem reajuste de voto": (CINZA_OUTROS, CINZA_OUTROS),
}

# Degraus de reserva para valores fora do vocabulário, atribuídos de forma
# determinística. Ordem validada como categórica na lista de pares adjacentes.
_RESERVA = (
    ("#4a3aa7", "#9085e9"),
    ("#e87ba4", "#d55181"),
    ("#008300", "#008300"),
    ("#e34948", "#e66767"),
)


def cor(nome: str, dark: bool = False) -> str:
    """Cor de um valor semântico. Desconhecido recebe um degrau de reserva fixo."""
    canon = canonico(nome)
    par = CORES.get(canon)
    if par is None:
        par = _RESERVA[sum(canon.encode("utf-8")) % len(_RESERVA)]
    return par[1] if dark else par[0]


def cores(nomes, dark: bool = False) -> dict[str, str]:
    """Mapa {rótulo canônico: cor} para uma lista de valores."""
    return {canonico(n): cor(n, dark) for n in nomes}
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_paleta.py`
Expected: `ok`

Se `test_desconhecido_cai_em_cinza_deterministico` falhar porque as duas strings caíram no mesmo degrau, trocar as strings do teste por outras que colidam menos — a função está correta, o teste é que escolheu mal.

- [ ] **Step 5: Commit**

```bash
git add app/paleta.py app/pages/test_paleta.py
git commit -m "feat: paleta semântica validada para daltonismo em modo claro e escuro"
git push
```

---

### Task 3: Tipografia, tamanhos e ângulo de tick

**Files:**
- Create: `app/tema.py`
- Test: `app/pages/test_tema.py`

**Interfaces:**
- Consumes: `paleta.canonico` (Task 1).
- Produces: `tema.FONTE: str`, `tema.TAMANHOS: dict[str, int]`, `tema.aplicar_tema(fig, tema="novo", dark=False) -> go.Figure`.

Esta é a task que resolve, sozinha, quatro dos pedidos de formatação em todos os gráficos das oito páginas.

- [ ] **Step 1: Escrever o teste que falha**

Criar `app/pages/test_tema.py`:

```python
"""Testes de tema.py — pós-processamento de figura."""
import plotly.graph_objects as go

from tema import FONTE, TAMANHOS, aplicar_tema


def _fig_suja() -> go.Figure:
    """Figura no estado em que as páginas produzem hoje: Arial, tamanhos
    avulsos, ano na diagonal, nome de série em caixa alta."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=["2020", "2021"], y=[10, 20], name="PLENÁRIO VIRTUAL",
        textfont=dict(family="Arial, sans-serif", size=17, color="black"),
    ))
    fig.add_trace(go.Bar(
        x=["2020", "2021"], y=[5, 8], name="PLENÁRIO FÍSICO",
        textfont=dict(family="Arial, sans-serif", size=17, color="black"),
    ))
    fig.update_layout(
        title="<b>Um achado qualquer</b>",
        font=dict(family="Arial, sans-serif", color="#000000"),
        title_font=dict(family="Arial, sans-serif", size=22),
        legend=dict(font=dict(family="Arial, sans-serif", size=14)),
        xaxis=dict(title="Ano", tickangle=-45,
                   tickfont=dict(family="Arial, sans-serif", size=22),
                   title_font=dict(family="Arial, sans-serif", size=22)),
        yaxis=dict(title="Inclusões em pauta",
                   tickfont=dict(family="Arial, sans-serif", size=15)),
    )
    fig.add_annotation(x=0, y=25, text="<b>ER 53</b>",
                       font=dict(family="Arial, sans-serif", size=11))
    return fig


def test_fonte_times_em_layout_eixos_legenda_e_traces():
    fig = aplicar_tema(_fig_suja())
    assert fig.layout.font.family == FONTE
    assert fig.layout.title.font.family == FONTE
    assert fig.layout.legend.font.family == FONTE
    assert fig.layout.xaxis.tickfont.family == FONTE
    assert fig.layout.xaxis.title.font.family == FONTE
    assert fig.layout.yaxis.tickfont.family == FONTE
    assert fig.layout.annotations[0].font.family == FONTE
    for tr in fig.data:
        assert tr.textfont.family == FONTE


def test_tamanhos_normalizados():
    fig = aplicar_tema(_fig_suja())
    assert fig.layout.title.font.size == TAMANHOS["titulo"]
    assert fig.layout.xaxis.tickfont.size == TAMANHOS["tick"]
    assert fig.layout.yaxis.tickfont.size == TAMANHOS["tick"]
    assert fig.layout.xaxis.title.font.size == TAMANHOS["eixo_titulo"]
    assert fig.layout.legend.font.size == TAMANHOS["legenda"]
    assert fig.layout.annotations[0].font.size == TAMANHOS["anotacao"]
    for tr in fig.data:
        assert tr.textfont.size == TAMANHOS["valor"]


def test_ano_fica_na_horizontal():
    fig = aplicar_tema(_fig_suja())
    assert fig.layout.xaxis.tickangle == 0


def test_legenda_em_caixa_de_frase_e_sem_plenario_fisico():
    fig = aplicar_tema(_fig_suja())
    nomes = [tr.name for tr in fig.data]
    assert nomes == ["Plenário Virtual", "Plenário Presencial"]


def test_tema_empirico_nao_toca_na_figura():
    original = _fig_suja()
    devolvida = aplicar_tema(original, tema="empirico")
    assert devolvida.layout.font.family == "Arial, sans-serif"
    assert devolvida.layout.xaxis.tickangle == -45
    assert devolvida.data[0].name == "PLENÁRIO VIRTUAL"


def test_modo_escuro_troca_fundo_e_tinta():
    fig = aplicar_tema(_fig_suja(), dark=True)
    assert fig.layout.paper_bgcolor == "#0e1117"
    assert fig.layout.plot_bgcolor == "#0e1117"
    assert fig.layout.font.color == "#fafafa"


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_tema.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'tema'`

- [ ] **Step 3: Implementar o mínimo**

Criar `app/tema.py`:

```python
"""Pós-processamento de figura para as oito páginas não-empíricas.

As funções de gráfico continuam produzindo go.Figure como sempre; este módulo
percorre a figura pronta e impõe o padrão da Pessoa 2. É o que permite aplicar
as regras em ~90 gráficos sem editar ~90 funções.

Com tema="empirico" a figura volta intocada — é assim que o alternador de tema
funciona sem duplicar código de gráfico.
"""

from __future__ import annotations

import plotly.graph_objects as go

from paleta import canonico

FONTE = "Times New Roman, Times, serif"

TAMANHOS = {
    "titulo": 22,
    "subtitulo": 14,
    "eixo_titulo": 16,
    "tick": 14,
    "legenda": 14,
    "valor": 13,
    "anotacao": 12,
}

TINTA_CLARA = "#0b0b0b"
TINTA_ESCURA = "#fafafa"
FUNDO_CLARO = "#ffffff"
FUNDO_ESCURO = "#0e1117"


def _fonte(size_key: str, dark: bool) -> dict:
    return dict(
        family=FONTE,
        size=TAMANHOS[size_key],
        color=TINTA_ESCURA if dark else TINTA_CLARA,
    )


def _normalizar_eixos(fig: go.Figure, dark: bool) -> None:
    """Tipografia, tamanho e tickangle=0 em todo eixo, inclusive subplots."""
    eixo_tick = _fonte("tick", dark)
    eixo_titulo = _fonte("eixo_titulo", dark)
    for chave in fig.layout:
        if not (chave.startswith("xaxis") or chave.startswith("yaxis")):
            continue
        eixo = fig.layout[chave]
        eixo.tickfont = eixo_tick
        eixo.title.font = eixo_titulo
        if chave.startswith("xaxis"):
            eixo.tickangle = 0


def _normalizar_traces(fig: go.Figure, dark: bool) -> None:
    """Nome de série em rótulo canônico e textfont padronizado."""
    valor = _fonte("valor", dark)
    for tr in fig.data:
        if getattr(tr, "name", None):
            tr.name = canonico(tr.name)
        if hasattr(tr, "textfont"):
            tr.textfont = valor


def _normalizar_anotacoes(fig: go.Figure, dark: bool) -> None:
    anotacao = _fonte("anotacao", dark)
    for ann in fig.layout.annotations:
        # a cor da anotação é semântica (ER preto, ESPIN vermelho) — preservar
        cor_original = ann.font.color
        ann.font = dict(family=FONTE, size=TAMANHOS["anotacao"],
                        color=cor_original or anotacao["color"])


def aplicar_tema(fig: go.Figure, tema: str = "novo", dark: bool = False) -> go.Figure:
    """Impõe o padrão visual da Pessoa 2 a uma figura já construída.

    tema="empirico" devolve a figura sem tocar em nada.
    """
    if tema == "empirico":
        return fig

    tinta = TINTA_ESCURA if dark else TINTA_CLARA
    fundo = FUNDO_ESCURO if dark else FUNDO_CLARO

    fig.update_layout(
        font=dict(family=FONTE, color=tinta),
        title_font=_fonte("titulo", dark),
        legend_font=_fonte("legenda", dark),
        paper_bgcolor=fundo,
        plot_bgcolor=fundo,
    )
    _normalizar_eixos(fig, dark)
    _normalizar_traces(fig, dark)
    _normalizar_anotacoes(fig, dark)
    return fig
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_tema.py`
Expected: `ok`

Se `test_tema_empirico_nao_toca_na_figura` falhar, o motivo é que `aplicar_tema` mutou a figura em outro teste antes — cada teste chama `_fig_suja()` de novo, então não deve acontecer. Se acontecer, é sinal de que algo virou estado de módulo.

- [ ] **Step 5: Commit**

```bash
git add app/tema.py app/pages/test_tema.py
git commit -m "feat: tema.py normaliza fonte, tamanhos, tickangle e rótulo de série"
git push
```

---

### Task 4: Recolorir por nome de série

**Files:**
- Modify: `app/tema.py`
- Modify: `app/pages/test_tema.py`

**Interfaces:**
- Consumes: `paleta.cor` (Task 2), `tema.aplicar_tema` (Task 3).
- Produces: `aplicar_tema` passa a recolorir traces cujo nome está no vocabulário da paleta.

É o que faz a mesma variável ter a mesma cor em todos os gráficos — o pedido de data storytelling.

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `app/pages/test_tema.py`, antes do bloco `__main__`:

```python
from paleta import cor as cor_paleta


def test_recolore_serie_conhecida_pelo_nome():
    fig = aplicar_tema(_fig_suja())
    assert fig.data[0].marker.color == cor_paleta("Plenário Virtual")
    assert fig.data[1].marker.color == cor_paleta("Plenário Presencial")


def test_recolore_no_modo_escuro_com_o_degrau_escuro():
    fig = aplicar_tema(_fig_suja(), dark=True)
    assert fig.data[0].marker.color == cor_paleta("Plenário Virtual", dark=True)


def test_nao_recolore_serie_fora_do_vocabulario_com_cor_explicita():
    fig = go.Figure(go.Bar(x=[1], y=[2], name="Série sem vocabulário",
                           marker_color="#123456"))
    aplicar_tema(fig)
    assert fig.data[0].marker.color == "#123456"


def test_recolore_linha_alem_de_barra():
    fig = go.Figure(go.Scatter(x=[1, 2], y=[3, 4], mode="lines",
                               name="Plenário Virtual"))
    aplicar_tema(fig)
    assert fig.data[0].line.color == cor_paleta("Plenário Virtual")


def test_nao_quebra_com_marker_color_vetorial():
    """acervo/plots.py e bloco1 passam uma lista de cores por barra."""
    fig = go.Figure(go.Bar(x=[1, 2], y=[3, 4], name="Variação",
                           marker_color=["#aaaaaa", "#bbbbbb"]))
    aplicar_tema(fig)
    assert list(fig.data[0].marker.color) == ["#aaaaaa", "#bbbbbb"]
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_tema.py`
Expected: FAIL em `test_recolore_serie_conhecida_pelo_nome` — a cor ainda é `None` ou a original.

- [ ] **Step 3: Implementar o mínimo**

Em `app/tema.py`, trocar o import e a função `_normalizar_traces`:

```python
from paleta import CORES, canonico, cor
```

```python
def _normalizar_traces(fig: go.Figure, dark: bool) -> None:
    """Nome canônico, textfont padronizado e cor semântica por nome de série.

    Só recolore o que está no vocabulário da paleta: uma série fora dele mantém
    a cor que a função de gráfico escolheu. Cor vetorial (uma por barra, como em
    acervo/plots.py) é preservada — recolorir destruiria a codificação.
    """
    valor = _fonte("valor", dark)
    for tr in fig.data:
        nome = getattr(tr, "name", None)
        if nome:
            tr.name = canonico(nome)
        if hasattr(tr, "textfont"):
            tr.textfont = valor
        if not nome or canonico(nome) not in CORES:
            continue
        nova = cor(nome, dark)
        marker = getattr(tr, "marker", None)
        if marker is not None and not isinstance(getattr(marker, "color", None), (list, tuple)):
            tr.marker.color = nova
        if hasattr(tr, "line") and tr.type in ("scatter", "scattergl"):
            tr.line.color = nova
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_tema.py`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add app/tema.py app/pages/test_tema.py
git commit -m "feat: tema recolore série por nome — mesma variável, mesma cor em todo gráfico"
git push
```

---

### Task 5: Neutralizar HTML inline de tamanho

**Files:**
- Modify: `app/tema.py`
- Modify: `app/pages/test_tema.py`

**Interfaces:**
- Consumes: `tema.aplicar_tema` (Task 4).
- Produces: `tema.limpar_html_de_fonte(texto: str) -> str`, chamada de dentro de `aplicar_tema`.

`bloco2_inclusoes/plots.py` embute `<span style='font-size:20px'>` em rótulos e títulos (linhas 276, 375, 425, 473, 506, 550, 624, 703, 736). Esses gráficos serão importados pelas páginas temáticas na Fase 5, e sem esta limpeza o tamanho embutido vence o `textfont`. Implementar agora para a Fase 5 não precisar tocar em `tema.py`.

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `app/pages/test_tema.py`, antes do bloco `__main__`:

```python
from tema import limpar_html_de_fonte


def test_remove_font_size_inline_preservando_o_texto():
    assert limpar_html_de_fonte(
        "<span style='font-size:20px'>1.234</span>"
    ) == "1.234"
    assert limpar_html_de_fonte(
        "<b>Total</b><br><span style='font-size:12px'>ADI 900</span>"
    ) == "<b>Total</b><br>ADI 900"


def test_texto_sem_span_nao_muda():
    assert limpar_html_de_fonte("<b>Achado</b>") == "<b>Achado</b>"
    assert limpar_html_de_fonte("1.234") == "1.234"


def test_aplicar_tema_limpa_titulo_anotacao_e_texto_de_barra():
    fig = go.Figure(go.Bar(
        x=[1], y=[2], name="ADI",
        text=["<span style='font-size:20px'>500</span>"],
    ))
    fig.update_layout(title="<b><span style='font-size:22px'>Título</span></b>")
    fig.add_annotation(x=0, y=1, text="<span style='font-size:14px'>nota</span>")
    aplicar_tema(fig)
    assert fig.layout.title.text == "<b>Título</b>"
    assert list(fig.data[0].text) == ["500"]
    assert fig.layout.annotations[0].text == "nota"
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_tema.py`
Expected: FAIL com `ImportError: cannot import name 'limpar_html_de_fonte' from 'tema'`

- [ ] **Step 3: Implementar o mínimo**

Em `app/tema.py`, acrescentar no topo:

```python
import re

_SPAN_FONTE = re.compile(r"<span[^>]*font-size[^>]*>(.*?)</span>", re.IGNORECASE | re.DOTALL)


def limpar_html_de_fonte(texto: str) -> str:
    """Remove <span style='font-size:...'> preservando o conteúdo.

    Os Blocos Empíricos embutem tamanho no próprio rótulo; sem isso o valor
    embutido vence o textfont padronizado quando essas figuras são importadas
    pelas páginas temáticas.
    """
    if not texto or "<span" not in texto.lower():
        return texto
    anterior = None
    while anterior != texto:
        anterior = texto
        texto = _SPAN_FONTE.sub(r"\1", texto)
    return texto
```

Em `_normalizar_traces`, depois de padronizar `textfont`:

```python
        texto = getattr(tr, "text", None)
        if isinstance(texto, str):
            tr.text = limpar_html_de_fonte(texto)
        elif isinstance(texto, (list, tuple)):
            tr.text = [limpar_html_de_fonte(t) if isinstance(t, str) else t for t in texto]
```

Em `_normalizar_anotacoes`, antes de trocar a fonte:

```python
        if ann.text:
            ann.text = limpar_html_de_fonte(ann.text)
```

Em `aplicar_tema`, depois do `update_layout`:

```python
    if fig.layout.title.text:
        fig.layout.title.text = limpar_html_de_fonte(fig.layout.title.text)
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_tema.py`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add app/tema.py app/pages/test_tema.py
git commit -m "feat: tema neutraliza font-size embutido em HTML de rótulo"
git push
```

---

### Task 6: Alternância de forma de plotagem

**Files:**
- Modify: `app/tema.py`
- Modify: `app/pages/test_tema.py`

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces: `tema.TIPOS: tuple[str, ...]` = `("barra", "linha", "area", "barra_h")`, `tema.converter_tipo(fig, tipo: str) -> go.Figure`.

Atende "priorize barra mas permita ver como linha". Converte preservando x, y, nome, cor e texto.

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `app/pages/test_tema.py`, antes do bloco `__main__`:

```python
from tema import TIPOS, converter_tipo


def _fig_barras() -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["2020", "2021"], y=[10, 20],
                         name="Plenário Virtual", marker_color="#2a78d6",
                         text=["10", "20"]))
    fig.add_trace(go.Bar(x=["2020", "2021"], y=[5, 8],
                         name="Plenário Presencial", marker_color="#eb6834",
                         text=["5", "8"]))
    fig.update_layout(barmode="group")
    return fig


def test_barra_para_linha_preserva_dado_nome_e_cor():
    fig = converter_tipo(_fig_barras(), "linha")
    assert all(tr.type == "scatter" for tr in fig.data)
    assert fig.data[0].mode == "lines+markers"
    assert list(fig.data[0].x) == ["2020", "2021"]
    assert list(fig.data[0].y) == [10, 20]
    assert fig.data[0].name == "Plenário Virtual"
    assert fig.data[0].line.color == "#2a78d6"
    assert fig.data[1].line.color == "#eb6834"


def test_barra_para_area_empilha():
    fig = converter_tipo(_fig_barras(), "area")
    assert all(tr.type == "scatter" for tr in fig.data)
    assert fig.data[0].stackgroup == "um"
    assert fig.data[0].fill == "tonexty"


def test_barra_para_horizontal_troca_os_eixos():
    fig = converter_tipo(_fig_barras(), "barra_h")
    assert all(tr.type == "bar" for tr in fig.data)
    assert fig.data[0].orientation == "h"
    assert list(fig.data[0].x) == [10, 20]
    assert list(fig.data[0].y) == ["2020", "2021"]


def test_barra_para_barra_devolve_igual():
    original = _fig_barras()
    fig = converter_tipo(original, "barra")
    assert all(tr.type == "bar" for tr in fig.data)
    assert list(fig.data[0].y) == [10, 20]


def test_tipo_desconhecido_devolve_a_figura_intacta():
    fig = converter_tipo(_fig_barras(), "sanfona")
    assert all(tr.type == "bar" for tr in fig.data)


def test_pizza_nao_e_um_tipo_oferecido():
    assert "pizza" not in TIPOS
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_tema.py`
Expected: FAIL com `ImportError: cannot import name 'TIPOS' from 'tema'`

- [ ] **Step 3: Implementar o mínimo**

Acrescentar a `app/tema.py`:

```python
TIPOS = ("barra", "linha", "area", "barra_h")


def _cor_do_trace(tr) -> str | None:
    marker = getattr(tr, "marker", None)
    c = getattr(marker, "color", None) if marker is not None else None
    if isinstance(c, (list, tuple)):
        return None
    if c:
        return c
    linha = getattr(tr, "line", None)
    return getattr(linha, "color", None) if linha is not None else None


def converter_tipo(fig: go.Figure, tipo: str = "barra") -> go.Figure:
    """Reconstrói os traces na forma pedida preservando x, y, nome, cor e texto.

    Tipo desconhecido devolve a figura como está — o seletor da casca só oferece
    as formas declaradas em GraficoSpec.tipos, então isso é rede de segurança.
    """
    if tipo not in TIPOS or tipo == "barra" or not fig.data:
        return fig

    novos = []
    for tr in fig.data:
        c = _cor_do_trace(tr)
        base = dict(x=tr.x, y=tr.y, name=tr.name, text=tr.text,
                    hovertemplate=tr.hovertemplate, legendgroup=tr.legendgroup,
                    showlegend=tr.showlegend)
        if tipo == "linha":
            novos.append(go.Scatter(mode="lines+markers",
                                    line=dict(color=c, width=2),
                                    marker=dict(color=c, size=8),
                                    textposition="top center", **base))
        elif tipo == "area":
            novos.append(go.Scatter(mode="lines", stackgroup="um", fill="tonexty",
                                    line=dict(color=c, width=2), **base))
        elif tipo == "barra_h":
            trocado = dict(base, x=tr.y, y=tr.x)
            novos.append(go.Bar(orientation="h", marker=dict(color=c), **trocado))

    layout = fig.layout
    nova = go.Figure(data=novos, layout=layout)
    if tipo == "barra_h":
        titulo_x = layout.xaxis.title.text
        titulo_y = layout.yaxis.title.text
        nova.update_layout(xaxis_title=titulo_y, yaxis_title=titulo_x)
    return nova
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_tema.py`
Expected: `ok`

Se `test_barra_para_area_empilha` falhar em `fill` no primeiro trace, o Plotly usa `tozeroy` no primeiro de um `stackgroup`. Nesse caso trocar a asserção para `fig.data[1].fill == "tonexty"` — o comportamento está correto, a asserção é que estava errada.

- [ ] **Step 5: Commit**

```bash
git add app/tema.py app/pages/test_tema.py
git commit -m "feat: converter_tipo permite ver o mesmo gráfico como barra, linha, área ou barra horizontal"
git push
```

---

### Task 7: Tabela derivada da figura

**Files:**
- Create: `app/components/grafico.py`
- Test: `app/pages/test_grafico.py`

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces: `grafico.tabela_da_figura(fig) -> pd.DataFrame`.

Deriva a tabela de acompanhamento lendo `fig.data`. É o que garante estruturalmente que a tabela nunca diverge do gráfico — ela é a mesma fonte. Substitui os seis `_render_tabela`/`_build_tabela` escritos à mão (`inclusoes/layout.py:263`, `tramitacao/layout.py:190`, `reajuste/layout.py:148`, `sustentacao/layout.py:111`, `sessoes_virtuais/layout.py:206`, `acervo/layout.py:88`).

- [ ] **Step 1: Escrever o teste que falha**

Criar `app/pages/test_grafico.py`:

```python
"""Testes das partes puras de components/grafico.py."""
import plotly.graph_objects as go

from components.grafico import tabela_da_figura


def _fig_duas_series() -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=["2020", "2021"], y=[10, 20], name="Plenário Virtual"))
    fig.add_trace(go.Bar(x=["2020", "2021"], y=[5, 8], name="Plenário Presencial"))
    fig.update_layout(xaxis_title="Ano")
    return fig


def test_uma_linha_por_categoria_do_eixo_x():
    tab = tabela_da_figura(_fig_duas_series())
    assert list(tab["Ano"]) == ["2020", "2021", "Total"]


def test_uma_coluna_por_serie_mais_total():
    tab = tabela_da_figura(_fig_duas_series())
    assert list(tab.columns) == ["Ano", "Plenário Virtual", "Plenário Presencial", "Total"]


def test_valores_batem_com_a_figura():
    tab = tabela_da_figura(_fig_duas_series())
    assert list(tab["Plenário Virtual"]) == [10, 20, 30]
    assert list(tab["Plenário Presencial"]) == [5, 8, 13]
    assert list(tab["Total"]) == [15, 28, 43]


def test_serie_unica_sem_nome_usa_rotulo_generico():
    fig = go.Figure(go.Bar(x=["A", "B"], y=[1, 2]))
    tab = tabela_da_figura(fig)
    assert "Valor" in tab.columns
    assert list(tab["Valor"]) == [1, 2, 3]


def test_barra_horizontal_le_a_categoria_do_eixo_y():
    fig = go.Figure(go.Bar(x=[70.0, 30.0], y=["Concluído", "Não concluído"],
                           orientation="h", name="Percentual"))
    tab = tabela_da_figura(fig)
    assert list(tab.iloc[:, 0])[:2] == ["Concluído", "Não concluído"]
    assert list(tab["Percentual"])[:2] == [70.0, 30.0]


def test_figura_vazia_devolve_dataframe_vazio():
    assert tabela_da_figura(go.Figure()).empty


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_grafico.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'components.grafico'`

- [ ] **Step 3: Implementar o mínimo**

Criar `app/components/grafico.py`:

```python
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
    """
    if not fig.data:
        return pd.DataFrame()

    horizontal = getattr(fig.data[0], "orientation", None) == "h"
    nome_eixo = (fig.layout.yaxis.title.text if horizontal
                 else fig.layout.xaxis.title.text) or "Categoria"

    colunas: dict[str, pd.Series] = {}
    for i, tr in enumerate(fig.data):
        cats = tr.y if horizontal else tr.x
        vals = tr.x if horizontal else tr.y
        if cats is None or vals is None:
            continue
        nome = tr.name or ("Valor" if len(fig.data) == 1 else f"Série {i + 1}")
        serie = pd.Series(list(vals), index=[str(c) for c in cats], name=nome)
        colunas[nome] = serie.groupby(level=0, sort=False).sum() if serie.index.has_duplicates else serie

    if not colunas:
        return pd.DataFrame()

    tab = pd.DataFrame(colunas).fillna(0)
    numericas = tab.select_dtypes("number").columns
    if len(numericas) > 1:
        tab["Total"] = tab[numericas].sum(axis=1)
    tab.loc["Total"] = tab.sum(numeric_only=True)
    tab.index.name = nome_eixo
    return tab.reset_index()
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_grafico.py`
Expected: `ok`

Nota sobre `test_serie_unica_sem_nome_usa_rotulo_generico`: com uma só série não há coluna `Total` por linha, mas a linha `Total` existe — por isso a asserção espera `[1, 2, 3]`.

- [ ] **Step 5: Commit**

```bash
git add app/components/grafico.py app/pages/test_grafico.py
git commit -m "feat: tabela de acompanhamento derivada da própria figura"
git push
```

---

### Task 8: A casca do gráfico

**Files:**
- Modify: `app/components/grafico.py`

**Interfaces:**
- Consumes: `tema.aplicar_tema`, `tema.converter_tipo`, `tema.TIPOS`, `grafico.tabela_da_figura`.
- Produces:
  - `grafico.GraficoSpec` — dataclass com campos `id: str`, `rotulo: str`, `subtitulo: str`, `descricao: str`, `fn: Callable`, `tipos: tuple[str, ...] = ("barra",)`, `filtros: tuple[str, ...] = ()`, `percentual: bool = False`, `kwargs_fixos: dict = {}` (kwargs sempre passados a `fn`, usados pela Fase 3 para registrar variantes como "sem não concluído" sem função nova).
  - `grafico.FILTROS_VALIDOS: tuple[str, ...]` = `("ambiente", "classe", "tipo_questao", "desfecho", "periodo")`.
  - `grafico.render_grafico(spec: GraficoSpec, df: pd.DataFrame, key: str) -> None`.

Todo gráfico das oito páginas passa por aqui. `fn` recebe o dataframe já filtrado mais os kwargs que declarar aceitar.

- [ ] **Step 1: Escrever o teste que falha**

Acrescentar a `app/pages/test_grafico.py`, antes do bloco `__main__`:

```python
import inspect

import pandas as pd

from components.grafico import FILTROS_VALIDOS, GraficoSpec, _aplicar_filtros, _kwargs_aceitos


def _df() -> pd.DataFrame:
    return pd.DataFrame({
        "ano": [2019, 2020, 2020, 2021],
        "classe": ["ADI", "ADI", "ADPF", "ADC"],
        "ambiente": ["Plenário Virtual", "Plenário Presencial",
                     "Plenário Virtual", "Plenário Virtual"],
        "tipo_questao": ["PR", "RC", "PR", "QI"],
        "desfecho": ["Concluído - decisão unânime", "Não concluído - destaque",
                     "Concluído - decisão unânime", "Não concluído - destaque"],
    })


def test_spec_tem_barra_como_forma_padrao():
    spec = GraficoSpec(id="X1", rotulo="X1 — teste", subtitulo="s",
                       descricao="d", fn=lambda df: None)
    assert spec.tipos == ("barra",)
    assert spec.filtros == ()
    assert spec.percentual is False


def test_filtros_validos_cobrem_os_recortes_pedidos():
    assert set(FILTROS_VALIDOS) == {
        "ambiente", "classe", "tipo_questao", "desfecho", "periodo",
    }


def test_filtro_de_periodo_recorta_pelos_anos():
    out = _aplicar_filtros(_df(), {"periodo": (2020, 2020)})
    assert sorted(out["ano"].unique()) == [2020]


def test_filtro_de_classe_recorta_pelos_valores():
    out = _aplicar_filtros(_df(), {"classe": ["ADI"]})
    assert set(out["classe"]) == {"ADI"}


def test_filtros_combinam():
    out = _aplicar_filtros(_df(), {"periodo": (2020, 2021), "classe": ["ADI", "ADC"]})
    assert len(out) == 2


def test_filtro_de_coluna_inexistente_e_ignorado():
    out = _aplicar_filtros(pd.DataFrame({"x": [1]}), {"classe": ["ADI"]})
    assert len(out) == 1


def test_kwargs_aceitos_filtra_pelo_que_a_funcao_declara():
    def fn(df, show_values=True, ambiente="Plenário Virtual"):
        return None
    aceitos = _kwargs_aceitos(fn, {"show_values": False, "ambiente": "X", "proporcao": True})
    assert aceitos == {"show_values": False, "ambiente": "X"}


def test_kwargs_aceitos_com_funcao_que_so_recebe_df():
    def fn(df):
        return None
    assert _kwargs_aceitos(fn, {"show_values": False}) == {}
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_grafico.py`
Expected: FAIL com `ImportError: cannot import name 'FILTROS_VALIDOS' from 'components.grafico'`

- [ ] **Step 3: Implementar o mínimo**

Acrescentar a `app/components/grafico.py`:

```python
import inspect
from collections.abc import Callable
from dataclasses import dataclass, field

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


def _aplicar_filtros(df, escolhas: dict):
    """Recorta o dataframe pelas escolhas. Filtro sem coluna correspondente é ignorado."""
    out = df
    periodo = escolhas.get("periodo")
    if periodo and "ano" in out.columns:
        out = out[out["ano"].between(periodo[0], periodo[1])]
    for nome, coluna in _COLUNA_DO_FILTRO.items():
        valores = escolhas.get(nome)
        if valores and coluna in out.columns:
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

    for aba, fig in pares:
        contexto = aba if aba is not None else st.container()
        with contexto:
            fig = converter_tipo(fig, estado["tipo"])
            fig = aplicar_tema(fig, tema=tema_atual, dark=dark)
            fig.update_layout(showlegend=estado["legenda"] and len(fig.data) > 1)
            if not estado["show_values"]:
                fig.update_traces(text=None, texttemplate=None)
            st.plotly_chart(fig, width="stretch", key=f"{key}_fig_{id(fig)}")
            with st.expander("📊 Dados da visualização"):
                tab = tabela_da_figura(fig)
                if tab.empty:
                    st.caption("Esta visualização não produz tabela.")
                else:
                    st.dataframe(tab, width="stretch", height=280)
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_grafico.py`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add app/components/grafico.py app/pages/test_grafico.py
git commit -m "feat: casca de gráfico com controles, filtros dinâmicos e tabela espelhada"
git push
```

---

### Task 9: A casca da página

**Files:**
- Create: `app/components/catalogo.py`

**Interfaces:**
- Consumes: `grafico.GraficoSpec`, `grafico.render_grafico`.
- Produces: `catalogo.filtrar_por_busca(catalogo: list[GraficoSpec], termo: str) -> list[GraficoSpec]`, `catalogo.sumario_por_bloco(catalogo: list[GraficoSpec]) -> dict[str, list[GraficoSpec]]`, `catalogo.render_pagina(catalogo: list[GraficoSpec], df, key_prefix: str, sumario_titulo: str = "Sumário — visualizações disponíveis") -> None`.

Substitui os seis `render_graficos` duplicados. Acrescenta busca de gráfico, sumário navegável e link compartilhável.

- [ ] **Step 1: Escrever o teste que falha**

Criar `app/pages/test_catalogo.py`:

```python
"""Testes das partes puras de components/catalogo.py."""
from components.catalogo import filtrar_por_busca, sumario_por_bloco
from components.grafico import GraficoSpec


def _cat() -> list[GraficoSpec]:
    def _f(df):
        return None
    return [
        GraficoSpec(id="T5", rotulo="T5 — Macro-desfecho por ambiente",
                    subtitulo="s", descricao="Volume de inclusões concluídas", fn=_f),
        GraficoSpec(id="T6", rotulo="T6 — Desfecho detalhado por ambiente",
                    subtitulo="s", descricao="Os sete desfechos detalhados", fn=_f),
        GraficoSpec(id="T7", rotulo="T7 — Classe dentro de cada ambiente",
                    subtitulo="s", descricao="Composição por classe processual", fn=_f),
    ]


def test_busca_vazia_devolve_tudo():
    assert len(filtrar_por_busca(_cat(), "")) == 3
    assert len(filtrar_por_busca(_cat(), "   ")) == 3


def test_busca_por_id():
    assert [s.id for s in filtrar_por_busca(_cat(), "T6")] == ["T6"]
    assert [s.id for s in filtrar_por_busca(_cat(), "t6")] == ["T6"]


def test_busca_por_palavra_do_rotulo():
    assert [s.id for s in filtrar_por_busca(_cat(), "desfecho")] == ["T5", "T6"]


def test_busca_por_palavra_da_descricao():
    assert [s.id for s in filtrar_por_busca(_cat(), "processual")] == ["T7"]


def test_busca_ignora_acento():
    assert [s.id for s in filtrar_por_busca(_cat(), "composicao")] == ["T7"]


def test_busca_sem_resultado_devolve_lista_vazia():
    assert filtrar_por_busca(_cat(), "sustentação") == []


def test_sumario_agrupa_pelo_prefixo_do_id():
    blocos = sumario_por_bloco(_cat())
    assert list(blocos.keys()) == ["T"]
    assert [s.id for s in blocos["T"]] == ["T5", "T6", "T7"]


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
```

- [ ] **Step 2: Rodar o teste e confirmar que falha**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_catalogo.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'components.catalogo'`

- [ ] **Step 3: Implementar o mínimo**

Criar `app/components/catalogo.py`:

```python
"""Casca de página: busca, sumário navegável, seletor e compartilhamento.

Substitui os seis render_graficos duplicados nas páginas temáticas.
filtrar_por_busca e sumario_por_bloco são puros para poderem ser testados.
"""

from __future__ import annotations

import unicodedata

import streamlit as st

from components.grafico import GraficoSpec, render_grafico


def _sem_acento(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def filtrar_por_busca(catalogo: list[GraficoSpec], termo: str) -> list[GraficoSpec]:
    """Filtra o catálogo por id, rótulo ou descrição, ignorando caixa e acento."""
    alvo = _sem_acento(termo.strip())
    if not alvo:
        return list(catalogo)
    return [
        s for s in catalogo
        if alvo in _sem_acento(f"{s.id} {s.rotulo} {s.descricao}")
    ]


def sumario_por_bloco(catalogo: list[GraficoSpec]) -> dict[str, list[GraficoSpec]]:
    """Agrupa o catálogo pelo prefixo alfabético do id (T5 -> 'T', 2.a -> '2')."""
    blocos: dict[str, list[GraficoSpec]] = {}
    for spec in catalogo:
        prefixo = "".join(c for c in spec.id if not c.isdigit()).split("/")[0].split(".")[0]
        blocos.setdefault(prefixo.strip() or spec.id[:1], []).append(spec)
    return blocos


def render_pagina(catalogo: list[GraficoSpec], df, key_prefix: str,
                  sumario_titulo: str = "Sumário — visualizações disponíveis") -> None:
    """Renderiza uma página inteira a partir do seu catálogo."""
    chave_sel = f"{key_prefix}_selecionado"

    # Estado vindo do link compartilhado, lido só uma vez.
    if chave_sel not in st.session_state:
        do_link = st.query_params.get("g")
        st.session_state[chave_sel] = do_link if any(
            s.id == do_link for s in catalogo) else catalogo[0].id

    with st.expander(sumario_titulo, expanded=True):
        blocos = sumario_por_bloco(catalogo)
        cols = st.columns(min(len(blocos), 2) or 1)
        for i, (bloco, specs) in enumerate(blocos.items()):
            with cols[i % len(cols)]:
                st.markdown(f"**Bloco {bloco}**")
                for spec in specs:
                    if st.button(spec.rotulo, key=f"{key_prefix}_ir_{spec.id}",
                                 width="stretch"):
                        st.session_state[chave_sel] = spec.id
                        st.rerun()

    st.markdown("---")

    busca = st.text_input("🔎 Buscar gráfico", key=f"{key_prefix}_busca",
                          placeholder="id, título ou palavra da descrição")
    visiveis = filtrar_por_busca(catalogo, busca)
    if not visiveis:
        st.warning(f"Nenhum gráfico corresponde a “{busca}”.")
        return

    ids = [s.id for s in visiveis]
    atual = st.session_state[chave_sel]
    indice = ids.index(atual) if atual in ids else 0
    escolhido = st.selectbox(
        "Selecione a visualização", ids, index=indice, key=f"{key_prefix}_sel",
        format_func=lambda i: next(s.rotulo for s in visiveis if s.id == i),
    )
    st.session_state[chave_sel] = escolhido
    spec = next(s for s in visiveis if s.id == escolhido)

    st.subheader(spec.subtitulo)
    st.caption(spec.descricao)

    render_grafico(spec, df, key=f"{key_prefix}_{spec.id}")

    if st.button("🔗 Copiar link deste gráfico", key=f"{key_prefix}_link"):
        st.query_params["g"] = spec.id
        st.code(f"?g={spec.id}", language=None)
        st.caption("Link atualizado na barra de endereço.")
```

- [ ] **Step 4: Rodar o teste e confirmar que passa**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_catalogo.py`
Expected: `ok`

- [ ] **Step 5: Commit**

```bash
git add app/components/catalogo.py app/pages/test_catalogo.py
git commit -m "feat: casca de página com busca, sumário navegável e link compartilhável"
git push
```

---

### Task 10: Seletor de tema e modo noturno

**Files:**
- Modify: `app/app.py`

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces: `st.session_state["tema_visual"]` ∈ `{"novo", "empirico"}` (padrão `"novo"`) e `st.session_state["modo_noturno"]: bool` (padrão `False`), lidos por `render_grafico` na Task 8.

O toggle vale só para as oito páginas — os Blocos Empíricos não chamam `render_grafico`, então não são afetados por construção.

- [ ] **Step 1: Escrever o teste que falha**

Não há teste automatizado: é código de UI do Streamlit. A verificação é manual, no Step 4. Pular direto para o Step 3.

- [ ] **Step 2: Confirmar o estado atual**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python -c "import app"`
Expected: erro de contexto do Streamlit ou execução silenciosa — o objetivo é só confirmar que o arquivo é importável antes de mexer.

- [ ] **Step 3: Implementar**

Em `app/app.py`, entre o bloco `# ── Path setup ──` e `# ── Navegação ──`, inserir:

```python
# ── Preferências globais (valem só para as páginas não-empíricas) ────────────
CSS_NOTURNO = """
<style>
  [data-testid="stAppViewContainer"], [data-testid="stHeader"] { background: #0e1117; }
  [data-testid="stSidebar"] { background: #161a23; }
  .stMarkdown, .stCaption, h1, h2, h3, h4, label, p { color: #fafafa !important; }
</style>
"""


def _preferencias_globais() -> None:
    """Seletor de tema visual e modo noturno.

    Os Blocos Empíricos não passam por render_grafico, então não respondem ao
    tema — é isso que protege a validação da Pessoa 1.
    """
    with st.sidebar:
        st.header("Aparência")
        st.session_state["tema_visual"] = st.radio(
            "Tema dos gráficos",
            options=["novo", "empirico"],
            index=0,
            format_func=lambda t: "Novo padrão" if t == "novo" else "Visual empírico",
            help="O visual empírico reproduz os gráficos como estão nos Blocos "
                 "Empíricos. Não afeta as páginas dos Blocos Empíricos, que "
                 "sempre usam o visual original.",
            key="pref_tema",
        )
        st.session_state["modo_noturno"] = st.toggle(
            "Modo noturno", value=False, key="pref_noturno",
            help="Escurece o app e troca os degraus de cor dos gráficos.",
        )
        st.divider()

    if st.session_state["modo_noturno"]:
        st.markdown(CSS_NOTURNO, unsafe_allow_html=True)


_preferencias_globais()
```

- [ ] **Step 4: Verificar rodando o app**

Run: `cd /home/boscodeb/prog/plenario_virtual && .venv/bin/streamlit run app/app.py`

Confirmar, no navegador:
1. O sidebar mostra "Aparência" com o rádio de tema e o toggle de modo noturno.
2. O padrão é "Novo padrão" com modo noturno desligado.
3. Ligar o modo noturno escurece o app.
4. Abrir "Bloco 1 — Acervo" e confirmar que os gráficos **não** mudam com o rádio de tema.

- [ ] **Step 5: Commit**

```bash
git add app/app.py
git commit -m "feat: seletor de tema visual e modo noturno no sidebar"
git push
```

---

### Tasks 11 a 18: Migrar as oito páginas

Uma task por página, na ordem abaixo. Cada uma é independente e pode ser rejeitada sem bloquear as outras. Tramitação vem primeiro por concentrar os problemas conhecidos (`"Plenário Físico"` em cinco pontos, T6, rótulos de pizza herdados).

| Task | Página | Arquivo | Nota específica |
|---|---|---|---|
| 11 | Tramitação | `app/pages/tramitacao/layout.py` | Remover os cinco `"Plenário Físico"` de `plots.py:19,410,433,442` e `layout.py:172`; corrigir os comentários de pizza em `plots.py:88,201` e `tramitacao.py:44`. `gt10_tabulador` e `DIMENSOES` são importados por 5 outras páginas — **não mudar suas assinaturas**. |
| 12 | Inclusões em Pauta | `app/pages/inclusoes/layout.py` | 18 entradas de catálogo, a maior. Remover os `.upper()` de `plots.py:96,152` (o `canonico` já cobriria, mas a origem deve sumir). As pizzas continuam pizzas nesta fase — a Fase 2 as substitui. |
| 13 | Reajuste de Voto | `app/pages/reajuste/layout.py` | R7 e R8 estão definidos em `layout.py:24,28`, não em `plots.py`. Movê-los para `plots.py` ao migrar. |
| 14 | Sustentação Oral | `app/pages/sustentacao/layout.py` | — |
| 15 | Sessões Virtuais | `app/pages/sessoes_virtuais/layout.py` | **Remover o seletor de âmbito** (`layout.py:412`): `sessoes_virtuais.parquet` só tem Plenário Virtual, o seletor é decorativo. Usa `_DIMS_SV` próprio em vez de `DIMENSOES` — manter. |
| 16 | Acervo Histórico | `app/pages/acervo/layout.py` | Estrutura desviante: usa `st.tabs` aninhados por métrica e por classe, e o sumário está em `acervo.py:50-60`. Converter para catálogo com uma entrada por métrica. `test_plots.py` afirma `tickfont.size == 22` e `height == 650` — **atualizar essas asserções** para os tamanhos padronizados. |
| 17 | Visão Geral | `app/pages/geral/layout.py` | Não tem `plots.py` e não importa `estilo.py`. A timeline (`layout.py:56`) é `go.Scatter` com anotações e `height=1400`; não cabe no catálogo — manter fora dele e aplicar só `aplicar_tema`. Única página usando `render_sidebar_filters`; `filtros["show_values"]` nunca é consumido — remover. |
| 18 | Gráficos Narrativa | `app/pages/narrativa/layout.py`, `plots.py` | **Religar ao dado real.** As seis funções têm valores fixos no código (`plot_na` a `plot_nf`) e assinatura `fn(show_values=...)` sem dataframe. `plot_nb`, `plot_ne` e `plot_nf` duplicam 2.l, 2.q e 2.r de `bloco2_inclusoes/plots.py:458,658,681`, que computam do parquet — reescrever as seis para receber `df` e calcular, conferindo que os números batem com os fixos de hoje (63,9 / 91,3 / 1,8 / 4,3 / 86,0 / 39,2). Só então declarar `filtros=("periodo", "classe")`. |

Cada uma das tasks 11–18 repete **verbatim** os seis passos abaixo, trocando o nome da página, o `key_prefix` e aplicando a nota específica da tabela. Tramitação aparece como exemplo concreto.

- [ ] **Step 1: Converter o `_CATALOGO` em lista de `GraficoSpec`**

Em `app/pages/tramitacao/layout.py`, trocar as tuplas de 4 elementos por `GraficoSpec`. Exemplo com T6, que hoje está em `layout.py:61-66`:

```python
from components.catalogo import render_pagina
from components.grafico import GraficoSpec

_CATALOGO = [
    # ... T1 a T5 ...
    GraficoSpec(
        id="T6",
        rotulo="T6 — Desfecho detalhado por ambiente de tramitação",
        subtitulo="Desfecho detalhado por ambiente de tramitação — Inclusões (2016–2025)",
        descricao="Os sete desfechos detalhados (unânime, maioria, pedido de vista "
                  "e os demais) em cada grupo de tramitação.",
        fn=gt6_desfecho_por_tram,
        tipos=("barra", "barra_h", "linha"),
        filtros=("classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    # ...
]
```

Regras para preencher os campos:
- `id`: o identificador já usado hoje (`T6`, `G12/G13`, `S1/S2`).
- `subtitulo` e `descricao`: reaproveitar o texto do catálogo atual, **corrigindo o período declarado** — `tramitacoes.parquet` cobre 2016–2025, não 2020–2025 como todos os subtítulos de Tramitação afirmam hoje.
- `tipos`: `("barra",)` quando outra forma não faz sentido; acrescentar `"linha"` quando o eixo x for temporal; `"barra_h"` quando as categorias tiverem nome longo; `"area"` só em série temporal empilhável.
- `filtros`: só os recortes que existem como coluna no dataframe da página.
- `percentual=True` quando a função aceitar `proporcao`.

- [ ] **Step 2: Substituir `render_graficos` pela casca**

Trocar o corpo de `render_graficos` (hoje `layout.py:274-303`) por:

```python
def render_graficos(df: pd.DataFrame) -> None:
    render_pagina(_CATALOGO, df, key_prefix="tram")
```

Apagar `_SUMARIO`, `_LABELS`, `_render_fig`, `_render_tabela`, `_build_tabela` e `_TABELA_SPECS` — a casca cobre todos. Manter `_render_tabulador`, que é um modo próprio, e registrá-lo como uma `GraficoSpec` com `fn=None` tratada à parte, ou deixá-lo fora do catálogo em um `st.expander` no fim da página.

- [ ] **Step 3: Rodar os testes existentes**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_paleta.py && PYTHONPATH=. ../.venv/bin/python pages/test_tema.py && PYTHONPATH=. ../.venv/bin/python pages/test_grafico.py && PYTHONPATH=. ../.venv/bin/python pages/test_catalogo.py`
Expected: quatro linhas `ok`

- [ ] **Step 4: Verificar a página no app**

Run: `cd /home/boscodeb/prog/plenario_virtual && .venv/bin/streamlit run app/app.py`

Confirmar, na página migrada:
1. Busca, sumário com botões e seletor funcionam.
2. Todo gráfico está em Times New Roman, com rótulo de ano na horizontal.
3. Nenhum texto diz "Plenário Físico".
4. Alternar o tipo de gráfico refaz a figura sem erro.
5. A tabela do expander bate com o que está plotado.
6. Modo noturno não deixa nenhum texto ilegível.

- [ ] **Step 5: Confirmar que os Blocos Empíricos não foram tocados**

Run: `git diff --stat -- app/pages/bloco1_acervo app/pages/bloco2_inclusoes app/pages/bloco3_pandemia`
Expected: saída vazia

- [ ] **Step 6: Commit**

```bash
git add app/pages/tramitacao/
git commit -m "refactor: Tramitação usa a casca de catálogo; remove 'Plenário Físico' e corrige período declarado"
git push
```

---

### Task 19: Portão de conformidade de estilo

**Files:**
- Create: `app/pages/test_conformidade.py`

**Interfaces:**
- Consumes: todos os `_CATALOGO` das tasks 11–18, `tema.aplicar_tema`.
- Produces: teste que trava regressão de estilo nas oito páginas.

Constrói toda figura de todo catálogo com um dataframe sintético e afirma as regras globais. É o que impede a próxima pessoa de reintroduzir Arial, `tickangle=-45` ou uma pizza.

- [ ] **Step 1: Escrever o teste que falha**

Criar `app/pages/test_conformidade.py`:

```python
"""Portão de estilo: toda figura das oito páginas obedece o padrão da Pessoa 2.

Constrói cada gráfico dos catálogos com um dataframe sintético e afirma fonte,
tamanhos, ângulo de tick, rótulo de ambiente e ausência de pizza. Os Blocos
Empíricos são deliberadamente excluídos.
"""
import pandas as pd
import plotly.graph_objects as go

from tema import FONTE, TAMANHOS, aplicar_tema

TAMANHOS_PERMITIDOS = set(TAMANHOS.values())


def _df_sintetico() -> pd.DataFrame:
    """Cobre as colunas que as oito páginas leem, com todos os valores do
    vocabulário para que nenhum groupby volte vazio."""
    desfechos = [
        "Concluído - decisão unânime",
        "Concluído - decisão maioria com o relator",
        "Concluído - decisão maioria, vencido o relator",
        "Não concluído - motivos diversos",
        "Não concluído - retirado de pauta",
        "Não concluído - pedido de vista",
        "Não concluído - destaque",
    ]
    linhas = []
    incidente = 0
    for ano in range(2016, 2026):
        for classe in ("ADI", "ADPF", "ADC", "ADO"):
            for ambiente in ("Plenário Virtual", "Plenário Presencial"):
                for i, desfecho in enumerate(desfechos):
                    incidente += 1
                    linhas.append({
                        "incidente": incidente,
                        "nome_processo": f"{classe} {incidente}",
                        "classe": classe,
                        "relator": "Min. Fulano",
                        "ano": ano,
                        "ambiente": ambiente,
                        "tipo_questao": ("PR", "RC", "QI")[i % 3],
                        "desfecho": desfecho,
                        "macro_desfecho": desfecho.split(" - ")[0],
                        "tramitacao": ("Só Virtual", "Ambos os ambientes",
                                       "Só Presencial")[i % 3],
                        "teve_reajuste": i % 2 == 0,
                        "teve_sustentacao": i % 3 == 0,
                        "tramitou_ambos": i % 2 == 1,
                        "virou_sessao": True,
                        "data_inclusao_dt": pd.Timestamp(f"{ano}-06-15"),
                        "data_sessao_dt": pd.Timestamp(f"{ano}-06-15"),
                    })
    return pd.DataFrame(linhas)


def _df_acervo() -> pd.DataFrame:
    """Acervo lê evolucao_acervo.parquet, de shape completamente diferente."""
    linhas = []
    for ano in range(1988, 2026):
        for classe, base in (("ADI", 900), ("ADPF", 300), ("ADC", 60), ("ADO", 30)):
            ativos = base + (ano - 1988) * 7
            linhas.append({
                "ano": ano, "classe": classe,
                "quantidade_ativos": ativos,
                "quantidade_inativos": ativos // 3,
                "quantidade_baixas": base // 4,
                "quantidade_distribuidos": base // 3,
                "total_geral": ativos + ativos // 3,
            })
    return pd.DataFrame(linhas)


def _catalogos():
    """(nome da página, catálogo). Import tardio: layout.py importa streamlit.

    Sete das oito páginas. 'geral' fica de fora porque não tem catálogo — sua
    única figura é a timeline de layout.py:56, coberta pela verificação manual.
    """
    from pages.acervo.layout import _CATALOGO as acervo
    from pages.inclusoes.layout import _CATALOGO as inclusoes
    from pages.narrativa.layout import _CATALOGO as narrativa
    from pages.reajuste.layout import _CATALOGO as reajuste
    from pages.sessoes_virtuais.layout import _CATALOGO as sessoes
    from pages.sustentacao.layout import _CATALOGO as sustentacao
    from pages.tramitacao.layout import _CATALOGO as tramitacao
    inclusoes_df = _df_sintetico()
    return [
        ("tramitacao", tramitacao, inclusoes_df),
        ("inclusoes", inclusoes, inclusoes_df),
        ("reajuste", reajuste, inclusoes_df),
        ("sustentacao", sustentacao, inclusoes_df),
        ("sessoes_virtuais", sessoes,
         inclusoes_df[inclusoes_df["ambiente"] == "Plenário Virtual"]),
        ("acervo", acervo, _df_acervo()),
        ("narrativa", narrativa, inclusoes_df),
    ]


def _figuras(resultado):
    if isinstance(resultado, dict):
        return list(resultado.values())
    if isinstance(resultado, (list, tuple)):
        return list(resultado)
    return [resultado]


def _todas_as_figuras():
    from components.grafico import _kwargs_aceitos
    for pagina, catalogo, df in _catalogos():
        for spec in catalogo:
            if spec.fn is None:
                continue
            kwargs = _kwargs_aceitos(spec.fn, {"show_values": True, "proporcao": False})
            for fig in _figuras(spec.fn(df, **kwargs)):
                if isinstance(fig, go.Figure):
                    yield pagina, spec.id, aplicar_tema(fig)


def test_nenhuma_pizza():
    for pagina, gid, fig in _todas_as_figuras():
        tipos = {tr.type for tr in fig.data}
        assert "pie" not in tipos, f"{pagina}/{gid} ainda tem gráfico de pizza"


def test_fonte_times_em_toda_figura():
    for pagina, gid, fig in _todas_as_figuras():
        assert fig.layout.font.family == FONTE, f"{pagina}/{gid}"
        assert fig.layout.xaxis.tickfont.family == FONTE, f"{pagina}/{gid}"
        assert fig.layout.yaxis.tickfont.family == FONTE, f"{pagina}/{gid}"


def test_tick_do_eixo_x_sempre_horizontal():
    for pagina, gid, fig in _todas_as_figuras():
        assert fig.layout.xaxis.tickangle == 0, f"{pagina}/{gid} gira o rótulo do eixo x"


def test_tamanhos_dentro_da_escala():
    for pagina, gid, fig in _todas_as_figuras():
        for tam in (fig.layout.xaxis.tickfont.size, fig.layout.yaxis.tickfont.size,
                    fig.layout.title.font.size):
            assert tam in TAMANHOS_PERMITIDOS, f"{pagina}/{gid} usa tamanho {tam}"


def test_nenhum_texto_diz_plenario_fisico():
    for pagina, gid, fig in _todas_as_figuras():
        textos = [fig.layout.title.text or ""]
        textos += [tr.name or "" for tr in fig.data]
        textos += [a.text or "" for a in fig.layout.annotations]
        for t in textos:
            assert "Plenário Físico" not in t, f"{pagina}/{gid}: “{t}”"


if __name__ == "__main__":
    for nome, fn in sorted(globals().items()):
        if nome.startswith("test_"):
            fn()
    print("ok")
```

- [ ] **Step 2: Rodar e ver quais páginas ainda violam**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_conformidade.py`
Expected: FAIL em `test_nenhuma_pizza` apontando os gráficos de Inclusões e Sustentação — as pizzas só saem na Fase 2. Todas as outras asserções devem passar.

- [ ] **Step 3: Marcar a falha esperada**

Trocar `test_nenhuma_pizza` para registrar o débito em vez de quebrar o portão, até a Fase 2:

```python
# ponytail: as pizzas de Inclusões e Sustentação saem na Fase 2 — até lá o teste
# só congela a lista para nenhuma nova aparecer. Apertar para == set() na Fase 2.
PIZZAS_CONHECIDAS = {
    ("inclusoes", "G5"), ("inclusoes", "G6/G7"), ("inclusoes", "G8/G9"),
    ("inclusoes", "G22/G23"), ("inclusoes", "G26/G27"),
    ("sustentacao", "S1/S2"),
}


def test_nenhuma_pizza_nova():
    encontradas = {
        (pagina, gid) for pagina, gid, fig in _todas_as_figuras()
        if "pie" in {tr.type for tr in fig.data}
    }
    assert encontradas <= PIZZAS_CONHECIDAS, (
        f"pizza nova: {encontradas - PIZZAS_CONHECIDAS}")
```

Ajustar os ids em `PIZZAS_CONHECIDAS` para os que a execução do Step 2 realmente reportou.

- [ ] **Step 4: Rodar e confirmar que passa**

Run: `cd app && PYTHONPATH=. ../.venv/bin/python pages/test_conformidade.py`
Expected: `ok`

- [ ] **Step 5: Rodar a suíte inteira**

Run:
```bash
cd app && for f in pages/test_*.py pages/acervo/test_plots.py; do
  echo "--- $f"; PYTHONPATH=. ../.venv/bin/python "$f" || break
done
```
Expected: `ok` em cada arquivo

- [ ] **Step 6: Commit**

```bash
git add app/pages/test_conformidade.py
git commit -m "test: portão de conformidade de estilo nas páginas não-empíricas"
git push
```

---

## Verificação da fase

1. Suíte completa verde (Task 19, Step 5).
2. `git diff --stat -- app/pages/bloco*/` vazio contra o commit inicial da fase.
3. `streamlit run app/app.py`: percorrer as oito páginas e conferir Times New Roman, ano na horizontal, controles presentes, tabela batendo com o gráfico, e ausência de "Plenário Físico".
4. Alternar o tema para "Visual empírico" e confirmar que os gráficos das oito páginas voltam ao visual atual.
5. Abrir "Bloco 1 — Acervo" e confirmar que nada mudou lá.

## Débito deliberado desta fase

- As pizzas continuam existindo — Fase 2.
- `estilo.py` mantém as constantes de cor antigas porque os Blocos Empíricos as importam. A limpeza só é possível se os blocos empíricos forem migrados, o que está fora de escopo.
- O modo noturno do cromo do Streamlit depende de CSS injetado (`CSS_NOTURNO` em `app.py`) e pode quebrar numa atualização do Streamlit. Os gráficos trocam corretamente por caminho suportado.
