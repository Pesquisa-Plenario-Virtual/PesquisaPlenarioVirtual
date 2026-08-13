# Plano — resolução das issues #4, #5, #6 e #7

## Context

O dashboard passou pela Fase 1 (motor de estilo e casca de gráfico, 19 tasks), pela
Fase 2 (fim das pizzas) e por um conserto de dado na origem que foi republicado no
Hugging Face. Restam quatro issues do pedido original da Pessoa 2: os 14 gráficos
novos (#4), estender o pipeline para 2009 (#5), portar os 17 gráficos que só existem
nos Blocos Empíricos (#6) e a camada de UI que falta — tela inicial e revisão de
textos (#7).

O objetivo é fechar o pedido dela com o dashboard consistente: todo gráfico obedecendo
o mesmo padrão visual, todo controle fazendo o que promete, e nenhum texto afirmando
coisa que o dado não sustenta.

**Nota sobre convenções:** o `CONTEXT.md` citado no pedido não existe neste repo. O
glossário efetivo está em `docs/CONTEXTO_DADOS.md` (esquema e vocabulário do domínio)
e em `app/PROJECT_STRUCTURE.md` (fronteiras de camada, reescrito na Fase 1). O código
deve seguir esses dois.

---

## Ordenação por dependências

```
  PREFACTOR ──► #4 (12 de 14) ──┐
                                ├──► #7 (textos, por último)
              #6 ───────────────┘
              #5 (isolada, por último) ──► #4: 7.a e 7.b
```

**Arestas bloqueantes reais:**

- **Prefactor → #4.** Três funções (`g22`, `g26`, `_composicao`) declaram `proporcao`
  e ignoram o parâmetro. Metade dos gráficos do item 6 são variantes percentuais
  dessas. Construir em cima de parâmetro morto produz toggle que não faz nada — já
  aconteceu antes neste projeto, em quatro funções do Reajuste.
- **#5 → 7.a e 7.b apenas.** Os outros 12 gráficos da #4 não dependem dela.
- **#4 e #6 → #7.** A revisão de textos deve vir depois de todo gráfico existir, senão
  se revisa duas vezes.
- **#5 fica isolada e por último** (decisão do usuário). É a única com risco de
  descobrir que o dado não presta; se falhar, só 7.a e 7.b ficam de fora.

`#6` não bloqueia nem é bloqueada por `#4` — podem ir em qualquer ordem entre si.

---

## Prefactor — "make the change easy"

Antes de escrever qualquer gráfico novo. Cada item é um commit próprio, com teste.

**P1. `proporcao` deixa de ser parâmetro morto.**
`app/pages/inclusoes/plots.py`: `g22_cat_periodo_filtravel:494`,
`g26_cat_tipo_periodo_filtravel:512` e `_composicao:94` (que absorve o parâmetro em
`**_ignorado`). Ou o parâmetro muda o resultado, ou some da assinatura e o
`percentual=True` sai do catálogo. Não pode continuar aceito e ignorado.

Como `_composicao` já mostra `"{pct}%  ({valor})"` na ponta da barra, o caminho natural
é `proporcao` alternar o eixo x entre contagem e percentual, mantendo o rótulo.

**P2. `excluir_nc` como conceito único.**
Não existe nada parecido no repo hoje. Quatro dos gráficos novos (6.b–6.e) são "o
mesmo gráfico, sem o balde de não concluído". Um helper em
`app/pages/inclusoes/plots.py` que recebe o dataframe e devolve só as três categorias
concluídas, reusado pelas quatro entradas via `kwargs_fixos={"excluir_nc": True}`.

A fonte da verdade é `_categoria_desfecho:138`, que produz `"4 - Não concluído (bloco)"`
como fallback. Excluir é remover essa categoria, não filtrar por string de desfecho —
assim a regra fica num lugar só.

**P3. Convenção declarada para entradas de período fixo.**
Necessária pela #6 (ver abaixo). Documentar em `app/PROJECT_STRUCTURE.md`: uma entrada
cujo `fn` filtra o ano internamente **não declara `periodo` em `filtros`** e recebe o
dataframe completo por closure. O padrão já existe em
`app/pages/sessoes_virtuais/layout.py:_montar_catalogo` (Bloco 5 captura `df_final`).

---

## Issue #4 — 14 gráficos novos

**Objetivo.** Os itens 6 e 7 do pedido: variantes sem "não concluído", desfecho em
percentual por ambiente, e seis linhas temporais de unanimidade contra divergência.

**Fatia 1 — variantes "sem não concluído" (6.b a 6.e).** 4 entradas.
Depende de P1 e P2. Cada uma é a função existente mais `kwargs_fixos`, sem função nova:
`g22` e `g26` com `excluir_nc`; `g24` e `g28` com `excluir_nc` e `proporcao`.
Demoável assim que a primeira aparece no catálogo.

**Fatia 2 — desfecho em % por ambiente (6.f).** 2 entradas, uma função nova.
Eixo X = os sete desfechos, eixo Y = `"Percentual de desfechos (%)"`. Recorte por
`ambiente` da inclusão, não por `tramitacao` — T6 continua sendo o por tramitação.
Reusar `_barras_grupo:158`, que já trata `proporcao` de verdade.

**Fatia 3 — seis linhas temporais (6.b2 e 6.b3).** 1 função, 6 entradas.
`linha_decisao(df, agrupamento, ambiente)` com dois agrupamentos × três âmbitos.
Não existe função de série temporal de duas séries agregadas no repo — esta é nova.
Mas **não construir um gráfico de linha à mão**: montar como barras agrupadas e
declarar `tipos=("linha", "barra")`, deixando `visual.tema.converter_tipo` fazer a
conversão. É o mecanismo que já serve as outras páginas.

Strings de desfecho verbatim (note "decisão maioria", sem "por", e a vírgula):
```
Concluído - decisão unânime
Concluído - decisão maioria com o relator
Concluído - decisão maioria, vencido o relator
```

**Fatia 4 — 7.a e 7.b.** Bloqueadas pela #5. Se ela não entregar, construir com o
período disponível e nota visível no subtítulo.

**Seams de teste.** As funções de plot são puras (`plots.py` não importa Streamlit) —
testar chamando direto e afirmando sobre os traces. TDD real: escrever a asserção de
que `excluir_nc=True` remove a categoria de não concluído **antes** de implementar.

**Verificação antes de concluir.**
- `pages/test_conformidade.py` cobre as entradas novas automaticamente (varre os
  catálogos), incluindo fonte, tamanhos, tickangle, paleta e formato numérico.
- Teste específico: para cada entrada com `percentual=True`, alternar `proporcao`
  **muda** os valores dos traces. Trava o parâmetro morto de voltar.
- `AppTest` numa página, uma instância por cenário (segunda `.run()` segfalha nesta venv).

---

## Issue #6 — portar os 17 gráficos empíricos

**Objetivo.** As páginas temáticas passam a ter os gráficos que só existem nos Blocos
Empíricos, sem duplicar código e sem tocar nos blocos.

**A restrição que define o desenho.** Medido, não presumido:

| Cenário | Resultado |
|---|---|
| `fig_2c` com a casca filtrando 2021–2023 | 0 pontos, gráfico vazio em silêncio |
| `fig_1c` com período 2021–2025 | `ValueError: '2019' is not in list` |

Os gráficos filtram o ano por dentro (`df["ano"].between(2016, 2019)` em `fig_2c:194`,
`fig_2d:229`, `fig_2i:361`, `fig_2j2:409`, `fig_2k1:446`, `fig_2l2:486`, `fig_31*`,
`fig_32*`) e o bloco 1 posiciona marcadores ER com `_frac_ano(ANO_MIN=1988, ...)`
(`plots.py:232`, `:327`, `:396`, `:463`) mais `anos.index(str(ano_er))`, que levanta
quando o ano some do recorte.

**Abordagem (decidida com o usuário).** Entradas portadas declaram `filtros=()` e
recebem o dataframe completo por closure, ignorando o recorte da casca. Nenhum controle
inerte aparece. O período fixo é parte da identidade desses gráficos — "composição
2016–2019" deixa de ser esse gráfico se o ano virar variável.

**Fatias verticais**, uma por página de destino, cada uma demoável:
1. **Acervo** — 9 entradas do bloco 1 (1.a, 1.a.2, 1.b, 1.b2, 1.b3, 1.b4, 1.c, 1.d, 1.d.2)
2. **Inclusões** — 7 do bloco 2 (2.a.2, 2.c, 2.d, 2.j2, 2.k1, 2.l.2, 2.n.3)
3. **Tramitação** — 4 do bloco 2 (2.i, 3.1, 3.1-alt, 3.2-alt)

**Cuidados verificados no mapeamento.**
- `fig_2n3_motivos_diversos_pp:719` tem números fixos no código e ignora o `df`. Já está
  marcada com `ponytail:`. Portar como está; não é regressão nova.
- HTML inline (`<span style='font-size:20px'>`) em vários rótulos. `visual.tema
  .limpar_html_de_fonte` foi feito na Fase 1 para isto — confirmar figura a figura, não
  presumir.
- Bloco 2 espera `tipo_questao` já com `IJ → QI` aplicado pelo chamador.

**Verificação antes de concluir.**
- **Portão dos blocos:** `git diff --stat -- app/pages/bloco*/` vazio, e o JSON das 38
  figuras dos blocos idêntico antes e depois. O padrão já foi usado na Fase 1.
- Cada figura portada passa por `converter_tipo` + `aplicar_tema` sem exceção, com o
  portão de conformidade cobrindo estilo.
- Teste explícito de que nenhuma entrada portada declara `periodo` em `filtros` — é a
  regra que impede o crash voltar.

---

## Issue #7 — tela inicial e revisão dos textos

**Fatia 1 — tela inicial.** `app/pages/home/`, registrada como primeira página em
`app/app.py` e default. Conteúdo: o que é o dashboard, como usar filtros, alternância
de forma e tabulador; link do repositório; link do dataset
(`JoaoBoscoooo/plenario_virtual`); espaço marcado para vídeo e para contribuidores, a
preencher manualmente. Sem gráfico — não entra no catálogo nem no portão.

**Fatia 2 — títulos que descrevem o eixo.** Escopo decidido: varrer as ~66 entradas de
catálogo, listar as que descrevem o eixo em vez de afirmar o achado, e reescrever essas.
Cada número citado num título conferido contra o dado, não estimado.

Distribuição atual: Inclusões 19, Sessões Virtuais 14, Tramitação 13, Reajuste 6,
Sustentação 6, Narrativa 6, Acervo 2 (mais as portadas pela #6, que entram nesta conta).

**Fatia 3 — pendências herdadas da Fase 1.**
- **Rampa ordinal das faixas de sessão.** `app/visual/paleta.py:126` tem um `ponytail:`
  marcando que os quatro degraus nunca passaram pelo validador de daltonismo. O script
  da skill `dataviz` não está disponível no ambiente agora — recuperar a skill ou
  validar por outro meio antes de tirar a marca.
- **Verificação visual em navegador.** Nunca feita por agente. Fonte renderizando de
  fato, contraste do modo noturno e colisão de rótulos de ano continuam por conferir.
- **8 minors adiados** no ledger (`.superpowers/sdd/2026-08-09-.../progress.md`), para
  triagem: quais valem consertar, quais viram nota. Dois já são moot (o das pizzas do
  G26/G27 foi resolvido pela Fase 2).

---

## Issue #5 — pipeline até 2009 (isolada, por último)

**Objetivo.** Destravar 7.a (PP 2009–2019) e 7.b (PP+PV 2010–2025).

**Procedimento, sem pular etapa:**
1. `ANO_INI = 2009` em `src/inclusao_pauta.py:7`.
2. **Portão de regressão:** 2016–2025 tem que bater exatamente com o parquet atual.
   `scripts/reprocessar_inclusoes.py` já compara os dois parquets e roda a cadeia
   derivada — estender para a mudança de janela.
3. **Inspeção de amostra 2009–2015** contra o texto de origem. O extrator de sufixo foi
   corrigido, mas as convenções de texto pré-2016 podem ser outras. O Plenário Virtual
   só existe desde 2007 e a primeira ampliação relevante é de 2010: é regime antigo,
   volume baixo, formato diferente.
4. Só então publicar e construir 7.a e 7.b.

**Critério de parada.** Se o passo 3 mostrar que a classificação pré-2016 não se
sustenta, parar e reportar com números. 7.a e 7.b ficam com o período disponível.

**Verificação.** Mesmo portão da #2, que já provou pegar problema real: ele barrou o
acréscimo de sessões e obrigou decisão explícita.

---

## Riscos e decisões em aberto

**O dado pré-2016 pode não prestar (#5).** É o risco principal e está isolado por
desenho — falha ali não trava mais nada.

**A #6 entrega gráficos que não respondem aos controles.** Consequência aceita da
decisão de reusar por import. Se a Pessoa 2 reclamar que eles não filtram como os
outros, a saída é a opção descartada: copiar e adaptar nas páginas de destino, ao custo
de ~2.000 linhas duplicadas.

**Sem validador de daltonismo no ambiente.** O diretório da skill `dataviz` sumiu. A
rampa das faixas de sessão fica com a marca `ponytail:` até haver como revalidar.

**Verificação visual continua sem cobertura automatizada.** `AppTest` e o portão de
conformidade cobrem estrutura, não aparência. Os achados de fonte, `6k` no eixo e eixo
esticado vieram do usuário olhando a tela — esse canal continua sendo o único.

**Convenção do pedido não existe.** Não há `CONTEXT.md`. Uso `docs/CONTEXTO_DADOS.md`
e `app/PROJECT_STRUCTURE.md` como glossário; se houver um `CONTEXT.md` pretendido em
outro lugar, isso muda a nomenclatura do código novo.

---

## Verificação de ponta a ponta

Ao fim de cada fatia, e obrigatoriamente antes de fechar cada issue:

```bash
# suíte completa — 13 arquivos no app + o do pipeline
cd app && for f in $(find . -name "test_*.py" | sort); do
  PYTHONPATH=. ../.venv/bin/python "$f"
done
cd .. && PYTHONPATH=. .venv/bin/python src/tests/test_inclusao_pauta.py

# blocos empíricos intocados (crítico na #6)
git diff --stat -- app/pages/bloco1_acervo app/pages/bloco2_inclusoes app/pages/bloco3_pandemia

# app sobe e responde
.venv/bin/streamlit run app/app.py --server.port 8501 --server.headless true
curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8501/
```

`app/pages/test_conformidade.py` é o portão que importa: varre toda figura de todo
catálogo em todas as formas declaradas e afirma fonte, escala de tamanhos, tickangle,
ausência de "Plenário Físico", ausência de pizza, cor vinda da paleta e formatação
numérica brasileira. Entrada nova entra nele automaticamente.

**Verificação humana, que os testes não cobrem:** abrir o dashboard e conferir os
gráficos novos em modo claro e escuro, com atenção a colisão de rótulos nos que têm
muitas categorias.

---
