"""Renderização da página de Inclusões em Pauta."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from components.tabulador import render_tabulador
from .plots import (
    g5_anual_ambiente, g6_classe_filtravel, g8_desfecho_filtravel,
    g10_macro_anual_filtravel, g12_concluidos_filtravel,
    g14_nao_concluidos_classe_filtravel, g16_concluidos_classe_filtravel,
    g18_nc_tipo_filtravel, g20_c_tipo_filtravel,
    g22_cat_periodo_filtravel, g24_cat_anual_filtravel,
    g26_cat_tipo_periodo_filtravel, g28_cat_tipo_anual_filtravel,
    g30_nc_cat_anual_filtravel, g32_nc_cat_classe_filtravel,
    g34_nc_cat_tipo_filtravel, g7a_desfechos_pp_2009_2019,
    g6f_desfecho_percentual_ambiente, linha_decisao,
    _refinar_motivos_diversos,
    g_pauta_concluidos,
    g7b_unanimidade_vs_divergencia_2010_2025,
)
from pages.tramitacao.plots import gt10_tabulador
from dados.filters import dimensoes_disponiveis
from pages.bloco2_inclusoes.plots import (
    fig_2a2_participacao_ano_marcos, fig_2c_composicao_pv_tipo,
    fig_2d_composicao_pv_tipo_2020, fig_2j2_recursos_2016,
    fig_2k1_tipo_ambiente_2016, fig_2l2_pauta_vs_concluidos,
    fig_2n3_motivos_diversos_pp,
)


def _portar_bloco2(fn):
    """Fecha sobre uma função do Bloco 2 para a casca.

    Aplica a convenção do chamador do Bloco 2 (tipo_questao já com IJ→QI) e
    ignora o recorte da casca — o período é fixo dentro da função e qualquer
    recorte devolveria gráfico vazio ou KeyError em silêncio.
    """
    def _wrap(df: pd.DataFrame, show_values: bool = True):
        d = df.assign(tipo_questao=df["tipo_questao"].replace({"IJ": "QI"}))
        return fn(d, show_values=show_values)
    return _wrap


_PREDEFINIDOS_TAB = [
    ("Ano × Ambiente (inclusões, agrupado)",           "ano",      "ambiente",       "inclusoes", "group"),
    ("Ano × Classe (inclusões, empilhado)",            "ano",      "classe",         "inclusoes", "stack"),
    ("Ano × Tipo de Questão (inclusões, agrupado)",    "ano",      "tipo_questao",   "inclusoes", "group"),
    ("Ambiente × Classe (inclusões, agrupado)",         "ambiente", "classe",         "inclusoes", "group"),
    ("Ambiente × Macro-Desfecho (inclusões, 100%)",    "ambiente", "macro_desfecho", "inclusoes", "100%"),
    ("Classe × Macro-Desfecho (inclusões, agrupado)",   "classe",   "macro_desfecho", "inclusoes", "group"),
    ("Classe × Desfecho Detalhado (inclusões)",         "classe",   "desfecho",       "inclusoes", "group"),
    ("Tipo de Questão × Macro-Desfecho (inclusões)",    "tipo_questao", "macro_desfecho", "inclusoes", "group"),
    ("Tipo de Questão × Desfecho Detalhado (inclusões)","tipo_questao", "desfecho",     "inclusoes", "group"),
]

# ── Catálogo I1–I40 ──────────────────────────────────────────────────────────
_CATALOGO: list[GraficoSpec] = [
    # ── Inclusões em Pauta ────────────────────────────────────────────────────
    GraficoSpec(
        id="I1",
        rotulo="I1 — Inclusões por Ano e Ambiente (Plenário Virtual vs Plenário Presencial)",
        subtitulo="Plenário Virtual assume a dianteira da pauta a partir de 2020",
        descricao="Comparação anual do volume de inclusões em pauta entre o Plenário Virtual e o Plenário Presencial. "
                  "Inclui a composição PV vs PP no período, em barra horizontal com o percentual na ponta.",
        fn=g5_anual_ambiente,
        tipos=("barra", "linha"),
        filtros=("classe", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="I2",
        rotulo="I2 — Inclusões por Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="ADI concentra as inclusões em todos os âmbitos",
        descricao="Barras agrupadas por classe (ADI, ADPF, ADC, ADO) com linha do total geral no eixo secundário. "
                  "Selecione o âmbito (Plenário Virtual / Plenário Presencial) e filtre as classes desejadas. "
                  "Inclui a composição por classe no período, em barra horizontal com o percentual na ponta.",
        fn=g6_classe_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "tipo_questao", "periodo"),
    ),
    GraficoSpec(
        id="I3",
        rotulo="I3 — Desfecho Geral (Plenário Virtual e Plenário Presencial)",
        subtitulo="Três de cada cinco inclusões concluem, e a unanimidade é o desfecho dominante",
        descricao="Composição de concluídos e não concluídos em barra horizontal, mais desfecho detalhado (PV) "
                  "ou apenas macro (Plenário Presencial). Selecione o âmbito.",
        fn=g8_desfecho_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao"),
    ),
    GraficoSpec(
        id="I4",
        rotulo="I4 — Macro-Desfecho Anual (Plenário Virtual e Plenário Presencial)",
        subtitulo="Inclusões concluídas superam as não concluídas em quase todos os anos",
        descricao="Evolução anual do volume de inclusões concluídas e não concluídas. Selecione o âmbito.",
        fn=g10_macro_anual_filtravel,
        tipos=("barra", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="I5",
        rotulo="I5 — Concluídos por Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Conclusões crescem até 2020 e recuam depois",
        descricao="Fluxo anual de inclusões com desfecho concluído. Selecione o âmbito.",
        fn=g12_concluidos_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="I6",
        rotulo="I6 — Concluídos por Ano, segmentado por desfecho (Plenário Virtual e Plenário Presencial)",
        subtitulo="Unanimidade responde pela maior parte das conclusões em todos os anos",
        descricao="Fluxo anual de inclusões concluídas, segmentado por unânime, maioria com o relator "
                  "ou maioria vencido o relator. Selecione o âmbito.",
        fn=g12_concluidos_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
        kwargs_fixos={"segmentar": True},
    ),
    GraficoSpec(
        id="I7",
        rotulo="I7 — Não Concluídos por Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="ADI também concentra as inclusões não concluídas",
        descricao="Barras por classe com linha do total de não concluídos. Selecione o âmbito.",
        fn=g14_nao_concluidos_classe_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="I8",
        rotulo="I8 — Concluídos por Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="ADI também concentra as inclusões concluídas",
        descricao="Barras por classe com linha do total de concluídos. Selecione o âmbito.",
        fn=g16_concluidos_classe_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "tipo_questao", "periodo"),
        percentual=True,
    ),
    # ── Tipo de Questão ───────────────────────────────────────────────────────
    GraficoSpec(
        id="I9",
        rotulo="I9 — Não Concluídos por Tipo de Questão (Plenário Virtual e Plenário Presencial)",
        subtitulo="PR responde pela maior parte das inclusões não concluídas",
        descricao="Barras por tipo de questão (PR / RC / QI) com linha do total de não concluídos. "
                  "IJ renomeado para QI na exibição. Selecione o âmbito.",
        fn=g18_nc_tipo_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="I10",
        rotulo="I10 — Concluídos por Tipo de Questão (Plenário Virtual e Plenário Presencial)",
        subtitulo="PR também responde pela maior parte das conclusões",
        descricao="Barras por tipo de questão (PR / RC / QI) com linha do total de concluídos. Selecione o âmbito.",
        fn=g20_c_tipo_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "periodo"),
        percentual=True,
    ),
    # ── Desfecho Concluído por Categoria ─────────────────────────────────────
    GraficoSpec(
        id="I11",
        rotulo="I11 — Categoria de Desfecho (Plenário Virtual e Plenário Presencial)",
        subtitulo="Unanimidade é a categoria mais frequente; não concluído vem logo atrás",
        descricao="Barra horizontal com as 4 categorias, percentual na ponta: Unânime, Maioria (relator vencedor), Maioria (relator vencido) "
                  "e Não concluído (bloco agregado). Selecione o âmbito.",
        fn=g22_cat_periodo_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao"),
        percentual=True,
    ),
    GraficoSpec(
        id="I12",
        rotulo="I12 — Categoria de Desfecho sem não concluído (Plenário Virtual e Plenário Presencial)",
        subtitulo="Entre os concluídos, a unanimidade domina com folga",
        descricao="Mesma barra horizontal do I11 com as três categorias de desfecho concluído — "
                  "o balde de não concluído sai. Selecione o âmbito.",
        fn=g22_cat_periodo_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao"),
        percentual=True,
        kwargs_fixos={"excluir_nc": True},
    ),
    GraficoSpec(
        id="I13",
        rotulo="I13 — Categoria de Desfecho por Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Unanimidade cresce com a universalização do PV e se consolida em primeiro",
        descricao="Evolução anual das 4 categorias de desfecho. Selecione o âmbito.",
        fn=g24_cat_anual_filtravel,
        tipos=("barra", "barra_h", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="I14",
        rotulo="I14 — Categoria de Desfecho por Ano sem não concluído (Plenário Virtual e Plenário Presencial)",
        subtitulo="Entre os concluídos, a unanimidade cresce e se consolida em primeiro",
        descricao="Mesma evolução anual do I13 com as três categorias de desfecho concluído. Selecione o âmbito.",
        fn=g24_cat_anual_filtravel,
        tipos=("barra", "barra_h", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
        kwargs_fixos={"excluir_nc": True},
    ),
    GraficoSpec(
        id="I15",
        rotulo="I15 — Categoria × Tipo de Questão (Plenário Virtual e Plenário Presencial)",
        subtitulo="Em PR e QI o não concluído supera a unanimidade; só em RC a unanimidade lidera",
        descricao="Uma barra horizontal por tipo de questão (PR/RC/QI) com as 4 categorias de desfecho. Período total. "
                  "Processos sem tipo de questão classificados como PR. Selecione o âmbito.",
        fn=g26_cat_tipo_periodo_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao"),
        percentual=True,
    ),
    GraficoSpec(
        id="I16",
        rotulo="I16 — Categoria × Tipo de Questão sem não concluído (Plenário Virtual e Plenário Presencial)",
        subtitulo="Unanimidade lidera as conclusões em todos os tipos de questão",
        descricao="Uma barra horizontal por tipo de questão (PR/RC/QI) com as três categorias de desfecho concluído. "
                  "Período total. Selecione o âmbito.",
        fn=g26_cat_tipo_periodo_filtravel,
        tipos=("barra",),
        filtros=("ambiente", "classe", "tipo_questao"),
        percentual=True,
        kwargs_fixos={"excluir_nc": True},
    ),
    GraficoSpec(
        id="I17",
        rotulo="I17 — Categoria × Tipo de Questão por Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Unanimidade cresce em todos os tipos de questão com a universalização do PV",
        descricao="Um gráfico por tipo de questão (PR, RC, QI) mostrando a evolução anual das categorias. "
                  "Selecione o âmbito e o tipo na aba.",
        fn=g28_cat_tipo_anual_filtravel,
        tipos=("barra", "barra_h", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="I18",
        rotulo="I18 — Categoria × Tipo de Questão por Ano sem não concluído (Plenário Virtual e Plenário Presencial)",
        subtitulo="Entre os concluídos, a unanimidade cresce em todos os tipos de questão",
        descricao="Um gráfico por tipo de questão (PR, RC, QI) com a evolução anual das três categorias de desfecho "
                  "concluído. Selecione o âmbito e o tipo na aba.",
        fn=g28_cat_tipo_anual_filtravel,
        tipos=("barra", "barra_h", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
        kwargs_fixos={"excluir_nc": True},
    ),
    GraficoSpec(
        id="I19",
        rotulo="I19 — Desfecho por Percentual — Plenário Virtual",
        subtitulo="No PV, a unanimidade é quase metade dos desfechos (43%)",
        descricao="Os sete desfechos como percentual do total de desfechos do Plenário Virtual. "
                  "Escala única, sem toggle: cada barra é fração do total do âmbito.",
        fn=g6f_desfecho_percentual_ambiente,
        tipos=("barra",),
        filtros=(),
        kwargs_fixos={"ambiente": "Plenário Virtual"},
    ),
    GraficoSpec(
        id="I20",
        rotulo="I20 — Desfecho por Percentual — Plenário Presencial",
        subtitulo="No PP, 'motivos diversos' concentra três quartos dos desfechos (76%)",
        descricao="Os sete desfechos como percentual do total de desfechos do Plenário Presencial. "
                  "Escala única, sem toggle: cada barra é fração do total do âmbito.",
        fn=g6f_desfecho_percentual_ambiente,
        tipos=("barra",),
        filtros=(),
        kwargs_fixos={"ambiente": "Plenário Presencial"},
    ),
    GraficoSpec(
        id="I21",
        rotulo="I21 — Unânime vs Divergência — Plenário Virtual",
        subtitulo="Unanimidade domina a divergência no PV a partir de 2019",
        descricao="Linha temporal de decisões unânimes contra divergentes (maioria com ou vencido o relator), "
                  "ano a ano, no Plenário Virtual. Período fixo do dado.",
        fn=linha_decisao,
        tipos=("linha", "barra"),
        filtros=(),
        kwargs_fixos={"agrupamento": "unânime_vs_divergência", "ambiente": "Plenário Virtual"},
    ),
    GraficoSpec(
        id="I22",
        rotulo="I22 — Unânime vs Divergência — Plenário Presencial",
        subtitulo="No PP, a divergência oscila perto da unanimidade",
        descricao="Linha temporal de decisões unânimes contra divergentes (maioria com ou vencido o relator), "
                  "ano a ano, no Plenário Presencial. Período fixo do dado.",
        fn=linha_decisao,
        tipos=("linha", "barra"),
        filtros=(),
        kwargs_fixos={"agrupamento": "unânime_vs_divergência", "ambiente": "Plenário Presencial"},
    ),
    GraficoSpec(
        id="I23",
        rotulo="I23 — Unânime vs Divergência — Ambos os ambientes",
        subtitulo="Unanimidade domina a divergência nos dois ambientes somados",
        descricao="Linha temporal de decisões unânimes contra divergentes (maioria com ou vencido o relator), "
                  "ano a ano, nos dois ambientes somados. Período fixo do dado.",
        fn=linha_decisao,
        tipos=("linha", "barra"),
        filtros=(),
        kwargs_fixos={"agrupamento": "unânime_vs_divergência", "ambiente": "Ambos os ambientes"},
    ),
    GraficoSpec(
        id="I24",
        rotulo="I24 — Com o relator vs Divergência — Plenário Virtual",
        subtitulo="No PV, a decisão com o relator esmaga a divergência",
        descricao="Linha temporal de decisões que confirmam o relator (unânime ou maioria com ele) contra as que "
                  "divergem (vencido o relator), ano a ano, no Plenário Virtual. Período fixo do dado.",
        fn=linha_decisao,
        tipos=("linha", "barra"),
        filtros=(),
        kwargs_fixos={"agrupamento": "relator_vs_divergência", "ambiente": "Plenário Virtual"},
    ),
    GraficoSpec(
        id="I25",
        rotulo="I25 — Com o relator vs Divergência — Plenário Presencial",
        subtitulo="No PP, a decisão com o relator também é amplamente majoritária",
        descricao="Linha temporal de decisões que confirmam o relator (unânime ou maioria com ele) contra as que "
                  "divergem (vencido o relator), ano a ano, no Plenário Presencial. Período fixo do dado.",
        fn=linha_decisao,
        tipos=("linha", "barra"),
        filtros=(),
        kwargs_fixos={"agrupamento": "relator_vs_divergência", "ambiente": "Plenário Presencial"},
    ),
    GraficoSpec(
        id="I26",
        rotulo="I26 — Com o relator vs Divergência — Ambos os ambientes",
        subtitulo="Decisão com o relator domina a divergência em todo o período",
        descricao="Linha temporal de decisões que confirmam o relator (unânime ou maioria com ele) contra as que "
                  "divergem (vencido o relator), ano a ano, nos dois ambientes somados. Período fixo do dado.",
        fn=linha_decisao,
        tipos=("linha", "barra"),
        filtros=(),
        kwargs_fixos={"agrupamento": "relator_vs_divergência", "ambiente": "Ambos os ambientes"},
    ),
    # ── Desfecho Não Concluído por Categoria ──────────────────────────────────
    GraficoSpec(
        id="I27",
        rotulo="I27 — Não Concluídos por Categoria e Ano (Plenário Virtual e Plenário Presencial)",
        subtitulo="Pedido de vista e retirada de pauta concentram as não conclusões",
        descricao="Evolução anual das 4 categorias de não conclusão: Pedido de vista, Destaque, "
                  "Retirado de pauta e Motivos diversos. Selecione o âmbito.",
        fn=g30_nc_cat_anual_filtravel,
        tipos=("barra", "barra_h", "linha"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="I28",
        rotulo="I28 — Não Concluídos por Categoria e Classe (Plenário Virtual e Plenário Presencial)",
        subtitulo="Nas classes dominantes, pedido de vista e retirada de pauta lideram as não conclusões",
        descricao="Um gráfico por classe (ADI, ADPF, ADC, ADO) com as categorias de não conclusão. "
                  "Selecione o âmbito e a classe na aba.",
        fn=g32_nc_cat_classe_filtravel,
        tipos=("barra", "barra_h"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    GraficoSpec(
        id="I29",
        rotulo="I29 — Não Concluídos por Categoria e Tipo (Plenário Virtual e Plenário Presencial)",
        subtitulo="Em PR, retirada de pauta e pedido de vista dominam as não conclusões",
        descricao="Um gráfico por tipo de questão (PR, RC, QI) com as categorias de não conclusão. "
                  "Selecione o âmbito e o tipo na aba.",
        fn=g34_nc_cat_tipo_filtravel,
        tipos=("barra", "barra_h"),
        filtros=("ambiente", "classe", "tipo_questao", "periodo"),
        percentual=True,
    ),
    # ── Pauta vs Concluídos ──────────────────────────────────────────────────
    GraficoSpec(
        id="I30",
        rotulo="I30 — Pauta vs Julgamentos Concluídos (PV, período total)",
        subtitulo="PV: Pauta vs Julgamentos Concluídos",
        descricao="Duas barras do PV no período: participação na pauta e participação nos "
                  "julgamentos concluídos. Contraste que mostra a concentração do PV nas conclusões.",
        fn=g_pauta_concluidos,
        tipos=("barra",),
        filtros=(),
    ),
    # ── 7.a (destravado pela #5) ──────────────────────────────────────────────
    GraficoSpec(
        id="I31",
        rotulo="I31 — Desfechos do Plenário Físico 2009–2019, só concluídos, em %",
        subtitulo="Pré-universalização, poucos desfechos registrados e a unanimidade lidera o que conclui",
        descricao="Desfecho por categoria e ano (só concluídos, em percentual) do Plenário Físico, "
                  "2009–2019 — o período anterior à universalização do Plenário Virtual, destravado "
                  "pela extensão do pipeline. Período fixo do gráfico, sem recorte.",
        fn=g7a_desfechos_pp_2009_2019,
        tipos=("barra",),
        filtros=(),
        percentual=True,
    ),
    GraficoSpec(
        id="I32",
        rotulo="I32 — Unanimidade vs Divergência, PP+PV, 2010–2025, com marcos ER",
        subtitulo="Unanimidade lidera no conjunto; só em 2020 a divergência a supera",
        descricao="Linha temporal de unanimidade contra divergência (maioria com o relator + maioria, "
                  "vencido o relator) somando Plenário Físico e Virtual, 2010–2025, com os marcos "
                  "regimentais ER 51/52 (ER 53 fica de fora do recorte do pedido) e o sombreamento "
                  "ESPIN. Período fixo do gráfico, sem recorte.",
        fn=g7b_unanimidade_vs_divergencia_2010_2025,
        tipos=("linha", "barra"),
        filtros=(),
    ),
    # ── Portados do Bloco 2 (período fixo) ────────────────────────────────────
    # Entradas com filtros=(): a função filtra o ano por dentro e o período é
    # parte da identidade do gráfico — nenhuma entrada portada declara `periodo`.
    GraficoSpec(
        id="I33",
        rotulo="I33 — Participação do PV, com marcos regimentais (2016–2025)",
        subtitulo="PV salta de 4% para 60–68% da pauta após os marcos regimentais",
        descricao="Participação do Plenário Virtual nas inclusões em pauta, ano a ano, com marcos "
                  "ER 51/52/53 e faixa ESPIN. Período fixo do dado, sem recorte.",
        fn=_portar_bloco2(fig_2a2_participacao_ano_marcos),
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="I34",
        rotulo="I34 — Composição do PV por tipo de questão (2016–2019)",
        subtitulo="Pré-universalização, RC domina até 2018 e PR irrompe em 2019",
        descricao="Inclusões em pauta do Plenário Virtual por tipo de questão (PR/RC/QI), 2016–2019. "
                  "Período fixo do dado, sem recorte.",
        fn=_portar_bloco2(fig_2c_composicao_pv_tipo),
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="I35",
        rotulo="I35 — Composição do PV por tipo de questão (2020–2025)",
        subtitulo="Pós-universalização, a pauta do PV passa a ser majoritariamente de PR",
        descricao="Inclusões em pauta do Plenário Virtual por tipo de questão (PR/RC/QI), 2020–2025. "
                  "Período fixo do dado, sem recorte.",
        fn=_portar_bloco2(fig_2d_composicao_pv_tipo_2020),
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="I36",
        rotulo="I36 — Destino das inclusões de recursos (2016–2019)",
        subtitulo="Pré-universalização, mais de 70% dos recursos vão ao virtual",
        descricao="Recursos (RC) incluídos em pauta antes da universalização: virtual contra presencial, "
                  "em número e percentual. Período fixo do dado, sem recorte.",
        fn=_portar_bloco2(fig_2j2_recursos_2016),
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="I37",
        rotulo="I37 — Inclusões por tipo de questão e ambiente (2016–2019)",
        subtitulo="Pré-universalização, PR domina a pauta dos dois ambientes",
        descricao="Composição da pauta por tipo de questão em cada ambiente, em percentual, 2016–2019. "
                  "Período fixo do dado, sem recorte.",
        fn=_portar_bloco2(fig_2k1_tipo_ambiente_2016),
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="I38",
        rotulo="I38 — Pauta e julgamentos concluídos por ambiente (2020–2025)",
        subtitulo="Pós-universalização, PV concentra a pauta e esmaga em conclusões",
        descricao="Inclusões em pauta e julgamentos concluídos, em número e percentual, por ambiente, "
                  "2020–2025. Período fixo do dado, sem recorte.",
        fn=_portar_bloco2(fig_2l2_pauta_vs_concluidos),
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
    GraficoSpec(
        id="I39",
        rotulo="I39 — Motivos diversos do PP (2020–2025)",
        subtitulo="'Motivos diversos' do PP é quase todo pauta sem julgamento na data",
        descricao="Desdobra o 'motivos diversos' dos não concluídos do PP nas 4 subcategorias, "
                  "2020–2025. Período fixo do dado, sem recorte.",
        fn=_portar_bloco2(fig_2n3_motivos_diversos_pp),
        tipos=("barra",),
        filtros=(),
        portada=True,
    ),
]


def _render_interactive_tabulador(df: pd.DataFrame, key: str = "inc_tab") -> None:
    render_tabulador(df, key, dimensoes_disponiveis(df.columns), _PREDEFINIDOS_TAB)


_CATALOGO.append(GraficoSpec(
    id="I40",
    rotulo="I40 — Tabulador interativo (eixos livres)",
    subtitulo="Tabulador interativo — eixos, agrupamento e métrica livres",
    descricao="Configure o eixo X, a cor/grupo, a métrica e o modo de barras. "
              "A tabela abaixo acompanha os mesmos eixos.",
    fn=None,
    renderer=lambda df, key: _render_interactive_tabulador(df),
))

def render_graficos(df: pd.DataFrame, df_dec: pd.DataFrame | None = None) -> None:
    df = _refinar_motivos_diversos(df, df_dec if df_dec is not None else pd.DataFrame())

    render_pagina(_CATALOGO, df, key_prefix="inc")
