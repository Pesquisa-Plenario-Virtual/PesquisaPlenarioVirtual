# STF Plenário Virtual — Jurimetria

Desde a redemocratização, o Supremo Tribunal Federal chegou a acumular mais
de 5 mil ações de controle concentrado de constitucionalidade ativas ao
mesmo tempo. Em menos de uma década esse número caiu para cerca de mil — e
boa parte da explicação está numa mudança silenciosa de rito: o **Plenário
Virtual**, hoje o ambiente onde a maioria dessas ações é de fato julgada.

Este é um projeto de pesquisa em jurimetria que investiga essa
transformação a partir dos dados públicos do STF: como o volume de
processos evoluiu ao longo do tempo, como itens entram e saem de pauta no
ambiente virtual, o que acontece quando um ministro pede destaque ou muda
de voto, e como tudo isso se compara ao rito físico tradicional. A ideia é
transformar ~9.358 processos de ADI, ADPF, ADC e ADO (1988–2026) — hoje
espalhados em campos de texto e listas aninhadas — num conjunto de dados
analítico, documentado e reprodutível, e usar isso tanto para produzir
indicadores quantitativos quanto para sustentar um dashboard exploratório.

O repositório tem duas partes:

- **Pipeline de dados** (`src/`, `notebooks/`) — do CSV bruto do STF até um
  modelo analítico (star schema) em Parquet, e a partir dele os
  indicadores de cada frente de análise (acervo, inclusão em pauta,
  tramitação, sustentação oral, reajuste de voto).
- **Dashboard** (`app/`, Streamlit) — visualização interativa desses
  indicadores.

## Estrutura

```
app/         Dashboard Streamlit (documentação própria, ver docs/dashboard/)
data/        Dados processados (.parquet) e brutos — repo git separado, clone HF
docs/        Documentação do projeto (pré-processamento, metodologias, dashboard)
notebooks/   Notebooks de orquestração e EDA do pipeline (numerados por ordem de execução)
src/         Pacote Python com a lógica de tratamento/transformação de dados
scripts/     Utilitários (ex: upload_hf.py)
```

## Documentação

- [**Pré-processamento**](docs/PRE_PROCESSAMENTO.md) — de onde vêm os dados, como o CSV bruto do STF é limpo e transformado no modelo analítico (star schema).
- [**Contrato dos dados**](docs/CONTEXTO_DADOS.md) — schema completo de cada tabela processada.
- [**Metodologias**](docs/metodologias/) — como cada frente de análise foi construída. Hoje cobre [Acervo](docs/metodologias/acervo.md); as demais (inclusão em pauta, tramitação, sustentação oral, reajuste de voto) estão em construção.
- [**Dashboard**](docs/dashboard/) — documentação da aplicação Streamlit.
- [Plano de refatoração do pipeline](docs/superpowers/specs/2026-07-23-refatoracao-pipeline-design.md) — registro histórico de como o projeto saiu de notebooks soltos para o pipeline versionado atual.

## Setup

```bash
pip install -e .
# ou
pip install -r requirements.txt
```

## Rodar o dashboard

```bash
streamlit run app/app.py
```

Lê `data/processed/` localmente; sem token necessário em dev. Em produção
(Streamlit Cloud) usa Hugging Face Datasets (`HF_REPO`/`HF_TOKEN`, ver
[app/DATA_LAYER.md](app/DATA_LAYER.md)).

## Pipeline de dados

```bash
stf-etl data/raw/ArquivosConcatenados.csv data/processed data/interim
```

Roda a etapa de pré-processamento (`src/cleaning.py`), gerando o star
schema em `data/processed/` e `data/interim/` a partir do CSV bruto. Os
demais âmbitos de análise (acervo, inclusão em pauta, tramitação,
sustentação oral, reajuste de voto) têm seus próprios módulos em `src/` e
notebooks de orquestração em `notebooks/` — ver
[docs/PRE_PROCESSAMENTO.md](docs/PRE_PROCESSAMENTO.md).

## Publicar dados no Hugging Face

```bash
python scripts/upload_hf.py
```
