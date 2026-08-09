# Padronização do dashboard para a Pessoa 2

**Data:** 2026-08-09
**Status:** desenho aprovado, aguardando plano de implementação

---

## 1. Contexto

O dashboard tem hoje 11 páginas servindo três leitoras diferentes. Três delas — os
**Blocos Empíricos** (`bloco1_acervo`, `bloco2_inclusoes`, `bloco3_pandemia`) —
reproduzem as figuras da dissertação da Pessoa 1 e já foram validadas por ela
número a número. As outras oito — Acervo, Inclusões em Pauta, Reajuste de Voto,
Tramitação por Ambiente, Sustentação Oral, Sessões Virtuais, Visão Geral e
Narrativa — são a área de trabalho da Pessoa 2, que pediu uma padronização visual
completa, novos recortes e uma camada de interatividade que hoje não existe.

O estado atual dessas oito páginas é de padronização declarada mas não cumprida.
Existe um módulo de estilo (`app/estilo.py`) que define o "PADRÃO GERAL", e
praticamente toda função de gráfico o sobrescreve: sete paletas de classe
processual diferentes convivem no mesmo app, tamanhos de fonte variam de 11 a 22
sem critério, nove pontos rotacionam o rótulo de ano em −45° e outros nove não,
e a mesma variável (Plenário Virtual, ADI, "Concluído") aparece em cores
diferentes dependendo da página. Há ainda seis gráficos de pizza e o rótulo
"Plenário Físico" persistindo em cinco pontos do código de Tramitação.

O resultado pretendido: as oito páginas passam a ler como um sistema único, com
tipografia Times New Roman, uma paleta semântica validada para daltonismo em modo
claro e escuro, filtros e alternância de forma em todo gráfico, e uma camada de UI
(tela inicial, busca, sumário navegável, modo noturno, compartilhamento). Os
Blocos Empíricos não são tocados.

---

## 2. Escopo

### Muda

| Página | Arquivos |
|---|---|
| Acervo Histórico | `app/pages/acervo/` |
| Inclusões em Pauta | `app/pages/inclusoes/` |
| Reajuste de Voto | `app/pages/reajuste/` |
| Tramitação por Ambiente | `app/pages/tramitacao/` |
| Sustentação Oral | `app/pages/sustentacao/` |
| Sessões Virtuais | `app/pages/sessoes_virtuais/` |
| Visão Geral | `app/pages/geral/` |
| Gráficos Narrativa | `app/pages/narrativa/` |

Mais os módulos compartilhados: `app/app.py`, `app/estilo.py`,
`app/components/`, e três módulos novos (§3).

### Não muda

`app/pages/bloco1_acervo/`, `app/pages/bloco2_inclusoes/`,
`app/pages/bloco3_pandemia/` — **somente leitura**. As oito páginas vão *importar*
funções desses módulos, nunca editá-los. Qualquer necessidade de alterar um
gráfico empírico é sinal de que a adaptação pertence à camada de tema, não à
função original.

`app/Codigos_graficos_completos.py` é código morto (matplotlib, caminhos
`/mnt/user-data/` inexistentes, nada o importa). Fica como está.

---

## 3. Arquitetura

A observação que define o desenho: seis das oito páginas já têm a **mesma**
estrutura de renderização duplicada — dicionário `_SUMARIO` → expander de sumário →
`st.selectbox` sobre um `_CATALOGO` de tuplas `(label, subtítulo, descrição, fn)` →
subheader + caption → checkbox "Exibir valores" → `st.plotly_chart` → expander com
`st.dataframe`. E `estilo.py` já é o ponto de passagem de quase toda figura.

Isso permite atender a maioria dos pedidos em **quatro módulos compartilhados**, em
vez de editar ~90 funções de gráfico uma a uma.

### 3.1 `app/paleta.py` (novo) — fonte única de cor

Mapa semântico `valor → cor`, com variante clara e escura, e uma função
`cor(nome, dark=False)` com fallback determinístico para valores desconhecidos.
Substitui as sete paletas espalhadas hoje por `inclusoes/plots.py:12-48`,
`tramitacao/plots.py:12-42`, `reajuste/plots.py:9-20`, `sustentacao/plots.py:9-20`,
`sessoes_virtuais/plots.py:9-17` e `acervo/plots.py:13`.

### 3.2 `app/tema.py` (novo) — pós-processador de figura

```python
aplicar_tema(fig, tema="novo", dark=False) -> go.Figure
converter_tipo(fig, tipo) -> go.Figure     # barra | linha | area | barra_h
```

`aplicar_tema` percorre a figura pronta e reescreve tipografia, tamanhos, ângulo
de tick, capitalização de legenda e cor por nome de série. É o mecanismo que faz
as regras de formatação valerem em **todo** gráfico das oito páginas sem editar
nenhuma função de gráfico:

| Pedido da Pessoa 2 | Como o pós-processador resolve |
|---|---|
| Times New Roman | `font.family` em layout, eixos, legenda, anotações e `textfont` de cada trace |
| Tamanhos padronizados | Escala fixa: título 22, subtítulo 14, título de eixo 16, tick 14, legenda 14, valor 13, anotação 12 |
| Ano sempre na horizontal | `tickangle=0` forçado; se houver colisão, reduz o tick em vez de girar |
| Legenda em maiúscula/minúscula | Sentence case preservando siglas (ADI, ADPF, ADC, ADO, PV, PP, PR, RC, QI, ER, ESPIN, STF) — desfaz os `.upper()` de `inclusoes/plots.py:96,152` |
| "Plenário Físico" → "Plenário Presencial" | Substituição em nome de série, título, título de eixo e anotação |
| Cor conta uma história | Recolore o trace por `paleta.cor(trace.name)` quando o nome é conhecido — garante que Plenário Virtual é a mesma cor em todos os gráficos |
| Modo noturno | Troca fundo e tinta; as séries usam o degrau escuro validado, não um flip automático |

Com `tema="empirico"` a função devolve a figura intocada — é assim que o
alternador de tema funciona, sem duplicar código de gráfico.

`converter_tipo` reconstrói os traces preservando x/y/nome/cor/texto, atendendo
"priorize barra mas permita ver como linha".

### 3.3 `app/components/grafico.py` (novo) — a casca do gráfico

`render_grafico(spec, df, key)` recebe a especificação vinda do catálogo da página
e renderiza, em uma linha de controles acima da figura:

- ☑ Exibir valores ☑ Exibir legenda
- Tipo de gráfico (só as formas declaradas como válidas para aquele gráfico)
- Absoluto / Percentual
- Filtros contextuais conforme `spec.filtros`: âmbito, classe, tipo de questão,
  desfecho, e **slider de período** com início e fim

Depois chama `fn`, aplica `aplicar_tema` + `converter_tipo`, renderiza, e monta a
tabela **derivada da própria figura** — lendo `fig.data` (x, y, name) e pivotando.
Isso é o que garante estruturalmente que "a tabela de acompanhamento segue a mesma
tabulação dinâmica do gráfico": ela não pode divergir porque é a mesma fonte.
Substitui os seis `_render_tabela`/`_build_tabela` escritos à mão hoje.

### 3.4 `app/components/catalogo.py` (novo) — a casca da página

`render_pagina(catalogo, df, key_prefix)` substitui os seis `render_graficos`
duplicados. Adiciona:

- **Busca de gráfico**: `st.text_input` filtrando os rótulos do catálogo
- **Sumário navegável**: cada item vira botão que seta o `session_state` do
  seletor — navegação real, já que a página mostra um gráfico por vez
- **Compartilhamento**: estado do gráfico e dos filtros em `st.query_params`,
  com botão "Copiar link". Download PNG já vem da modebar do Plotly.

### 3.5 Alterações em módulos existentes

- `app/app.py`: registra a página inicial como primeira e default; adiciona no
  sidebar o seletor de tema (Novo padrão / Visual empírico) e o toggle de modo
  noturno, guardados em `st.session_state`.
- `app/estilo.py`: passa a delegar cor para `paleta.py`; mantém `ER_DATAS`,
  `ESPIN_*`, `add_er_marker`, `add_espin_shade`, `br` inalterados (os Blocos
  Empíricos importam esses símbolos).
- `app/pages/home/` (novo): tela inicial.

---

## 4. Paleta

Construída pelo método da skill `dataviz` e **validada com
`scripts/validate_palette.js`** contra as superfícies reais do app (claro
`#ffffff`, escuro `#0e1117`). Nenhum valor foi escolhido a olho.

### Ambiente — a espinha da narrativa

| Valor | Claro | Escuro |
|---|---|---|
| Plenário Virtual | `#2a78d6` | `#3987e5` |
| Plenário Presencial | `#eb6834` | `#d95926` |

Azul = o ambiente digital que absorve o trabalho da corte; laranja = o
contraponto presencial. Esse par se repete em macro-desfecho (Concluído /
Não concluído) e ancora a leitura de todo o dashboard.

### Tramitação

Só Virtual `#2a78d6`/`#3987e5` · Ambos os ambientes `#1baf7a`/`#199e70` ·
Só Presencial `#eb6834`/`#d95926` — ecoa o par de ambiente. Passa em todos os
pares nos dois modos.

### Classe processual

ADI `#2a78d6`/`#3987e5` · ADPF `#eb6834`/`#d95926` · ADC `#1baf7a`/`#199e70` ·
ADO `#eda100`/`#c98500`. Aprovado na lista de pares adjacentes (a correta para
barras agrupadas) nos dois modos.

### Desfecho detalhado — a correção do item 2.a

Sete séries discrimináveis em uma figura só **não existem**: nenhuma ordenação de
sete matizes passa nos limiares de daltonismo. Essa é a causa real da queixa
"as cores de concluído-maioria-vencido-o-relator e não-concluído-retirado-de-pauta
estão muito parecidas". A solução é **matiz carrega a família, tom carrega o
degrau**, com os degraus ordenados por volume:

| Desfecho | n | Claro | Escuro |
|---|---|---|---|
| Concluído - decisão unânime | 2.500 | `#184f95` | `#184f95` |
| Concluído - decisão maioria com o relator | 1.055 | `#2a78d6` | `#3987e5` |
| Concluído - decisão maioria, vencido o relator | 165 | `#86b6ef` | `#9ec5f4` |
| Não concluído - motivos diversos | 3.938 | `#9c3d13` | `#c9541d` |
| Não concluído - retirado de pauta | 1.434 | `#c9541d` | `#eb6834` |
| Não concluído - pedido de vista | 1.021 | `#eb6834` | `#f5a184` |
| Não concluído - destaque | 172 | `#f5a184` | `#fac7b6` |

Ambas as rampas passam como ordinais nos dois modos. O par específico da queixa
passa de indistinguível para ΔE 30,5 (visão normal) e 26,2 (daltonismo) — família
azul contra família laranja, decidido contra travado.

### Tipo de questão

PR `#2a78d6`/`#3987e5` · RC `#eb6834`/`#d95926` · QI `#1baf7a`/`#199e70`.

### Binários e resíduo

Com sustentação / Com reajuste: `#1baf7a`/`#199e70`. Sem: `#898781` (cinza
reservado para ausência e para o balde "outros", nunca para uma categoria com
conteúdo próprio).

### Regra de alívio

`#1baf7a` (2,82:1) e `#eda100` (2,17:1) ficam abaixo de 3:1 sobre branco. A regra
de alívio do método exige rótulo visível ou tabela — as duas coisas existem por
desenho na casca do gráfico (toggle de valores + expander de tabela). Não é
dispensável: o toggle "Exibir valores" nasce **ligado**.

---

## 5. Fases

Cada fase deixa o app rodando e revisável.

### Fase 1 — Motor de estilo e casca de gráfico

Entrega `paleta.py`, `tema.py`, `components/grafico.py`, `components/catalogo.py`,
e converte as oito páginas para a casca.

Resolve de uma vez, nas oito páginas: Times New Roman, tamanhos padronizados, ano
horizontal, capitalização de legenda, "Plenário Presencial", cor consistente por
variável, toggle de valores, toggle de legenda, alternância barra/linha/área/barra
horizontal, filtro de período, filtro de classe e demais recortes, e tabela
espelhando o gráfico.

Levantamento de formas alternativas por gráfico (quais fazem sentido para cada um)
é parte desta fase e vira o campo `tipos` de cada entrada de catálogo.

### Fase 2 — Fim das pizzas e correções específicas

- Substitui os três pontos de `go.Pie` (`inclusoes/plots.py:95`,
  `inclusoes/plots.py:440`, `sustentacao/plots.py:52`, alimentando G5, G6/G7,
  G8/G9, G22/G23, G26/G27, S1/S2) por barra horizontal com percentual na ponta.
- **T6**: eixo X "Ambiente de tramitação", eixo Y "Quantidade de desfechos",
  valores visíveis por padrão, cores da nova paleta.
- **G12/G13**: segmentação por tipo de desfecho concluído.
- **G22/G23**: barra horizontal, rótulo à esquerda, percentual na ponta.
- **G24/G25**: eixo Y "Quantidade de processos incluídos em pauta".
- Corrige os rótulos herdados errados: comentários de pizza em
  `tramitacao/plots.py:88,201` e `tramitacao.py:44`, e "Plenário Físico" em
  `tramitacao/plots.py:19,410,433,442` e `tramitacao/layout.py:172`.

### Fase 3 — Gráficos novos (itens 6 e 7)

| Item | Gráfico | Implementação |
|---|---|---|
| 6.b | G22/23 sem não concluído, %, barra | flag `excluir_nc` na função de barra horizontal |
| 6.c | G24/25 sem não concluído, % | `g24` com `proporcao=True, excluir_nc=True` |
| 6.d | G26/27 sem não concluído, barras | barra horizontal por tipo |
| 6.e | G28/29 sem não concluído, % | flags na função existente |
| 6.f | Desfecho em % por ambiente — um para PV, um para PP; X = tipo de desfecho, Y = "Percentual de desfechos (%)" | função nova, 2 entradas de catálogo |
| 6.b(2) | Linha temporal unânime vs divergência ("maioria com o relator" + "maioria, vencido o relator") — PP, PV, ambos | **uma** função `linha_decisao(df, agrupamento, ambiente)`, 3 entradas |
| 6.b(3) | Linha temporal com o relator ("unânime" + "maioria com o relator") vs divergência ("maioria, vencido o relator") — PP, PV, ambos | mesma função, outro `agrupamento`, 3 entradas |
| 7.a | Desfechos do PP 2009–2019, só concluídos, %, estilo G24/25 | depende da Fase 4 |
| 7.b | Linha temporal unânime vs divergência, PP+PV, 2010–2025, com marcos ER exceto ER 53 | depende da Fase 4 |

Catorze entradas de catálogo, seis funções novas — os recortes "sem não concluído"
e "em percentual" já são parâmetros da casca da Fase 1, e ganham entrada própria só
para a Pessoa 2 achar pronto.

### Fase 4 — Estender o pipeline para 2009

`src/inclusao_pauta.py:7` fixa `ANO_INI, ANO_FIM = 2016, 2025`. Os andamentos
brutos (`data/interim/dim_andamentos.parquet`) têm eventos de pauta desde 2005, então
2009 é alcançável, mas o classificador de desfecho foi validado só em 2016+.

Procedimento, nesta ordem:

1. Rodar com `ANO_INI = 2009`.
2. **Portão de regressão**: os números de 2016–2025 têm que bater exatamente com o
   parquet atual. Se divergirem, parar e reportar.
3. Inspecionar amostra de 2009–2015 contra o texto de origem. A correção de
   `tipo_questao` em `app/dados/correcao_tipo_questao_2016_2019.csv` cobre só
   2016–2019 e **não** se aplica ao período novo.
4. Só então subir ao HF via `scripts/upload_hf.py` e construir 7.a e 7.b.

Se o passo 3 mostrar que a classificação pré-2016 não se sustenta, reporto e paro —
7.a e 7.b ficam com o período disponível e nota visível.

### Fase 5 — Portar os gráficos empíricos

Os 17 gráficos dos Blocos Empíricos sem equivalente fora deles entram nos catálogos
das páginas temáticas **por import**, passando pelo `aplicar_tema`. Zero duplicação,
zero edição nos blocos empíricos.

| Destino | Gráficos |
|---|---|
| Acervo | 1.a, 1.a.2, 1.b, 1.b2, 1.b3, 1.b4, 1.c, 1.d, 1.d.2 |
| Inclusões em Pauta | 2.a.2, 2.c, 2.d, 2.j2, 2.k1, 2.l.2, 2.n.3 |
| Tramitação | 2.i, 3.1, 3.1 (alt), 3.2 (alt) |

Cuidado conhecido: esses gráficos embutem tamanho de fonte de 13 a 22, `tickangle`
de −90, alturas de 420 a 1500 e HTML inline (`<span style='font-size:20px'>`) nos
rótulos. O pós-processador precisa neutralizar o HTML inline, não só o `textfont`.

### Fase 6 — Camada de UI

- **Tela inicial** (`app/pages/home/`): o que é o dashboard, como usar os filtros e
  a alternância de forma, link para o repositório, link para o dataset no Hugging
  Face (`JoaoBoscoooo/plenario_virtual`), espaço marcado para vídeo de uso, e
  espaço marcado para contribuidores e responsáveis pela pesquisa — a preencher
  manualmente.
- **Modo noturno**: toggle no sidebar. Figuras vêm de `aplicar_tema(dark=True)`.
  O cromo do Streamlit vai por injeção de CSS — o Streamlit 1.59 não troca o
  próprio tema em runtime pela API pública, e essa é a limitação honesta da
  abordagem. Padrão é claro.
- **Textos**: reescrever títulos e legendas para afirmarem o achado (regra do
  PADRÃO GERAL), corrigir "Plenário Físico", corrigir os períodos declarados
  errados — a página Tramitação anuncia 2020–2025 em todos os subtítulos mas
  `tramitacoes.parquet` cobre 2016–2025 — e escrever o texto dos gráficos novos.

---

## 6. Limitações conhecidas

1. **7.a e 7.b dependem da Fase 4.** Sem o reprocessamento, o dado não existe.
2. **Modo noturno do cromo é CSS.** Streamlit 1.59 não expõe troca de tema em
   runtime. Os gráficos trocam corretamente; a moldura do app depende de CSS
   injetado e pode quebrar numa atualização do Streamlit.
3. **Sete desfechos numa figura só nunca ficarão plenamente discrimináveis.** A
   paleta por família mais os rótulos de valor resolvem a queixa concreta; a
   leitura ideal continua sendo o recorte por família, que a casca oferece por
   filtro.
4. **`sessoes_virtuais.parquet` só tem Plenário Virtual** (4.335 linhas, ambiente
   único). O seletor de âmbito nessa página é decorativo hoje e será removido em
   vez de padronizado.
5. **Gráficos da Narrativa têm valores fixos no código** (`narrativa/plots.py`, seis
   funções sem dataframe). Filtro de período e de classe não se aplicam a eles; vão
   receber só a padronização visual, ou serão religados ao dado real — decisão a
   tomar na Fase 1 ao montar o catálogo.

---

## 7. Verificação

Por fase:

1. `streamlit run app/app.py` e percorrer as oito páginas, gráfico a gráfico.
2. **Portão de não-regressão dos Blocos Empíricos**: os três blocos precisam
   renderizar idênticos ao estado atual. `git diff --stat` sobre
   `app/pages/bloco*/` tem que vir vazio ao fim de cada fase.
3. **Portão de paleta**: reexecutar `validate_palette.js` sobre cada grupo
   semântico nos dois modos sempre que a paleta mudar.
4. **Portão do dado (Fase 4)**: contagens de 2016–2025 idênticas às do parquet
   atual antes de qualquer upload ao HF.
5. Checagem automatizável de estilo: um teste que percorre as figuras produzidas
   pelas oito páginas e afirma família de fonte, tamanhos, `tickangle == 0` e
   ausência de `go.Pie`. `app/pages/acervo/test_plots.py` já estabelece o padrão de
   teste do repositório.
