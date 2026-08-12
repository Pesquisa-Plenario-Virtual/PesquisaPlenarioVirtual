"""Camada visual do dashboard: cor, tipografia e mobiliário de gráfico.

São três módulos porque são três papéis distintos, não por acidente:

- `paleta` — qual cor cada variável do domínio tem. Sem Plotly, sem Streamlit:
  é um dicionário semântico validado para daltonismo em modo claro e escuro.
  Responde "de que cor é o Plenário Virtual", não "como desenhar".

- `tema` — o que fazer com uma figura já construída. Percorre a figura pronta e
  impõe fonte, tamanhos, ângulo de tick, rótulo canônico e cor da paleta. É o
  que permite padronizar ~90 gráficos sem editar ~90 funções, e o que o
  alternador de tema liga e desliga.

- `base` — o mobiliário de domínio que as figuras usam enquanto são
  construídas: marcadores de Emenda Regimental e do período da ESPIN,
  formatação numérica brasileira, e o layout de referência. Não é legado: os
  Blocos Empíricos e as oito páginas temáticas consomem daqui.

A ordem de uso é: a função de gráfico monta a figura usando `base`, e a casca
passa o resultado por `tema`, que consulta `paleta`.

As páginas devem importar deste pacote, não dos módulos internos.
"""

from visual.base import (
    ER_DATAS,
    ESPIN_FIM,
    ESPIN_INICIO,
    add_er_marker,
    add_espin_shade,
    aplicar_padrao,
    br,
)
from visual.paleta import CINZA_OUTROS, CORES, canonico, conhecido, cor, cores, sentence_case
from visual.tema import (
    FONTE,
    TAMANHOS,
    TIPOS,
    aplicar_tema,
    converter_tipo,
    limpar_html_de_fonte,
    texto_numerico_br,
)

__all__ = [
    # paleta — cor por valor semântico
    "CORES", "CINZA_OUTROS", "cor", "cores", "canonico", "conhecido", "sentence_case",
    # tema — pós-processamento da figura pronta
    "FONTE", "TAMANHOS", "TIPOS", "aplicar_tema", "converter_tipo",
    "limpar_html_de_fonte", "texto_numerico_br",
    # base — mobiliário de domínio
    "aplicar_padrao", "br", "add_er_marker", "add_espin_shade",
    "ER_DATAS", "ESPIN_INICIO", "ESPIN_FIM",
]
