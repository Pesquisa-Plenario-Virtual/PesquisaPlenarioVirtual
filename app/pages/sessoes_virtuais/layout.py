"""Renderização da página de Sessões Virtuais."""

from __future__ import annotations
import streamlit as st
import pandas as pd
from components.catalogo import render_pagina
from components.grafico import GraficoSpec
from components.tabulador import render_tabulador
from .plots import (
    g0_sessoes_vs_inclusoes,
    g3_1_distribuicao_sessoes, g3_2_faixa_sessoes_classe,
    g3_3_taxa_conclusao_primeira, g3_4_taxa_conclusao_posicao,
    g4_2_sessoes_classe_tipo, g4_3_macro_ano_tipo,
    g4_4_macro_ano_classe, g4_5_taxa_conclusao_classe_tipo,
    g5_1_distribuicao_duracao, g5_2_duracao_mediana_classe,
    g5_3_duracao_mediana_tipo,
    prep_duracao,
)
from pages.tramitacao.plots import gt10_tabulador

_DIMS_SV = {
    "Classe":           "classe",
    "Tipo de questão":  "tipo_questao",
    "Macro-desfecho":   "macro_desfecho",
    "Desfecho detalhado": "desfecho",
    "Ano":              "ano",
    "Relator":          "relator",
}

_PREDEFINIDOS = [
    ("Ano × Classe (sessões, agrupado)",              "ano",      "classe",         "sessoes", "group"),
    ("Ano × Tipo (sessões, agrupado)",                "ano",      "tipo_questao",   "sessoes", "group"),
    ("Ano × Macro-desfecho (sessões, empilhado)",     "ano",      "macro_desfecho", "sessoes", "stack"),
    ("Classe × Tipo (sessões, agrupado)",             "classe",   "tipo_questao",   "sessoes", "group"),
    ("Classe × Macro-desfecho (sessões, 100%)",       "classe",   "macro_desfecho", "sessoes", "100%"),
    ("Classe × Desfecho (sessões, agrupado)",         "classe",   "desfecho",       "sessoes", "group"),
    ("Relator × Classe (sessões, agrupado)",          "relator",  "classe",         "sessoes", "group"),
    ("Relator × Macro-desfecho (sessões, agrupado)",  "relator",  "macro_desfecho", "sessoes", "group"),
]


def _dims_disponiveis(colunas) -> dict[str, str]:
    """Subconjunto de _DIMS_SV cujas colunas existem em `colunas`.

    Mesmo raciocínio de dados.filters.dimensoes_disponiveis, mas aplicado a
    _DIMS_SV — o dicionário de dimensões desta página, não ao DIMENSOES
    compartilhado com Tramitação/Inclusões/Reajuste/Sustentação (que tem
    colunas, como "tramitacao", que sessoes_virtuais.parquet não tem).
    """
    disponiveis = set(colunas)
    return {label: col for label, col in _DIMS_SV.items() if col in disponiveis}


def _montar_catalogo(df_final: pd.DataFrame) -> list[GraficoSpec]:
    """Monta o catálogo com `df_final` (inclusões em pauta) capturado por closure.

    A casca chama spec.fn(df, **kwargs) com um único dataframe (df_s). G0 e o
    Bloco 5 (G5.1-G5.3) precisam também de df_final — G0 para comparar sessões
    com inclusões, o Bloco 5 para prep_duracao calcular a data da primeira
    pauta. Os wrappers do Bloco 5 declaram `ambiente` na assinatura para a
    casca oferecer o seletor de âmbito (ver GraficoSpec.filtros abaixo).
    """

    def _g0(df_s, show_values=True, **kw):
        return g0_sessoes_vs_inclusoes(df_s, df_final, show_values=show_values)

    def _g5_1(df_s, show_values=True, ambiente="Plenário Virtual", **kw):
        return g5_1_distribuicao_duracao(prep_duracao(df_s, df_final, ambiente), show_values)

    def _g5_2(df_s, show_values=True, ambiente="Plenário Virtual", **kw):
        return g5_2_duracao_mediana_classe(prep_duracao(df_s, df_final, ambiente), show_values)

    def _g5_3(df_s, show_values=True, ambiente="Plenário Virtual", **kw):
        return g5_3_duracao_mediana_tipo(prep_duracao(df_s, df_final, ambiente), show_values)

    # Opções reais do seletor de âmbito do Bloco 5: df_s (sessões) só tem
    # "Plenário Virtual", então a casca (que deriva opções do dataframe que
    # recebe) nunca ofereceria "Plenário Presencial". A opção que importa
    # vive em df_final — declarada via GraficoSpec.opcoes_filtro nas três
    # entradas do Bloco 5, abaixo.
    opcoes_ambiente = (sorted(df_final["ambiente"].dropna().unique().tolist())
                       if "ambiente" in df_final.columns else ["Plenário Virtual"])

    return [
        GraficoSpec(
            id="G0",
            rotulo="G0 — Sessões virtuais vs Inclusões em pauta (PV)",
            subtitulo="Sessões Virtuais vs Inclusões em Pauta (PV)",
            descricao="Comparação anual entre o volume de sessões virtuais iniciadas e o total de "
                      "inclusões em pauta no Plenário Virtual.",
            fn=_g0,
            tipos=("barra", "linha"),
        ),
        GraficoSpec(
            id="G3.1",
            rotulo="G3.1 — Distribuição de sessões por processo",
            subtitulo="Distribuição de Sessões por Processo",
            descricao="Quantos processos tiveram 1, 2–3, 4–5 ou 6+ sessões virtuais.",
            fn=g3_1_distribuicao_sessoes,
            tipos=("barra", "linha"),
            filtros=("classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G3.2",
            rotulo="G3.2 — Faixa de sessões por classe",
            subtitulo="Número de Sessões por Processo e Classe",
            descricao="Distribuição das faixas de sessões por classe processual.",
            fn=g3_2_faixa_sessoes_classe,
            tipos=("barra",),
            filtros=("tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G3.3",
            rotulo="G3.3 — Taxa de conclusão: 1ª vs posteriores",
            subtitulo="Taxa de Conclusão: 1ª Sessão vs Sessões Posteriores",
            descricao="Comparação da taxa de conclusão entre a primeira sessão e as sessões seguintes.",
            fn=g3_3_taxa_conclusao_primeira,
            tipos=("barra",),
            filtros=("classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G3.4",
            rotulo="G3.4 — Taxa de conclusão por posição da sessão",
            subtitulo="Taxa de Conclusão por Posição da Sessão",
            descricao="Taxa de conclusão para a 1ª, 2ª, 3ª e 4ª+ sessão no histórico do processo.",
            fn=g3_4_taxa_conclusao_posicao,
            tipos=("barra", "linha"),
            filtros=("classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G4.1",
            rotulo="G4.1 — Classe × Tipo de Questão (quadro de referência)",
            subtitulo="Classe × Tipo de Questão",
            descricao="Barras agrupadas por tipo de questão (PR/RC/QI) com o volume de sessões por "
                      "classe — mesma leitura do G4.2, útil como quadro de referência com totais na tabela.",
            fn=g4_2_sessoes_classe_tipo,
            tipos=("barra",),
            filtros=("periodo",),
        ),
        GraficoSpec(
            id="G4.2",
            rotulo="G4.2 — Sessões por classe e tipo de questão",
            subtitulo="Sessões por Classe e Tipo de Questão",
            descricao="Barras agrupadas por tipo de questão (PR/RC/QI) com o volume de sessões por classe.",
            fn=g4_2_sessoes_classe_tipo,
            tipos=("barra",),
            filtros=("periodo",),
        ),
        GraficoSpec(
            id="G4.3",
            rotulo="G4.3 — Macro-desfecho por ano e tipo de questão",
            subtitulo="Macro-Desfecho por Ano e Tipo de Questão",
            descricao="Barras empilhadas (Concluído/Não concluído) por ano. "
                      "Uma aba por tipo: PR, RC e QI.",
            fn=g4_3_macro_ano_tipo,
            tipos=("barra", "linha"),
            filtros=("classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G4.4",
            rotulo="G4.4 — Macro-desfecho por ano e classe",
            subtitulo="Macro-Desfecho por Ano e Classe (ADI e ADPF)",
            descricao="Barras empilhadas por ano para ADI e ADPF. ADC e ADO omitidos por base pequena.",
            fn=g4_4_macro_ano_classe,
            tipos=("barra", "linha"),
            filtros=("classe", "tipo_questao", "periodo"),
        ),
        GraficoSpec(
            id="G4.5",
            rotulo="G4.5 — Taxa de conclusão: classe × tipo de questão",
            subtitulo="Taxa de Conclusão por Classe e Tipo de Questão",
            descricao="Percentual de sessões concluídas, agrupado por classe e tipo de questão.",
            fn=g4_5_taxa_conclusao_classe_tipo,
            tipos=("barra",),
            filtros=("periodo",),
        ),
        GraficoSpec(
            id="G5.1",
            rotulo="G5.1 — Distribuição de duração até conclusão",
            subtitulo="Tempo até Conclusão",
            descricao="Distribuição do tempo decorrido entre a primeira inclusão em pauta e a sessão de "
                      "conclusão, em faixas. Selecione o âmbito da primeira pauta.",
            fn=_g5_1,
            tipos=("barra", "linha"),
            filtros=("ambiente", "classe", "tipo_questao", "periodo"),
            opcoes_filtro={"ambiente": opcoes_ambiente},
        ),
        GraficoSpec(
            id="G5.2",
            rotulo="G5.2 — Duração mediana por classe",
            subtitulo="Tempo Mediano até Conclusão por Classe (dias)",
            descricao="Mediana de dias entre a primeira pauta e a conclusão, por classe. "
                      "Selecione o âmbito da primeira pauta.",
            fn=_g5_2,
            tipos=("barra",),
            filtros=("ambiente", "tipo_questao", "periodo"),
            opcoes_filtro={"ambiente": opcoes_ambiente},
        ),
        GraficoSpec(
            id="G5.3",
            rotulo="G5.3 — Duração mediana por tipo de questão",
            subtitulo="Tempo Mediano até Conclusão por Tipo de Questão (dias)",
            descricao="Mediana de dias entre a primeira pauta e a conclusão, por tipo. "
                      "Selecione o âmbito da primeira pauta.",
            fn=_g5_3,
            tipos=("barra",),
            filtros=("ambiente", "classe", "periodo"),
            opcoes_filtro={"ambiente": opcoes_ambiente},
        ),
        GraficoSpec(
            id="G6",
            rotulo="G6 — Tabulador interativo (eixos livres)",
            subtitulo="Tabulador interativo — eixos, agrupamento e métrica livres",
            descricao="Configure o eixo X, a cor/grupo, a métrica e o modo de barras. "
                      "A tabela abaixo acompanha os mesmos eixos.",
            fn=None,
            renderer=lambda df, key: _render_interactive_tabulador(df),
        ),
    ]


# ── Tabulador interativo ──────────────────────────────────────────────────────

def _render_interactive_tabulador(df_s: pd.DataFrame, key: str = "sv_tab") -> None:
    render_tabulador(
        df_s, key, _dims_disponiveis(df_s.columns), _PREDEFINIDOS,
        metricas={"sessoes": "Sessões", "processos": "Processos distintos"},
        titulo_y={"sessoes": "Nº de sessões"},
    )


# ── Renderização principal ────────────────────────────────────────────────────

def render_graficos(df_s: pd.DataFrame, df_final: pd.DataFrame) -> None:
    render_pagina(_montar_catalogo(df_final), df_s, key_prefix="sv")
