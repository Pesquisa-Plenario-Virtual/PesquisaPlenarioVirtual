# Estrutura do Projeto

Onde cada coisa mora, por quê, e as regras que mantêm isso verdadeiro. Serve de
referência para qualquer pessoa ou modelo que precise trabalhar no código.

---

## Árvore

```
app/
├── app.py                  # entrada: navegação + preferências globais (tema, modo noturno)
│
├── visual/                 # cor, tipografia e mobiliário de gráfico
│   ├── __init__.py         # API pública — as páginas importam daqui
│   ├── paleta.py           # qual cor cada variável do domínio tem
│   ├── tema.py             # o que fazer com a figura já construída
│   └── base.py             # marcadores ER/ESPIN, formatação brasileira, layout base
│
├── components/             # cascas de renderização reutilizáveis
│   ├── grafico.py          # GraficoSpec + controles + tabela espelhada
│   ├── catalogo.py         # busca, sumário navegável, seletor de visualização
│   └── tabulador.py        # tabulador de eixos livres, compartilhado por 6 páginas
│
├── dados/                  # carga e filtragem
│   ├── config.py           # repositório HF e mapa de arquivos
│   ├── loader.py           # download + cache; devolve dataframe bruto
│   └── filters.py          # filtragem pura, sem Streamlit
│
└── pages/
    ├── acervo/  inclusoes/  reajuste/  tramitacao/
    ├── sustentacao/  sessoes_virtuais/  narrativa/     # as oito da Pessoa 2
    ├── geral/
    └── bloco1_acervo/  bloco2_inclusoes/  bloco3_pandemia/   # Blocos Empíricos
```

---

## A regra que este projeto aprendeu do jeito difícil

**O pipeline corrige o dado. O app nunca o remenda.**

Havia um CSV de 72 linhas dentro de `dados/` que reclassificava `tipo_questao`
em tempo de carga, contornando um bug de regex no extrator de
`src/inclusao_pauta.py`. O remendo escondia o problema: o parquet publicado no
Hugging Face continuava errado, e quem o consumisse fora deste app recebia a
classificação incorreta sem ter como saber. Nada importava o CSV como módulo —
ele era lido por caminho de arquivo, então sumia do grafo de dependências e só
reapareceu quando quebrou.

Se um número está errado, o conserto é no pipeline e o parquet é reprocessado.
`scripts/reprocessar_inclusoes.py` faz a comparação com portão de regressão.

---

## Camada visual

Três módulos porque são três papéis, não por acidente.

`paleta` responde *de que cor é o Plenário Virtual*. É um dicionário semântico,
sem Plotly e sem Streamlit, validado para daltonismo em modo claro e escuro.
Os hex não devem ser alterados sem revalidar com o script da skill `dataviz`.

`tema` responde *o que fazer com uma figura pronta*. Percorre a figura e impõe
fonte, tamanhos, ângulo de tick, rótulo canônico, cor da paleta e formatação
numérica brasileira. É o que permite padronizar ~90 gráficos sem editar ~90
funções, e o que o alternador de tema liga e desliga.

`base` é o mobiliário de domínio usado *enquanto* a figura é construída:
marcadores de Emenda Regimental, sombreamento da ESPIN, `br()` e o layout de
referência. O nome não é `legado` de propósito — tanto a camada nova quanto os
Blocos Empíricos consomem daqui.

Fluxo: a função de gráfico monta a figura com `base`; a casca passa o resultado
por `tema`, que consulta `paleta`.

---

## Como uma página funciona

Cada página é uma pasta com três arquivos:

- **`plots.py`** constrói e devolve `go.Figure`. Não importa Streamlit.
- **`layout.py`** declara o catálogo (`list[GraficoSpec]`) e chama a casca.
- **`<pagina>.py`** carrega o dado, aplica o recorte e chama o layout.

O catálogo é a superfície inteira da página. Cada entrada declara o que oferece:

```python
GraficoSpec(
    id="T6",
    rotulo="T6 — Desfecho detalhado por ambiente de tramitação",
    subtitulo="...", descricao="...",
    fn=gt6_desfecho_por_tram,
    tipos=("barra", "barra_h", "linha"),      # formas alternativas oferecidas
    filtros=("classe", "tipo_questao", "periodo"),
    percentual=True,                           # só se o toggle mudar o resultado
)
```

A casca cuida do resto: controles, filtros, conversão de forma, tema, e a tabela
— que é **derivada da própria figura**, então não pode divergir do gráfico.

Uma entrada pode trazer o próprio renderizador via `renderer` quando seus
controles não cabem no conjunto fixo. É assim que o tabulador entra no catálogo.

### Regras de preenchimento que já custaram bug

- `filtros` só aceita nome cuja coluna **existe** no dataframe da página. Um
  filtro apontando para coluna ausente não faz nada em silêncio — ou derruba a
  página, se o tabulador tentar usá-la.
- `percentual=True` só se alternar a escala **mudar o resultado**. Quatro
  funções declaravam `proporcao` e ignoravam o parâmetro; o toggle aparecia e
  não fazia nada.
- Título e subtítulo não devem fixar período. A casca oferece filtro de tempo,
  então qualquer intervalo escrito à mão vira mentira no primeiro recorte.
  Derive do dataframe.
- Período fixo é **identidade do gráfico**, não configuração. Gráficos de
  panorama/bloco (ex.: bloco1/bloco2) fixam o ano na própria função — a origem
  do dado impõe o recorte e o eixo fica travado nele. Ao portar uma figura com
  período fixo para a casca, declarar `filtros=()` e receber o dataframe inteiro
  por closure: um recorte temporal quebrado vira `KeyError` ou eixo vazio, nunca
  um gráfico "menos um ano" em silêncio. `percentual=True` exige `proporcao`
  com efeito real no eixo (contagem ↔ percentual), como em `_composicao`.

---

## Fronteiras

| Arquivo | `st.*` | Plotly | Filtra dado |
| --- | --- | --- | --- |
| `dados/filters.py` | não | não | sim |
| `dados/loader.py` | só `st.cache_data` | não | não |
| `visual/paleta.py` | não | não | não |
| `visual/tema.py` | não | sim | não |
| `visual/base.py` | não | sim | não |
| `components/*` | sim | só recebe figura | só recorte declarado |
| `pages/*/plots.py` | não | sim | não |
| `pages/*/layout.py` | sim | só recebe figura | não |
| `pages/*/<pagina>.py` | só configuração | não | só orquestração |

Os dados sempre fluem para baixo. Nenhuma camada inferior conhece a superior, e
**nenhuma página importa de outra página** — se duas precisam do mesmo helper,
ele sobe para `dados/` ou `components/`.

---

## Os Blocos Empíricos

`bloco1_acervo`, `bloco2_inclusoes` e `bloco3_pandemia` reproduzem as figuras da
dissertação e são de outra leitora. Eles **não** passam pela casca nem pela
camada de tema: chamam `st.plotly_chart` direto e mantêm o visual original de
propósito. O alternador de tema não os afeta.

Ao mexer neles, o padrão de verificação é comparar o JSON das figuras antes e
depois — igualdade byte a byte, não inspeção visual.

---

## Testes

`assert` puro, sem framework, com bloco `__main__` de descoberta automática:

```python
if __name__ == "__main__":
    for _nome, _fn in sorted(globals().items()):
        if _nome.startswith("test_"):
            _fn()
    print("ok")
```

Chamar os testes por nome nesse bloco já fez teste novo passar despercebido.

Rodar tudo:

```bash
cd app && for f in $(find . -name "test_*.py" | sort); do
  PYTHONPATH=. ../.venv/bin/python "$f"
done
PYTHONPATH=. .venv/bin/python src/tests/test_inclusao_pauta.py
```

`pages/test_conformidade.py` é o portão de estilo: percorre toda figura de todo
catálogo em todas as formas declaradas e afirma fonte, escala de tamanhos,
tickangle, ausência de "Plenário Físico", cor vinda da paleta e formatação
numérica. É o que impede o padrão de se desfazer aos poucos.

Limitação de ambiente: um segundo `AppTest.run()` na mesma instância segfalha
nesta venv (pandas + pyarrow). Uma instância por cenário funciona.

---

## Como adicionar

**Um gráfico**: escreva `fig_*` em `plots.py`, acrescente um `GraficoSpec` ao
catálogo. Mais nada.

**Uma página**: crie a pasta com os três arquivos e registre em `app.py`.

**Um filtro**: acrescente a `FILTROS_VALIDOS` e ao mapa de colunas em
`components/grafico.py`; as páginas passam a poder declará-lo.

**Um dataset**: registre em `dados/config.py` e crie `load_<nome>()` em
`loader.py`.
