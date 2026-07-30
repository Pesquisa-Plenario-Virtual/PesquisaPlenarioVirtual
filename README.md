# STF Plenário Virtual — Jurimetria

Projeto de jurimetria sobre o Plenário Virtual do Supremo Tribunal Federal:
~9.358 processos de controle concentrado de constitucionalidade
(ADI/ADPF/ADC/ADO), 1988–2026. Duas entregas principais:

- **Pipeline de dados** — transforma o export bruto do STF num modelo
  analítico (star schema) em Parquet, e a partir dele constrói indicadores
  por âmbito de análise (acervo, inclusão em pauta, tramitação, sustentação
  oral, reajuste de voto).
- **Dashboard** (Streamlit, `app/`) — visualização interativa desses
  indicadores.

## Estrutura

```
app/         Dashboard Streamlit (documentação própria, ver docs/DASHBOARD.md)
data/        Dados processados (.parquet) e brutos — repo git separado, clone HF
docs/        Documentação de pré-processamento, metodologia e specs de design
notebooks/   Notebooks de orquestração e EDA do pipeline (numerados por ordem de execução)
src/         Pacote Python com a lógica de tratamento/transformação de dados
scripts/     Utilitários (ex: upload_hf.py)
```

## Documentação

| Tema | Onde |
|---|---|
| Pré-processamento (organização dos dados, limpeza, star schema) | [docs/PRE_PROCESSAMENTO.md](docs/PRE_PROCESSAMENTO.md) |
| Contrato dos dados processados (schema de cada parquet) | [docs/CONTEXTO_DADOS.md](docs/CONTEXTO_DADOS.md) |
| Metodologia por âmbito de análise | [docs/METODOLOGIA_ACERVO.md](docs/METODOLOGIA_ACERVO.md) (Acervo — demais âmbitos em construção) |
| Dashboard | [docs/DASHBOARD.md](docs/DASHBOARD.md) |
| Plano de refatoração do pipeline | [docs/superpowers/specs/2026-07-23-refatoracao-pipeline-design.md](docs/superpowers/specs/2026-07-23-refatoracao-pipeline-design.md) |

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
