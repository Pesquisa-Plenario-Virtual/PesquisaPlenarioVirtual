# Metodologia — Acervo Histórico

## Definição e Escopo

### O que é o indicador de Acervo

O indicador de **Acervo** mede o volume de processos de controle concentrado de constitucionalidade em tramitação ativa no Supremo Tribunal Federal, ano a ano, entre 1988 e 2025. Responde à pergunta: *"quantos processos o STF tinha em carteira em 31 de dezembro de cada ano, e de que natureza jurídica eram?"*

Diferente de um retrato do status atual do tribunal, o Acervo é uma **reconstrução histórica**: reconstitui, para cada ano do intervalo, o estoque de processos que estavam de fato ativos naquele momento — abrindo mão do estado presente (2026) para recompor a série temporal completa.

### Classes processuais cobertas

O escopo abrange exclusivamente as ações de controle concentrado de constitucionalidade:
- **ADI** — Ação Direta de Inconstitucionalidade
- **ADPF** — Arguição de Descumprimento de Preceito Fundamental
- **ADC** — Ação Declaratória de Constitucionalidade
- **ADO** — Ação Direta de Inconstitucionalidade por Omissão

Ficam fora do escopo quaisquer outras classes processuais do STF (recursos extraordinários, habeas corpus, mandados de segurança etc.) — o dataset de origem (`data/raw/ArquivosConcatenados.csv`) já é recortado a esse universo antes de chegar ao pipeline de Acervo.

### Cobertura temporal

1988 (marco da Constituição Federal, início do controle concentrado no desenho atual) até 2025, com corte de leitura sempre em 31 de dezembro de cada ano.

### O que o indicador mede — e o que não mede

**Mede:**
- Estoque de processos ativos por ano e por classe (o "quanto tem em carteira");
- Fluxo de saída — quantos processos foram baixados/arquivados em cada ano;
- Fluxo de entrada — quantos processos novos foram distribuídos em cada ano;
- Composição proporcional do acervo por classe ao longo do tempo (ex.: participação crescente da ADPF).

**Não mede:**
- Tempo de tramitação individual de cada processo (esse é outro indicador, fora do escopo do Acervo);
- Mérito ou resultado das decisões;
- Reaberturas/reativações pós-baixa (tratadas como fora de escopo — ver limitações da metodologia);
- Granularidade infra-anual (mês/trimestre) — o corte é sempre anual.

### Por que esse indicador importa

O Acervo é o indicador-base para entender a capacidade operacional do tribunal ao longo do tempo: mostra se o STF está acumulando ou dando vazão a processos, e permite associar mudanças de patamar a eventos institucionais conhecidos — como as Emendas Regimentais (ER 51/52/53) e o período da ESPIN (2020–2022), que marcam o Plenário Virtual como principal ferramenta de aceleração de julgamentos. Serve de contexto quantitativo para os demais indicadores do projeto (inclusão em pauta, tramitação, sustentação oral, reajuste de voto), que operam sobre subconjuntos ou eventos dentro desse mesmo universo de processos.

## Metodologia

### Unidade de análise

A unidade de análise é o **processo** (ações de controle concentrado de constitucionalidade — ADI, ADPF, ADC, ADO e CC), identificado de forma única pelo campo `incidente`, chave primária da tabela fato (`arquivosConcatenados.parquet`) e chave estrangeira nas tabelas de dimensão (`dim_andamentos.parquet`). A separação em modelo estrela (fato/dimensão) permitiu isolar apenas as variáveis necessárias à reconstrução — `incidente`, `classe`, `data_protocolo` na fato; `and_nome` e `and_data` em `dim_andamentos` — sem sobrecarregar memória com colunas irrelevantes ao problema do acervo.

### Problema metodológico: por que não usar o status atual

Para responder "qual era o acervo em 31/12/AAAA", não é possível usar o campo de status atual do processo (`status_processo`): um processo hoje baixado pode ter estado plenamente ativo em anos anteriores. Foi necessário reconstruir a **linha do tempo** de cada processo — período de vida útil entre entrada e saída — e então aplicar um corte (*snapshot*) a cada 31 de dezembro do intervalo 1988–2025.

### Ajuste da unidade de análise: de andamento para processo

A fonte primária do desfecho (`dim_andamentos`) está no nível de **andamento** (evento processual, N por processo). Para se chegar à unidade de análise desejada (processo), aplicou-se:

1. **Marco de início** — `data_protocolo` da tabela fato, marco de nascimento do processo.
2. **Marco de encerramento** — extraído do texto livre de `and_nome` via expressão regular, buscando os termos que configuram baixa definitiva:
   `baixa ao arquivo | baixa definitiva dos autos | baixa dos autos | processo findo`
   Todo andamento cujo nome (normalizado para minúsculas, sem espaços nas pontas) casa com esse padrão é candidato a marco de encerramento.
3. **Colapso N:1** — como um processo pode ter múltiplos andamentos que casam com o padrão de baixa (ex.: baixa seguida de reativação por recurso), tomou-se a **data mínima** (`groupby(incidente).min()`) entre os andamentos de baixa como `data_baixa`. Premissa assumida: a primeira baixa já encerra a contagem do processo no acervo ativo, mesmo que haja reativação — escopo deste indicador não modela reaberturas.

O resultado é uma tabela em nível de processo (`acervo_historico`), com três colunas: `incidente`, `classe`, `data_protocolo`, `data_baixa` (nula quando o processo nunca foi baixado).

### Lógica do snapshot anual

Para cada ano do intervalo 1988–2025 e cada classe (ADI, ADC, ADO, ADPF, CC), um processo é contado no acervo daquele ano se, e somente se, simultaneamente:

- **Já existia**: `data_protocolo <= 31/12/ano`;
- **Ainda tramitava**: `data_baixa` é nula **ou** `data_baixa > 31/12/ano` (baixado só em ano futuro).

Dessa contagem derivam-se três métricas por ano/classe:
- **Ativos** — atendem aos dois critérios acima e ainda não baixaram até o corte;
- **Inativos** — existiam no corte, mas já haviam baixado;
- **Total geral** — ativos + inativos (todo processo protocolado até o corte).

Duas métricas complementares, com corte por **ano de ocorrência** (não cumulativas):
- **Baixas do ano** — `data_baixa` cai dentro do intervalo `[01/01, 31/12]` do ano;
- **Distribuições do ano** — `data_protocolo` cai dentro do mesmo intervalo.

### Validação

Como checagem de consistência interna, cada linha ano/classe é validada pela identidade `ativos + inativos == total_geral`, garantida por `assert` no pipeline (`src/acervo.py::evolucao_acervo_por_ano`) — qualquer violação interrompe a execução em vez de gerar dado silenciosamente incorreto.

## Referências de implementação

- Pipeline: [`src/acervo.py`](../../src/acervo.py)
- Notebook de orquestração e EDA: [`notebooks/02_acervo.ipynb`](../../notebooks/02_acervo.ipynb)
- Contrato geral dos dados processados: [`CONTEXTO_DADOS.md`](../CONTEXTO_DADOS.md)
