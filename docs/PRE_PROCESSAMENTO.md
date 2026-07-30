# Pré-processamento

Etapa que roda antes de qualquer análise: transforma o CSV bruto exportado do
STF num modelo estrela (star schema) em Parquet, pronto para consumo pelo
dashboard e pelos pipelines de análise por âmbito.

## Organização dos arquivos de dados

`data/` é um repositório git separado (clone do dataset publicado no
Hugging Face), não versionado junto com o código deste repositório.

```
data/raw/ArquivosConcatenados.csv     fonte bruta, 1 linha por processo, colunas JSON aninhadas
data/processed/                       saída final, pronta para consumo direto
  arquivosConcatenados.parquet          tabela fato
  dim_decisoes.parquet                  dimensão decisões
data/interim/                         dimensões de alto volume, usadas por múltiplos pipelines downstream
  dim_partes.parquet
  dim_andamentos.parquet
  dim_deslocamentos.parquet
```

O critério `interim` vs `processed`: tabelas já fechadas para consumo direto
(dashboard, análise final) vão para `processed`; dimensões que ainda
alimentam outras etapas do pipeline (ex.: `dim_andamentos` é insumo de
Acervo, Inclusão em Pauta, Reajuste de Voto) ficam em `interim`.

Contrato completo de colunas de cada arquivo: [`CONTEXTO_DADOS.md`](CONTEXTO_DADOS.md).

## Pré-processamento

Implementação: [`src/cleaning.py`](../src/cleaning.py). Notebook de
orquestração e EDA: [`notebooks/01_limpeza_preprocessamento.ipynb`](../notebooks/01_limpeza_preprocessamento.ipynb).

Fluxo do `run_pipeline`:

```
load_raw(csv) → clean(df) → build_fact_table(proc)  → arquivosConcatenados.parquet
                          → explode_partes(proc)      → dim_partes.parquet
                          → explode_andamentos(proc)  → dim_andamentos.parquet
                          → explode_decisoes(proc)    → dim_decisoes.parquet
                          → explode_deslocamentos(proc) → dim_deslocamentos.parquet
```

`clean()` aplica, em sequência:
- **Padronização de nulos** (`limpar_nulos`) — normaliza marcadores como
  `"NA"`, `"nan"`, `""`, `"[]"` para `None`.
- **`numero_processo`** — extraído do segundo token de `nome_processo`
  (ex.: `"ADI 1234"` → `1234`).
- **`liminar`** — parse de string-lista (`"['MEDIDA LIMINAR']"`) para lista
  Python real.
- **`esfera_origem`** (`categorizar_esfera`) — coluna derivada por
  varredura textual de `origem_orgao`, ver racional na seção de metodologia.
- **`lista_assuntos`** — mesmo parse de string-lista, com fallback
  `["Não Informado"]` para vazios.
- **Tipagem** — `data_protocolo` vira `datetime`, `incidente` vira `int`,
  colunas de baixa cardinalidade (`classe`, `classe_extenso`,
  `tipo_processo`, `origem`, `relator`, `status_processo`) viram `category`.

`build_fact_table()` remove as 4 colunas de JSON pesado
(`partes_total`, `andamentos_lista`, `decisões`, `deslocamentos_lista`) do
dataset principal — elas já foram exportadas separadamente.

`explodir_json_veloz()` (a função por trás dos 4 `explode_*`) resolve o
problema central desta etapa: cada uma dessas colunas guarda uma lista de
dicionários (relação 1 processo : N eventos) serializada como string dentro
de uma única célula. O algoritmo faz `ast.literal_eval` seguro sobre a
string, dá `explode` na lista (1 linha por evento), normaliza os
dicionários resultantes em colunas (`json_normalize`) com um prefixo por
dimensão (`par_`, `and_`, `dec_`, `des_`), e concatena de volta as colunas
de contexto (`incidente`, `classe`, `tipo_processo`).

Como rodar:

```bash
python -m src.cleaning data/raw/ArquivosConcatenados.csv data/processed data/interim
# ou, via entry point registrado em pyproject.toml:
stf-etl data/raw/ArquivosConcatenados.csv data/processed data/interim
```

## Metodologia de tratamento

### Por que a coluna derivada `esfera_origem`

O campo bruto `origem_orgao` é altamente fragmentado — termos genéricos,
abreviações e varas específicas coexistem (`"TRIBUNAL REGIONAL FEDERAL"` ao
lado de `"3ª VARA FEDERAL DO DF"`). Sem tratamento, essa dispersão
pulverizaria qualquer agregação ou gráfico. A solução foi criar uma coluna
nova (`esfera_origem`), agrupando os órgãos em macrocategorias
institucionais homogêneas (Justiça Federal, Justiça Estadual, Justiça
Eleitoral, Justiça do Trabalho, Tribunais Superiores, Ministério Público,
Conselhos de Justiça, Outros/Administração), **sem remover** a coluna
original — preserva-se o nível de detalhe bruto para investigações
específicas futuras, e disponibiliza-se uma variável pronta para
frequência/gráfico.

### Achados de qualidade de dados

Nulos no dataset bruto (9.358 processos):

| Coluna | Nulos | % |
|---|---|---|
| `origem` | 23 | 0,25% |
| `relator` | 71 | 0,76% |
| `autor1` | 7 | 0,07% |
| `origem_orgao` | 180 | 1,92% |

`origem_orgao` concentra a maior lacuna — esperado em processos que nascem
no próprio STF ou vêm de migrações de sistemas antigos. Os 369 nulos
observados em `lista_assuntos` foram confirmados como nulos já na fonte
(não é bug de parsing do pipeline).

### Por que star schema em vez de colunas JSON no dataset principal

Manter `partes_total`/`andamentos_lista`/`decisões`/`deslocamentos_lista`
como strings JSON dentro da tabela fato inviabilizaria contagens exatas e
qualquer cruzamento estatístico (ex.: nome do julgador de uma decisão
específica ficaria inacessível a `groupby`/pivot padrão). Separar em fato +
4 dimensões, ligadas por `incidente`, elimina redundância de
armazenamento, reduz uso de memória e permite agregações diretas sobre cada
evento.

### Por que Parquet em vez de CSV

Formato colunar e binário: compressão mais eficiente, preserva os tipos de
dado definidos em memória (datas, categorias) sem reparsing a cada leitura,
mais rápido para as etapas analíticas subsequentes.

## Referências de implementação

- Pipeline: [`src/cleaning.py`](../src/cleaning.py)
- Notebook de orquestração e EDA: [`notebooks/01_limpeza_preprocessamento.ipynb`](../notebooks/01_limpeza_preprocessamento.ipynb)
- Contrato dos dados processados: [`CONTEXTO_DADOS.md`](CONTEXTO_DADOS.md)
