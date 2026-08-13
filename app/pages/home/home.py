"""Página inicial: apresenta o dashboard, sem gráfico.

Fora do catálogo e do portão de conformidade — só texto.
"""

import streamlit as st

st.title("Plenário Virtual do STF — Painel Interativo")

st.markdown(
    """
Este painel analisa a evolução do **Plenário Virtual** do Supremo Tribunal Federal
no julgamento de processos de Controle Concentrado (ADI, ADC, ADO e ADPF),
entre **2016 e 2025**.

É a contraparte interativa da série *Plenário Virtual: a máquina de julgamentos
do STF*, que documenta os dados e a metodologia por trás dos gráficos.
"""
)

st.header("O que você encontra aqui")

st.markdown(
    """
- **Inclusões em Pauta** — o que entrou na pauta do Plenário Virtual e do
  Plenário Presencial, por ano, classe, tipo de questão e desfecho.
- **Tramitação por Ambiente** — em quais ambientes cada processo tramitou
  (só virtual, só presencial ou ambos) e como isso se relaciona com os resultados.
- **Sessões Virtuais** — duração, distribuição e taxa de conclusão das sessões
  de julgamento virtual.
- **Acervo Histórico** — evolução do acervo e das baixas desde 1988.
- **Reajuste de Voto, Sustentação Oral e Narrativa** — recortes específicos de
  cada mecanismo de julgamento.
- **Blocos Empíricos** — as figuras originais da série, reproduzidas como estavam.
"""
)

st.header("Como usar")

st.markdown(
    """
- **Filtros** no menu lateral para recortar por período, classe, tipo de questão
  e ambiente. Todo gráfico responde aos filtros.
- **Alternância de forma** em cada gráfico: barras, barras horizontais ou linha.
- **Tabulador interativo** em cada seção, para cruzar livremente as dimensões e
  extrair os números exatos.
- **Tema dos gráficos** no menu lateral: *novo padrão* ou o visual empírico das
  figuras originais.
"""
)

st.header("Fontes")

st.markdown(
    """
- Código: [JoaoBoscoooo/plenario_virtual](https://github.com/JoaoBoscoooo/plenario_virtual)
- Dados e metodologia: série *Plenário Virtual: a máquina de julgamentos do STF*.
"""
)

st.markdown(
    """
---
*Espaço reservado para vídeo de demonstração e para a lista de contribuidores.*
"""
)
